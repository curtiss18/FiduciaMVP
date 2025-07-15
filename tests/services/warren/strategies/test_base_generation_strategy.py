"""
Tests for Base Generation Strategy

Test Coverage:
- BaseGenerationStrategy extracted common functionality
- Platform extraction logic
- Error handling patterns
- Result population logic
- Input validation
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from src.services.warren.strategies.base_generation_strategy import BaseGenerationStrategy
from src.services.warren.strategies.content_generation_strategy import GenerationResult


class ConcreteBaseStrategy(BaseGenerationStrategy):
    """Concrete implementation for testing the abstract base class."""
    
    async def generate_content(self, context_data, user_request, content_type, **kwargs):
        """Minimal implementation for testing."""
        return GenerationResult()
    
    def can_handle(self, context_data):
        """Minimal implementation for testing."""
        return True
    
    def get_strategy_name(self):
        """Minimal implementation for testing."""
        return "test_base"


class TestBaseGenerationStrategy:
    """Test BaseGenerationStrategy common functionality."""
    
    @pytest.fixture
    def strategy(self):
        """Create concrete strategy instance for testing."""
        return ConcreteBaseStrategy()
    
    def test_extract_platform_from_content_type_known_types(self, strategy):
        """Test platform extraction for known content types."""
        test_cases = [
            ('linkedin_post', 'linkedin'),
            ('email_template', 'email'),
            ('website_content', 'website'),
            ('newsletter', 'newsletter'),
            ('social_media', 'twitter'),
            ('blog_post', 'website')
        ]
        
        for content_type, expected_platform in test_cases:
            result = strategy._extract_platform_from_content_type(content_type)
            assert result == expected_platform, f"Content type {content_type} should map to {expected_platform}"
    
    def test_extract_platform_from_content_type_case_insensitive(self, strategy):
        """Test platform extraction is case insensitive."""
        test_cases = [
            ('LINKEDIN_POST', 'linkedin'),
            ('Email_Template', 'email'),
            ('WEBSITE_CONTENT', 'website')
        ]
        
        for content_type, expected_platform in test_cases:
            result = strategy._extract_platform_from_content_type(content_type)
            assert result == expected_platform
    
    def test_extract_platform_from_content_type_unknown_type(self, strategy):
        """Test platform extraction for unknown content types returns general."""
        unknown_types = ['unknown_type', 'custom_content', '', 'random_string']
        
        for content_type in unknown_types:
            result = strategy._extract_platform_from_content_type(content_type)
            assert result == 'general'
    
    @patch('src.services.warren.strategies.base_generation_strategy.logger')
    def test_handle_generation_error(self, mock_logger, strategy):
        """Test common error handling pattern."""
        test_error = Exception("Test error message")
        strategy_name = "test_strategy"
        
        result = strategy._handle_generation_error(test_error, strategy_name)
        
        # Verify result structure
        assert isinstance(result, GenerationResult)
        assert result.success is False
        assert result.error_message == "Test error message"
        assert result.strategy_used == "test_strategy"
        assert result.metadata == {"error_type": "test_strategy_generation_failure"}
        
        # Verify logging was called
        mock_logger.error.assert_called_once()
        log_call_args = mock_logger.error.call_args[0][0]
        assert "Test_Strategy generation strategy failed" in log_call_args
        assert "Test error message" in log_call_args
    
    def test_populate_success_result_basic(self, strategy):
        """Test basic success result population."""
        result = GenerationResult()
        content = "Generated content"
        strategy_name = "test_strategy"
        start_time = time.time() - 2.5  # Simulate 2.5 second generation
        
        strategy._populate_success_result(result, content, strategy_name, start_time)
        
        assert result.content == "Generated content"
        assert result.success is True
        assert result.strategy_used == "test_strategy"
        assert result.generation_time > 2.0  # Should be around 2.5 seconds
        assert result.generation_time < 3.0
        assert "strategy_used" in result.metadata
        assert "generation_time" in result.metadata
    
    def test_populate_success_result_with_metadata(self, strategy):
        """Test success result population with additional metadata."""
        result = GenerationResult()
        content = "Generated content"
        strategy_name = "test_strategy"
        start_time = time.time() - 1.0
        
        additional_metadata = {
            "phase": "Phase_2_Advanced",
            "document_count": 3,
            "quality_score": 0.85
        }
        
        strategy._populate_success_result(
            result, content, strategy_name, start_time, **additional_metadata
        )
        
        assert result.content == "Generated content"
        assert result.success is True
        assert result.strategy_used == "test_strategy"
        
        # Check that additional metadata was merged
        assert result.metadata["phase"] == "Phase_2_Advanced"
        assert result.metadata["document_count"] == 3
        assert result.metadata["quality_score"] == 0.85
        assert result.metadata["strategy_used"] == "test_strategy"  # Base metadata preserved
        assert "generation_time" in result.metadata
    
    def test_build_base_prompt_context_with_audience(self, strategy):
        """Test base prompt context building with audience type."""
        content_type = "linkedin_post"
        audience_type = "existing_clients"
        
        result = strategy._build_base_prompt_context(content_type, audience_type)
        
        expected = {
            'platform': 'linkedin',
            'content_type': 'linkedin_post',
            'audience_type': 'existing_clients'
        }
        assert result == expected
    
    def test_build_base_prompt_context_without_audience(self, strategy):
        """Test base prompt context building without audience type."""
        content_type = "email_template"
        
        result = strategy._build_base_prompt_context(content_type)
        
        expected = {
            'platform': 'email',
            'content_type': 'email_template',
            'audience_type': None
        }
        assert result == expected
    
    def test_build_base_prompt_context_unknown_content_type(self, strategy):
        """Test base prompt context with unknown content type."""
        content_type = "unknown_type"
        audience_type = "prospects"
        
        result = strategy._build_base_prompt_context(content_type, audience_type)
        
        expected = {
            'platform': 'general',  # Should default to general
            'content_type': 'unknown_type',
            'audience_type': 'prospects'
        }
        assert result == expected
    
    def test_validate_basic_inputs_valid(self, strategy):
        """Test basic input validation with valid inputs."""
        user_request = "Create a post about retirement planning"
        content_type = "linkedin_post"
        
        is_valid, error_message = strategy._validate_basic_inputs(user_request, content_type)
        
        assert is_valid is True
        assert error_message is None
    
    def test_validate_basic_inputs_empty_request(self, strategy):
        """Test basic input validation with empty user request."""
        test_cases = ["", "   ", None]
        
        for user_request in test_cases:
            is_valid, error_message = strategy._validate_basic_inputs(user_request, "linkedin_post")
            
            assert is_valid is False
            assert error_message == "User request cannot be empty"
    
    def test_validate_basic_inputs_empty_content_type(self, strategy):
        """Test basic input validation with empty content type."""
        test_cases = ["", "   ", None]
        
        for content_type in test_cases:
            is_valid, error_message = strategy._validate_basic_inputs("Valid request", content_type)
            
            assert is_valid is False
            assert error_message == "Content type cannot be empty"


class TestBaseGenerationStrategyInheritance:
    """Test that BaseGenerationStrategy properly extends ContentGenerationStrategy."""
    
    def test_inherits_from_content_generation_strategy(self):
        """Test inheritance hierarchy."""
        from src.services.warren.strategies.content_generation_strategy import ContentGenerationStrategy
        
        strategy = ConcreteBaseStrategy()
        assert isinstance(strategy, ContentGenerationStrategy)
        assert isinstance(strategy, BaseGenerationStrategy)
    
    def test_abstract_methods_still_required(self):
        """Test that abstract methods from parent are still required."""
        with pytest.raises(TypeError):
            # This should fail because BaseGenerationStrategy is still abstract
            BaseGenerationStrategy()
    
    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be instantiated."""
        strategy = ConcreteBaseStrategy()
        
        # Test that all required methods are implemented
        assert strategy.get_strategy_name() == "test_base"
        assert strategy.can_handle({}) is True
        
        # Test that inherited methods work
        platform = strategy._extract_platform_from_content_type("linkedin_post")
        assert platform == "linkedin"


class TestBaseGenerationStrategyIntegration:
    """Integration tests for BaseGenerationStrategy with realistic scenarios."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy for integration testing."""
        return ConcreteBaseStrategy()
    
    def test_error_handling_integration(self, strategy):
        """Test full error handling workflow."""
        # Simulate an error that might occur during generation
        original_error = ValueError("Database connection failed")
        
        result = strategy._handle_generation_error(original_error, "advanced")
        
        # Verify complete error result structure
        assert result.success is False
        assert result.error_message == "Database connection failed"
        assert result.strategy_used == "advanced"
        assert result.metadata["error_type"] == "advanced_generation_failure"
        assert result.content is None
        assert result.generation_time == 0.0
    
    def test_success_workflow_integration(self, strategy):
        """Test complete success workflow."""
        # Simulate successful generation workflow
        result = GenerationResult()
        start_time = time.time() - 1.5
        
        metadata = {
            "phase": "Phase_1_Standard",
            "token_count": 150,
            "optimization_applied": False
        }
        
        strategy._populate_success_result(
            result, "Generated marketing content", "standard", start_time, **metadata
        )
        
        # Verify complete success result
        assert result.success is True
        assert result.content == "Generated marketing content"
        assert result.strategy_used == "standard"
        assert result.generation_time > 1.0
        assert result.metadata["phase"] == "Phase_1_Standard"
        assert result.metadata["token_count"] == 150
        assert result.metadata["optimization_applied"] is False
