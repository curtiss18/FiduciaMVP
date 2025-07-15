"""
Tests for YouTube Context Service

Test Coverage:
- YouTubeContextService functionality
- Context integration and formatting
- Validation and error handling
- Transcript truncation
- Summary generation
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.warren.youtube_context_service import YouTubeContextService, youtube_context_service


class TestYouTubeContextService:
    """Test YouTubeContextService implementation."""
    
    @pytest.fixture
    def service(self):
        """Create YouTubeContextService instance for testing."""
        return YouTubeContextService(max_transcript_length=100)
    
    @pytest.fixture
    def sample_youtube_data(self):
        """Sample YouTube data for testing."""
        return {
            "metadata": {
                "url": "https://youtube.com/watch?v=test123",
                "title": "Test Investment Video"
            },
            "stats": {
                "word_count": 50
            },
            "transcript": "This is a test transcript about investment strategies and market analysis."
        }
    
    def test_service_initialization(self):
        """Test service initialization with different parameters."""
        service1 = YouTubeContextService()
        assert service1.max_transcript_length == 4000  # Default
        
        service2 = YouTubeContextService(max_transcript_length=200)
        assert service2.max_transcript_length == 200
    
    def test_add_youtube_context_basic(self, service, sample_youtube_data):
        """Test basic YouTube context addition."""
        context_parts = ["Initial context"]
        original_length = len(context_parts)
        
        result = service.add_youtube_context(context_parts, sample_youtube_data)
        
        # Should add content
        assert len(result) > original_length
        assert any("VIDEO CONTEXT" in part for part in result)
        assert any("transcript" in part.lower() for part in result)
        assert any("https://youtube.com/watch?v=test123" in part for part in result)
    
    def test_add_youtube_context_empty_data(self, service):
        """Test handling of empty YouTube context."""
        context_parts = ["Initial context"]
        
        # Test with None
        result = service.add_youtube_context(context_parts, None)
        assert result == context_parts
        
        # Test with empty dict - should still return unchanged since no content to add
        result = service.add_youtube_context(context_parts, {})
        assert len(result) >= len(context_parts)  # Should be same or add minimal structure
    
    def test_transcript_truncation(self, service):
        """Test that long transcripts are properly truncated."""
        context_parts = []
        long_youtube_data = {
            "transcript": "This is a very long transcript " * 20  # Much longer than 100 chars
        }
        
        result = service.add_youtube_context(context_parts, long_youtube_data)
        
        # Find the transcript part
        transcript_part = None
        for part in result:
            if "This is a very long transcript" in part:
                transcript_part = part
                break
        
        assert transcript_part is not None
        assert len(transcript_part) < len(long_youtube_data["transcript"])
        assert "..." in transcript_part
    
    def test_transcript_no_truncation_needed(self, service, sample_youtube_data):
        """Test that short transcripts are not truncated."""
        context_parts = []
        
        result = service.add_youtube_context(context_parts, sample_youtube_data)
        
        # Find the transcript part
        transcript_part = None
        for part in result:
            if sample_youtube_data["transcript"] in part:
                transcript_part = part
                break
        
        assert transcript_part is not None
        assert "..." not in transcript_part
    
    def test_format_youtube_context_for_prompt(self, service, sample_youtube_data):
        """Test standalone string formatting."""
        result = service.format_youtube_context_for_prompt(sample_youtube_data)
        
        assert isinstance(result, str)
        assert "VIDEO CONTEXT" in result
        assert sample_youtube_data["transcript"] in result
        assert sample_youtube_data["metadata"]["url"] in result
    
    def test_format_youtube_context_empty(self, service):
        """Test standalone string formatting with empty data."""
        result = service.format_youtube_context_for_prompt(None)
        assert result == ""
        
        result = service.format_youtube_context_for_prompt({})
        assert isinstance(result, str)
    
    def test_validate_youtube_context(self, service, sample_youtube_data):
        """Test YouTube context validation."""
        # Valid context
        assert service.validate_youtube_context(sample_youtube_data) is True
        
        # Invalid context (not dict)
        assert service.validate_youtube_context("not a dict") is False
        assert service.validate_youtube_context(None) is False
        assert service.validate_youtube_context([]) is False
        
        # Empty context
        assert service.validate_youtube_context({}) is False
        
        # Context with only metadata
        metadata_only = {"metadata": {"url": "test"}}
        assert service.validate_youtube_context(metadata_only) is True
        
        # Context with only transcript
        transcript_only = {"transcript": "test transcript"}
        assert service.validate_youtube_context(transcript_only) is True
    
    def test_get_transcript_summary(self, service, sample_youtube_data):
        """Test transcript summary generation."""
        summary = service.get_transcript_summary(sample_youtube_data)
        
        assert summary["has_transcript"] is True
        assert summary["transcript_length"] == len(sample_youtube_data["transcript"])
        assert summary["word_count"] == 50
        assert summary["will_be_truncated"] is False  # Short transcript
        assert summary["truncated_length"] == len(sample_youtube_data["transcript"])
    
    def test_get_transcript_summary_long_transcript(self, service):
        """Test transcript summary with truncation."""
        long_transcript = "word " * 50  # 250 characters, will be truncated at 100
        youtube_data = {
            "transcript": long_transcript,
            "stats": {"word_count": 50}
        }
        
        summary = service.get_transcript_summary(youtube_data)
        
        assert summary["has_transcript"] is True
        assert summary["transcript_length"] == len(long_transcript)
        assert summary["will_be_truncated"] is True
        assert summary["truncated_length"] == 100
    
    def test_get_transcript_summary_no_transcript(self, service):
        """Test transcript summary with no transcript."""
        youtube_data = {"metadata": {"url": "test"}}
        
        summary = service.get_transcript_summary(youtube_data)
        
        assert summary["has_transcript"] is False
        assert summary["transcript_length"] == 0
        assert summary["word_count"] == 0
        assert summary["will_be_truncated"] is False
        assert summary["truncated_length"] == 0
    
    def test_error_handling(self, service):
        """Test error handling for malformed data."""
        context_parts = ["Initial"]
        
        # Should not raise exception, just log error
        malformed_data = {"metadata": "not a dict"}
        result = service.add_youtube_context(context_parts, malformed_data)
        
        # Should still return something, even if error occurred
        assert len(result) >= len(context_parts)
    
    def test_default_service_instance(self):
        """Test that default youtube_context_service instance works."""
        context_parts = []
        youtube_data = {"transcript": "Test"}
        
        # Should work with default instance
        result = youtube_context_service.add_youtube_context(context_parts, youtube_data)
        assert len(result) > 0
        assert youtube_context_service.max_transcript_length == 4000  # Default value


class TestYouTubeContextServiceIntegration:
    """Integration tests for YouTube Context Service."""
    
    @pytest.fixture
    def service(self):
        """Create service for integration testing."""
        return YouTubeContextService()
    
    def test_real_world_youtube_data_structure(self, service):
        """Test with realistic YouTube data structure."""
        realistic_data = {
            "metadata": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": "Understanding Market Volatility",
                "description": "A comprehensive guide to market analysis",
                "duration": "PT10M30S"
            },
            "stats": {
                "word_count": 1500,
                "duration_seconds": 630
            },
            "transcript": "Welcome to today's discussion on market volatility. " * 100  # Long transcript
        }
        
        context_parts = ["## EXISTING CONTEXT"]
        result = service.add_youtube_context(context_parts, realistic_data)
        
        assert len(result) > 1
        assert any("Understanding Market Volatility" in part for part in result)
        assert any("market volatility" in part.lower() for part in result)
    
    def test_multiple_context_additions(self, service):
        """Test adding multiple YouTube contexts."""
        context_parts = ["Initial"]
        
        youtube1 = {"transcript": "First video content"}
        youtube2 = {"transcript": "Second video content"}
        
        # Add first video
        result1 = service.add_youtube_context(context_parts, youtube1)
        
        # Add second video to existing context
        result2 = service.add_youtube_context(result1, youtube2)
        
        # Should contain both
        full_text = " ".join(result2)
        assert "First video content" in full_text
        assert "Second video content" in full_text
