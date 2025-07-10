"""
Unit tests for context models.

Tests for RequestType, ContextType, ContextElement, and CompressionStrategy.
Requirement: 95%+ coverage for all models.
"""

import pytest
from datetime import datetime
from src.services.context_assembler.models.context_models import (
    RequestType,
    ContextType,
    ContextElement,
    CompressionStrategy
)


class TestRequestType:
    """Test RequestType enum."""
    
    def test_enum_values(self):
        """Test that all enum values are correct."""
        assert RequestType.CREATION.value == "creation_mode"
        assert RequestType.REFINEMENT.value == "refinement_mode"
        assert RequestType.ANALYSIS.value == "analysis_mode"
        assert RequestType.CONVERSATION.value == "conversation_mode"
    
    def test_enum_membership(self):
        """Test enum membership checks."""
        assert RequestType.CREATION in RequestType
        assert RequestType.REFINEMENT in RequestType
        assert RequestType.ANALYSIS in RequestType
        assert RequestType.CONVERSATION in RequestType
    
    def test_string_conversion(self):
        """Test string representation."""
        assert str(RequestType.CREATION) == "RequestType.CREATION"
        assert repr(RequestType.CREATION) == "<RequestType.CREATION: 'creation_mode'>"


class TestContextType:
    """Test ContextType enum."""
    
    def test_enum_values(self):
        """Test that all enum values are correct."""
        assert ContextType.SYSTEM_PROMPT.value == "system_prompt"
        assert ContextType.CONVERSATION_HISTORY.value == "conversation_history"
        assert ContextType.DOCUMENT_SUMMARIES.value == "document_summaries"
        assert ContextType.COMPLIANCE_SOURCES.value == "compliance_sources"
        assert ContextType.CURRENT_CONTENT.value == "current_content"
        assert ContextType.VECTOR_SEARCH_RESULTS.value == "vector_search_results"
        assert ContextType.YOUTUBE_CONTEXT.value == "youtube_context"
        assert ContextType.USER_INPUT.value == "user_input"
    
    def test_enum_completeness(self):
        """Test that we have all expected context types."""
        expected_types = {
            "system_prompt", "conversation_history", "document_summaries",
            "compliance_sources", "current_content", "vector_search_results",
            "youtube_context", "user_input"
        }
        actual_types = {ct.value for ct in ContextType}
        assert actual_types == expected_types


class TestCompressionStrategy:
    """Test CompressionStrategy enum."""
    
    def test_enum_values(self):
        """Test that all enum values are correct."""
        assert CompressionStrategy.PRESERVE_STRUCTURE.value == "preserve_structure"
        assert CompressionStrategy.EXTRACT_KEY_POINTS.value == "extract_key_points"
        assert CompressionStrategy.SUMMARIZE_SEMANTIC.value == "summarize_semantic"
        assert CompressionStrategy.TRUNCATE_SMART.value == "truncate_smart"
        assert CompressionStrategy.CONVERSATION_COMPRESS.value == "conversation_compress"


class TestContextElement:
    """Test ContextElement dataclass."""
    
    def create_valid_element(self, **overrides):
        """Helper to create a valid ContextElement."""
        defaults = {
            "content": "Sample content for testing",
            "context_type": ContextType.COMPLIANCE_SOURCES,
            "priority_score": 5.0,
            "relevance_score": 0.7,
            "token_count": 100,
            "source_metadata": {"source": "test", "type": "unit_test"},
            "compression_level": 0.0
        }
        defaults.update(overrides)
        return ContextElement(**defaults)
    
    def test_valid_element_creation(self):
        """Test creating a valid ContextElement."""
        element = self.create_valid_element()
        
        assert element.content == "Sample content for testing"
        assert element.context_type == ContextType.COMPLIANCE_SOURCES
        assert element.priority_score == 5.0
        assert element.relevance_score == 0.7
        assert element.token_count == 100
        assert element.compression_level == 0.0
        assert element.source_metadata == {"source": "test", "type": "unit_test"}
    
    def test_empty_content_validation(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="ContextElement content cannot be empty"):
            self.create_valid_element(content="")
    
    def test_invalid_context_type_validation(self):
        """Test that invalid context_type raises TypeError."""
        with pytest.raises(TypeError, match="context_type must be a ContextType enum"):
            self.create_valid_element(context_type="invalid_type")
    
    def test_priority_score_validation(self):
        """Test priority_score validation."""
        # Test negative priority
        with pytest.raises(ValueError, match="priority_score must be between 0.0 and 10.0"):
            self.create_valid_element(priority_score=-1.0)
        
        # Test too high priority
        with pytest.raises(ValueError, match="priority_score must be between 0.0 and 10.0"):
            self.create_valid_element(priority_score=11.0)
        
        # Test boundary values
        element_min = self.create_valid_element(priority_score=0.0)
        assert element_min.priority_score == 0.0
        
        element_max = self.create_valid_element(priority_score=10.0)
        assert element_max.priority_score == 10.0
    
    def test_relevance_score_validation(self):
        """Test relevance_score validation."""
        # Test negative relevance
        with pytest.raises(ValueError, match="relevance_score must be between 0.0 and 1.0"):
            self.create_valid_element(relevance_score=-0.1)
        
        # Test too high relevance
        with pytest.raises(ValueError, match="relevance_score must be between 0.0 and 1.0"):
            self.create_valid_element(relevance_score=1.1)
        
        # Test boundary values
        element_min = self.create_valid_element(relevance_score=0.0)
        assert element_min.relevance_score == 0.0
        
        element_max = self.create_valid_element(relevance_score=1.0)
        assert element_max.relevance_score == 1.0
    
    def test_token_count_validation(self):
        """Test token_count validation."""
        with pytest.raises(ValueError, match="token_count cannot be negative"):
            self.create_valid_element(token_count=-1)
        
        # Test zero tokens (should be valid)
        element = self.create_valid_element(token_count=0)
        assert element.token_count == 0
    
    def test_compression_level_validation(self):
        """Test compression_level validation."""
        # Test negative compression
        with pytest.raises(ValueError, match="compression_level must be between 0.0 and 1.0"):
            self.create_valid_element(compression_level=-0.1)
        
        # Test too high compression
        with pytest.raises(ValueError, match="compression_level must be between 0.0 and 1.0"):
            self.create_valid_element(compression_level=1.1)
        
        # Test boundary values
        element_min = self.create_valid_element(compression_level=0.0)
        assert element_min.compression_level == 0.0
        
        element_max = self.create_valid_element(compression_level=1.0)
        assert element_max.compression_level == 1.0
    
    def test_effective_priority_calculation(self):
        """Test effective_priority property calculation."""
        element = self.create_valid_element(priority_score=5.0, relevance_score=0.6)
        expected = 5.0 * (1.0 + 0.6)  # 5.0 * 1.6 = 8.0
        assert element.effective_priority == expected
        
        # Test with zero relevance
        element_zero = self.create_valid_element(priority_score=5.0, relevance_score=0.0)
        assert element_zero.effective_priority == 5.0
        
        # Test with maximum relevance
        element_max = self.create_valid_element(priority_score=5.0, relevance_score=1.0)
        assert element_max.effective_priority == 10.0
    
    def test_compression_ratio_calculation(self):
        """Test compression_ratio property calculation."""
        # No compression
        element_none = self.create_valid_element(compression_level=0.0)
        assert element_none.compression_ratio == 1.0
        
        # 50% compression
        element_half = self.create_valid_element(compression_level=0.5)
        assert element_half.compression_ratio == 0.5
        
        # Maximum compression
        element_max = self.create_valid_element(compression_level=1.0)
        assert element_max.compression_ratio == 0.0
    
    def test_is_high_priority(self):
        """Test is_high_priority method."""
        # High priority element (effective_priority >= 8.0)
        high_priority = self.create_valid_element(priority_score=8.0, relevance_score=0.0)
        assert high_priority.is_high_priority() is True
        
        # Another high priority (priority * (1 + relevance) >= 8.0)
        high_priority2 = self.create_valid_element(priority_score=5.0, relevance_score=0.6)  # 5.0 * 1.6 = 8.0
        assert high_priority2.is_high_priority() is True
        
        # Low priority element
        low_priority = self.create_valid_element(priority_score=3.0, relevance_score=0.5)  # 3.0 * 1.5 = 4.5
        assert low_priority.is_high_priority() is False
    
    def test_is_compressible(self):
        """Test is_compressible method."""
        # Compressible: large content with low compression
        compressible = self.create_valid_element(
            token_count=1000, 
            compression_level=0.2
        )
        assert compressible.is_compressible() is True
        
        # Not compressible: already highly compressed
        not_compressible_high_compression = self.create_valid_element(
            token_count=1000,
            compression_level=0.9
        )
        assert not_compressible_high_compression.is_compressible() is False
        
        # Not compressible: small content
        not_compressible_small = self.create_valid_element(
            token_count=100,
            compression_level=0.2
        )
        assert not_compressible_small.is_compressible() is False
        
        # Edge case: exactly 500 tokens with 0.8 compression
        edge_case = self.create_valid_element(
            token_count=500,
            compression_level=0.8
        )
        assert edge_case.is_compressible() is False
        
        # Edge case: 501 tokens with 0.7 compression
        edge_case2 = self.create_valid_element(
            token_count=501,
            compression_level=0.7
        )
        assert edge_case2.is_compressible() is True
