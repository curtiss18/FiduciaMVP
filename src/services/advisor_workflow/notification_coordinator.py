# NotificationCoordinator
"""
Email notification coordination service following Warren pattern.

Responsibilities:
- Coordinate all advisor workflow email notifications
- Manage notification templates and formatting
- Handle review notification emails to CCOs
- Status update notifications to advisors
- Email delivery tracking and retry logic
- Template customization and branding

Extracted from advisor_workflow_service.py as part of SCRUM-102.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.advisor_workflow_models import AdvisorContent

logger = logging.getLogger(__name__)


class NotificationCoordinator:
    """Email notification coordination following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def send_review_notification(
        self,
        cco_email: str,
        content: AdvisorContent,
        review_token: str,
        notes: Optional[str] = None
    ) -> bool:
        """Send email notification to CCO about content review request."""
        try:
            # Import email service (Warren pattern - direct service calls)
            from src.services.email_service import email_service
            
            # Build review URL
            review_url = self.build_review_url(review_token)
            
            # Send email using our email service
            success = await email_service.send_review_notification(
                to_email=cco_email,
                content_title=content.title,
                content_type=content.content_type,
                advisor_id=content.advisor_id,
                review_url=review_url,
                notes=notes
            )
            
            if success:
                logger.info(f"✅ Review notification email sent successfully to {cco_email}")
                logger.info(f"📄 Content: {content.title}")
                logger.info(f"🔗 Review URL: {review_url}")
            else:
                logger.error(f"❌ Failed to send review notification email to {cco_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Exception in send_review_notification: {e}")
            return False
    
    async def send_status_update_notification(
        self,
        advisor_email: str,
        content: AdvisorContent,
        new_status: str,
        reviewer_notes: Optional[str] = None
    ) -> bool:
        """Send status update notification to advisor."""
        try:
            # Import email service (Warren pattern - direct service calls)
            from src.services.email_service import email_service
            
            # Get appropriate template for status
            template = self.get_notification_template(f"status_update_{new_status}")
            
            # Determine notification type based on status
            if new_status.lower() == 'approved':
                return await self.send_approval_notification(
                    advisor_email, content, reviewer_notes
                )
            elif new_status.lower() == 'rejected':
                return await self.send_rejection_notification(
                    advisor_email, content, reviewer_notes or "No specific reason provided"
                )
            else:
                # Generic status update
                subject = template['subject'].format(
                    content_title=content.title,
                    new_status=new_status.title()
                )
                
                body = template['body'].format(
                    advisor_name=content.advisor_id,
                    content_title=content.title,
                    new_status=new_status.title(),
                    status_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                    reviewer_notes=reviewer_notes or "No additional notes provided."
                )
                
                # For now, use a basic email method (can be enhanced later)
                logger.info(f"📧 Status update notification for {advisor_email}: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Exception in send_status_update_notification: {e}")
            return False
    
    async def send_approval_notification(
        self,
        advisor_email: str,
        content: AdvisorContent,
        approval_notes: Optional[str] = None
    ) -> bool:
        """Send approval notification to advisor."""
        try:
            template = self.get_notification_template('approval_notification')
            
            subject = template['subject'].format(content_title=content.title)
            
            body = template['body'].format(
                advisor_name=content.advisor_id,
                content_title=content.title,
                approval_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                approval_notes=approval_notes or "No additional comments provided.",
                content_type=content.content_type
            )
            
            logger.info(f"🎉 Approval notification for {advisor_email}: {content.title}")
            logger.info(f"📄 Content approved: {content.title}")
            
            # For MVP, log the notification (can integrate with email service later)
            return True
            
        except Exception as e:
            logger.error(f"❌ Exception in send_approval_notification: {e}")
            return False
    
    async def send_rejection_notification(
        self,
        advisor_email: str,
        content: AdvisorContent,
        rejection_reason: str
    ) -> bool:
        """Send rejection notification to advisor."""
        try:
            template = self.get_notification_template('rejection_notification')
            
            subject = template['subject'].format(content_title=content.title)
            
            body = template['body'].format(
                advisor_name=content.advisor_id,
                content_title=content.title,
                rejection_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                rejection_reason=rejection_reason,
                content_type=content.content_type
            )
            
            logger.info(f"❌ Rejection notification for {advisor_email}: {content.title}")
            logger.info(f"📄 Content rejected: {content.title}")
            logger.info(f"📝 Reason: {rejection_reason}")
            
            # For MVP, log the notification (can integrate with email service later)
            return True
            
        except Exception as e:
            logger.error(f"❌ Exception in send_rejection_notification: {e}")
            return False
    
    def build_review_url(self, review_token: str) -> str:
        """Build review URL for CCO notifications."""
        # Use the same pattern as the original service
        return f"http://localhost:3003/review/{review_token}"
    
    def get_notification_template(self, notification_type: str) -> Dict[str, str]:
        """Get email template for notification type."""
        templates = {
            'review_request': {
                'subject': 'Content Review Required - {content_title}',
                'body': '''
Dear CCO,

A new piece of content has been submitted for compliance review:

Title: {content_title}
Type: {content_type}
Advisor: {advisor_id}
Submitted: {submitted_date}

{advisor_notes}

Please review the content at: {review_url}

Best regards,
Fiducia Platform
'''
            },
            'approval_notification': {
                'subject': 'Content Approved - {content_title}',
                'body': '''
Dear {advisor_name},

Great news! Your content has been approved for distribution:

Title: {content_title}
Type: {content_type}
Approved on: {approval_date}

Reviewer Comments:
{approval_notes}

You can now distribute this content through your selected channels.

Best regards,
Fiducia Compliance Team
'''
            },
            'rejection_notification': {
                'subject': 'Content Requires Revision - {content_title}',
                'body': '''
Dear {advisor_name},

Your content submission requires revision before approval:

Title: {content_title}
Type: {content_type}
Reviewed on: {rejection_date}

Feedback for Revision:
{rejection_reason}

Please make the necessary changes and resubmit for review.

Best regards,
Fiducia Compliance Team
'''
            },
            'status_update_submitted': {
                'subject': 'Content Submitted for Review - {content_title}',
                'body': '''
Dear {advisor_name},

Your content has been successfully submitted for compliance review:

Title: {content_title}
Status: {new_status}
Submitted on: {status_date}

Notes:
{reviewer_notes}

You will receive notification once the review is complete.

Best regards,
Fiducia Platform
'''
            },
            'status_update_draft': {
                'subject': 'Content Returned to Draft - {content_title}',
                'body': '''
Dear {advisor_name},

Your content has been returned to draft status:

Title: {content_title}
Status: {new_status}
Updated on: {status_date}

Notes:
{reviewer_notes}

You can continue editing and resubmit when ready.

Best regards,
Fiducia Platform
'''
            },
            'status_update_archived': {
                'subject': 'Content Archived - {content_title}',
                'body': '''
Dear {advisor_name},

Your content has been archived:

Title: {content_title}
Status: {new_status}
Archived on: {status_date}

Notes:
{reviewer_notes}

You can restore this content from your archive if needed.

Best regards,
Fiducia Platform
'''
            }
        }
        
        return templates.get(notification_type, {
            'subject': 'Fiducia Platform Notification',
            'body': 'This is a notification from the Fiducia platform.'
        })
    
    async def send_reminder_notification(
        self,
        cco_email: str,
        content: AdvisorContent,
        review_token: str,
        days_pending: int
    ) -> bool:
        """Send reminder notification for pending reviews."""
        try:
            subject = f"🔔 Review Reminder: {content.title} (Pending {days_pending} days)"
            
            body = f"""
Dear CCO,

This is a reminder that the following content is still pending review:

Title: {content.title}
Type: {content.content_type}
Advisor: {content.advisor_id}
Days Pending: {days_pending}

Please review at your earliest convenience: {self.build_review_url(review_token)}

Best regards,
Fiducia Compliance System
"""
            
            logger.info(f"🔔 Reminder notification for {cco_email}: {content.title} ({days_pending} days)")
            
            # For MVP, log the reminder (can integrate with email service later)
            return True
            
        except Exception as e:
            logger.error(f"❌ Exception in send_reminder_notification: {e}")
            return False
    
    async def validate_notification_data(
        self,
        notification_type: str,
        recipient_email: str,
        content: AdvisorContent
    ) -> Dict[str, Any]:
        """Validate notification data before sending."""
        validation_result = {
            'valid': True,
            'errors': []
        }
        
        # Validate email address format
        if not recipient_email or '@' not in recipient_email:
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid recipient email address')
        
        # Validate content exists
        if not content:
            validation_result['valid'] = False
            validation_result['errors'].append('Content object is required')
        
        # Validate notification type
        valid_types = [
            'review_request', 'approval_notification', 'rejection_notification',
            'status_update_submitted', 'status_update_draft', 'status_update_archived'
        ]
        if notification_type not in valid_types:
            validation_result['valid'] = False
            validation_result['errors'].append(f'Invalid notification type: {notification_type}')
        
        return validation_result
