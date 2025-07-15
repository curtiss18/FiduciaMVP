"""
Content Generation Strategy Factory

Manages selection and instantiation of content generation strategies.
Implements 2-strategy architecture: Advanced (primary) → Legacy (fallback).

Epic: [SCRUM-116] Warren Strategy Consolidation - Reduce Code Redundancy
Task: [SCRUM-122] Update Strategy Factory for 2-Strategy Architecture
"""

import logging
from typing import Dict, Any, List, Optional

from .content_generation_strategy import ContentGenerationStrategy
from .advanced_generation_strategy import AdvancedGenerationStrategy
from .legacy_generation_strategy import LegacyGenerationStrategy

logger = logging.getLogger(__name__)


class StrategyFactory:
    """
    Factory for content generation strategies.
    
    Implements 2-strategy architecture:
    - Advanced strategy (priority 10): Primary strategy with sophisticated context validation
    - Legacy strategy (priority 100): Emergency fallback that always works
    
    Selection Logic:
    1. Try Advanced strategy if it can handle the context
    2. Fall back to Legacy strategy (guaranteed to work)
    """
    
    def __init__(self):
        """Initialize factory with 2-strategy architecture."""
        self._strategies = {
            "advanced": AdvancedGenerationStrategy(),
            "legacy": LegacyGenerationStrategy()
        }
        logger.info("✅ StrategyFactory initialized with 2-strategy architecture: Advanced → Legacy")
    
    def get_strategy(self, strategy_name: str) -> Optional[ContentGenerationStrategy]:
        """
        Get a specific strategy by name.
        
        Args:
            strategy_name: Name of strategy ("advanced" or "legacy")
            
        Returns:
            Strategy instance or None if not found
        """
        strategy = self._strategies.get(strategy_name)
        if strategy:
            logger.debug(f"Retrieved {strategy_name} strategy")
        else:
            logger.warning(f"Strategy '{strategy_name}' not found. Available: {list(self._strategies.keys())}")
        return strategy
    
    def get_best_strategy(self, context_data: Dict[str, Any]) -> ContentGenerationStrategy:
        """
        Select the best strategy for the given context.
        
        Uses simplified 2-strategy selection:
        1. Advanced strategy if it can handle the context
        2. Legacy strategy as guaranteed fallback
        
        Args:
            context_data: Context information for strategy selection
            
        Returns:
            Best strategy for the context (never None due to Legacy fallback)
        """
        # Try Advanced strategy first (primary strategy)
        advanced_strategy = self._strategies["advanced"]
        if advanced_strategy.can_handle(context_data):
            logger.info("🎯 Selected Advanced strategy (sophisticated context handling)")
            logger.debug(f"Advanced strategy can handle context: {self._summarize_context(context_data)}")
            return advanced_strategy
        
        # Fallback to Legacy strategy (always works)
        legacy_strategy = self._strategies["legacy"]
        logger.info("🔄 Selected Legacy strategy (emergency fallback - always works)")
        logger.debug(f"Advanced strategy could not handle context, using Legacy fallback: {self._summarize_context(context_data)}")
        return legacy_strategy
    
    def get_fallback_chain(self, context_data: Dict[str, Any]) -> List[ContentGenerationStrategy]:
        """
        Get ordered list of strategies to try (fallback chain).
        
        For 2-strategy architecture, this is simplified:
        - If Advanced can handle context: [Advanced, Legacy]
        - If Advanced cannot handle context: [Legacy]
        
        Args:
            context_data: Context information for strategy selection
            
        Returns:
            Ordered list of strategies to try
        """
        chain = []
        
        # Advanced strategy first (if it can handle the context)
        advanced_strategy = self._strategies["advanced"]
        if advanced_strategy.can_handle(context_data):
            chain.append(advanced_strategy)
            logger.debug("Fallback chain: Advanced strategy included")
        
        # Legacy strategy always included as final fallback
        legacy_strategy = self._strategies["legacy"]
        chain.append(legacy_strategy)
        logger.debug("Fallback chain: Legacy strategy included as final fallback")
        
        strategy_names = [s.get_strategy_name() for s in chain]
        logger.info(f"📋 Fallback chain: {' → '.join(strategy_names)}")
        
        return chain
    
    def get_all_strategies(self) -> Dict[str, ContentGenerationStrategy]:
        """
        Get all registered strategies.
        
        Returns:
            Dictionary of all available strategies
        """
        logger.debug(f"Available strategies: {list(self._strategies.keys())}")
        return self._strategies.copy()
    
    def _summarize_context(self, context_data: Dict[str, Any]) -> str:
        """
        Create a summary of context data for logging.
        
        Args:
            context_data: Context data to summarize
            
        Returns:
            Human-readable summary string
        """
        if not isinstance(context_data, dict):
            return f"Invalid context type: {type(context_data)}"
        
        summary_parts = []
        
        # Check key context elements
        if context_data.get("marketing_examples"):
            summary_parts.append(f"marketing_examples({len(context_data['marketing_examples'])})")
        if context_data.get("disclaimers"):
            summary_parts.append(f"disclaimers({len(context_data['disclaimers'])})")
        if context_data.get("session_documents"):
            summary_parts.append(f"documents({len(context_data['session_documents'])})")
        if context_data.get("conversation_context"):
            summary_parts.append("conversation")
        
        if summary_parts:
            return f"Context: {', '.join(summary_parts)}"
        else:
            return "Context: minimal/empty"


# Global strategy factory instance
strategy_factory = StrategyFactory()
