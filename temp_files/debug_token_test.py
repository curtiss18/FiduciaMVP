import asyncio
from src.services.context_assembly_service.budget.budget_allocator import BudgetAllocator
from src.services.context_assembly_service.models import RequestType, ContextType

async def debug_token_counting():
    allocator = BudgetAllocator()
    long_input = "a" * 50000
    
    # Test token counting directly
    token_count = allocator.token_manager.count_tokens(long_input)
    print(f"Token count for 16,000 'a' characters: {token_count}")
    
    # Test budget allocation
    allocations = await allocator.allocate_budget(RequestType.CREATION, long_input)
    user_input_allocation = allocations[ContextType.USER_INPUT]
    print(f"User input allocation: {user_input_allocation.allocated_tokens}")
    
    # Test base budget
    base_budget = allocator._get_base_budget(RequestType.CREATION)
    print(f"Base budget for USER_INPUT: {base_budget[ContextType.USER_INPUT]}")

if __name__ == "__main__":
    asyncio.run(debug_token_counting())
