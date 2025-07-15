"""
Content Generation Strategies Package

Provides strategy pattern implementation for different content generation approaches.

Epic: [SCRUM-116] Warren Strategy Consolidation - Reduce Code Redundancy

Available Strategies (2-Strategy Architecture):
- AdvancedGenerationStrategy: Sophisticated context assembly with document integration
- LegacyGenerationStrategy: Manual context building, emergency fallback (always works)

Strategy Selection:
- Advanced strategy (priority 10): Handles rich context with validation
- Legacy strategy (priority 100): Ultimate fallback, handles any context

Usage:
    from src.services.warren.strategies import strategy_factory
    
    # Automatic best strategy selection
    strategy = strategy_factory.get_best_strategy(context_data)
    result = await strategy.generate_content(...)
    
    # Manual strategy selection
    advanced_strategy = strategy_factory.get_strategy("advanced")
    legacy_strategy = strategy_factory.get_strategy("legacy")
    
    # Fallback chain for error handling
    fallback_chain = strategy_factory.get_fallback_chain(context_data)
"""

from .content_generation_strategy import ContentGenerationStrategy, GenerationResult
from .base_generation_strategy import BaseGenerationStrategy
from .advanced_generation_strategy import AdvancedGenerationStrategy
from .legacy_generation_strategy import LegacyGenerationStrategy
from .strategy_factory import StrategyFactory, strategy_factory

__all__ = [
    'ContentGenerationStrategy',
    'GenerationResult',
    'BaseGenerationStrategy',
    'AdvancedGenerationStrategy',
    'LegacyGenerationStrategy',
    'StrategyFactory',
    'strategy_factory'
]
