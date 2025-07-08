"""
Content Generation Strategy Factory

Manages selection and instantiation of content generation strategies.
"""

import logging
from typing import Dict, Any, List, Optional

from .content_generation_strategy import ContentGenerationStrategy
from .advanced_generation_strategy import AdvancedGenerationStrategy
from .standard_generation_strategy import StandardGenerationStrategy
from .legacy_generation_strategy import LegacyGenerationStrategy

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for content generation strategies."""
    
    def __init__(self):
        self._strategies = {
            "advanced": AdvancedGenerationStrategy(),
            "standard": StandardGenerationStrategy(),
            "legacy": LegacyGenerationStrategy()
        }
    
    def get_strategy(self, strategy_name: str) -> Optional[ContentGenerationStrategy]:
        """Get a specific strategy by name."""
        return self._strategies.get(strategy_name)
    
    def get_best_strategy(self, context_data: Dict[str, Any]) -> ContentGenerationStrategy:
        """Select the best strategy for the given context."""
        available_strategies = [
            strategy for strategy in self._strategies.values()
            if strategy.can_handle(context_data)
        ]
        
        if not available_strategies:
            logger.warning("No strategies can handle context, using legacy fallback")
            return self._strategies["legacy"]
        
        available_strategies.sort(key=lambda s: s.get_strategy_priority())
        selected_strategy = available_strategies[0]
        logger.info(f"Selected {selected_strategy.get_strategy_name()} strategy")
        
        return selected_strategy
    
    def get_fallback_chain(self, context_data: Dict[str, Any]) -> List[ContentGenerationStrategy]:
        """Get ordered list of strategies to try (fallback chain)."""
        available_strategies = [
            strategy for strategy in self._strategies.values()
            if strategy.can_handle(context_data)
        ]
        
        available_strategies.sort(key=lambda s: s.get_strategy_priority())
        
        # Always include legacy as final fallback
        legacy_strategy = self._strategies["legacy"]
        if legacy_strategy not in available_strategies:
            available_strategies.append(legacy_strategy)
        
        return available_strategies
    
    def get_all_strategies(self) -> Dict[str, ContentGenerationStrategy]:
        """Get all registered strategies."""
        return self._strategies.copy()


# Global strategy factory instance
strategy_factory = StrategyFactory()
