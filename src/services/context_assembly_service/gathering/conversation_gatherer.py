"""Conversation context gathering service"""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces import ContextGatheringStrategy
from ..models import ContextType, ContextElement
from src.services.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class ConversationGatherer(ContextGatheringStrategy):
    
    def __init__(self):
        pass
    
    async def gather_context(
        self, 
        session_id: str, 
        db_session: AsyncSession,
        context_data: Optional[dict] = None
    ) -> List[ContextElement]:
        
        elements = []
        
        try:
            conversation_manager = ConversationManager(db_session)
            conversation_context = await conversation_manager.get_conversation_context(session_id)
            
            if conversation_context:
                element = ContextElement(
                    content=conversation_context,
                    context_type=ContextType.CONVERSATION_HISTORY,
                    priority_score=7.0,  # High priority for conversation context
                    relevance_score=0.8,  # Generally relevant
                    token_count=len(conversation_context) // 4,  # Rough estimation
                    source_metadata={"session_id": session_id}
                )
                elements.append(element)
                
        except Exception as e:
            logger.warning(f"Could not get conversation context: {e}")
        
        return elements
    
    def get_supported_context_types(self) -> List[ContextType]:
        return [ContextType.CONVERSATION_HISTORY]
