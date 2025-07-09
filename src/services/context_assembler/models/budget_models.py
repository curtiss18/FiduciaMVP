"""Budget Configuration Models"""

from dataclasses import dataclass
from typing import Dict
from .context_models import RequestType, ContextType


@dataclass
class BudgetAllocation:
    """Token budget allocation for a specific context type."""
    context_type: ContextType
    allocated_tokens: int
    used_tokens: int = 0
    
    def __post_init__(self):
        """Validate budget allocation data."""
        if self.allocated_tokens < 0:
            raise ValueError("allocated_tokens cannot be negative")
        if self.used_tokens < 0:
            raise ValueError("used_tokens cannot be negative")
        if self.used_tokens > self.allocated_tokens:
            raise ValueError("used_tokens cannot exceed allocated_tokens")
    
    @property
    def remaining_tokens(self) -> int:
        """Calculate remaining tokens in this allocation."""
        return self.allocated_tokens - self.used_tokens
    
    @property
    def utilization_rate(self) -> float:
        """Calculate utilization rate as a percentage (0.0 to 1.0)."""
        return 0.0 if self.allocated_tokens == 0 else self.used_tokens / self.allocated_tokens
    
    def can_allocate(self, tokens: int) -> bool:
        """Check if we can allocate additional tokens."""
        return self.remaining_tokens >= tokens
    
    def allocate_tokens(self, tokens: int) -> bool:
        """Allocate tokens if available. Returns True if successful."""
        if self.can_allocate(tokens):
            self.used_tokens += tokens
            return True
        return False


@dataclass
class BudgetConfig:
    """Configuration for token budget allocation strategies."""
    request_type: RequestType
    context_budgets: Dict[ContextType, int]
    buffer_tokens: int
    max_total_tokens: int = 200000
    
    def __post_init__(self):
        """Validate budget configuration."""
        if self.buffer_tokens < 0:
            raise ValueError("buffer_tokens cannot be negative")
        if self.max_total_tokens <= 0:
            raise ValueError("max_total_tokens must be positive")
        
        total_allocated = sum(self.context_budgets.values()) + self.buffer_tokens
        if total_allocated > self.max_total_tokens:
            raise ValueError(f"Total allocated tokens ({total_allocated}) exceeds max_total_tokens ({self.max_total_tokens})")
    
    @property
    def total_allocated_tokens(self) -> int:
        """Calculate total tokens allocated across all context types."""
        return sum(self.context_budgets.values())
    
    @property
    def available_tokens(self) -> int:
        """Calculate available tokens for content (excluding buffer)."""
        return self.max_total_tokens - self.buffer_tokens
    
    def get_allocation_for_context(self, context_type: ContextType) -> int:
        """Get token allocation for a specific context type."""
        return self.context_budgets.get(context_type, 0)
    
    def create_allocations(self) -> Dict[ContextType, BudgetAllocation]:
        """Create BudgetAllocation objects for all context types."""
        return {
            context_type: BudgetAllocation(context_type, tokens)
            for context_type, tokens in self.context_budgets.items()
        }
    
    @classmethod
    def get_default_config(cls, request_type: RequestType) -> "BudgetConfig":
        """Get default budget configuration for a request type."""
        configs = {
            RequestType.CREATION: (
                {ContextType.SYSTEM_PROMPT: 5000, ContextType.CONVERSATION_HISTORY: 40000,
                 ContextType.DOCUMENT_SUMMARIES: 30000, ContextType.COMPLIANCE_SOURCES: 25000,
                 ContextType.VECTOR_SEARCH_RESULTS: 20000, ContextType.YOUTUBE_CONTEXT: 30000,
                 ContextType.USER_INPUT: 2000}, 48000
            ),
            RequestType.REFINEMENT: (
                {ContextType.SYSTEM_PROMPT: 5000, ContextType.CURRENT_CONTENT: 15000,
                 ContextType.CONVERSATION_HISTORY: 25000, ContextType.DOCUMENT_SUMMARIES: 20000,
                 ContextType.COMPLIANCE_SOURCES: 20000, ContextType.VECTOR_SEARCH_RESULTS: 15000,
                 ContextType.USER_INPUT: 2000}, 98000
            ),
            RequestType.ANALYSIS: (
                {ContextType.SYSTEM_PROMPT: 5000, ContextType.DOCUMENT_SUMMARIES: 50000,
                 ContextType.CONVERSATION_HISTORY: 30000, ContextType.COMPLIANCE_SOURCES: 30000,
                 ContextType.VECTOR_SEARCH_RESULTS: 25000, ContextType.USER_INPUT: 2000}, 58000
            ),
            RequestType.CONVERSATION: (
                {ContextType.SYSTEM_PROMPT: 5000, ContextType.CONVERSATION_HISTORY: 60000,
                 ContextType.COMPLIANCE_SOURCES: 15000, ContextType.VECTOR_SEARCH_RESULTS: 10000,
                 ContextType.USER_INPUT: 2000}, 108000
            )
        }
        
        budgets, buffer = configs[request_type]
        return cls(request_type=request_type, context_budgets=budgets, buffer_tokens=buffer)
