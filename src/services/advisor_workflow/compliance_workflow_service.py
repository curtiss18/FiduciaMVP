# ComplianceWorkflowService
"""
Compliance review workflow service following Warren pattern.

Responsibilities:
- Submit advisor content for CCO compliance review
- Generate secure review tokens with expiration
- Coordinate with NotificationCoordinator for review notifications
- Track review status and submission timestamps
- Handle content status transitions for compliance workflow
- Maintain audit trail for regulatory compliance

Extracted from advisor_workflow_service.py as part of SCRUM-100.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_, text
from src.models.advisor_workflow_models import AdvisorContent
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ComplianceWorkflowService:
    """Compliance review workflow management following Warren pattern."""
    
    def __init__(self, notification_coordinator=None):
        """Initialize with dependency injection for testing (Warren pattern)."""
        # Import NotificationCoordinator with lazy loading for circular import prevention
        if notification_coordinator is None:
            from .notification_coordinator import NotificationCoordinator
            self.notification_coordinator = NotificationCoordinator()
        else:
            self.notification_coordinator = notification_coordinator
        pass
    
    async def submit_for_review(
        self,
        content_id: int,
        advisor_id: str,
        cco_email: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit content for CCO compliance review."""
        async with AsyncSessionLocal() as db:
            try:
                # First, verify content belongs to advisor and get content details
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    logger.warning(f"Content {content_id} not found or access denied for advisor {advisor_id}")
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Generate secure review token
                review_token = self.generate_review_token(content_id, cco_email)
                
                # Update content with compliance review information
                query = text("""
                    UPDATE advisor_content 
                    SET status = 'submitted',
                        cco_review_status = 'submitted',
                        cco_email = :cco_email,
                        submitted_for_review_at = NOW(),
                        updated_at = NOW()
                    WHERE id = :content_id
                """)
                await db.execute(query, {
                    "content_id": content_id,
                    "cco_email": cco_email
                })
                
                await db.commit()
                
                # Send email notification to CCO using NotificationCoordinator
                try:
                    email_sent = await self.notification_coordinator.send_review_notification(
                        cco_email=cco_email,
                        content=content,
                        review_token=review_token,
                        notes=notes
                    )
                except Exception as email_error:
                    logger.warning(f"Email notification failed for content {content_id}: {email_error}")
                    email_sent = False  # Continue workflow even if email fails
                
                logger.info(f"Content {content_id} submitted for review to {cco_email}")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "review": {
                        "review_token": review_token,
                        "cco_email": cco_email,
                        "submitted_at": datetime.now().isoformat(),
                        "email_sent": email_sent
                    }
                }
                
            except Exception as e:
                logger.error(f"Error submitting content for review: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def update_review_status(
        self,
        content_id: int,
        new_status: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update content review status (CCO decision)."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content exists
                result = await db.execute(
                    select(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    logger.warning(f"Content {content_id} not found for status update")
                    return {"status": "error", "error": "Content not found"}
                
                # Update status with review decision
                new_status_str = new_status.lower()
                
                # Use raw SQL for update with enum casting
                if notes:
                    query = text("""
                        UPDATE advisor_content 
                        SET status = :status,
                            cco_review_status = :status,
                            cco_review_notes = :notes,
                            reviewed_by = :reviewer,
                            reviewed_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :content_id
                    """)
                    await db.execute(query, {
                        "status": new_status_str,
                        "notes": notes,
                        "reviewer": reviewer,
                        "content_id": content_id
                    })
                else:
                    query = text("""
                        UPDATE advisor_content 
                        SET status = :status,
                            cco_review_status = :status,
                            reviewed_by = :reviewer,
                            reviewed_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :content_id
                    """)
                    await db.execute(query, {
                        "status": new_status_str,
                        "reviewer": reviewer,
                        "content_id": content_id
                    })
                
                await db.commit()
                
                logger.info(f"Updated content {content_id} review status to {new_status} by {reviewer}")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "new_status": new_status,
                    "reviewer": reviewer,
                    "reviewed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error updating review status: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def get_review_history(self, content_id: int) -> Dict[str, Any]:
        """Get compliance review history for content."""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"status": "error", "error": "Content not found"}
                
                review_history = {
                    "content_id": content_id,
                    "current_status": content.status.value if content.status else None,
                    "cco_review_status": content.cco_review_status,
                    "cco_email": content.cco_email,
                    "submitted_for_review_at": content.submitted_for_review_at.isoformat() if content.submitted_for_review_at else None,
                    "reviewed_by": content.reviewed_by,
                    "reviewed_at": content.reviewed_at.isoformat() if content.reviewed_at else None,
                    "cco_review_notes": content.cco_review_notes,
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat()
                }
                
                logger.info(f"Retrieved review history for content {content_id}")
                
                return {
                    "status": "success",
                    "review_history": review_history
                }
                
            except Exception as e:
                logger.error(f"Error getting review history: {e}")
                return {"status": "error", "error": str(e)}
    
    def generate_review_token(self, content_id: int, cco_email: str) -> str:
        """Generate secure review token using centralized token manager."""
        try:
            from src.services.token_manager import token_manager
            
            # Use the token manager to generate a proper signed token
            return token_manager.generate_review_token(
                content_id=content_id,
                cco_email=cco_email,
                expires_hours=24 * 7  # 7 days
            )
            
        except Exception as e:
            logger.error(f"Error generating review token: {e}")
            # Fallback to simple token if token_manager fails
            import uuid
            return f"review_{content_id}_{uuid.uuid4().hex[:8]}"
    
    def validate_review_access(self, token: str) -> Dict[str, Any]:
        """Validate review token and return content access information."""
        try:
            from src.services.token_manager import token_manager
            
            # Validate token using token manager
            validation_result = token_manager.validate_review_token(token)
            
            if validation_result.get("valid"):
                logger.info(f"Valid review token for content {validation_result.get('content_id')}")
                return {
                    "status": "success",
                    "valid": True,
                    "content_id": validation_result.get("content_id"),
                    "cco_email": validation_result.get("cco_email"),
                    "expires_at": validation_result.get("expires_at")
                }
            else:
                logger.warning(f"Invalid review token: {validation_result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "valid": False,
                    "error": validation_result.get("error", "Invalid token")
                }
                
        except Exception as e:
            logger.error(f"Error validating review token: {e}")
            return {
                "status": "error",
                "valid": False,
                "error": "Token validation failed"
            }
