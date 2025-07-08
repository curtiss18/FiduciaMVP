"""
Context Retrieval Service

Handles all context retrieval operations for Warren content generation.

Responsibilities:
- Vector search for marketing examples and compliance content
- Text search fallback for compliance content  
- Context result combination and deduplication
- Context quality assessment

"""

import logging
from typing import List, Dict, Any, Optional

from src.services.vector_search_service import VectorSearchService
from src.services.warren_database_service import WarrenDatabaseService
from src.models.refactored_database import ContentType

logger = logging.getLogger(__name__)

class ContextRetrievalService:
    
    def __init__(self, 
                 vector_search_service=None,
                 warren_db_service=None,
                 enable_vector_search: bool = True,
                 vector_similarity_threshold: float = 0.1,
                 min_results_threshold: int = 1):
        """Initialize the context retrieval service."""
        # Dependency injection for testing, with defaults for production
        self.vector_search_service = vector_search_service or VectorSearchService()
        self.warren_db_service = warren_db_service or WarrenDatabaseService()
        
        # Configuration (matching enhanced_warren_service defaults)
        self.enable_vector_search = enable_vector_search
        self.vector_similarity_threshold = vector_similarity_threshold
        self.min_results_threshold = min_results_threshold
    
    async def get_vector_search_context(
        self,
        user_request: str,
        content_type: str,
        content_type_enum: Optional[ContentType],
        audience_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get context using vector similarity search.
        Direct port of enhanced_warren_service._get_vector_search_context()
        """
        try:
            if not self.enable_vector_search:
                return {"marketing_examples": [], "disclaimers": [], "vector_available": False}
            
            # Check if vector search is available
            readiness_check = await self.vector_search_service.check_readiness()
            if not readiness_check.get("ready", False):
                logger.warning(f"Vector search not ready: {readiness_check.get('reason', 'Unknown')}")
                return {"marketing_examples": [], "disclaimers": [], "vector_available": False}
            
            # Search for relevant marketing content examples
            marketing_examples = await self.vector_search_service.search_marketing_content(
                query_text=user_request,
                content_type=content_type_enum,
                similarity_threshold=self.vector_similarity_threshold,
                limit=3
            )
            
            # Try to search compliance rules, but fall back gracefully if it fails
            compliance_rules = []
            try:
                compliance_rules = await self.vector_search_service.search_compliance_rules(
                    query_text=f"{content_type} compliance rules disclaimer",
                    content_type=content_type,
                    similarity_threshold=0.1,
                    limit=3
                )
            except Exception as e:
                logger.warning(f"Compliance rules vector search failed: {e}, continuing with marketing examples only")
                compliance_rules = []
            
            # If no compliance rules found via vector search, try marketing content for disclaimers as backup
            disclaimers = compliance_rules
            if not disclaimers:
                disclaimer_query = f"{content_type} disclaimer risk disclosure"
                potential_disclaimers = await self.vector_search_service.search_marketing_content(
                    query_text=disclaimer_query,
                    similarity_threshold=0.1,
                    limit=3
                )
                
                # Filter for disclaimer-like content
                disclaimers = [
                    d for d in potential_disclaimers 
                    if any(keyword in d.get("title", "").lower() or keyword in d.get("tags", "").lower() 
                           for keyword in ["disclaimer", "risk", "disclosure"])
                ]
            
            return {
                "marketing_examples": marketing_examples,
                "disclaimers": disclaimers,
                "vector_available": True,
                "search_method": "vector",
                "vector_results_count": len(marketing_examples),
                "disclaimer_count": len(disclaimers),
                "total_sources": len(marketing_examples) + len(disclaimers)
            }
            
        except Exception as e:
            logger.error(f"Error in vector search context: {str(e)}")
            return {"marketing_examples": [], "disclaimers": [], "vector_available": False, "error": str(e)}
    
    async def get_text_search_context(
        self,
        user_request: str,
        content_type: str,
        content_type_enum: Optional[ContentType]
    ) -> Dict[str, Any]:
        """
        Get context using traditional text search (fallback method).
        Direct port of enhanced_warren_service._get_text_search_context()
        """
        try:
            # Use the original Warren database service text search logic
            marketing_examples = await self.warren_db_service.search_marketing_content(
                query=user_request,
                content_type=content_type_enum,
                limit=3
            )
            
            disclaimers = await self.warren_db_service.get_disclaimers_for_content_type(content_type)
            
            return {
                "marketing_examples": marketing_examples,
                "disclaimers": disclaimers,
                "search_method": "text",
                "text_results_count": len(marketing_examples),
                "disclaimer_count": len(disclaimers),
                "total_sources": len(marketing_examples) + len(disclaimers)
            }
            
        except Exception as e:
            logger.error(f"Error in text search context: {str(e)}")
            return {"marketing_examples": [], "disclaimers": [], "error": str(e)}
    
    def combine_contexts(
        self, 
        vector_context: Dict[str, Any], 
        text_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine vector and text search contexts intelligently.
        Direct port of enhanced_warren_service._combine_contexts()
        """
        # Start with vector context
        combined = vector_context.copy()
        
        # Add text results that aren't already included
        vector_ids = {ex.get("id") for ex in vector_context.get("marketing_examples", [])}
        text_examples = [
            ex for ex in text_context.get("marketing_examples", [])
            if ex.get("id") not in vector_ids
        ]
        
        # Combine marketing examples (vector first, then unique text results)
        combined["marketing_examples"] = (
            vector_context.get("marketing_examples", []) + text_examples[:2]
        )
        
        # For disclaimers, prefer vector results but supplement with text if needed
        if len(vector_context.get("disclaimers", [])) < 2:
            vector_disclaimer_ids = {d.get("id") for d in vector_context.get("disclaimers", [])}
            text_disclaimers = [
                d for d in text_context.get("disclaimers", [])
                if d.get("id") not in vector_disclaimer_ids
            ]
            combined["disclaimers"] = (
                vector_context.get("disclaimers", []) + text_disclaimers[:2]
            )
        
        # Update metadata
        combined["search_strategy"] = "hybrid"
        combined["text_results_count"] = len(text_examples)
        combined["total_sources"] = (
            len(combined.get("marketing_examples", [])) + 
            len(combined.get("disclaimers", []))
        )
        
        return combined
    
    def assess_context_quality(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of retrieved context and determine if it's sufficient.
        Direct port of enhanced_warren_service._assess_context_quality()
        """
        marketing_count = len(context_data.get("marketing_examples", []))
        disclaimer_count = len(context_data.get("disclaimers", []))
        vector_available = context_data.get("vector_available", False)
        
        # Quality assessment logic (exact copy from original)
        if not vector_available:
            return {"sufficient": False, "score": 0.0, "reason": "vector_search_unavailable"}
        
        if marketing_count == 0 and disclaimer_count == 0:
            return {"sufficient": False, "score": 0.1, "reason": "no_relevant_content_found"}
        
        if disclaimer_count == 0:
            return {"sufficient": False, "score": 0.4, "reason": "no_disclaimers_found"}
        
        # Context is sufficient if we have disclaimers (minimum requirement)
        total_sources = marketing_count + disclaimer_count
        quality_score = min(1.0, (marketing_count * 0.4) + (disclaimer_count * 0.3) + 0.3)
        
        return {"sufficient": True, "score": quality_score, "reason": "sufficient_quality"}
