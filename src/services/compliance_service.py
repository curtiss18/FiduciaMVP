# Compliance Service
"""
Business logic service for compliance portal operations.
Handles content retrieval, compliance context, and CCO-specific data formatting.

Key Features:
- Token-based content access for CCOs
- Compliance policies and regulatory guidelines
- Content metadata and advisor information
- Mobile-optimized responses
- Upgrade prompts for full version
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from src.core.database import AsyncSessionLocal
from src.models.compliance_models import ContentReview, ComplianceCCO
from src.models.advisor_workflow_models import AdvisorContent, AdvisorSessions
from src.services.token_manager import token_manager, TokenValidationError

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for compliance portal business logic"""
    
    def __init__(self):
        self.compliance_policies = self._load_compliance_policies()
        self.regulatory_guidelines = self._load_regulatory_guidelines()
        self.violation_types = self._load_violation_types()
    
    async def get_content_for_review(
        self, 
        token: str,
        include_policies: bool = True,
        include_guidelines: bool = True,
        format_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Get content for CCO review using secure token.
        
        Args:
            token: Review token for content access
            include_policies: Whether to include compliance policies
            include_guidelines: Whether to include regulatory guidelines  
            format_type: Response format ('full', 'summary', 'mobile')
            
        Returns:
            Complete content review data
            
        Raises:
            TokenValidationError: If token is invalid
            ValueError: If content not found or not accessible
        """
        try:
            # Validate token and extract data
            token_data = token_manager.validate_review_token(token)
            content_id = int(token_data['content_id'])  # Convert to integer
            cco_email = token_data['cco_email']
            
            logger.info(f"Retrieving content {content_id} for CCO {cco_email}")
            
            async with AsyncSessionLocal() as db:
                # Get content - note: AdvisorContent doesn't have session relationship
                # We'll need to manually get session data if needed
                content_query = select(AdvisorContent).where(AdvisorContent.id == content_id)
                
                result = await db.execute(content_query)
                content = result.scalar_one_or_none()
                
                if not content:
                    raise ValueError(f"Content {content_id} not found")
                
                # Get review record if exists
                review_query = select(ContentReview).where(
                    and_(
                        ContentReview.content_id == content_id,
                        ContentReview.review_token == token
                    )
                )
                review_result = await db.execute(review_query)
                review = review_result.scalar_one_or_none()
                
                # Build response based on format type
                if format_type == "mobile":
                    return await self._build_mobile_response(
                        content, review, token_data, include_policies, include_guidelines
                    )
                elif format_type == "summary":
                    return await self._build_summary_response(
                        content, review, token_data
                    )
                else:
                    return await self._build_full_response(
                        content, review, token_data, include_policies, include_guidelines
                    )
                    
        except TokenValidationError:
            logger.warning(f"Invalid token used for content access: {token[:20]}...")
            raise
        except Exception as e:
            logger.error(f"Error retrieving content for review: {str(e)}")
            raise ValueError(f"Content retrieval failed: {str(e)}")
    
    async def _build_full_response(
        self,
        content: AdvisorContent,
        review: Optional[ContentReview],
        token_data: Dict[str, Any],
        include_policies: bool,
        include_guidelines: bool
    ) -> Dict[str, Any]:
        """Build complete response with all data"""
        
        # Extract advisor information
        advisor_info = self._extract_advisor_info(content)
        
        # Calculate content metadata
        content_metadata = self._calculate_content_metadata(content)
        
        # Build base response
        response = {
            "content": {
                "id": content.id,
                "title": content.title or f"Content from {advisor_info['name']}",
                "content": content.content_text,
                "contentType": content.content_type if content.content_type else "unknown",
                "platform": "Unknown Platform",  # AdvisorContent doesn't have platform field
                "audience": content.audience_type if content.audience_type else "unknown",
                "createdAt": content.created_at.isoformat(),
                "metadata": content_metadata
            },
            "advisor": advisor_info,
            "review": self._build_review_info(review, token_data),
            "upgrade": self._build_upgrade_prompts(),
            "compliance": self._build_compliance_context(
                include_policies, include_guidelines
            )
        }
            
        return response
    
    async def _build_mobile_response(
        self,
        content: AdvisorContent,
        review: Optional[ContentReview],
        token_data: Dict[str, Any],
        include_policies: bool,
        include_guidelines: bool
    ) -> Dict[str, Any]:
        """Build mobile-optimized response"""
        
        advisor_info = self._extract_advisor_info(content)
        content_metadata = self._calculate_content_metadata(content, mobile_optimized=True)
        
        response = {
            "content": {
                "id": content.id,
                "title": content.title or f"Content from {advisor_info['name']}",
                "content": content.content_text,
                "contentType": content.content_type if content.content_type else "unknown",
                "platform": "Unknown Platform",  # AdvisorContent doesn't have platform field
                "audience": content.audience_type if content.audience_type else "unknown",
                "createdAt": content.created_at.isoformat(),
                "metadata": content_metadata
            },
            "advisor": {
                "name": advisor_info["name"],
                "email": advisor_info["email"], 
                "firm": advisor_info["firm"]
            },
            "review": {
                "id": review.id if review else None,
                "status": review.status.value if review else "pending",
                "submittedAt": review.created_at.isoformat() if review else token_data.get('issued_at'),
                "ageInDays": self._calculate_age_days(review, token_data)
            },
            "policies": self._get_essential_policies() if include_policies else [],
            "compliance": self._build_compliance_context(
                include_policies, include_guidelines
            ),
            "upgrade": {
                "showPrompt": True,
                "message": "Upgrade for advanced review tools and analytics",
                "ctaText": "Learn More"
            }
        }
        
        return response
    
    async def _build_summary_response(
        self,
        content: AdvisorContent,
        review: Optional[ContentReview],
        token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build summary response with essential information"""
        
        advisor_info = self._extract_advisor_info(content)
        
        return {
            "content": {
                "id": content.id,
                "title": content.title or f"Content from {advisor_info['name']}",
                "contentType": content.content_type if content.content_type else "unknown",
                "platform": "Unknown Platform",  # AdvisorContent doesn't have platform field
                "wordCount": len(content.content_text.split()) if content.content_text else 0
            },
            "advisor": {
                "name": advisor_info["name"],
                "firm": advisor_info["firm"]
            },
            "review": {
                "status": review.status.value if review else "pending",
                "ageInDays": self._calculate_age_days(review, token_data)
            }
        }
    
    def _extract_advisor_info(self, content: AdvisorContent) -> Dict[str, Any]:
        """Extract advisor information from content"""
        
        # Get advisor info from content fields - AdvisorContent doesn't have session relationship
        # We'll use the advisor_id and other available fields
        advisor_name = f"Advisor {content.advisor_id}"  # Basic fallback
        advisor_email = f"{content.advisor_id}@advisor.example"  # Basic fallback
        advisor_firm = "Unknown Firm"
        phone = None
        license_number = None
        specialties = []
        
        # If we had a way to get session info, we'd do it here
        # For now, use basic info from content
        if hasattr(content, 'advisor_id') and content.advisor_id:
            advisor_name = f"Advisor {content.advisor_id}"
            advisor_email = f"{content.advisor_id}@example.com"
        
        return {
            "name": advisor_name,
            "email": advisor_email,
            "firm": advisor_firm,
            "phone": phone,
            "licenseNumber": license_number,
            "specialties": specialties
        }
    
    def _calculate_content_metadata(
        self, 
        content: AdvisorContent, 
        mobile_optimized: bool = False
    ) -> Dict[str, Any]:
        """Calculate content metadata"""
        
        content_text = content.content_text or ""
        
        metadata = {
            "wordCount": len(content_text.split()),
            "characterCount": len(content_text),
            "estimatedReadTime": max(1, len(content_text.split()) // 200),  # ~200 WPM
        }
        
        if not mobile_optimized:
            metadata.update({
                "tags": self._extract_content_tags(content),
                "complexity": self._assess_content_complexity(content_text),
                "complianceRisk": self._assess_compliance_risk(content_text)
            })
            
        return metadata
    
    def _build_review_info(
        self, 
        review: Optional[ContentReview], 
        token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build review information"""
        
        if review:
            return {
                "id": review.id,
                "status": review.status.value,
                "submittedAt": review.created_at.isoformat(),
                "deadline": review.expires_at.isoformat() if review.expires_at else None,
                "priority": "normal",  # Default priority
                "ageInDays": self._calculate_age_days(review, token_data),
                "estimatedReviewTime": self._estimate_review_time(review)
            }
        else:
            # Create review info from token data
            issued_at = datetime.fromtimestamp(token_data['issued_at'])
            return {
                "id": None,
                "status": "pending",
                "submittedAt": issued_at.isoformat(),
                "deadline": datetime.fromtimestamp(token_data['expires_at']).isoformat() if 'expires_at' in token_data else None,
                "priority": "normal",
                "ageInDays": (datetime.now() - issued_at).days,
                "estimatedReviewTime": 15  # Default 15 minutes
            }
    
    def _build_compliance_context(
        self, 
        include_policies: bool, 
        include_guidelines: bool
    ) -> Dict[str, Any]:
        """Build compliance context with policies and guidelines"""
        
        context = {}
        
        if include_policies:
            context["companyPolicies"] = self.compliance_policies
            
        if include_guidelines:
            context["regulatoryGuidelines"] = self.regulatory_guidelines
            
        context["violationTypes"] = self.violation_types
        
        return context
    
    def _build_upgrade_prompts(self) -> Dict[str, Any]:
        """Build upgrade prompts for full version"""
        
        return {
            "showPrompt": True,
            "benefits": [
                "Advanced review tools with AI assistance",
                "Multi-advisor dashboard and analytics", 
                "Bulk review operations",
                "Custom policies and templates",
                "Priority support"
            ],
            "pricingUrl": "https://compliance.fiducia.ai/pricing",
            "trialInfo": {
                "available": True,
                "durationDays": 30,
                "featuresIncluded": [
                    "Full dashboard access",
                    "AI-powered violation detection",
                    "Advanced analytics",
                    "Team collaboration tools"
                ]
            }
        }
    
    def _calculate_age_days(
        self, 
        review: Optional[ContentReview], 
        token_data: Dict[str, Any]
    ) -> int:
        """Calculate how many days old the review request is"""
        
        if review:
            return (datetime.now() - review.created_at).days
        else:
            issued_at = datetime.fromtimestamp(token_data['issued_at'])
            return (datetime.now() - issued_at).days
    
    def _estimate_review_time(self, review: ContentReview) -> int:
        """Estimate review time in minutes based on content"""
        
        # Base time: 10 minutes
        base_time = 10
        
        # Add time based on content length (rough estimate)
        if hasattr(review, 'content') and review.content and review.content.content_text:
            word_count = len(review.content.content_text.split())
            # Add 1 minute per 100 words
            base_time += word_count // 100
            
        return min(base_time, 60)  # Cap at 60 minutes
    
    def _extract_content_tags(self, content: AdvisorContent) -> List[str]:
        """Extract relevant tags from content"""
        
        tags = []
        
        if content.content_type:
            tags.append(content.content_type.lower())
            
        if content.audience_type:
            tags.append(content.audience_type.lower())
            
        # Add content-based tags (simplified)
        content_text = (content.content_text or "").lower()
        
        financial_terms = [
            "investment", "portfolio", "retirement", "savings", 
            "market", "financial", "planning", "advisor"
        ]
        
        for term in financial_terms:
            if term in content_text:
                tags.append(term)
                
        return list(set(tags))  # Remove duplicates
    
    def _assess_content_complexity(self, content_text: str) -> str:
        """Assess content complexity for review estimation"""
        
        word_count = len(content_text.split())
        
        if word_count < 50:
            return "simple"
        elif word_count < 200:
            return "moderate"
        else:
            return "complex"
    
    def _assess_compliance_risk(self, content_text: str) -> str:
        """Assess compliance risk level"""
        
        # Simplified risk assessment based on keywords
        high_risk_terms = [
            "guarantee", "promise", "guaranteed return", "no risk",
            "sure thing", "can't lose", "risk-free"
        ]
        
        medium_risk_terms = [
            "performance", "return", "profit", "gain", "growth"
        ]
        
        content_lower = content_text.lower()
        
        if any(term in content_lower for term in high_risk_terms):
            return "high"
        elif any(term in content_lower for term in medium_risk_terms):
            return "medium"
        else:
            return "low"
    
    def _get_essential_policies(self) -> List[Dict[str, Any]]:
        """Get essential policies for mobile view"""
        
        return [
            {
                "id": "marketing_basics",
                "title": "Marketing Communications Policy",
                "category": "marketing",
                "summary": "Core requirements for marketing content creation and distribution."
            },
            {
                "id": "disclosure_requirements", 
                "title": "Disclosure Requirements",
                "category": "disclosure",
                "summary": "Required disclaimers and risk disclosures for financial content."
            }
        ]
    
    def _load_compliance_policies(self) -> List[Dict[str, Any]]:
        """Load compliance policies (placeholder - would come from database)"""
        
        return [
            {
                "id": "marketing_policy",
                "title": "Marketing Communications Policy",
                "category": "marketing",
                "lastUpdated": "2024-01-15",
                "summary": "Guidelines for creating compliant marketing communications.",
                "applicableContent": ["linkedin_post", "email", "website_copy"],
                "documentUrl": "/policies/marketing-communications.pdf"
            },
            {
                "id": "disclosure_policy",
                "title": "Required Disclosures Policy", 
                "category": "disclosure",
                "lastUpdated": "2024-02-01",
                "summary": "Mandatory disclosures for financial advisory content.",
                "applicableContent": ["all"],
                "documentUrl": "/policies/required-disclosures.pdf"
            },
            {
                "id": "social_media_policy",
                "title": "Social Media Usage Policy",
                "category": "communication",
                "lastUpdated": "2024-01-30",
                "summary": "Guidelines for professional social media usage.",
                "applicableContent": ["linkedin_post", "facebook_post", "x_post"],
                "documentUrl": "/policies/social-media.pdf"
            }
        ]
    
    def _load_regulatory_guidelines(self) -> List[Dict[str, Any]]:
        """Load regulatory guidelines (placeholder - would come from database)"""
        
        return [
            {
                "id": "finra_2210",
                "source": "FINRA",
                "ruleNumber": "2210",
                "title": "Communications with the Public",
                "category": "marketing",
                "summary": "FINRA requirements for public communications by financial advisors.",
                "fullTextUrl": "https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210",
                "effectiveDate": "2022-05-01",
                "lastUpdated": "2024-01-01"
            },
            {
                "id": "sec_marketing_rule",
                "source": "SEC",
                "ruleNumber": "206(4)-1",
                "title": "Investment Adviser Marketing Rule",
                "category": "marketing",
                "summary": "SEC requirements for investment adviser marketing communications.",
                "fullTextUrl": "https://www.sec.gov/rules/final/2020/ia-5653.pdf",
                "effectiveDate": "2022-11-04",
                "lastUpdated": "2024-01-01"
            }
        ]
    
    def _load_violation_types(self) -> List[Dict[str, Any]]:
        """Load violation types for CCO reference"""
        
        return [
            {
                "id": "performance_guarantee",
                "category": "finra_rule",
                "name": "Performance Guarantee",
                "description": "Guaranteeing investment performance or returns",
                "commonExamples": [
                    "Guaranteed 10% annual returns",
                    "Promise of no losses",
                    "Risk-free investment claims"
                ],
                "severity": "high",
                "regulationReference": "FINRA Rule 2210"
            },
            {
                "id": "misleading_statement",
                "category": "sec_regulation", 
                "name": "Misleading Statement",
                "description": "False or misleading information about services or performance",
                "commonExamples": [
                    "Exaggerated past performance",
                    "Omitted material facts",
                    "Unsubstantiated claims"
                ],
                "severity": "high",
                "regulationReference": "SEC Marketing Rule"
            },
            {
                "id": "omitted_disclosure",
                "category": "company_policy",
                "name": "Omitted Disclosure",
                "description": "Missing required risk disclosures or disclaimers",
                "commonExamples": [
                    "No risk disclaimer",
                    "Missing fee disclosure",
                    "Incomplete conflict of interest disclosure"
                ],
                "severity": "medium",
                "regulationReference": "Company Policy Section 3.2"
            }
        ]


# Global compliance service instance
compliance_service = ComplianceService()
