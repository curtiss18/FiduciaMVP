"""
Context Quality Assessor

Handles context quality assessment and sufficiency determination for Warren.

Responsibilities:
- Evaluate quality of retrieved context (marketing examples, disclaimers)
- Calculate quality scores based on multiple factors
- Determine if context is sufficient for content generation
- Provide quality reasoning for decision making

"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContextQualityAssessor:
    """Service for assessing context quality and sufficiency."""
    
    def __init__(self):
        """Initialize the context quality assessor."""
        pass
    
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
    
    def is_context_sufficient(self, context_data: Dict[str, Any]) -> bool:
        """
        Helper method to check if context is sufficient for content generation.
        Convenience wrapper around assess_context_quality().
        """
        return self.assess_context_quality(context_data)["sufficient"]
    
    def get_quality_score(self, context_data: Dict[str, Any]) -> float:
        """
        Helper method to get just the quality score.
        Convenience wrapper around assess_context_quality().
        """
        return self.assess_context_quality(context_data)["score"]
    
    def get_quality_reason(self, context_data: Dict[str, Any]) -> str:
        """
        Helper method to get just the quality reason.
        Convenience wrapper around assess_context_quality().
        """
        return self.assess_context_quality(context_data)["reason"]
