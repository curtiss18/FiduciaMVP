"""
Conversation Context Service

Handles conversation memory and session context management for Warren.

Responsibilities:
- Retrieve conversation history for sessions
- Manage session document context
- Save conversation turns with metadata
- Handle context persistence and retrieval
- Session lifecycle management

"""

import logging
from typing import List, Dict, Any, Optional

from src.services.conversation_manager import ConversationManager
from src.services.document_manager import DocumentManager
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ConversationContextService:
    """Service for managing conversation memory and session context."""
    
    def __init__(self, 
                 conversation_manager=None,
                 document_manager=None):
        """Initialize the conversation context service."""
        # Dependency injection for testing, with defaults for production
        self.conversation_manager_class = conversation_manager or ConversationManager
        self.document_manager = document_manager or DocumentManager()
    
    async def get_conversation_context(self, session_id: str) -> str:
        """
        Get conversation context for a session using ConversationManager.
        Direct port of enhanced_warren_service._get_conversation_context()
        """
        try:
            async with AsyncSessionLocal() as db_session:
                conversation_manager = self.conversation_manager_class(db_session)
                return await conversation_manager.get_conversation_context(session_id)
        except Exception as e:
            logger.error(f"Error getting conversation context for session {session_id}: {e}")
            return ""
    
    async def get_session_documents(self, session_id: str) -> List[Dict]:
        """Get session documents for document context."""
        if not session_id:
            logger.info("No session_id provided, skipping session documents")
            return []
        
        async with AsyncSessionLocal() as db_session:
            return await self._get_session_documents_with_session(db_session, session_id)
    
    async def _get_session_documents_with_session(self, db_session, session_id: str) -> List[Dict]:
        """Get session documents using provided database session (efficiency improvement)."""
        session_documents = []
        logger.info(f"Getting session documents for session {session_id}")
        try:
            documents = await self.document_manager.get_session_documents(
                session_id=session_id,
                include_content=True
            )
            
            logger.info(f"Found {len(documents)} total documents for session")
            for idx, doc in enumerate(documents):
                logger.info(f"Document {idx+1}: {doc.get('title', 'Unknown')} "
                          f"Status: {doc.get('processing_status', 'Unknown')} "
                          f"Summary: {len(doc.get('summary', '')) if doc.get('summary') else 0} chars")
            
            # Filter for processed documents with summaries
            for doc in documents:
                if doc.get('processing_status') == 'processed' and doc.get('summary'):
                    session_documents.append({
                        'title': doc['title'],
                        'summary': doc['summary'],
                        'content_type': doc['content_type'],
                        'word_count': doc.get('word_count', 0),
                        'document_id': doc['id']
                    })
            
            if session_documents:
                logger.info(f"Found {len(session_documents)} processed documents with summaries")
                for doc in session_documents:
                    logger.info(f"{doc['title']} ({doc['content_type']}) - {doc['word_count']} words")
            else:
                logger.info(f"No processed documents with summaries found for session {session_id}")
                
        except Exception as e:
            logger.warning(f"Failed to retrieve session documents: {str(e)}")
        
        return session_documents
    
    async def get_session_context(self, session_id: str, use_conversation_context: bool = True) -> Dict[str, Any]:
        """
        Get complete session context including conversation history and documents.
        Combines the conversation and document retrieval logic from enhanced_warren_service.
        """
        conversation_context = ""
        session_documents = []
        
        if session_id:
            # Use single database session for both operations (efficiency improvement)
            async with AsyncSessionLocal() as db_session:
                # Get conversation context if enabled
                if use_conversation_context:
                    logger.info(f"Getting conversation context for session {session_id}")
                    try:
                        conversation_manager = self.conversation_manager_class(db_session)
                        conversation_context = await conversation_manager.get_conversation_context(session_id)
                        if conversation_context:
                            logger.info(f"Retrieved conversation context: {len(conversation_context)} characters")
                        else:
                            logger.info(f"No conversation context found for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error getting conversation context for session {session_id}: {e}")
                        conversation_context = ""
                
                # Get session documents using same database session
                session_documents = await self._get_session_documents_with_session(db_session, session_id)
        else:
            if not use_conversation_context:
                logger.info("Conversation context disabled")
            logger.info("No session_id provided, skipping session context")
        
        return {
            "conversation_context": conversation_context,
            "session_documents": session_documents,
            "session_id": session_id,
            "conversation_context_available": bool(conversation_context),
            "session_documents_available": bool(session_documents),
            "session_documents_count": len(session_documents)
        }
    
    async def save_conversation_turn(self, session_id: str, user_input: str, warren_response: str, context_data: Dict[str, Any]):
        """Save a conversation turn using ConversationManager."""
        try:
            # Prepare Warren metadata for storage
            warren_metadata = {
                'sources_used': context_data.get('marketing_examples', []) + context_data.get('disclaimers', []),
                'generation_confidence': context_data.get('context_quality_score', 0.5),
                'search_strategy': context_data.get('search_strategy', 'unknown'),
                'total_sources': context_data.get('total_sources', 0),
                'marketing_examples': context_data.get('marketing_examples_count', 0),
                'compliance_rules': context_data.get('compliance_rules_count', 0)
            }
            
            async with AsyncSessionLocal() as db_session:
                conversation_manager = self.conversation_manager_class(db_session)
                await conversation_manager.save_conversation_turn(
                    session_id=session_id, user_input=user_input,
                    warren_response=warren_response, warren_metadata=warren_metadata
                )
                logger.info(f"Saved conversation turn for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation turn for session {session_id}: {e}")
            # Don't raise the exception - conversation saving shouldn't break content generation
