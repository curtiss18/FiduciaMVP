# ConversationManagerService
"""
Warren chat session management service following Warren pattern.

Responsibilities:
- Create and manage Warren chat sessions for advisors
- Save user and Warren messages with conversation threading
- Retrieve conversation history with proper advisor access control
- Session activity tracking and metadata management
- Warren-specific metadata handling (sources, confidence, search strategy)

Extracted from advisor_workflow_service.py as part of SCRUM-98.
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, func, and_, update, desc
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ConversationManagerService:
    """Warren chat session management following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def create_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new Warren chat session for advisor."""
        async with AsyncSessionLocal() as db:
            try:
                session_id = f"session_{advisor_id}_{uuid.uuid4().hex[:8]}"
                default_title = f"Chat Session {datetime.now().strftime('%m/%d %H:%M')}"
                session = AdvisorSessions(
                    advisor_id=advisor_id,
                    session_id=session_id,
                    title=title or default_title
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
    
    async def save_message(
        self,
        session_id: str,
        message_type: str,  # 'user' or 'warren'
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Save Warren message with metadata handling."""
        async with AsyncSessionLocal() as db:
            try:
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
                
                logger.info(f"Saved message for session {session_id}: {message_type}")
                
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
        """Get conversation history with access control."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify session belongs to advisor (security)
                session_result = await db.execute(
                    select(AdvisorSessions)
                    .where(and_(
                        AdvisorSessions.session_id == session_id,
                        AdvisorSessions.advisor_id == advisor_id
                    ))
                )
                session = session_result.scalar_one_or_none()
                
                if not session:
                    logger.warning(f"Session access denied: {session_id} for advisor {advisor_id}")
                    return {"status": "error", "error": "Session not found or access denied"}
                
                # Get messages ordered by creation time
                messages_result = await db.execute(
                    select(AdvisorMessages)
                    .where(AdvisorMessages.session_id == session_id)
                    .order_by(AdvisorMessages.created_at)
                )
                messages = messages_result.scalars().all()
                
                logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
                
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
        """Get advisor's sessions with pagination."""
        async with AsyncSessionLocal() as db:
            try:
                # Get sessions ordered by last activity
                result = await db.execute(
                    select(AdvisorSessions)
                    .where(AdvisorSessions.advisor_id == advisor_id)
                    .order_by(desc(AdvisorSessions.last_activity))
                    .limit(limit)
                    .offset(offset)
                )
                sessions = result.scalars().all()
                
                # Get total count for pagination
                count_result = await db.execute(
                    select(func.count(AdvisorSessions.id))
                    .where(AdvisorSessions.advisor_id == advisor_id)
                )
                total_count = count_result.scalar()
                
                logger.info(f"Retrieved {len(sessions)} sessions for advisor {advisor_id}")
                
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
    
    async def update_session_activity(self, session_id: str) -> None:
        """Update session activity timestamp."""
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(
                    update(AdvisorSessions)
                    .where(AdvisorSessions.session_id == session_id)
                    .values(
                        last_activity=func.now(),
                        updated_at=func.now()
                    )
                )
                await db.commit()
                logger.debug(f"Updated session activity: {session_id}")
                
            except Exception as e:
                logger.error(f"Error updating session activity: {e}")
                await db.rollback()
