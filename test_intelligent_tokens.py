"""
Test script for Phase 1: Intelligent Token Management and Context Assembly
Tests the new ContextAssembler and TokenManager implementations.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.context_assembler import ContextAssembler, TokenManager, RequestType
from src.services.enhanced_warren_service import EnhancedWarrenService
from src.core.database import AsyncSessionLocal

async def test_token_manager():
    """Test the TokenManager token counting and compression."""
    print("Testing TokenManager...")
    
    token_manager = TokenManager()
    
    # Test token counting
    test_text = "This is a sample text for testing token counting functionality."
    token_count = token_manager.count_tokens(test_text)
    print(f"   [OK] Token counting: '{test_text}' = {token_count} tokens")
    
    # Test content compression
    long_text = "This is a very long piece of text that we will use to test the compression functionality. " * 50
    original_tokens = token_manager.count_tokens(long_text)
    
    from src.services.context_assembler import ContextType
    compressed_text = await token_manager.compress_content(long_text, 100, ContextType.CONVERSATION_HISTORY)
    compressed_tokens = token_manager.count_tokens(compressed_text)
    
    print(f"   [OK] Content compression: {original_tokens} -> {compressed_tokens} tokens")
    print(f"   [INFO] Compressed preview: {compressed_text[:100]}...")
    
    return True

async def test_context_assembler():
    """Test the ContextAssembler intelligent allocation."""
    print("\nTesting ContextAssembler...")
    
    async with AsyncSessionLocal() as db_session:
        context_assembler = ContextAssembler(db_session)
        
        # Test token budget allocation
        budget = await context_assembler.allocate_token_budget(RequestType.CREATION, "Create a LinkedIn post")
        print(f"   [OK] Token budget allocation for CREATION mode:")
        for context_type, tokens in budget.items():
            print(f"      {context_type.value}: {tokens} tokens")
        
        # Test different request types
        refinement_budget = await context_assembler.allocate_token_budget(RequestType.REFINEMENT, "Make this more engaging")
        print(f"\n   [OK] Token budget allocation for REFINEMENT mode:")
        for context_type, tokens in refinement_budget.items():
            print(f"      {context_type.value}: {tokens} tokens")
        
        # Test context building (without actual session data)
        mock_context_data = {
            "examples": [
                {"title": "Test Example", "content_text": "This is a test marketing example.", "tags": "linkedin, test"},
                {"title": "Another Example", "content_text": "Another example of compliant content.", "tags": "email, test"}
            ],
            "disclaimers": [
                {"title": "Risk Disclaimer", "content_text": "Investments involve risk including potential loss of principal."},
                {"title": "Performance Disclaimer", "content_text": "Past performance does not guarantee future results."}
            ]
        }
        
        assembly_result = await context_assembler.build_warren_context(
            session_id="test-session",
            user_input="Create a LinkedIn post about retirement planning",
            context_data=mock_context_data
        )
        
        print(f"\n   [OK] Context assembly result:")
        print(f"      Request Type: {assembly_result['request_type']}")
        print(f"      Total Tokens: {assembly_result['total_tokens']}")
        print(f"      Optimization Applied: {assembly_result['optimization_applied']}")
        print(f"      Context Preview: {assembly_result['context'][:200]}...")
        
    return True

async def test_enhanced_warren_integration():
    """Test the integration with Enhanced Warren Service."""
    print("\nTesting Enhanced Warren Integration...")
    
    enhanced_warren = EnhancedWarrenService()
    
    try:
        # Test content generation with new intelligent context assembly
        result = await enhanced_warren.generate_content_with_enhanced_context(
            user_request="Create a LinkedIn post about the importance of diversification",
            content_type="linkedin_post",
            audience_type="general_education",
            session_id="test-session-integration",
            use_conversation_context=False  # Disable conversation context for this test
        )
        
        print(f"   [OK] Content generation successful!")
        print(f"      Status: {result['status']}")
        print(f"      Search Strategy: {result.get('search_strategy', 'unknown')}")
        print(f"      Total Sources: {result.get('total_knowledge_sources', 0)}")
        
        # Check for token management data
        if 'token_management' in result:
            token_info = result['token_management']
            print(f"   [INFO] Token Management Info:")
            print(f"      Total Tokens: {token_info.get('total_tokens', 'unknown')}")
            print(f"      Request Type: {token_info.get('request_type', 'unknown')}")
            print(f"      Optimization Applied: {token_info.get('optimization_applied', False)}")
        
        # Preview the generated content
        content_preview = result.get('content', '')[:300]
        print(f"   [INFO] Content Preview: {content_preview}...")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Error in Enhanced Warren integration: {e}")
        return False

async def test_large_context_handling():
    """Test how the system handles large context scenarios."""
    print("\nTesting Large Context Handling...")
    
    async with AsyncSessionLocal() as db_session:
        context_assembler = ContextAssembler(db_session)
        
        # Create very large mock context data
        large_context_data = {
            "examples": [
                {
                    "title": f"Large Example {i}", 
                    "content_text": "This is a very long example of marketing content. " * 100,
                    "tags": f"test, large, example{i}"
                } 
                for i in range(10)
            ],
            "disclaimers": [
                {
                    "title": f"Large Disclaimer {i}", 
                    "content_text": "This is a very long disclaimer with lots of legal text. " * 50
                }
                for i in range(5)
            ]
        }
        
        # Create large user input
        large_user_input = "Create a comprehensive LinkedIn post about retirement planning strategies for high-net-worth individuals, including diversification techniques, tax-advantaged accounts, estate planning considerations, and market volatility management." * 10
        
        assembly_result = await context_assembler.build_warren_context(
            session_id="test-large-context",
            user_input=large_user_input,
            context_data=large_context_data
        )
        
        print(f"   [OK] Large context handling:")
        print(f"      Total Tokens: {assembly_result['total_tokens']}")
        print(f"      Under Token Limit: {assembly_result['total_tokens'] <= 180000}")
        print(f"      Optimization Applied: {assembly_result['optimization_applied']}")
        print(f"      Context Breakdown: {assembly_result['context_breakdown']}")
        
        return assembly_result['total_tokens'] <= 180000

async def main():
    """Run all Phase 1 tests."""
    print("Starting Phase 1: Intelligent Token Management Tests\n")
    
    tests = [
        ("Token Manager", test_token_manager),
        ("Context Assembler", test_context_assembler),
        ("Enhanced Warren Integration", test_enhanced_warren_integration),
        ("Large Context Handling", test_large_context_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"[PASS] {test_name}: PASSED")
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name}: ERROR - {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All Phase 1 tests PASSED! Intelligent Token Management is ready.")
    else:
        print("WARNING: Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
