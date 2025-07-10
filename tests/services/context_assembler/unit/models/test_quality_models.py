"""
Unit tests for quality models.

Tests for QualityMetrics and FormattingOptions classes.
Requirement: 95%+ coverage for all models.
"""

import pytest
from datetime import datetime, timedelta
from src.services.context_assembly_service.models.quality_models import (
    QualityMetrics,
    FormattingOptions
)


class TestQualityMetrics:
    """Test QualityMetrics dataclass."""
    
    def create_valid_metrics(self, **overrides):
        """Helper to create valid QualityMetrics."""
        defaults = {
            "relevance_score": 0.8,
            "completeness_score": 0.7,
            "coherence_score": 0.9,
            "diversity_score": 0.6,
            "token_efficiency": 0.75,
            "compression_ratio": 0.8
        }
        defaults.update(overrides)
        return QualityMetrics(**defaults)
    
    def test_valid_metrics_creation(self):
        """Test creating valid QualityMetrics."""
        metrics = self.create_valid_metrics()
        
        assert metrics.relevance_score == 0.8
        assert metrics.completeness_score == 0.7
        assert metrics.coherence_score == 0.9
        assert metrics.diversity_score == 0.6
        assert metrics.token_efficiency == 0.75
        assert metrics.compression_ratio == 0.8
        assert isinstance(metrics.assessment_timestamp, datetime)
    
    def test_invalid_score_validation(self):
        """Test that invalid scores raise ValueError."""
        # Test each metric with invalid values
        invalid_metrics = [
            ("relevance_score", -0.1),
            ("relevance_score", 1.1),
            ("completeness_score", -0.1),
            ("completeness_score", 1.1),
            ("coherence_score", -0.1),
            ("coherence_score", 1.1),
            ("diversity_score", -0.1),
            ("diversity_score", 1.1),
            ("token_efficiency", -0.1),
            ("token_efficiency", 1.1),
            ("compression_ratio", -0.1),
            ("compression_ratio", 1.1),
        ]
        
        for metric_name, invalid_value in invalid_metrics:
            with pytest.raises(ValueError, match=f"{metric_name} must be between 0.0 and 1.0"):
                self.create_valid_metrics(**{metric_name: invalid_value})
    
    def test_boundary_score_values(self):
        """Test boundary score values (0.0 and 1.0)."""
        # Test minimum values
        min_metrics = self.create_valid_metrics(
            relevance_score=0.0,
            completeness_score=0.0,
            coherence_score=0.0,
            diversity_score=0.0,
            token_efficiency=0.0,
            compression_ratio=0.0
        )
        assert min_metrics.relevance_score == 0.0
        
        # Test maximum values
        max_metrics = self.create_valid_metrics(
            relevance_score=1.0,
            completeness_score=1.0,
            coherence_score=1.0,
            diversity_score=1.0,
            token_efficiency=1.0,
            compression_ratio=1.0
        )
        assert max_metrics.relevance_score == 1.0
    
    def test_overall_quality_score_calculation(self):
        """Test overall_quality_score property calculation."""
        metrics = self.create_valid_metrics(
            relevance_score=0.8,    # weight: 0.3
            completeness_score=0.6, # weight: 0.25
            coherence_score=0.9,    # weight: 0.2
            diversity_score=0.5,    # weight: 0.15
            token_efficiency=0.7    # weight: 0.1
        )
        
        expected = (0.8 * 0.3) + (0.6 * 0.25) + (0.9 * 0.2) + (0.5 * 0.15) + (0.7 * 0.1)
        # 0.24 + 0.15 + 0.18 + 0.075 + 0.07 = 0.715
        assert abs(metrics.overall_quality_score - 0.715) < 0.001
    
    def test_quality_grade_calculation(self):
        """Test quality_grade property calculation."""
        # Grade A (>= 0.9)
        grade_a = self.create_valid_metrics(
            relevance_score=1.0, completeness_score=1.0, coherence_score=1.0,
            diversity_score=1.0, token_efficiency=1.0
        )
        assert grade_a.quality_grade == "A"
        
        # Grade B (>= 0.8)
        grade_b = self.create_valid_metrics(
            relevance_score=0.8, completeness_score=0.8, coherence_score=0.8,
            diversity_score=0.8, token_efficiency=0.8
        )
        assert grade_b.quality_grade == "B"
        
        # Grade C (>= 0.7)
        grade_c = self.create_valid_metrics(
            relevance_score=0.7, completeness_score=0.7, coherence_score=0.7,
            diversity_score=0.7, token_efficiency=0.7
        )
        assert grade_c.quality_grade == "C"
        
        # Grade D (>= 0.6) - use 0.67 to account for floating point precision
        grade_d = self.create_valid_metrics(
            relevance_score=0.67, completeness_score=0.67, coherence_score=0.67,
            diversity_score=0.67, token_efficiency=0.67
        )
        assert grade_d.quality_grade == "D"
        
        # Grade F (< 0.6)
        grade_f = self.create_valid_metrics(
            relevance_score=0.5, completeness_score=0.5, coherence_score=0.5,
            diversity_score=0.5, token_efficiency=0.5
        )
        assert grade_f.quality_grade == "F"
    
    def test_is_high_quality(self):
        """Test is_high_quality method."""
        # High quality (>= 0.8)
        high_quality = self.create_valid_metrics(
            relevance_score=0.9, completeness_score=0.8, coherence_score=0.9,
            diversity_score=0.7, token_efficiency=0.8
        )
        assert high_quality.is_high_quality() is True
        
        # Low quality (< 0.8)
        low_quality = self.create_valid_metrics(
            relevance_score=0.6, completeness_score=0.6, coherence_score=0.6,
            diversity_score=0.6, token_efficiency=0.6
        )
        assert low_quality.is_high_quality() is False
    
    def test_get_improvement_suggestions(self):
        """Test get_improvement_suggestions method."""
        # Perfect metrics (no suggestions)
        perfect_metrics = self.create_valid_metrics(
            relevance_score=1.0, completeness_score=1.0, coherence_score=1.0,
            diversity_score=1.0, token_efficiency=1.0
        )
        assert perfect_metrics.get_improvement_suggestions() == []
        
        # Poor relevance
        poor_relevance = self.create_valid_metrics(relevance_score=0.6)
        suggestions = poor_relevance.get_improvement_suggestions()
        assert any("relevance" in s.lower() for s in suggestions)
        
        # Poor completeness
        poor_completeness = self.create_valid_metrics(completeness_score=0.6)
        suggestions = poor_completeness.get_improvement_suggestions()
        assert any("comprehensive" in s.lower() for s in suggestions)
        
        # Poor coherence
        poor_coherence = self.create_valid_metrics(coherence_score=0.6)
        suggestions = poor_coherence.get_improvement_suggestions()
        assert any("coherence" in s.lower() or "ordering" in s.lower() for s in suggestions)
        
        # Poor diversity
        poor_diversity = self.create_valid_metrics(diversity_score=0.4)
        suggestions = poor_diversity.get_improvement_suggestions()
        assert any("diverse" in s.lower() for s in suggestions)
        
        # Poor efficiency
        poor_efficiency = self.create_valid_metrics(token_efficiency=0.5)
        suggestions = poor_efficiency.get_improvement_suggestions()
        assert any("compression" in s.lower() for s in suggestions)
        
        # Multiple issues
        poor_multiple = self.create_valid_metrics(
            relevance_score=0.6, completeness_score=0.6, token_efficiency=0.5
        )
        suggestions = poor_multiple.get_improvement_suggestions()
        assert len(suggestions) == 3  # Should have 3 suggestions
    
    def test_timestamp_default(self):
        """Test that assessment_timestamp defaults to current time."""
        before = datetime.now()
        metrics = self.create_valid_metrics()
        after = datetime.now()
        
        assert before <= metrics.assessment_timestamp <= after
    
    def test_custom_timestamp(self):
        """Test custom assessment_timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        metrics = self.create_valid_metrics(assessment_timestamp=custom_time)
        assert metrics.assessment_timestamp == custom_time


class TestFormattingOptions:
    """Test FormattingOptions dataclass."""
    
    def create_valid_options(self, **overrides):
        """Helper to create valid FormattingOptions."""
        defaults = {}  # Use class defaults
        defaults.update(overrides)
        return FormattingOptions(**defaults)
    
    def test_default_options_creation(self):
        """Test creating FormattingOptions with defaults."""
        options = FormattingOptions()
        
        assert options.include_section_headers is True
        assert options.include_source_attribution is True
        assert options.include_token_counts is False
        assert options.include_timestamps is False
        assert options.max_line_length is None
        assert options.section_separator == "\n\n---\n\n"
        assert options.indent_nested_content is False
        assert options.preserve_original_formatting is True
    
    def test_custom_options_creation(self):
        """Test creating FormattingOptions with custom values."""
        options = self.create_valid_options(
            include_section_headers=False,
            include_token_counts=True,
            max_line_length=80,
            section_separator="===",
            indent_nested_content=True
        )
        
        assert options.include_section_headers is False
        assert options.include_token_counts is True
        assert options.max_line_length == 80
        assert options.section_separator == "==="
        assert options.indent_nested_content is True
    
    def test_invalid_max_line_length_validation(self):
        """Test validation of max_line_length."""
        with pytest.raises(ValueError, match="max_line_length must be positive if specified"):
            self.create_valid_options(max_line_length=0)
        
        with pytest.raises(ValueError, match="max_line_length must be positive if specified"):
            self.create_valid_options(max_line_length=-10)
    
    def test_empty_section_separator_validation(self):
        """Test validation of section_separator."""
        with pytest.raises(ValueError, match="section_separator cannot be empty"):
            self.create_valid_options(section_separator="")
    
    def test_has_debug_info_property(self):
        """Test has_debug_info property."""
        # No debug info
        no_debug = self.create_valid_options()
        assert no_debug.has_debug_info is False
        
        # Token counts enabled
        token_debug = self.create_valid_options(include_token_counts=True)
        assert token_debug.has_debug_info is True
        
        # Timestamps enabled
        timestamp_debug = self.create_valid_options(include_timestamps=True)
        assert timestamp_debug.has_debug_info is True
        
        # Both enabled
        both_debug = self.create_valid_options(include_token_counts=True, include_timestamps=True)
        assert both_debug.has_debug_info is True
    
    def test_create_section_header(self):
        """Test create_section_header method."""
        options = self.create_valid_options(include_section_headers=True)
        
        # Basic header
        header = options.create_section_header("Test Section")
        assert header == "## Test Section\n\n"
        
        # Header with token count
        options_with_tokens = self.create_valid_options(
            include_section_headers=True, 
            include_token_counts=True
        )
        header_with_tokens = options_with_tokens.create_section_header("Test Section", 1500)
        assert "## Test Section (1500 tokens)" in header_with_tokens
        
        # Header with timestamps
        options_with_time = self.create_valid_options(
            include_section_headers=True, 
            include_timestamps=True
        )
        header_with_time = options_with_time.create_section_header("Test Section")
        assert "## Test Section" in header_with_time
        assert ":" in header_with_time  # Should contain timestamp
        
        # Headers disabled
        options_no_headers = self.create_valid_options(include_section_headers=False)
        header_disabled = options_no_headers.create_section_header("Test Section")
        assert header_disabled == ""
    
    def test_create_source_attribution(self):
        """Test create_source_attribution method."""
        options = self.create_valid_options(include_source_attribution=True)
        
        # Basic attribution
        source_info = {"source": "test_source", "type": "document"}
        attribution = options.create_source_attribution(source_info)
        assert "*Source: test_source | Type: document*\n\n" == attribution
        
        # Attribution with confidence
        source_info_conf = {
            "source": "test_source", 
            "type": "document", 
            "confidence": 0.85
        }
        attribution_conf = options.create_source_attribution(source_info_conf)
        assert "Confidence: 0.85" in attribution_conf
        
        # Empty source info
        empty_attribution = options.create_source_attribution({})
        assert empty_attribution == ""
        
        # Attribution disabled
        options_no_attr = self.create_valid_options(include_source_attribution=False)
        disabled_attribution = options_no_attr.create_source_attribution(source_info)
        assert disabled_attribution == ""
    
    def test_format_content_block(self):
        """Test format_content_block method."""
        options = self.create_valid_options()
        
        # Basic content formatting
        content = "This is test content."
        formatted = options.format_content_block(content)
        assert formatted == content
        
        # Empty content
        empty_formatted = options.format_content_block("")
        assert empty_formatted == ""
        
        # Whitespace-only content
        whitespace_formatted = options.format_content_block("   \n  \n  ")
        assert whitespace_formatted == "   \n  \n  "
    
    def test_format_content_block_with_line_length(self):
        """Test format_content_block with max_line_length."""
        options = self.create_valid_options(max_line_length=20)
        
        # Content that needs wrapping
        long_content = "This is a very long line that should be wrapped at twenty characters"
        formatted = options.format_content_block(long_content)
        
        lines = formatted.split('\n')
        for line in lines:
            assert len(line) <= 20, f"Line too long: '{line}'"
        
        # Content that fits
        short_content = "Short line"
        short_formatted = options.format_content_block(short_content)
        assert short_formatted == short_content
    
    def test_format_content_block_with_indentation(self):
        """Test format_content_block with indentation."""
        options = self.create_valid_options(indent_nested_content=True)
        
        content = "Line 1\nLine 2\nLine 3"
        
        # No indentation
        formatted_0 = options.format_content_block(content, indent_level=0)
        assert formatted_0 == content
        
        # Single level indentation
        formatted_1 = options.format_content_block(content, indent_level=1)
        expected_1 = "  Line 1\n  Line 2\n  Line 3"
        assert formatted_1 == expected_1
        
        # Multiple level indentation
        formatted_2 = options.format_content_block(content, indent_level=2)
        expected_2 = "    Line 1\n    Line 2\n    Line 3"
        assert formatted_2 == expected_2
        
        # Content with empty lines
        content_with_empty = "Line 1\n\nLine 3"
        formatted_empty = options.format_content_block(content_with_empty, indent_level=1)
        expected_empty = "  Line 1\n\n  Line 3"
        assert formatted_empty == expected_empty
    
    def test_format_content_block_combined_options(self):
        """Test format_content_block with multiple options."""
        options = self.create_valid_options(
            max_line_length=15,
            indent_nested_content=True
        )
        
        content = "This is a long line that needs wrapping and indentation"
        formatted = options.format_content_block(content, indent_level=1)
        
        lines = formatted.split('\n')
        for line in lines:
            if line.strip():  # Non-empty lines
                assert line.startswith("  "), f"Line not indented: '{line}'"
                assert len(line) <= 17, f"Line too long (including indent): '{line}'"  # 15 + 2 indent
    
    def test_create_debug_options(self):
        """Test create_debug_options class method."""
        debug_options = FormattingOptions.create_debug_options()
        
        assert debug_options.include_section_headers is True
        assert debug_options.include_source_attribution is True
        assert debug_options.include_token_counts is True
        assert debug_options.include_timestamps is True
        assert debug_options.section_separator == "\n\n=== DEBUG SEPARATOR ===\n\n"
        assert debug_options.has_debug_info is True
    
    def test_create_production_options(self):
        """Test create_production_options class method."""
        prod_options = FormattingOptions.create_production_options()
        
        assert prod_options.include_section_headers is False
        assert prod_options.include_source_attribution is False
        assert prod_options.include_token_counts is False
        assert prod_options.include_timestamps is False
        assert prod_options.section_separator == "\n\n"
        assert prod_options.has_debug_info is False
