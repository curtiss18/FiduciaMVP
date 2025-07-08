"""
Search Orchestrator

Handles search execution and fallback logic for Warren content generation.

Responsibilities:
- Execute vector search with fallback to text search
- Coordinate with ContextRetrievalService and ContextQualityAssessor
- Manage search strategy selection and metadata

"""

import logging
from typing import Dict, Any, Optional

from src.services.warren.context_retrieval_service import ContextRetrievalService
from src.services.warren.context_quality_assessor import ContextQualityAssessor
from src.models.refactored_database import ContentType

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Service for orchestrating search execution with fallback logic."""
    
    def __init__(self, 
                 context_retrieval_service=None,
                 context_quality_assessor=None):
        """Initialize the search orchestrator."""
        # Dependency injection for testing, with defaults for production
        self.context_retrieval = context_retrieval_service or ContextRetrievalService()
        self.quality_assessor = context_quality_assessor or ContextQualityAssessor()
    
    async def execute_search_with_fallback(
        self,
        user_request: str,
        content_type: str,
        content_type_enum: Optional[ContentType],
        audience_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute search with fallback logic.
        """
        # Try vector search first (primary method)
        context_data = await self.context_retrieval.get_vector_search_context(
            user_request, content_type, content_type_enum, audience_type
        )
        
        # Validate context quality
        context_quality = self.quality_assessor.assess_context_quality(context_data)
        
        # Fall back to text search if vector search results are poor
        if not context_quality["sufficient"]:
            fallback_context = await self.context_retrieval.get_text_search_context(
                user_request, content_type, content_type_enum
            )
            
            # Combine vector and text results
            context_data = self.context_retrieval.combine_contexts(context_data, fallback_context)
            context_data["fallback_used"] = True
            context_data["fallback_reason"] = context_quality["reason"]
        else:
            context_data["fallback_used"] = False
            context_data["search_strategy"] = "vector"  # Explicitly set vector strategy
        
        return context_data
