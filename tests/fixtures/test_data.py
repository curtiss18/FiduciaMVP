"""
Test fixtures and data for Warren integration tests.
"""

import json
from typing import Dict, List, Any


# Sample vector search results for testing
SAMPLE_VECTOR_RESULTS = [
    {
        "id": "vector_example_1",
        "title": "Retirement Planning LinkedIn Post",
        "content_text": "Start planning for retirement early to secure your financial future. The power of compound interest means that even small contributions now can grow significantly over time.",
        "content_type": "linkedin_post",
        "tags": "retirement, planning, linkedin, compound_interest",
        "similarity_score": 0.85,
        "source": "approved_content"
    },
    {
        "id": "vector_example_2", 
        "title": "Investment Strategy Newsletter",
        "content_text": "Diversification is key to successful long-term investing. Don't put all your eggs in one basket - spread your investments across different asset classes.",
        "content_type": "newsletter",
        "tags": "investment, strategy, diversification, newsletter",
        "similarity_score": 0.73,
        "source": "approved_content"
    },
    {
        "id": "vector_example_3",
        "title": "Market Volatility Education",
        "content_text": "Market volatility is normal and expected. Understanding this helps investors stay calm during turbulent times and stick to their long-term strategy.",
        "content_type": "blog_post",
        "tags": "market, volatility, education, strategy",
        "similarity_score": 0.68,
        "source": "approved_content"
    }
]

# Sample compliance/disclaimer results
SAMPLE_COMPLIANCE_RESULTS = [
    {
        "id": "compliance_1",
        "title": "Investment Risk Disclaimer",
        "content_text": "Past performance does not guarantee future results. All investments carry risk of loss and may lose value.",
        "tags": "disclaimer, risk, investment",
        "content_type": "disclaimer"
    },
    {
        "id": "compliance_2", 
        "title": "General Financial Advice Disclaimer",
        "content_text": "This content is for educational purposes only and should not be considered personalized financial advice.",
        "tags": "disclaimer, educational, advice",
        "content_type": "disclaimer"
    },
    {
        "id": "compliance_3",
        "title": "Securities Disclaimer",
        "content_text": "Securities offered through XYZ Financial Services. Investment advisory services offered through ABC Advisors.",
        "tags": "disclaimer, securities, advisory",
        "content_type": "disclaimer"
    }
]

# Sample text search results (fallback)
SAMPLE_TEXT_RESULTS = [
    {
        "id": "text_example_1",
        "title": "Retirement Savings Tips",
        "content_text": "Here are some practical tips for building your retirement savings effectively over time.",
        "content_type": "blog_post",
        "tags": "retirement, savings, tips"
    },
    {
        "id": "text_example_2",
        "title": "401k Contribution Guide", 
        "content_text": "Maximize your 401k contributions to take advantage of employer matching and tax benefits.",
        "content_type": "guide",
        "tags": "401k, contributions, tax, employer"
    }
]

# Sample conversation history
SAMPLE_CONVERSATION_HISTORY = [
    {
        "role": "user",
        "content": "I need help creating a LinkedIn post about retirement planning",
        "timestamp": "2024-01-01T10:00:00Z"
    },
    {
        "role": "assistant", 
        "content": "I'd be happy to help you create a LinkedIn post about retirement planning. To make this content compliant and relevant, I need to understand a few things...",
        "timestamp": "2024-01-01T10:00:05Z"
    },
    {
        "role": "user",
        "content": "My target audience is professionals in their 30s who haven't started retirement planning yet",
        "timestamp": "2024-01-01T10:01:00Z"
    }
]

# Sample session documents
SAMPLE_SESSION_DOCUMENTS = [
    {
        "id": "doc_1",
        "filename": "client_demographics.pdf",
        "content_summary": "Analysis of client demographics showing 65% are professionals aged 25-40 with limited retirement savings",
        "upload_timestamp": "2024-01-01T09:30:00Z"
    },
    {
        "id": "doc_2", 
        "filename": "market_trends_2024.docx",
        "content_summary": "Current market trends and economic outlook for 2024, focusing on retirement planning strategies",
        "upload_timestamp": "2024-01-01T09:45:00Z"
    }
]

# User request scenarios for testing
TEST_USER_REQUESTS = [
    {
        "scenario": "simple_linkedin_post",
        "user_request": "Create a LinkedIn post about retirement planning for young professionals",
        "content_type": "linkedin_post",
        "audience_type": "retail_investors",
        "expected_elements": ["retirement", "planning", "professionals", "disclaimer"]
    },
    {
        "scenario": "newsletter_with_context",
        "user_request": "Write a newsletter section about investment diversification",
        "content_type": "newsletter", 
        "audience_type": "existing_clients",
        "session_documents": ["market_trends_2024.docx"],
        "expected_elements": ["diversification", "investment", "strategy", "disclaimer"]
    },
    {
        "scenario": "complex_blog_post",
        "user_request": "Create a comprehensive blog post about 401k planning strategies",
        "content_type": "blog_post",
        "audience_type": "prospective_clients",
        "conversation_history": SAMPLE_CONVERSATION_HISTORY,
        "session_documents": ["client_demographics.pdf"],
        "expected_elements": ["401k", "planning", "strategies", "professional", "disclaimer"]
    }
]

# Performance test scenarios
PERFORMANCE_TEST_SCENARIOS = [
    {
        "name": "simple_request",
        "request": TEST_USER_REQUESTS[0],
        "expected_max_time": 2.0  # seconds
    },
    {
        "name": "complex_request_with_context",
        "request": TEST_USER_REQUESTS[2],
        "expected_max_time": 5.0  # seconds
    }
]

# Error scenarios for failure testing
ERROR_TEST_SCENARIOS = [
    {
        "scenario": "vector_search_failure",
        "description": "Vector search service unavailable",
        "mock_failures": ["vector_search_service"],
        "expected_fallback": "text_search"
    },
    {
        "scenario": "database_failure",
        "description": "Database connection failure",
        "mock_failures": ["warren_database_service"],
        "expected_behavior": "graceful_error"
    },
    {
        "scenario": "openai_api_failure",
        "description": "OpenAI API unavailable",
        "mock_failures": ["openai_api"],
        "expected_behavior": "api_error_response"
    }
]


def get_test_data(data_type: str) -> List[Dict[str, Any]]:
    """Get test data by type."""
    data_map = {
        "vector_results": SAMPLE_VECTOR_RESULTS,
        "compliance_results": SAMPLE_COMPLIANCE_RESULTS,
        "text_results": SAMPLE_TEXT_RESULTS,
        "conversation_history": SAMPLE_CONVERSATION_HISTORY,
        "session_documents": SAMPLE_SESSION_DOCUMENTS,
        "user_requests": TEST_USER_REQUESTS,
        "performance_scenarios": PERFORMANCE_TEST_SCENARIOS,
        "error_scenarios": ERROR_TEST_SCENARIOS
    }
    return data_map.get(data_type, [])


def save_test_data_to_json():
    """Save all test data to JSON files for external use."""
    import os
    fixture_dir = os.path.dirname(__file__)
    
    data_files = {
        "vector_search_data.json": SAMPLE_VECTOR_RESULTS,
        "compliance_data.json": SAMPLE_COMPLIANCE_RESULTS,
        "text_search_data.json": SAMPLE_TEXT_RESULTS,
        "conversation_examples.json": SAMPLE_CONVERSATION_HISTORY,
        "session_documents.json": SAMPLE_SESSION_DOCUMENTS,
        "test_scenarios.json": TEST_USER_REQUESTS
    }
    
    for filename, data in data_files.items():
        filepath = os.path.join(fixture_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    save_test_data_to_json()
