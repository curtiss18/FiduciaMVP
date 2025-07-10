"""Context gathering coordinator service"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ContextElement
from .conversation_gatherer import ConversationGatherer
from .compliance_gatherer import ComplianceGatherer
from .document_gatherer import DocumentGatherer

logger = logging.getLogger(__name__)


class ContextGatherer:
    
    def __init__(self):
        self.conversation_gatherer = ConversationGatherer()
        self.compliance_gatherer = ComplianceGatherer()
        self.document_gatherer = DocumentGatherer()
    
    async def gather_all_context(
        self,
        session_id: str,
        db_session: AsyncSession,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[ContextElement]:
        
        all_elements = []
        
        # Gather conversation context
        try:
            conversation_elements = await self.conversation_gatherer.gather_context(
                session_id=session_id,
                db_session=db_session
            )
            all_elements.extend(conversation_elements)
        except Exception as e:
            logger.warning(f"Failed to gather conversation context: {e}")
        
        # Gather compliance context
        try:
            compliance_elements = await self.compliance_gatherer.gather_context(
                context_data=context_data
            )
            all_elements.extend(compliance_elements)
        except Exception as e:
            logger.warning(f"Failed to gather compliance context: {e}")
        
        # Gather document context
        try:
            document_elements = await self.document_gatherer.gather_context(
                session_id=session_id,
                db_session=db_session,
                context_data=context_data
            )
            all_elements.extend(document_elements)
        except Exception as e:
            logger.warning(f"Failed to gather document context: {e}")
        
        return all_elements
    
    async def gather_conversation_only(
        self,
        session_id: str,
        db_session: AsyncSession
    ) -> List[ContextElement]:
        
        return await self.conversation_gatherer.gather_context(
            session_id=session_id,
            db_session=db_session
        )
    
    async def gather_compliance_only(
        self,
        context_data: Dict[str, Any]
    ) -> List[ContextElement]:
        
        return await self.compliance_gatherer.gather_context(
            context_data=context_data
        )
    
    async def gather_documents_only(
        self,
        session_id: str,
        db_session: AsyncSession
    ) -> List[ContextElement]:
        
        return await self.document_gatherer.gather_context(
            session_id=session_id,
            db_session=db_session
        )
