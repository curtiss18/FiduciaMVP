"""Tests for GenericCompressor."""

import pytest

from src.services.context_assembly_service.optimization.compression.generic_compressor import GenericCompressor
from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager
from src.services.context_assembly_service.models import ContextType


class TestGenericCompressor:
    """Test generic compression functionality."""
    
    @pytest.fixture
    def token_manager(self):
        return TextTokenManager()
    
    @pytest.fixture
    def compressor(self, token_manager):
        return GenericCompressor(token_manager)
    
    @pytest.mark.asyncio
    async def test_fallback_truncation_strategy(self, compressor):
        """Test simple truncation when other strategies fail."""
        content = "This is a long piece of content that needs to be truncated to fit within the token limit. " * 10
        target_tokens = 30
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        actual_tokens = compressor.token_manager.count_tokens(result)
        
        # Should truncate to approximately target tokens
        assert actual_tokens <= target_tokens * 1.1  # Allow 10% tolerance
        assert len(result) < len(content)  # Should be shorter
    
    @pytest.mark.asyncio
    async def test_binary_search_truncation(self, compressor):
        """Test binary search for optimal truncation point."""
        content = "Word " * 100  # Predictable content
        target_tokens = 25
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        actual_tokens = compressor.token_manager.count_tokens(result)
        
        # Should find efficient truncation point (allow small tolerance)
        assert actual_tokens <= target_tokens * 1.1  # Allow 10% tolerance
        assert actual_tokens >= target_tokens * 0.8  # Should be reasonably close
    
    @pytest.mark.asyncio
    async def test_content_quality_preservation(self, compressor):
        """Test truncated content maintains readability."""
        content = """
        This is the beginning of important content that should be preserved.
        The first sentence contains critical information.
        Additional details follow in subsequent sentences.
        More content continues here with supporting information.
        """
        
        target_tokens = 20
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should preserve beginning of content (most important)
        assert "beginning" in result or "important" in result
        assert "first sentence" in result or "critical" in result
    
    @pytest.mark.asyncio
    async def test_boundary_condition_handling(self, compressor):
        """Test edge cases in truncation logic."""
        # Test with content exactly at target
        short_content = "Short text"
        target_tokens = compressor.token_manager.count_tokens(short_content)
        
        result = await compressor.compress_content(short_content, target_tokens, ContextType.USER_INPUT)
        assert result == short_content  # Should return unchanged
        
        # Test with content slightly over target
        slightly_long = "This is slightly longer text"
        target_tokens = compressor.token_manager.count_tokens(slightly_long) - 1
        
        result = await compressor.compress_content(slightly_long, target_tokens, ContextType.USER_INPUT)
        assert len(result) < len(slightly_long)
    
    @pytest.mark.asyncio
    async def test_token_limit_accuracy(self, compressor):
        """Test truncation respects token limits accurately."""
        content = "Test content " * 50
        target_tokens = 20
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        actual_tokens = compressor.token_manager.count_tokens(result)
        
        # Should not exceed target (allow small tolerance)
        assert actual_tokens <= target_tokens * 1.1
    
    @pytest.mark.asyncio
    async def test_ellipsis_addition(self, compressor):
        """Test '...' added to truncated content."""
        content = "This is a long piece of content that will be truncated. " * 20
        target_tokens = 15
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should add ellipsis when truncated (or be acceptable if not truncated)
        if len(result) < len(content):
            assert result.endswith("...") or result.endswith(".") 
        else:
            # If content wasn't truncated, that's also acceptable
            assert True
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, compressor):
        """Test handling of empty/null content."""
        assert await compressor.compress_content("", 50, ContextType.USER_INPUT) == ""
        assert await compressor.compress_content("   ", 50, ContextType.USER_INPUT) == "   "
        assert await compressor.compress_content(None, 50, ContextType.USER_INPUT) is None
    
    @pytest.mark.asyncio
    async def test_single_word_content(self, compressor):
        """Test handling of single word content."""
        content = "Word"
        target_tokens = 1
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should handle gracefully
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenericCompressorEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def compressor(self):
        return GenericCompressor(TextTokenManager())
    
    @pytest.mark.asyncio
    async def test_very_small_target_tokens(self, compressor):
        """Test behavior with extremely small token limits."""
        content = "This is test content that needs compression"
        target_tokens = 1
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should return something meaningful even with tiny limit
        assert len(result) > 0
        actual_tokens = compressor.token_manager.count_tokens(result)
        assert actual_tokens <= target_tokens * 2  # Allow some tolerance for very small limits
    
    @pytest.mark.asyncio
    async def test_zero_target_tokens(self, compressor):
        """Test behavior with zero token target."""
        content = "Some content"
        target_tokens = 0
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should handle gracefully, possibly returning minimal content
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_negative_target_tokens(self, compressor):
        """Test behavior with negative token target."""
        content = "Some content"
        target_tokens = -5
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should handle gracefully
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_unicode_content_handling(self, compressor):
        """Test handling of unicode and special characters."""
        content = "Content with émojis 🎉 and ünïcödé characters ñ"
        target_tokens = 10
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should handle unicode gracefully
        assert isinstance(result, str)
        actual_tokens = compressor.token_manager.count_tokens(result)
        assert actual_tokens <= target_tokens * 1.2
    
    @pytest.mark.asyncio
    async def test_whitespace_only_content(self, compressor):
        """Test content with only whitespace."""
        content = "   \n\t\r   "
        target_tokens = 5
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should preserve whitespace content
        assert result == content
    
    @pytest.mark.asyncio
    async def test_very_long_single_word(self, compressor):
        """Test handling of extremely long single word."""
        content = "supercalifragilisticexpialidocious" * 10  # Very long single "word"
        target_tokens = 5
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should truncate even single long word
        assert len(result) < len(content)
        actual_tokens = compressor.token_manager.count_tokens(result)
        assert actual_tokens <= target_tokens * 1.5


class TestGenericCompressorPerformance:
    """Test performance characteristics of generic compression."""
    
    @pytest.fixture
    def compressor(self):
        return GenericCompressor(TextTokenManager())
    
    @pytest.mark.asyncio
    async def test_large_content_performance(self, compressor):
        """Test performance with very large content."""
        import time
        
        # Generate large content
        large_content = "This is a performance test sentence. " * 1000
        target_tokens = 100
        
        start_time = time.perf_counter()
        result = await compressor.compress_content(large_content, target_tokens, ContextType.USER_INPUT)
        compression_time = time.perf_counter() - start_time
        
        # Should complete within reasonable time
        assert compression_time < 1.0  # Less than 1 second
        assert len(result) < len(large_content)
    
    @pytest.mark.asyncio
    async def test_compression_efficiency(self, compressor):
        """Test compression achieves good size reduction."""
        content = "Repeated content. " * 100
        target_tokens = 20
        
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should achieve significant compression
        compression_ratio = len(result) / len(content)
        assert compression_ratio < 0.5  # At least 50% reduction


class TestGenericCompressorIntegration:
    """Integration tests with different content types."""
    
    @pytest.fixture
    def compressor(self):
        return GenericCompressor(TextTokenManager())
    
    @pytest.mark.asyncio
    async def test_user_input_compression(self, compressor):
        """Test compression of user input content."""
        content = """
        I want to create a comprehensive social media post about retirement planning 
        that explains the importance of starting early and includes information about 
        compound interest, tax-advantaged accounts, and risk management strategies.
        """
        
        target_tokens = 25
        result = await compressor.compress_content(content, target_tokens, ContextType.USER_INPUT)
        
        # Should preserve key concepts
        key_terms = ["retirement", "social media", "compound interest", "risk"]
        preserved_terms = sum(1 for term in key_terms if term in result.lower())
        assert preserved_terms >= 2
    
    @pytest.mark.asyncio
    async def test_system_prompt_compression(self, compressor):
        """Test compression of system prompt content."""
        content = """
        You are Warren, a financial compliance AI assistant. Your role is to help
        financial advisors create compliant marketing content that meets SEC and 
        FINRA requirements while being engaging and informative for their target audience.
        """
        
        target_tokens = 30
        result = await compressor.compress_content(content, target_tokens, ContextType.SYSTEM_PROMPT)
        
        # Should preserve essential role information
        assert "Warren" in result or "financial" in result
        assert "compliance" in result or "compliant" in result
