"""Tests for BudgetAllocator service."""

import pytest
from src.services.context_assembly_service.budget import BudgetAllocator
from src.services.context_assembly_service.models import RequestType, ContextType, BudgetAllocation


class TestBudgetAllocator:
    
    def setup_method(self):
        self.allocator = BudgetAllocator()
    
    @pytest.mark.asyncio
    async def test_creation_budget_allocation(self):
        allocations = await self.allocator.allocate_budget(RequestType.CREATION, "test input")
        
        assert ContextType.SYSTEM_PROMPT in allocations
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 40000
        assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens == 30000
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 25000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens == 20000
        assert allocations[ContextType.YOUTUBE_CONTEXT].allocated_tokens == 30000
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_refinement_budget_allocation(self):
        allocations = await self.allocator.allocate_budget(RequestType.REFINEMENT, "edit this")
        
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.CURRENT_CONTENT].allocated_tokens == 15000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 25000
        assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens == 20000
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 20000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens == 15000
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_analysis_budget_allocation(self):
        allocations = await self.allocator.allocate_budget(RequestType.ANALYSIS, "analyze document")
        
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens == 50000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 30000
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 30000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens == 25000
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_conversation_budget_allocation(self):
        allocations = await self.allocator.allocate_budget(RequestType.CONVERSATION, "hello")
        
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 60000
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 15000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens == 10000
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_oversized_user_input_adjustment(self):
        # Create long input that exceeds 2000 token budget (20000+ chars = 2500+ tokens)
        long_input = "a" * 20000
        allocations = await self.allocator.allocate_budget(RequestType.CREATION, long_input)
        
        # User input should be adjusted upward
        assert allocations[ContextType.USER_INPUT].allocated_tokens > 2000
        
        # Adjustable contexts should be reduced
        assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens < 30000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens < 20000
        assert allocations[ContextType.YOUTUBE_CONTEXT].allocated_tokens < 30000
        
        # Non-adjustable contexts should remain unchanged
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 40000
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 25000
    
    @pytest.mark.asyncio
    async def test_minimum_budget_enforcement(self):
        # Extremely long input to test minimum budget enforcement
        very_long_input = "a" * 50000
        allocations = await self.allocator.allocate_budget(RequestType.CREATION, very_long_input)
        
        # All adjustable contexts should maintain minimum of 1000 tokens
        assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens >= 1000
        assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens >= 1000
        assert allocations[ContextType.YOUTUBE_CONTEXT].allocated_tokens >= 1000
    
    @pytest.mark.asyncio
    async def test_budget_allocation_objects(self):
        allocations = await self.allocator.allocate_budget(RequestType.CREATION, "test")
        
        for context_type, allocation in allocations.items():
            assert isinstance(allocation, BudgetAllocation)
            assert allocation.context_type == context_type
            assert allocation.allocated_tokens > 0
            assert allocation.used_tokens == 0
            assert allocation.remaining_tokens == allocation.allocated_tokens
    
    @pytest.mark.asyncio
    async def test_empty_input(self):
        allocations = await self.allocator.allocate_budget(RequestType.CREATION, "")
        
        # Should still return valid allocations
        assert len(allocations) > 0
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    def test_get_budget_config(self):
        config = self.allocator.get_budget_config(RequestType.CREATION)
        
        assert config.request_type == RequestType.CREATION
        assert config.buffer_tokens == 48000
        assert ContextType.SYSTEM_PROMPT in config.context_budgets
    
    def test_base_budget_methods(self):
        budget = self.allocator._get_base_budget(RequestType.CREATION)
        
        assert isinstance(budget, dict)
        assert ContextType.SYSTEM_PROMPT in budget
        assert budget[ContextType.SYSTEM_PROMPT] == 5000
    
    @pytest.mark.asyncio
    async def test_invalid_request_type_fallback(self):
        # Test with None to trigger fallback
        allocations = await self.allocator.allocate_budget(None, "test")
        
        # Should fallback to CREATION budget
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 40000
