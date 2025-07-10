"""Tests for TextTokenManager."""

import pytest
import time
import hashlib
from unittest.mock import patch, MagicMock

from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager


class TestTextTokenManagerAccuracy:
    """Test token counting accuracy."""
    
    def test_empty_content_returns_zero(self):
        manager = TextTokenManager()
        assert manager.count_tokens("") == 0
        assert manager.count_tokens(None) == 0
    
    def test_basic_text_counting(self):
        manager = TextTokenManager()
        # Test with known text
        text = "Hello world this is a test"
        count = manager.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)
    
    def test_special_characters_handling(self):
        manager = TextTokenManager()
        text = "Hello! @#$%^&*() 🎉 special chars"
        count = manager.count_tokens(text)
        assert count > 0
    
    def test_very_long_content(self):
        manager = TextTokenManager()
        # Generate long text (>10k chars)
        long_text = "This is a test sentence. " * 500
        count = manager.count_tokens(long_text)
        assert count > 1000
    
    def test_whitespace_handling(self):
        manager = TextTokenManager()
        assert manager.count_tokens("   ") > 0
        assert manager.count_tokens("\n\t\r") > 0
        assert manager.count_tokens("word   word") > 0


class TestTextTokenManagerCaching:
    """Test cache performance and functionality."""
    
    def test_cache_hit_scenario(self):
        manager = TextTokenManager()
        text = "Test content for caching"
        
        # First call - cache miss
        count1 = manager.count_tokens(text)
        stats1 = manager.get_cache_stats()
        
        # Second call - cache hit
        count2 = manager.count_tokens(text)
        stats2 = manager.get_cache_stats()
        
        assert count1 == count2
        assert stats2["cache_hits"] > stats1["cache_hits"]
    
    def test_cache_miss_scenario(self):
        manager = TextTokenManager()
        text1 = "First text content"
        text2 = "Second different text content"
        
        manager.count_tokens(text1)
        stats1 = manager.get_cache_stats()
        
        manager.count_tokens(text2)
        stats2 = manager.get_cache_stats()
        
        assert stats2["cache_misses"] > stats1["cache_misses"]
    
    def test_cache_size_limit_enforcement(self):
        manager = TextTokenManager(cache_size_limit=2)
        
        # Fill cache beyond limit
        manager.count_tokens("text1")
        manager.count_tokens("text2")
        manager.count_tokens("text3")  # Should evict first entry
        
        stats = manager.get_cache_stats()
        assert stats["cache_size"] <= 2
    
    def test_performance_improvement_measurement(self):
        manager = TextTokenManager()
        text = "Performance test content for measuring speed improvements"
        
        # Measure first call (miss)
        start = time.perf_counter()
        manager.count_tokens(text)
        miss_time = time.perf_counter() - start
        
        # Measure second call (hit)
        start = time.perf_counter()
        manager.count_tokens(text)
        hit_time = time.perf_counter() - start
        
        # Cache should be significantly faster
        assert hit_time < miss_time
        
    def test_cache_stats_accuracy(self):
        manager = TextTokenManager()
        
        # Initial stats
        initial_stats = manager.get_cache_stats()
        assert initial_stats["cache_hits"] == 0
        assert initial_stats["cache_misses"] == 0
        
        # After operations
        manager.count_tokens("test1")  # miss
        manager.count_tokens("test2")  # miss
        manager.count_tokens("test1")  # hit
        
        final_stats = manager.get_cache_stats()
        assert final_stats["cache_hits"] == 1
        assert final_stats["cache_misses"] == 2
        assert final_stats["hit_rate_percent"] == 33.33


class TestTextTokenManagerCacheManagement:
    """Test cache management functionality."""
    
    def test_cache_clear_functionality(self):
        manager = TextTokenManager()
        
        # Add content to cache
        manager.count_tokens("test content")
        assert manager.get_cache_stats()["cache_size"] > 0
        
        # Clear cache
        manager.clear_cache()
        stats = manager.get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
    
    def test_memory_usage_reasonable(self):
        manager = TextTokenManager(cache_size_limit=100)
        
        # Fill cache with various content
        for i in range(50):
            manager.count_tokens(f"test content number {i}")
        
        # Cache should not exceed limit
        assert manager.get_cache_stats()["cache_size"] <= 100
    
    def test_hash_collision_handling(self):
        manager = TextTokenManager()
        
        # Mock hash collision scenario
        with patch.object(hashlib, 'md5') as mock_md5:
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "same_hash"
            mock_md5.return_value = mock_hash
            
            count1 = manager.count_tokens("text1")
            count2 = manager.count_tokens("text2")
            
            # Should handle collision gracefully
            assert isinstance(count1, int)
            assert isinstance(count2, int)


class TestTextTokenManagerFallback:
    """Test fallback functionality."""
    
    def test_tiktoken_unavailable_fallback(self):
        with patch('src.services.context_assembly_service.optimization.text_token_manager.tiktoken') as mock_tiktoken:
            mock_tiktoken.encoding_for_model.side_effect = Exception("No tiktoken")
            
            manager = TextTokenManager()
            count = manager.count_tokens("test content")
            
            # Should fallback to character estimation
            assert count > 0
            assert count == len("test content") // 4
    
    def test_encoding_error_fallback(self):
        manager = TextTokenManager()
        
        # Mock encoding failure
        if manager.tokenizer:
            with patch.object(manager.tokenizer, 'encode', side_effect=Exception("Encoding error")):
                count = manager.count_tokens("test content")
                assert count == len("test content") // 4
    
    def test_fallback_accuracy_approximation(self):
        # Test fallback provides reasonable approximation
        with patch('src.services.context_assembly_service.optimization.text_token_manager.tiktoken') as mock_tiktoken:
            mock_tiktoken.encoding_for_model.side_effect = Exception("No tiktoken")
            
            manager = TextTokenManager()
            text = "This is a test sentence with multiple words"
            count = manager.count_tokens(text)
            
            # Should be approximately 1 token per 4 characters
            expected = len(text) // 4
            assert count == expected


class TestTextTokenManagerPerformance:
    """Test performance characteristics."""
    
    def test_cache_performance_improvement(self):
        manager = TextTokenManager()
        text = "Performance test content " * 100  # Larger text
        
        # Measure multiple cache misses
        miss_times = []
        for i in range(3):
            start = time.perf_counter()
            manager.count_tokens(f"{text}_{i}")
            miss_times.append(time.perf_counter() - start)
        
        # Measure cache hits
        hit_times = []
        for i in range(3):
            start = time.perf_counter()
            manager.count_tokens(f"{text}_{i}")
            hit_times.append(time.perf_counter() - start)
        
        avg_miss = sum(miss_times) / len(miss_times)
        avg_hit = sum(hit_times) / len(hit_times)
        
        # Cache should provide significant improvement
        improvement = (avg_miss - avg_hit) / avg_miss * 100
        assert improvement > 50  # At least 50% improvement
    
    def test_concurrent_operations(self):
        manager = TextTokenManager()
        
        # Simulate concurrent access
        results = []
        for i in range(10):
            count = manager.count_tokens(f"concurrent test {i}")
            results.append(count)
        
        # All operations should complete successfully
        assert len(results) == 10
        assert all(isinstance(r, int) and r > 0 for r in results)
    
    def test_large_content_performance(self):
        manager = TextTokenManager()
        
        # Very large content
        large_text = "This is a large content test. " * 1000
        
        start = time.perf_counter()
        count = manager.count_tokens(large_text)
        duration = time.perf_counter() - start
        
        # Should complete within reasonable time
        assert duration < 1.0  # Less than 1 second
        assert count > 5000


class TestTextTokenManagerUtilityMethods:
    """Test utility estimation methods."""
    
    def test_estimate_tokens_from_chars(self):
        manager = TextTokenManager()
        
        char_count = 1000
        estimated_tokens = manager.estimate_tokens_from_chars(char_count)
        
        assert estimated_tokens == 250  # 1000 / 4
    
    def test_estimate_chars_from_tokens(self):
        manager = TextTokenManager()
        
        token_count = 250
        estimated_chars = manager.estimate_chars_from_tokens(token_count)
        
        assert estimated_chars == 1000  # 250 * 4
