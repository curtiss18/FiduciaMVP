"""Budget Allocation Service"""

import logging
from typing import Dict, Optional

from ..interfaces import BudgetAllocationStrategy
from ..models import RequestType, ContextType, BudgetConfig, BudgetAllocation
from ..optimization.text_token_manager import TextTokenManager

logger = logging.getLogger(__name__)


class BudgetAllocator(BudgetAllocationStrategy):
    
    def __init__(self, token_manager: Optional[TextTokenManager] = None):
        self.token_manager = token_manager or TextTokenManager()
    
    async def allocate_budget(self, request_type: RequestType, user_input: str, available_tokens: int = 200000) -> Dict[ContextType, BudgetAllocation]:
        base_budget = self._get_base_budget(request_type)
        
        # Use TextTokenManager for accurate token counting
        user_input_tokens = self.token_manager.count_tokens(user_input)
        logger.debug(f"User input tokens: {user_input_tokens} (was estimated, now accurate)")
        
        # Adjust for longer user input
        if user_input_tokens > base_budget.get(ContextType.USER_INPUT, 2000):
            excess_tokens = user_input_tokens - base_budget[ContextType.USER_INPUT]
            base_budget[ContextType.USER_INPUT] = user_input_tokens
            
            # Reduce other budgets proportionally
            adjustable_contexts = [
                ContextType.DOCUMENT_SUMMARIES,
                ContextType.VECTOR_SEARCH_RESULTS,
                ContextType.YOUTUBE_CONTEXT
            ]
            
            reduction_per_context = excess_tokens // len(adjustable_contexts)
            for context_type in adjustable_contexts:
                if context_type in base_budget:
                    base_budget[context_type] = max(1000, base_budget[context_type] - reduction_per_context)
        
        # Convert to BudgetAllocation objects
        allocations = {}
        for context_type, tokens in base_budget.items():
            allocations[context_type] = BudgetAllocation(context_type, tokens)
        
        return allocations
    
    def get_budget_config(self, request_type: RequestType) -> BudgetConfig:
        return BudgetConfig.get_default_config(request_type)
    
    def _get_base_budget(self, request_type: RequestType) -> Dict[ContextType, int]:
        """Get base budget allocation for request type."""
        budgets = {
            RequestType.CREATION: {
                ContextType.SYSTEM_PROMPT: 5000,
                ContextType.CONVERSATION_HISTORY: 40000,
                ContextType.DOCUMENT_SUMMARIES: 30000,
                ContextType.COMPLIANCE_SOURCES: 25000,
                ContextType.VECTOR_SEARCH_RESULTS: 20000,
                ContextType.YOUTUBE_CONTEXT: 30000,
                ContextType.USER_INPUT: 2000
            },
            RequestType.REFINEMENT: {
                ContextType.SYSTEM_PROMPT: 5000,
                ContextType.CURRENT_CONTENT: 15000,
                ContextType.CONVERSATION_HISTORY: 25000,
                ContextType.DOCUMENT_SUMMARIES: 20000,
                ContextType.COMPLIANCE_SOURCES: 20000,
                ContextType.VECTOR_SEARCH_RESULTS: 15000,
                ContextType.USER_INPUT: 2000
            },
            RequestType.ANALYSIS: {
                ContextType.SYSTEM_PROMPT: 5000,
                ContextType.DOCUMENT_SUMMARIES: 50000,
                ContextType.CONVERSATION_HISTORY: 30000,
                ContextType.COMPLIANCE_SOURCES: 30000,
                ContextType.VECTOR_SEARCH_RESULTS: 25000,
                ContextType.USER_INPUT: 2000
            },
            RequestType.CONVERSATION: {
                ContextType.SYSTEM_PROMPT: 5000,
                ContextType.CONVERSATION_HISTORY: 60000,
                ContextType.COMPLIANCE_SOURCES: 15000,
                ContextType.VECTOR_SEARCH_RESULTS: 10000,
                ContextType.USER_INPUT: 2000
            }
        }
        
        return budgets.get(request_type, budgets[RequestType.CREATION]).copy()
