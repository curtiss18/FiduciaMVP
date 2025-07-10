"""Document context gathering service"""

import logging
import tiktoken
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ContextElement, ContextType

logger = logging.getLogger(__name__)


class DocumentGatherer:
    
    def __init__(self):
        # Import here to avoid circular import issue
        from ...document_manager import DocumentManager
        self.document_manager = DocumentManager()
        
        # Use direct tiktoken instead of importing TokenManager to avoid circular import
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        if not text:
            return 0
            
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4
    
    async def gather_context(
        self,
        session_id: str,
        db_session: AsyncSession,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[ContextElement]:
        """Gather document context from session documents."""
        elements = []
        
        try:
            # Get session documents with summaries
            documents = await self.document_manager.get_session_documents(
                session_id=session_id,
                include_content=True
            )
            
            for doc in documents:
                if doc.get('processing_status') != 'completed':
                    continue
                    
                content_parts = [f"## DOCUMENT: {doc['title']}"]
                content_parts.append(f"Document Type: {doc['content_type'].upper()}")
                content_parts.append(f"Word Count: {doc.get('word_count', 'Unknown')}")
                
                if doc.get('summary'):
                    content_parts.append("**DOCUMENT SUMMARY:**")
                    content_parts.append(doc['summary'])
                
                content = "\n".join(content_parts)
                
                elements.append(ContextElement(
                    content=content,
                    context_type=ContextType.DOCUMENT_SUMMARIES,
                    priority_score=0.6,
                    relevance_score=0.5,  # Basic implementation
                    token_count=self.count_tokens(content),
                    source_metadata={
                        "type": "session_document",
                        "document_id": doc.get('id'),
                        "document_title": doc['title'],
                        "document_type": doc['content_type'],
                        "word_count": doc.get('word_count', 0)
                    }
                ))
                
        except Exception as e:
            logger.warning(f"Failed to gather document context: {e}")
        
        logger.info(f"Gathered {len(elements)} document context elements")
        return elements
