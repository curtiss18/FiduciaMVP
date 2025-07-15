"""
Base Generation Strategy

Abstract base class containing common functionality for all content generation strategies.
Eliminates code duplication by extracting shared methods from individual strategies.
"""

import logging
import time
from typing import Dict, Any, Optional

from .content_generation_strategy import ContentGenerationStrategy, GenerationResult

logger = logging.getLogger(__name__)


class BaseGenerationStrategy(ContentGenerationStrategy):
    """
    Abstract base class containing common functionality for all strategies.
    
    """
    
    def _extract_platform_from_content_type(self, content_type: str) -> str:
        """Extract platform from content type."""
        platform_mapping = {
            'linkedin_post': 'linkedin',
            'email_template': 'email',
            'website_content': 'website',
            'newsletter': 'newsletter',
            'social_media': 'twitter',
            'blog_post': 'website'
        }
        return platform_mapping.get(content_type.lower(), 'general')
    
    def _handle_generation_error(self, error: Exception, strategy_name: str) -> GenerationResult:
        """Common error handling pattern for all strategies."""
        result = GenerationResult()
        result.success = False
        result.error_message = str(error)
        result.strategy_used = strategy_name
        result.metadata = {"error_type": f"{strategy_name}_generation_failure"}
        logger.error(f"❌ {strategy_name.title()} generation strategy failed: {error}")
        return result
    
    def _populate_success_result(
        self, 
        result: GenerationResult, 
        content: str, 
        strategy_name: str,
        start_time: float,
        **metadata_kwargs
    ) -> None:
        """Common success result population for all strategies."""
        result.content = content
        result.success = True
        result.strategy_used = strategy_name
        result.generation_time = time.time() - start_time
        
        # Merge provided metadata with base metadata
        base_metadata = {
            "strategy_used": strategy_name,
            "generation_time": result.generation_time
        }
        result.metadata = {**base_metadata, **metadata_kwargs}
    
    def _build_base_prompt_context(
        self, 
        content_type: str, 
        audience_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build common prompt context used by all strategies."""
        return {
            'platform': self._extract_platform_from_content_type(content_type),
            'content_type': content_type,
            'audience_type': audience_type
        }
    
    def _validate_basic_inputs(
        self, 
        user_request: str, 
        content_type: str
    ) -> tuple[bool, Optional[str]]:
        """Basic input validation common to all strategies."""
        if not user_request or not user_request.strip():
            return False, "User request cannot be empty"
        
        if not content_type or not content_type.strip():
            return False, "Content type cannot be empty"
        
        return True, None
