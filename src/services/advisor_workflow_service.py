# Advisor Workflow Service
"""
Service for managing advisor content lifecycle:
1. Save Warren conversations
2. Manage advisor content library
3. Submit content for compliance review
4. Track content status and distribution
"""

import logging
import json
import uuid
import hashlib
import hmac
import base64
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, desc, text
from sqlalchemy.orm import selectinload

from src.models.advisor_workflow_models import (
    AdvisorSessions, AdvisorMessages, AdvisorContent, 
    ComplianceReviews, ContentDistribution,
    ContentStatus, ReviewDecision
)
from src.models.refactored_database import ContentType, AudienceType
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AdvisorWorkflowService:
    """Service for advisor content workflow management."""
    
    def __init__(self):
        """Initialize the advisor workflow service."""
        pass
    
    def _generate_review_token(self, content_id: int, cco_email: str) -> str:
        """Generate a review token using the centralized token manager"""
        from src.services.token_manager import token_manager
        
        # Use the token manager to generate a proper signed token
        token_data = {
            "content_id": str(content_id),
            "cco_email": cco_email,
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return token_manager.generate_review_token(
            content_id=content_id,
            cco_email=cco_email,
            expires_hours=24 * 7  # 7 days
        )
    
    # ===== WARREN CONVERSATION MANAGEMENT =====
    
    async def create_advisor_session(
        self, 
        advisor_id: str, 
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Warren chat session for an advisor."""
        async with AsyncSessionLocal() as db:
            try:
                # Generate unique session ID
                session_id = f"session_{advisor_id}_{uuid.uuid4().hex[:8]}"
                
                # Create session
                session = AdvisorSessions(
                    advisor_id=advisor_id,
                    session_id=session_id,
                    title=title or f"Chat Session {datetime.now().strftime('%m/%d %H:%M')}"
                )
                
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"Created new advisor session: {session_id}")
                
                return {
                    "status": "success",
                    "session": {
                        "id": session.id,
                        "session_id": session.session_id,
                        "advisor_id": session.advisor_id,
                        "title": session.title,
                        "created_at": session.created_at.isoformat(),
                        "message_count": session.message_count
                    }
                }
                
            except Exception as e:
                logger.error(f"Error creating advisor session: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def save_warren_message(
        self,
        session_id: str,
        message_type: str,  # 'user' or 'warren'
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Save a message to an advisor's Warren conversation."""
        async with AsyncSessionLocal() as db:
            try:
                # Create message
                message = AdvisorMessages(
                    session_id=session_id,
                    message_type=message_type,
                    content=content
                )
                
                # Add Warren-specific metadata if available
                if message_type == 'warren' and metadata:
                    message.sources_used = json.dumps(metadata.get('sources_used', []))
                    message.generation_confidence = metadata.get('generation_confidence')
                    message.search_strategy = metadata.get('search_strategy')
                    message.total_sources = metadata.get('total_sources')
                    message.marketing_examples = metadata.get('marketing_examples')
                    message.compliance_rules = metadata.get('compliance_rules')
                
                db.add(message)
                
                # Update session activity and message count
                await db.execute(
                    update(AdvisorSessions)
                    .where(AdvisorSessions.session_id == session_id)
                    .values(
                        last_activity=func.now(),
                        message_count=AdvisorSessions.message_count + 1,
                        updated_at=func.now()
                    )
                )
                
                await db.commit()
                await db.refresh(message)
                
                return {
                    "status": "success",
                    "message": {
                        "id": message.id,
                        "session_id": message.session_id,
                        "message_type": message.message_type,
                        "content": message.content,
                        "created_at": message.created_at.isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error saving Warren message: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def get_session_messages(
        self, 
        session_id: str, 
        advisor_id: str
    ) -> Dict[str, Any]:
        """Get all messages for a specific Warren chat session."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify session belongs to advisor
                session_result = await db.execute(
                    select(AdvisorSessions)
                    .where(and_(
                        AdvisorSessions.session_id == session_id,
                        AdvisorSessions.advisor_id == advisor_id
                    ))
                )
                session = session_result.scalar_one_or_none()
                
                if not session:
                    return {"status": "error", "error": "Session not found or access denied"}
                
                # Get messages
                messages_result = await db.execute(
                    select(AdvisorMessages)
                    .where(AdvisorMessages.session_id == session_id)
                    .order_by(AdvisorMessages.created_at)
                )
                messages = messages_result.scalars().all()
                
                return {
                    "status": "success",
                    "session": {
                        "id": session.id,
                        "session_id": session.session_id,
                        "title": session.title,
                        "message_count": session.message_count,
                        "created_at": session.created_at.isoformat()
                    },
                    "messages": [
                        {
                            "id": message.id,
                            "message_type": message.message_type,
                            "content": message.content,
                            "created_at": message.created_at.isoformat(),
                            "metadata": {
                                "sources_used": json.loads(message.sources_used) if message.sources_used else None,
                                "generation_confidence": message.generation_confidence,
                                "search_strategy": message.search_strategy,
                                "total_sources": message.total_sources,
                                "marketing_examples": message.marketing_examples,
                                "compliance_rules": message.compliance_rules
                            } if message.message_type == 'warren' else None
                        }
                        for message in messages
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error getting session messages: {e}")
                return {"status": "error", "error": str(e)}
    
    async def get_advisor_sessions(
        self,
        advisor_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get advisor's Warren chat sessions."""
        async with AsyncSessionLocal() as db:
            try:
                # Get sessions
                result = await db.execute(
                    select(AdvisorSessions)
                    .where(AdvisorSessions.advisor_id == advisor_id)
                    .order_by(desc(AdvisorSessions.last_activity))
                    .limit(limit)
                    .offset(offset)
                )
                sessions = result.scalars().all()
                
                # Get total count
                count_result = await db.execute(
                    select(func.count(AdvisorSessions.id))
                    .where(AdvisorSessions.advisor_id == advisor_id)
                )
                total_count = count_result.scalar()
                
                return {
                    "status": "success",
                    "sessions": [
                        {
                            "id": session.id,
                            "session_id": session.session_id,
                            "title": session.title,
                            "message_count": session.message_count,
                            "created_at": session.created_at.isoformat(),
                            "last_activity": session.last_activity.isoformat() if session.last_activity else None
                        }
                        for session in sessions
                    ],
                    "total_count": total_count,
                    "has_more": (offset + limit) < total_count
                }
                
            except Exception as e:
                logger.error(f"Error getting advisor sessions: {e}")
                return {"status": "error", "error": str(e)}

    # ===== CONTENT MANAGEMENT =====
    
    async def save_advisor_content(
        self,
        advisor_id: str,
        title: str,
        content_text: str,
        content_type: str,
        audience_type: str = "general_education",
        source_session_id: Optional[str] = None,
        source_message_id: Optional[int] = None,
        advisor_notes: Optional[str] = None,
        intended_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save content piece to advisor's library."""
        async with AsyncSessionLocal() as db:
            try:
                # Force string values and ensure lowercase
                content_type_str = str(content_type).lower() if content_type else "linkedin_post"
                audience_type_str = str(audience_type).lower() if audience_type else "general_education"
                status_str = "draft"
                
                # Use raw SQL insert without enum casting for advisor_content table
                query = text("""
                    INSERT INTO advisor_content 
                    (advisor_id, title, content_text, content_type, audience_type, 
                     source_session_id, source_message_id, advisor_notes, 
                     intended_channels, status, created_at, updated_at)
                    VALUES 
                    (:advisor_id, :title, :content_text, :content_type, 
                     :audience_type, :source_session_id, :source_message_id, 
                     :advisor_notes, :intended_channels, :status, NOW(), NOW())
                    RETURNING id, created_at, updated_at
                """)
                
                result = await db.execute(query, {
                    'advisor_id': advisor_id,
                    'title': title,
                    'content_text': content_text,
                    'content_type': content_type_str,
                    'audience_type': audience_type_str,
                    'source_session_id': source_session_id,
                    'source_message_id': source_message_id,
                    'advisor_notes': advisor_notes,
                    'intended_channels': json.dumps(intended_channels) if intended_channels else None,
                    'status': status_str
                })
                
                row = result.fetchone()
                content_id = row[0]
                created_at = row[1]
                updated_at = row[2]
                
                await db.commit()
                
                logger.info(f"Saved advisor content: {content_id} for advisor {advisor_id}")
                
                return {
                    "status": "success",
                    "content": {
                        "id": content_id,
                        "title": title,
                        "content_type": content_type_str,
                        "audience_type": audience_type_str,
                        "status": status_str,
                        "created_at": created_at.isoformat(),
                        "source_session_id": source_session_id
                    }
                }
                
            except Exception as e:
                logger.error(f"Error saving advisor content: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def get_advisor_content_library(
        self,
        advisor_id: str,
        status_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get advisor's content library with filtering."""
        async with AsyncSessionLocal() as db:
            try:
                # Build query with filters
                query = select(AdvisorContent).where(
                    AdvisorContent.advisor_id == advisor_id
                )
                
                # Filter logic
                if status_filter:
                    # If specific status requested, show only that status
                    print(f"DEBUG: Filtering by status: {status_filter}")
                    try:
                        # Try both the raw value and lowercase
                        if status_filter.lower() == 'archived':
                            query = query.where(AdvisorContent.status == 'archived')
                        else:
                            status_enum = ContentStatus(status_filter.lower())
                            query = query.where(AdvisorContent.status == status_enum.value)
                        print(f"DEBUG: Status filter applied successfully")
                    except ValueError as e:
                        print(f"DEBUG: Status enum error: {e}")
                        # Fallback to raw string comparison
                        query = query.where(AdvisorContent.status == status_filter.lower())
                else:
                    # Default: exclude archived content from results
                    query = query.where(AdvisorContent.status != ContentStatus.ARCHIVED.value)
                
                if content_type_filter:
                    content_type_enum = ContentType(content_type_filter.lower())
                    query = query.where(AdvisorContent.content_type == content_type_enum)
                
                # Get content with pagination
                result = await db.execute(
                    query.order_by(desc(AdvisorContent.updated_at))
                    .limit(limit)
                    .offset(offset)
                )
                content_items = result.scalars().all()
                
                # Get total count with same filtering logic
                count_query = select(func.count(AdvisorContent.id)).where(
                    AdvisorContent.advisor_id == advisor_id
                )
                
                if status_filter:
                    # If specific status requested, count only that status
                    print(f"DEBUG: Count filtering by status: {status_filter}")
                    try:
                        if status_filter.lower() == 'archived':
                            count_query = count_query.where(AdvisorContent.status == 'archived')
                        else:
                            count_query = count_query.where(AdvisorContent.status == ContentStatus(status_filter.lower()).value)
                    except ValueError:
                        # Fallback to raw string comparison
                        count_query = count_query.where(AdvisorContent.status == status_filter.lower())
                else:
                    # Default: exclude archived content from count
                    count_query = count_query.where(AdvisorContent.status != ContentStatus.ARCHIVED.value)
                    
                if content_type_filter:
                    count_query = count_query.where(AdvisorContent.content_type == ContentType(content_type_filter.lower()))
                
                count_result = await db.execute(count_query)
                total_count = count_result.scalar()
                
                return {
                    "status": "success",
                    "content": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "content_text": item.content_text,
                            "content_type": item.content_type,
                            "audience_type": item.audience_type,
                            "status": item.status,
                            "advisor_notes": item.advisor_notes,
                            "intended_channels": json.loads(item.intended_channels) if item.intended_channels else None,
                            "source_session_id": item.source_session_id,
                            "submitted_for_review_at": item.submitted_for_review_at.isoformat() if item.submitted_for_review_at else None,
                            "created_at": item.created_at.isoformat(),
                            "updated_at": item.updated_at.isoformat()
                        }
                        for item in content_items
                    ],
                    "total_count": total_count,
                    "has_more": (offset + limit) < total_count
                }
                
            except Exception as e:
                logger.error(f"Error getting advisor content library: {e}")
                return {"status": "error", "error": str(e)}
    
    async def update_content_status(
        self,
        content_id: int,
        advisor_id: str,
        new_status: str,
        advisor_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update content status (e.g., submit for review)."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content belongs to advisor
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Update status with string value (database handles enum casting)
                new_status_str = new_status.lower()
                
                # Use raw SQL for update with enum casting
                if advisor_notes and new_status_str == "submitted":
                    query = text("""
                        UPDATE advisor_content 
                        SET status = CAST(:status AS contentstatus),
                            advisor_notes = :advisor_notes,
                            submitted_for_review_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :content_id
                    """)
                    await db.execute(query, {
                        "status": new_status_str,
                        "advisor_notes": advisor_notes,
                        "content_id": content_id
                    })
                elif advisor_notes:
                    query = text("""
                        UPDATE advisor_content 
                        SET status = CAST(:status AS contentstatus),
                            advisor_notes = :advisor_notes,
                            updated_at = NOW()
                        WHERE id = :content_id
                    """)
                    await db.execute(query, {
                        "status": new_status_str,
                        "advisor_notes": advisor_notes,
                        "content_id": content_id
                    })
                else:
                    query = text("""
                        UPDATE advisor_content 
                        SET status = CAST(:status AS contentstatus),
                            updated_at = NOW()
                        WHERE id = :content_id
                    """)
                    await db.execute(query, {
                        "status": new_status_str,
                        "content_id": content_id
                    })
                
                await db.commit()
                
                logger.info(f"Updated content {content_id} status to {new_status}")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "new_status": new_status,
                    "updated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error updating content status: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}

    async def submit_content_for_review(
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
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Generate secure review token
                review_token = self._generate_review_token(content_id, cco_email)
                
                # Update content with compliance review information
                query = text("""
                    UPDATE advisor_content 
                    SET status = CAST('submitted' AS contentstatus),
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
                
                # Send email notification to CCO
                email_sent = await self._send_review_notification(
                    cco_email=cco_email,
                    content=content,
                    review_token=review_token,
                    notes=notes
                )
                
                logger.info(f"Content {content_id} submitted for review to {cco_email}")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "review_token": review_token,
                    "cco_email": cco_email,
                    "email_sent": email_sent,
                    "submitted_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error submitting content for review: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}

    async def _send_review_notification(
        self,
        cco_email: str,
        content: AdvisorContent,
        review_token: str,
        notes: Optional[str] = None
    ) -> bool:
        """Send email notification to CCO about content review request."""
        try:
            # Basic email template for now
            review_url = f"http://localhost:3003/review/{review_token}"
            
            subject = f"Content Review Request: {content.title}"
            
            email_body = f"""
Dear Compliance Officer,

A new content piece has been submitted for your review:

Title: {content.title}
Content Type: {content.content_type}
Submitted By: {content.advisor_id}
{f'Notes: {notes}' if notes else ''}

Please review this content by clicking the link below:
{review_url}

Best regards,
Fiducia Compliance System
            """
            
            # TODO: Implement actual email sending
            # For now, just log the email
            logger.info(f"Email notification sent to {cco_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Review URL: {review_url}")
            logger.info(f"Email Body: {email_body}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def update_content(
        self,
        content_id: int,
        advisor_id: str,
        title: Optional[str] = None,
        content_text: Optional[str] = None,
        advisor_notes: Optional[str] = None,
        source_metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Update full content (for session updates)."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content belongs to advisor
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Build update data (excluding source_metadata since column doesn't exist)
                update_data = {"updated_at": func.now()}
                
                if title is not None:
                    update_data["title"] = title
                if content_text is not None:
                    update_data["content_text"] = content_text
                if advisor_notes is not None:
                    update_data["advisor_notes"] = advisor_notes
                
                # Perform update
                await db.execute(
                    update(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                    .values(**update_data)
                )
                await db.commit()
                
                # Return updated content
                updated_result = await db.execute(
                    select(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                )
                updated_content = updated_result.scalar_one()
                
                return {
                    "status": "success",
                    "content": {
                        "id": updated_content.id,
                        "title": updated_content.title,
                        "content_text": updated_content.content_text,
                        "advisor_notes": updated_content.advisor_notes,
                        "updated_at": updated_content.updated_at.isoformat() if updated_content.updated_at else None
                    }
                }
                
            except Exception as e:
                await db.rollback()
                print(f"Error updating content: {str(e)}")
                return {"status": "error", "error": str(e)}

    async def get_content_statistics(self, advisor_id: str) -> Dict[str, Any]:
        """Get advisor's content statistics."""
        async with AsyncSessionLocal() as db:
            try:
                # Count by status using raw SQL with proper enum casting
                status_counts = {}
                for status in ContentStatus:
                    query = text("""
                        SELECT COUNT(id) 
                        FROM advisor_content 
                        WHERE advisor_id = :advisor_id 
                        AND status = CAST(:status AS contentstatus)
                    """)
                    result = await db.execute(query, {
                        "advisor_id": advisor_id,
                        "status": status.value
                    })
                    status_counts[status.value] = result.scalar()
                
                # Total content count
                total_result = await db.execute(
                    select(func.count(AdvisorContent.id))
                    .where(AdvisorContent.advisor_id == advisor_id)
                )
                total_count = total_result.scalar()
                
                # Session count
                session_result = await db.execute(
                    select(func.count(AdvisorSessions.id))
                    .where(AdvisorSessions.advisor_id == advisor_id)
                )
                session_count = session_result.scalar()
                
                return {
                    "status": "success",
                    "statistics": {
                        "total_content": total_count,
                        "total_sessions": session_count,
                        "content_by_status": status_counts,
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting content statistics: {e}")
                return {"status": "error", "error": str(e)}


# Create global instance
advisor_workflow_service = AdvisorWorkflowService()
