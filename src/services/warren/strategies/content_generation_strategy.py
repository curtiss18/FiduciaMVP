"""
Content Generation Strategy Interface

Abstract base class for all content generation strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GenerationResult:
    """Result container for content generation."""
    
    def __init__(self):
        self.content = None
        self.success = False
        self.error_message = None
        self.metadata = {}
        self.strategy_used = None
        self.generation_time = 0.0
        self.token_usage = {}


class ContentGenerationStrategy(ABC):
    """Abstract base class for content generation strategies."""
    
    @abstractmethod
    async def generate_content(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str] = None,
        current_content: Optional[str] = None,
        is_refinement: bool = False,
        youtube_context: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Generate content using this strategy."""
        pass
    
    @abstractmethod
    def can_handle(self, context_data: Dict[str, Any]) -> bool:
        """Determine if this strategy can handle the given context."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name identifier for this strategy."""
        pass
    
    def get_strategy_priority(self) -> int:
        """Get the priority of this strategy (lower number = higher priority)."""
        return 100
    
    def requires_advanced_context(self) -> bool:
        """Whether this strategy requires advanced context assembly."""
        return False
