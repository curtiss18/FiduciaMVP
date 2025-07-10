"""Integration test for BudgetAllocator."""

import pytest
from src.services.context_assembler import BudgetAllocator, RequestType, ContextType


@pytest.mark.asyncio
async def test_budget_allocator_integration():
    """Test BudgetAllocator produces expected outputs for known inputs."""
    allocator = BudgetAllocator()
    
    # Test normal creation request
    allocations = await allocator.allocate_budget(RequestType.CREATION, "Create a LinkedIn post about retirement planning")
    
    # Verify expected budget distribution
    assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
    assert allocations[ContextType.CONVERSATION_HISTORY].allocated_tokens == 40000
    assert allocations[ContextType.DOCUMENT_SUMMARIES].allocated_tokens == 30000
    assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 25000
    assert allocations[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens == 20000
    assert allocations[ContextType.YOUTUBE_CONTEXT].allocated_tokens == 30000
    assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    # Test dynamic adjustment with long input (need >8000 chars for >2000 tokens)
    long_input = "Please create a comprehensive LinkedIn post about retirement planning strategies for high-net-worth individuals, including information about tax-advantaged accounts, estate planning considerations, and the importance of working with qualified financial advisors. The post should be engaging, professional, and compliant with all SEC and FINRA regulations regarding financial advice and marketing communications. " * 50  # Repeat to ensure >8000 chars
    
    allocations_long = await allocator.allocate_budget(RequestType.CREATION, long_input)
    
    # User input budget should be adjusted upward
    assert allocations_long[ContextType.USER_INPUT].allocated_tokens > 2000
    
    # Some adjustable contexts should be reduced
    assert (allocations_long[ContextType.DOCUMENT_SUMMARIES].allocated_tokens < 30000 or
            allocations_long[ContextType.VECTOR_SEARCH_RESULTS].allocated_tokens < 20000 or
            allocations_long[ContextType.YOUTUBE_CONTEXT].allocated_tokens < 30000)
    
    print("BudgetAllocator integration test passed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_budget_allocator_integration())
