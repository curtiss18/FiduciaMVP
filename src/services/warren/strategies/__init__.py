"""
Content Generation Strategies Package

Provides strategy pattern implementation for different content generation approaches.

Epic: [SCRUM-76] Refactor Enhanced Warren Service
Task: [SCRUM-82] Create ContentGenerationStrategy Interface

Available Strategies:
- AdvancedGenerationStrategy: Phase 2 advanced context assembly
- StandardGenerationStrategy: Phase 1 standard context assembly
- LegacyGenerationStrategy: Original manual context building

Usage:
    from src.services.warren.strategies import strategy_factory
    
    strategy = strategy_factory.get_best_strategy(context_data)
    result = await strategy.generate_content(...)
"""

from .content_generation_strategy import ContentGenerationStrategy, GenerationResult
from .advanced_generation_strategy import AdvancedGenerationStrategy
from .standard_generation_strategy import StandardGenerationStrategy
from .legacy_generation_strategy import LegacyGenerationStrategy
from .strategy_factory import StrategyFactory, strategy_factory

__all__ = [
    'ContentGenerationStrategy',
    'GenerationResult',
    'AdvancedGenerationStrategy',
    'StandardGenerationStrategy', 
    'LegacyGenerationStrategy',
    'StrategyFactory',
    'strategy_factory'
]
