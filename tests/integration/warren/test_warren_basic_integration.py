"""
Basic Integration Tests for Warren Service - Real Dependencies

Epic: [SCRUM-86] Warren Service Tech Debt Remediation  
Task: [SCRUM-90] Create comprehensive integration test suite

Purpose: Test Warren service with minimal mocking to verify real integration behavior.
"""

import pytest
from unittest.mock import patch
from src.services.warren import ContentGenerationOrchestrator


class TestWarrenBasicIntegration:
    """Basic integration tests with minimal mocking."""
    
    @pytest.fixture
    def warren_orchestrator(self):
        """Warren orchestrator with mostly real dependencies."""
        return ContentGenerationOrchestrator()
    
    @pytest.fixture
    def mock_claude_only(self):
        """Mock only Claude service to avoid external API calls."""
        with patch('src.services.claude_service.ClaudeService.generate_content') as mock_claude:
            mock_claude.return_value = "Here's your compliant financial content with proper disclaimers and risk warnings. Past performance does not guarantee future results."
            yield mock_claude
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_warren_end_to_end_basic_workflow(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        mock_claude_only
    ):
        """
        Test basic Warren end-to-end workflow with real dependencies.
        
        This tests the actual Warren service behavior with real database fallbacks.
        """
        # Arrange
        test_request = {
            "user_request": "Create a LinkedIn post about retirement planning",
            "content_type": "linkedin_post",
            "audience_type": "retail_investors"
        }
        
        # Act
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request=test_request["user_request"],
            content_type=test_request["content_type"],
            audience_type=test_request["audience_type"]
        )
        
        # Assert - Basic functionality verification
        assert result is not None, "Warren should return a result"
        assert result["status"] == "success", f"Expected success, got: {result.get('status')}"
        assert "content" in result, "Response should contain generated content"
        assert result["content"] is not None, "Generated content should not be None"
        assert len(result["content"]) > 0, "Generated content should not be empty"
        
        # Verify response structure
        expected_fields = [
            "status", "content", "content_type", "search_strategy",
            "marketing_examples_count", "compliance_rules_count", 
            "context_quality_score", "user_request"
        ]
        
        for field in expected_fields:
            assert field in result, f"Response missing required field: {field}"
        
        # Verify content type was preserved
        assert result["content_type"] == "linkedin_post"
        
        # Verify Claude was called for content generation
        mock_claude_only.assert_called_once()
        
        # Verify some search strategy was used (even if fallback)
        assert result["search_strategy"] in ["vector", "text", "hybrid", "text_fallback"]
        
        print(f"Test Results:")
        print(f"  Status: {result['status']}")
        print(f"  Content Length: {len(result['content'])} chars")
        print(f"  Search Strategy: {result['search_strategy']}")
        print(f"  Marketing Examples: {result['marketing_examples_count']}")
        print(f"  Compliance Rules: {result['compliance_rules_count']}")
        print(f"  Quality Score: {result['context_quality_score']}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_warren_error_handling(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        mock_claude_only
    ):
        """
        Test Warren error handling with invalid inputs.
        """
        # Test empty request
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request="",
            content_type="linkedin_post",
            audience_type="retail_investors"
        )
        
        assert result["status"] == "error"
        assert "error" in result
        assert result["content"] is None
        
        # Test invalid content type
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request="Create content",
            content_type="invalid_type",
            audience_type="retail_investors"
        )
        
        # Should either handle gracefully or work with unknown type
        assert result is not None
        assert "status" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_warren_different_content_types(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        mock_claude_only
    ):
        """
        Test Warren with different content types.
        """
        content_types = ["linkedin_post", "newsletter", "blog_post", "email_template"]
        
        for content_type in content_types:
            result = await warren_orchestrator.generate_content_with_enhanced_context(
                user_request=f"Create {content_type.replace('_', ' ')} about financial planning",
                content_type=content_type,
                audience_type="retail_investors"
            )
            
            # Basic assertions for each content type
            assert result is not None, f"Failed for content type: {content_type}"
            assert result["status"] == "success", f"Failed status for {content_type}: {result.get('status')}"
            assert result["content_type"] == content_type, f"Content type mismatch for {content_type}"
            assert len(result["content"]) > 0, f"Empty content for {content_type}"
            
            print(f"PASS {content_type}: Generated {len(result['content'])} chars")
    
    @pytest.mark.asyncio
    @pytest.mark.integration  
    async def test_warren_performance_basic(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        mock_claude_only
    ):
        """
        Test basic Warren performance benchmarks.
        """
        import time
        
        start_time = time.time()
        
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request="Create a quick LinkedIn post about investment basics",
            content_type="linkedin_post",
            audience_type="retail_investors"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Assert functionality
        assert result["status"] == "success"
        assert len(result["content"]) > 0
        
        # Assert performance (generous limits for integration test)
        assert response_time < 10.0, f"Response time {response_time:.2f}s exceeds 10s limit"
        
        print(f"Performance Result: {response_time:.2f} seconds")
        
        # Verify reasonable response time for SaaS standards
        if response_time < 2.0:
            print("EXCELLENT performance (<2s)")
        elif response_time < 5.0:
            print("GOOD performance (<5s)")
        else:
            print("ACCEPTABLE but could be improved")
