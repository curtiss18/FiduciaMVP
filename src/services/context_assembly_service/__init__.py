"""
Context Assembler Service Package

Refactored context assembler following Single Responsibility Principle.
Provides token budget allocation, context gathering, optimization, assembly,
and quality assessment services with dependency injection support.
"""

# Import models from the refactored version (they're identical to original)
from .models import (
    RequestType,
    ContextType,
    ContextElement,
    CompressionStrategy,
    BudgetConfig,
    BudgetAllocation,
    QualityMetrics,
    FormattingOptions
)

from .interfaces import (
    ContextGatheringStrategy,
    BudgetAllocationStrategy,
    CompressionStrategy as CompressionStrategyInterface,
    ContextAssemblyStrategy,
    RequestAnalysisStrategy
)

# Import services as they are implemented
from .budget import BudgetAllocator, RequestTypeAnalyzer
from .gathering import ContextGatherer, ConversationGatherer, ComplianceGatherer, DocumentGatherer
# TODO: Add as implemented  
# from .optimization import TextTokenManager, ContextOptimizer
# from .assembly import ContextBuilder, QualityAssessor
# from .orchestrator import ContextAssemblyOrchestrator

# TEMPORARY: Import original ContextAssembler for backward compatibility
# This allows existing imports to work while we complete the refactoring
try:
    from ..context_assembler import ContextAssembler
except ImportError:
    # If there's a conflict, we'll handle it gracefully
    import sys
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Could not import original ContextAssembler, may need to update imports")
    ContextAssembler = None

# TEMPORARY: Create placeholder TokenManager for backward compatibility
# This addresses the immediate import issue identified in SCRUM-114
# Will be replaced with proper TextTokenManager in SCRUM-110

import tiktoken
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """
    TEMPORARY: Placeholder TokenManager for backward compatibility.
    
    This is a simplified version to resolve import errors until SCRUM-110
    implements the proper TextTokenManager service.
    """
    
    def __init__(self):
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        if not text:
            return 0
            
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4

__version__ = "1.0.0"

__all__ = [
    # Models
    'RequestType',
    'ContextType', 
    'ContextElement',
    'CompressionStrategy',
    'BudgetConfig',
    'BudgetAllocation',
    'QualityMetrics',
    'FormattingOptions',
    
    # Interfaces
    'ContextGatheringStrategy',
    'BudgetAllocationStrategy', 
    'CompressionStrategyInterface',
    'ContextAssemblyStrategy',
    'RequestAnalysisStrategy',
    
    # Temporary backward compatibility
    'ContextAssembler',  # Original class for backward compatibility
    'TokenManager',  # Will be replaced with TextTokenManager in SCRUM-110
    
    # Services (implemented)
    'BudgetAllocator',
    'RequestTypeAnalyzer',
    'ContextGatherer',
    'ConversationGatherer',
    'ComplianceGatherer', 
    'DocumentGatherer',
    
    # Services (TODO: Add as implemented)
    # 'TextTokenManager',
    # 'ContextOptimizer',
    # 'ContextBuilder',
    # 'QualityAssessor',
    # 'ContextAssemblyOrchestrator'
]
