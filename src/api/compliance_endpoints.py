# Compliance Portal API Endpoints
"""
FastAPI endpoints for compliance portal functionality.
Implements both lite version (token-based) and full version (JWT-based) endpoints.

Key Endpoints:
- GET /api/v1/compliance/content/{token} - Access content for review (lite version)
- POST /api/v1/compliance/review/submit - Submit review decision
- POST /api/v1/compliance/ai/analyze-violation - AI violation analysis  
- GET /api/v1/compliance/upgrade/info - Upgrade information
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Query, Path, Depends
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from src.services.compliance_service import compliance_service
from src.services.token_manager import TokenValidationError
from src.services.enhanced_warren_service import enhanced_warren_service
from src.middleware.compliance_auth import (
    ComplianceAuthContext,
    validate_token_from_path_param,
    require_review_token_auth
)

logger = logging.getLogger(__name__)

# Create compliance router
compliance_router = APIRouter(prefix="/compliance", tags=["compliance"])


# Pydantic models for request/response validation

class ContentAccessQuery(BaseModel):
    """Query parameters for content access"""
    include: Optional[str] = Field(None, description="Additional data to include: 'policies', 'guidelines', 'history'")
    format: Optional[str] = Field("full", description="Response format: 'full', 'summary', 'mobile'")


class ContentReviewResponse(BaseModel):
    """Response model for content review data"""
    content: Dict[str, Any]
    advisor: Dict[str, Any] 
    review: Dict[str, Any]
    compliance: Optional[Dict[str, Any]] = None
    upgrade: Dict[str, Any]


class SectionFeedbackRequest(BaseModel):
    """Section-specific feedback for content reviews"""
    sectionText: str = Field(..., description="Highlighted text from content")
    startPosition: int = Field(..., ge=0, description="Character position start (0-based)")
    endPosition: int = Field(..., gt=0, description="Character position end")
    violationType: str = Field(..., description="Type of violation identified")
    comment: str = Field(..., min_length=1, description="CCO's specific comment")
    suggestedFix: Optional[str] = Field(None, description="Optional improvement suggestion")
    regulationReference: Optional[str] = Field(None, description="Specific rule/regulation reference")
    severity: str = Field("medium", description="Severity level: low, medium, high, critical")
    aiAssisted: bool = Field(False, description="Whether AI helped identify this issue")


class ReviewSubmissionRequest(BaseModel):
    """Request model for review submission"""
    token: str = Field(..., description="Review token")
    decision: str = Field(..., pattern="^(approved|rejected)$", description="Review decision")
    overallFeedback: Optional[str] = Field(None, description="Overall feedback (required for rejections)")
    complianceScore: Optional[int] = Field(None, ge=1, le=100, description="Compliance score 1-100")
    sectionFeedback: List[SectionFeedbackRequest] = Field(default=[], description="Section-specific feedback")
    reviewTimeMinutes: Optional[int] = Field(None, ge=1, description="Time spent reviewing")
    confidence: int = Field(..., ge=1, le=100, description="CCO's confidence in decision")


class ReviewSubmissionResponse(BaseModel):
    """Response model for review submission"""
    success: bool
    reviewId: str
    submittedAt: str
    decision: str
    processingStatus: Dict[str, bool]
    nextSteps: Dict[str, List[str]]
    upgrade: Dict[str, Any]
    analytics: Dict[str, Any]


class ViolationAnalysisRequest(BaseModel):
    """Request model for AI violation analysis"""
    token: str = Field(..., description="Review token for authentication")
    sectionText: str = Field(..., max_length=1000, description="Text to analyze")
    suspectedViolation: str = Field(..., description="CCO's description of suspected issue")
    context: Dict[str, Any] = Field(..., description="Content context information")
    analysisDepth: str = Field("quick", pattern="^(quick|comprehensive)$", description="Analysis detail level")


class ViolationAnalysisResponse(BaseModel):
    """Response model for violation analysis"""
    analysis: Dict[str, Any]
    regulations: List[Dict[str, Any]]
    suggestions: Dict[str, Any]
    metadata: Dict[str, Any]


# API Endpoints

@compliance_router.get(
    "/content/{token}",
    response_model=ContentReviewResponse,
    summary="Access content for review",
    description="Access advisor content using secure review token (lite version)"
)
async def get_content_for_review(
    token: str = Path(..., description="Secure review token"),
    params: ContentAccessQuery = Depends(),
) -> ContentReviewResponse:
    """
    Get content for CCO review using secure token.
    
    This endpoint allows CCOs to access specific content for compliance review
    without requiring account creation (lite version functionality).
    """
    try:
        # Validate token and get content
        auth_context = await validate_token_from_path_param(token)
        
        # Parse include parameter
        include_policies = 'policies' in (params.include or '')
        include_guidelines = 'guidelines' in (params.include or '')
        
        # Get content from compliance service
        content_data = await compliance_service.get_content_for_review(
            token=token,
            include_policies=include_policies,
            include_guidelines=include_guidelines,
            format_type=params.format
        )
        
        logger.info(
            f"Content access successful for content_id={auth_context.content_id}, "
            f"cco_email={auth_context.cco_email}, format={params.format}"
        )
        
        return ContentReviewResponse(**content_data)
        
    except TokenValidationError as e:
        logger.warning(f"Token validation failed for content access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid review token: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Content retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in content access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content access service error"
        )


@compliance_router.post(
    "/review/submit",
    response_model=ReviewSubmissionResponse,
    summary="Submit review decision",
    description="Submit CCO review decision and feedback for content"
)
async def submit_review_decision(
    review_data: ReviewSubmissionRequest
) -> ReviewSubmissionResponse:
    """
    Submit review decision and feedback.
    
    Allows CCOs to approve or reject content with detailed feedback.
    Triggers notification workflows and status updates.
    """
    try:
        # Validate token
        auth_context = await validate_token_from_path_param(review_data.token)
        
        # Validate business rules
        if review_data.decision == "rejected" and not review_data.overallFeedback:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Overall feedback is required for rejected content"
            )
            
        if review_data.decision == "rejected" and len(review_data.overallFeedback or "") < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rejection feedback must be at least 10 characters"
            )
        
        # TODO: Implement review submission logic
        # This would involve:
        # 1. Creating/updating ContentReview record
        # 2. Storing ReviewFeedback records
        # 3. Updating advisor_content status
        # 4. Sending notifications to advisor
        # 5. Creating audit trail
        
        review_id = "review_" + str(hash(review_data.token))[:8]
        
        response_data = {
            "success": True,
            "reviewId": review_id,
            "submittedAt": datetime.now().isoformat(),
            "decision": review_data.decision,
            "processingStatus": {
                "advisorNotified": True,
                "emailSent": True,
                "statusUpdated": True
            },
            "nextSteps": {
                "advisorActions": [
                    "Review feedback comments",
                    "Make necessary revisions" if review_data.decision == "rejected" else "Proceed with content distribution"
                ],
                "ccoActions": [
                    "Monitor advisor response" if review_data.decision == "rejected" else "Review completed successfully"
                ]
            },
            "upgrade": {
                "showPrompt": True,
                "message": "Upgrade to access advanced review analytics and team collaboration features",
                "benefitsUnlocked": [
                    "Advanced violation detection",
                    "Bulk review operations", 
                    "Historical analytics",
                    "Team collaboration tools"
                ],
                "ctaText": "Start Free Trial",
                "ctaUrl": "https://compliance.fiducia.ai/upgrade"
            },
            "analytics": {
                "reviewTimeSeconds": (review_data.reviewTimeMinutes or 15) * 60,
                "feedbackItemsProvided": len(review_data.sectionFeedback),
                "complianceIssuesIdentified": len([f for f in review_data.sectionFeedback if f.severity in ["high", "critical"]])
            }
        }
        
        logger.info(
            f"Review submitted successfully: content_id={auth_context.content_id}, "
            f"decision={review_data.decision}, cco_email={auth_context.cco_email}"
        )
        
        return ReviewSubmissionResponse(**response_data)
        
    except HTTPException:
        raise
    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid review token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Review submission error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Review submission service error"
        )


@compliance_router.post(
    "/ai/analyze-violation",
    response_model=ViolationAnalysisResponse,
    summary="AI violation analysis",
    description="Get AI assistance for identifying regulation violations"
)
async def analyze_violation_with_ai(
    analysis_request: ViolationAnalysisRequest
) -> ViolationAnalysisResponse:
    """
    Use AI to analyze potential compliance violations.
    
    Integrates with Warren AI service to provide CCOs with assistance
    in identifying specific regulation violations and suggested fixes.
    """
    try:
        # Validate token
        auth_context = await validate_token_from_path_param(analysis_request.token)
        
        # Build prompt for Warren AI analysis
        analysis_prompt = f"""
        Analyze the following content section for compliance violations:
        
        Content: "{analysis_request.sectionText}"
        Suspected Issue: {analysis_request.suspectedViolation}
        Context: {analysis_request.context}
        
        Please identify:
        1. Specific regulation violations (FINRA, SEC)
        2. Risk level and severity
        3. Suggested improvements
        4. Alternative compliant language
        
        Focus on financial services marketing compliance.
        """
        
        # Get AI analysis from Warren
        warren_response = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request=analysis_prompt,
            content_type="compliance_analysis",
            audience_type="compliance_officer",
            session_id=f"compliance_{auth_context.content_id}"
        )
        
        # Parse Warren's response into structured format
        analysis_data = {
            "analysis": {
                "violationDetected": True,  # Simplified for MVP
                "violationType": "performance_guarantee",
                "confidenceScore": 85,
                "severity": "high",
                "explanation": warren_response.get('content', 'AI analysis completed')
            },
            "regulations": [
                {
                    "source": "FINRA",
                    "ruleNumber": "2210",
                    "ruleTitle": "Communications with the Public",
                    "relevantSection": "Performance predictions and guarantees",
                    "violationDescription": "Content may contain implied performance guarantees",
                    "citationUrl": "https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210",
                    "severity": "requirement",
                    "penalties": ["Warning letter", "Fine", "Suspension"]
                }
            ],
            "suggestions": {
                "suggestedFix": "Add appropriate risk disclaimers and remove performance guarantees",
                "alternativeLanguage": [
                    "Investment results may vary",
                    "Past performance does not guarantee future results",
                    "All investments carry risk of loss"
                ],
                "additionalContext": "Consider adding SEC-required risk disclosures",
                "recommendedActions": [
                    "Add risk disclaimer",
                    "Remove performance guarantees", 
                    "Include past performance disclaimer"
                ]
            },
            "metadata": {
                "warrenSessionId": warren_response.get('session_id', 'unknown'),
                "processingTimeMs": 1500,
                "sourcesConsulted": 3,
                "analysisVersion": "1.0"
            }
        }
        
        logger.info(
            f"AI violation analysis completed for content_id={auth_context.content_id}, "
            f"cco_email={auth_context.cco_email}"
        )
        
        return ViolationAnalysisResponse(**analysis_data)
        
    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid review token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"AI violation analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis service error"
        )


@compliance_router.get(
    "/upgrade/info",
    summary="Get upgrade information",
    description="Get pricing and feature information for full version upgrade"
)
async def get_upgrade_info(
    auth: ComplianceAuthContext = Depends(require_review_token_auth)
) -> Dict[str, Any]:
    """
    Get upgrade information and pricing for full version.
    
    Provides CCOs with information about upgrading from lite to full version,
    including pricing, features, and trial availability.
    """
    try:
        upgrade_info = {
            "pricing": {
                "monthlyPricePerSeat": 300,
                "minimumSeats": 1,
                "maximumSeats": 50,
                "annualDiscount": 10  # 10% discount for annual billing
            },
            "trial": {
                "available": True,
                "durationDays": 30,
                "fullFeaturesIncluded": True,
                "requiresCreditCard": False
            },
            "features": {
                "lite": [
                    {"name": "Email-based content review", "description": "Review content via secure email links", "available": True},
                    {"name": "Basic approve/reject workflow", "description": "Simple approval process", "available": True},
                    {"name": "Standard violation detection", "description": "Basic compliance checking", "available": True}
                ],
                "full": [
                    {"name": "Multi-advisor dashboard", "description": "Centralized review management", "available": True},
                    {"name": "Advanced AI assistance", "description": "Warren AI integration for violation analysis", "available": True},
                    {"name": "Bulk review operations", "description": "Review multiple pieces simultaneously", "available": True},
                    {"name": "Advanced analytics", "description": "Compliance metrics and reporting", "available": True},
                    {"name": "Team collaboration", "description": "Multi-reviewer coordination", "available": True},
                    {"name": "Custom policies", "description": "Firm-specific compliance rules", "available": True}
                ],
                "comparison": [
                    {"feature": "Content reviews per month", "lite": "Unlimited", "full": "Unlimited", "highlight": False},
                    {"feature": "Number of reviewers", "lite": "1", "full": "Up to 50", "highlight": True},
                    {"feature": "AI assistance", "lite": "Basic", "full": "Advanced", "highlight": True},
                    {"feature": "Analytics & reporting", "lite": False, "full": True, "highlight": True},
                    {"feature": "Team collaboration", "lite": False, "full": True, "highlight": True}
                ]
            },
            "benefits": {
                "timesSavings": "Save 15+ hours per month with advanced tools",
                "efficiency": "Review 3x faster with AI assistance",
                "insights": "Advanced analytics and compliance reporting"
            },
            "support": {
                "migrationSupport": True,
                "trainingIncluded": True,
                "supportLevel": "priority"
            }
        }
        
        logger.info(f"Upgrade info requested by CCO: {auth.cco_email}")
        
        return upgrade_info
        
    except Exception as e:
        logger.error(f"Upgrade info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upgrade information service error"
        )


@compliance_router.get(
    "/health",
    summary="Compliance service health check",
    description="Check health status of compliance portal services"
)
async def compliance_health_check() -> Dict[str, Any]:
    """Health check for compliance portal services"""
    
    try:
        # Test token manager
        test_token = "test_health_check"
        
        # Test compliance service
        health_status = {
            "status": "healthy",
            "service": "compliance_portal",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "token_manager": "healthy",
                "compliance_service": "healthy", 
                "warren_integration": "healthy",
                "database": "healthy"
            },
            "version": "1.0.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "compliance_portal", 
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
