"""
Email Service for FiduciaMVP
Handles all email notifications using SendGrid
"""
import os
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        # Try to import settings, fallback to environment variables
        try:
            from config.settings import settings
            self.api_key = settings.sendgrid_api_key
            self.from_email = settings.sendgrid_from_email
            self.from_name = settings.sendgrid_from_name
        except ImportError:
            # Fallback to environment variables for testing
            self.api_key = os.getenv("SENDGRID_API_KEY")
            self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "notifications@fiducia.ai")
            self.from_name = os.getenv("SENDGRID_FROM_NAME", "Fiducia Compliance System")
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = SendGridAPIClient(api_key=self.api_key)
    
    async def send_review_notification(
        self,
        to_email: str,
        content_title: str,
        content_type: str,
        advisor_id: str,
        review_url: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Send content review notification to CCO
        
        Args:
            to_email: CCO email address
            content_title: Title of the content to review
            content_type: Type of content (social post, email, etc.)
            advisor_id: ID of the advisor who submitted content
            review_url: URL for reviewing the content
            notes: Optional notes from advisor
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.error("SendGrid client not initialized - check SENDGRID_API_KEY")
            return False
        
        try:
            subject = f"🔍 Content Review Request: {content_title}"
            
            # Create HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e5e9; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; color: #6c757d; font-size: 14px; }}
                    .review-button {{ display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                    .review-button:hover {{ background: #218838; }}
                    .details {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; }}
                    .details strong {{ color: #495057; }}
                    .notes {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
                    .urgent {{ color: #dc3545; font-weight: 600; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📋 Content Review Request</h1>
                        <p>New content awaiting your approval</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear Compliance Officer,</p>
                        
                        <p>A new content piece has been submitted for your review and requires your attention.</p>
                        
                        <div class="details">
                            <h3>📄 Content Details</h3>
                            <p><strong>Title:</strong> {content_title}</p>
                            <p><strong>Content Type:</strong> {content_type}</p>
                            <p><strong>Submitted By:</strong> Advisor ID {advisor_id}</p>
                            <p><strong>Submission Time:</strong> Just now</p>
                        </div>
                        
                        {f'<div class="notes"><h4>📝 Advisor Notes:</h4><p>{notes}</p></div>' if notes else ''}
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{review_url}" class="review-button">
                                🔍 Review Content Now
                            </a>
                        </div>
                        
                        <p><small>If the button doesn't work, copy and paste this URL into your browser:</small><br>
                        <code>{review_url}</code></p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e1e5e9;">
                            <p class="urgent">⏰ Please review this content promptly to maintain compliance standards.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Best regards,<br>
                        <strong>Fiducia Compliance System</strong></p>
                        <p><small>This is an automated message. Please do not reply to this email.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            plain_body = f"""
Content Review Request: {content_title}

Dear Compliance Officer,

A new content piece has been submitted for your review:

CONTENT DETAILS:
- Title: {content_title}
- Content Type: {content_type}
- Submitted By: Advisor ID {advisor_id}
- Submission Time: Just now

{f'ADVISOR NOTES: {notes}' if notes else ''}

Please review this content by visiting:
{review_url}

Please review this content promptly to maintain compliance standards.

Best regards,
Fiducia Compliance System

---
This is an automated message. Please do not reply to this email.
            """
            
            # Create the email
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            # Create mail object with both HTML and plain text
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=plain_body,
                html_content=html_body
            )
            
            # Send the email
            response = self.client.send(mail)
            
            if response.status_code == 202:
                logger.info(f"✅ Review notification email sent successfully to {to_email}")
                logger.info(f"📧 Subject: {subject}")
                logger.info(f"🔗 Review URL: {review_url}")
                return True
            else:
                logger.error(f"❌ SendGrid returned status code: {response.status_code}")
                logger.error(f"Response body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send review notification email: {e}")
            return False
    
    async def send_approval_notification(
        self,
        to_email: str,
        content_title: str,
        status: str,
        reviewer_feedback: Optional[str] = None
    ) -> bool:
        """
        Send approval status notification to advisor
        
        Args:
            to_email: Advisor email address
            content_title: Title of the reviewed content
            status: approved, rejected, or needs_revision
            reviewer_feedback: Optional feedback from reviewer
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.error("SendGrid client not initialized - check SENDGRID_API_KEY")
            return False
        
        try:
            # Customize subject and content based on status
            status_configs = {
                "approved": {
                    "emoji": "✅",
                    "color": "#28a745",
                    "title": "Content Approved",
                    "message": "Great news! Your content has been approved and is ready for distribution."
                },
                "rejected": {
                    "emoji": "❌", 
                    "color": "#dc3545",
                    "title": "Content Rejected",
                    "message": "Your content requires significant changes before it can be approved."
                },
                "needs_revision": {
                    "emoji": "📝",
                    "color": "#ffc107", 
                    "title": "Revision Requested",
                    "message": "Your content needs minor revisions before final approval."
                }
            }
            
            config = status_configs.get(status, status_configs["needs_revision"])
            
            subject = f"{config['emoji']} {config['title']}: {content_title}"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: {config['color']}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #ffffff; padding: 30px; border: 1px solid #e1e5e9; }}
                    .footer {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; color: #6c757d; font-size: 14px; }}
                    .feedback {{ background: #f8f9fa; padding: 20px; border-left: 4px solid {config['color']}; margin: 20px 0; }}
                    .status-badge {{ background: {config['color']}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{config['emoji']} {config['title']}</h1>
                        <p>Review completed for your content</p>
                    </div>
                    
                    <div class="content">
                        <p>Hello,</p>
                        
                        <p>{config['message']}</p>
                        
                        <div style="margin: 20px 0;">
                            <p><strong>Content:</strong> {content_title}</p>
                            <p><strong>Status:</strong> <span class="status-badge">{status.replace('_', ' ').title()}</span></p>
                        </div>
                        
                        {f'<div class="feedback"><h4>📝 Reviewer Feedback:</h4><p>{reviewer_feedback}</p></div>' if reviewer_feedback else ''}
                        
                        <p>You can log back into your Fiducia portal to view the full details and take any necessary actions.</p>
                    </div>
                    
                    <div class="footer">
                        <p>Best regards,<br>
                        <strong>Fiducia Compliance Team</strong></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_body = f"""
{config['title']}: {content_title}

Hello,

{config['message']}

Content: {content_title}
Status: {status.replace('_', ' ').title()}

{f'Reviewer Feedback: {reviewer_feedback}' if reviewer_feedback else ''}

You can log back into your Fiducia portal to view the full details and take any necessary actions.

Best regards,
Fiducia Compliance Team
            """
            
            # Create and send email
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=plain_body,
                html_content=html_body
            )
            
            response = self.client.send(mail)
            
            if response.status_code == 202:
                logger.info(f"✅ Approval notification sent to {to_email} - Status: {status}")
                return True
            else:
                logger.error(f"❌ SendGrid returned status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send approval notification: {e}")
            return False

# Global email service instance
email_service = EmailService()
