"""
Warren Refactored Services

This package contains the refactored Warren services, breaking down the monolithic
enhanced_warren_service.py into focused, testable, and maintainable components.

Architecture:
- ContentGenerationOrchestrator: Main workflow coordinator
- SearchStrategyManager: Manages search strategies & fallbacks  
- ContextRetrievalService: Handles all context search operations
- ConversationContextService: Manages session & conversation memory
- PromptConstructionService: Builds prompts for generation scenarios
- ContextQualityAssessor: Evaluates context quality & sufficiency
- FallbackManager: Centralizes error recovery & degradation strategies
- strategies/: Content generation strategy implementations

Epic: [SCRUM-76] Refactor Enhanced Warren Service
"""

# Import all services for easy access
from .context_retrieval_service import ContextRetrievalService
from .conversation_context_service import ConversationContextService
from .context_quality_assessor import ContextQualityAssessor
from .search_orchestrator import SearchOrchestrator

# Future services (not yet implemented)
# from .prompt_construction_service import PromptConstructionService
# from .fallback_manager import FallbackManager
# from .content_generation_orchestrator import ContentGenerationOrchestrator

# Future strategy interfaces (not yet implemented)
# from .strategies.content_generation_strategy import ContentGenerationStrategy
# from .strategies.advanced_generation_strategy import AdvancedGenerationStrategy
# from .strategies.standard_generation_strategy import StandardGenerationStrategy
# from .strategies.legacy_generation_strategy import LegacyGenerationStrategy

__all__ = [
    # Core Services (implemented)
    'ContextRetrievalService',
    'ConversationContextService', 
    'ContextQualityAssessor',
    'SearchOrchestrator',
    
    # Future Services (not yet implemented)
    # 'PromptConstructionService',
    # 'FallbackManager',
    # 'ContentGenerationOrchestrator',
    
    # Future Strategy Interfaces (not yet implemented)
    # 'ContentGenerationStrategy',
    # 'AdvancedGenerationStrategy',
    # 'StandardGenerationStrategy',
    # 'LegacyGenerationStrategy',
]
"""
Warren Refactored Services

This package contains the refactored Warren services, breaking down the monolithic
enhanced_warren_service into focused, testable components using clean architecture patterns.

Key Components:
- ContentGenerationOrchestrator: Main workflow coordinator
- SearchOrchestrator: Search strategy management  
- ConversationContextService: Session & conversation memory
- ContextQualityAssessor: Context quality evaluation
- PromptConstructionService: Prompt building & optimization
- FallbackManager: Error recovery strategies
- Generation Strategies: Pluggable generation approaches
"""

# Import main orchestrator for easy access
from .content_generation_orchestrator import ContentGenerationOrchestrator

# Create service instance for drop-in replacement
warren_orchestrator = ContentGenerationOrchestrator()

# For backward compatibility, alias to match existing enhanced_warren_service pattern
enhanced_warren_service = warren_orchestrator

__all__ = [
    'ContentGenerationOrchestrator',
    'warren_orchestrator', 
    'enhanced_warren_service'  # Drop-in replacement
]
