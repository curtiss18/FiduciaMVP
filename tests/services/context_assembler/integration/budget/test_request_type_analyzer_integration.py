"""Integration test for RequestTypeAnalyzer."""

import pytest
from src.services.context_assembly_service import RequestTypeAnalyzer, RequestType


@pytest.mark.asyncio
async def test_request_type_analyzer_integration():
    """Test RequestTypeAnalyzer produces expected outputs for known inputs."""
    analyzer = RequestTypeAnalyzer()
    
    # Test cases: (input, current_content, expected_type)
    test_cases = [
        # Creation requests
        ("Create a LinkedIn post about retirement planning", None, RequestType.CREATION),
        ("Write an email newsletter for our clients", None, RequestType.CREATION),
        ("Generate social media content", None, RequestType.CREATION),
        ("Draft a blog post", None, RequestType.CREATION),
        ("Help me with a marketing message", None, RequestType.CREATION),
        
        # Refinement requests - with keywords
        ("Edit this content to make it better", None, RequestType.REFINEMENT),
        ("Modify the tone of this message", None, RequestType.REFINEMENT),
        ("Improve this draft", None, RequestType.REFINEMENT),
        ("Make it more professional", None, RequestType.REFINEMENT),
        
        # Refinement requests - with current content
        ("Please help me with this", "Existing content", RequestType.REFINEMENT),
        ("What do you think?", "Some draft content", RequestType.REFINEMENT),
        
        # Analysis requests
        ("Analyze this market research document", None, RequestType.ANALYSIS),
        ("Review the quarterly results", None, RequestType.ANALYSIS),
        ("Compare our performance", None, RequestType.ANALYSIS),
        ("What do you think about this strategy?", None, RequestType.ANALYSIS),
        
        # Conversation requests (fallback)
        ("Hello there", None, RequestType.CONVERSATION),
        ("Tell me about investment strategies", None, RequestType.CONVERSATION),
        ("What's the weather like?", None, RequestType.CONVERSATION),
        ("Random question", None, RequestType.CONVERSATION),
        
        # Priority order tests
        ("Edit and create a new post", None, RequestType.REFINEMENT),
        ("Analyze and create a report", None, RequestType.ANALYSIS),
        ("Review and modify this content", None, RequestType.REFINEMENT),
    ]
    
    # Run all test cases
    for user_input, current_content, expected_type in test_cases:
        result = analyzer.analyze_request_type(user_input, current_content)
        assert result == expected_type, f"Failed for input: '{user_input}' (current_content: {current_content is not None})"
    
    # Test extract_requirements functionality
    requirements = analyzer.extract_requirements("Create a comprehensive LinkedIn post")
    assert requirements['request_type'] == RequestType.CREATION
    assert requirements['has_keywords']['creation'] == True
    assert requirements['has_keywords']['refinement'] == False
    assert requirements['has_keywords']['analysis'] == False
    assert requirements['input_length'] > 0
    
    print("RequestTypeAnalyzer integration test passed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_request_type_analyzer_integration())
