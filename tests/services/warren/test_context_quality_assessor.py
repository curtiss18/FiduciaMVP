"""
Tests for ContextQualityAssessor

Test Coverage:
- assess_context_quality (direct port of _assess_context_quality)
- is_context_sufficient (convenience wrapper)
- get_quality_score (convenience wrapper)
- get_quality_reason (convenience wrapper)
"""

import pytest
from src.services.warren.context_quality_assessor import ContextQualityAssessor


class TestContextQualityAssessor:
    """Test suite for ContextQualityAssessor."""
    
    @pytest.fixture
    def assessor(self):
        """Create ContextQualityAssessor instance for testing."""
        return ContextQualityAssessor()
    
    @pytest.fixture
    def vector_unavailable_context(self):
        """Context data with vector search unavailable."""
        return {
            "marketing_examples": [{"id": "ex1"}],
            "disclaimers": [{"id": "disc1"}],
            "vector_available": False
        }
    
    @pytest.fixture
    def no_content_context(self):
        """Context data with no content found."""
        return {
            "marketing_examples": [],
            "disclaimers": [],
            "vector_available": True
        }
    
    @pytest.fixture
    def no_disclaimers_context(self):
        """Context data with marketing examples but no disclaimers."""
        return {
            "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
            "disclaimers": [],
            "vector_available": True
        }
    
    @pytest.fixture
    def sufficient_context(self):
        """Context data with sufficient quality."""
        return {
            "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
            "disclaimers": [{"id": "disc1"}],
            "vector_available": True
        }
    
    @pytest.fixture
    def high_quality_context(self):
        """Context data with high quality content."""
        return {
            "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}, {"id": "ex3"}],
            "disclaimers": [{"id": "disc1"}, {"id": "disc2"}],
            "vector_available": True
        }
    
    # Test assess_context_quality method
    def test_assess_context_quality_vector_unavailable(self, assessor, vector_unavailable_context):
        """Test quality assessment when vector search is unavailable."""
        result = assessor.assess_context_quality(vector_unavailable_context)
        
        expected = {"sufficient": False, "score": 0.0, "reason": "vector_search_unavailable"}
        assert result == expected
    
    def test_assess_context_quality_no_content(self, assessor, no_content_context):
        """Test quality assessment when no content is found."""
        result = assessor.assess_context_quality(no_content_context)
        
        expected = {"sufficient": False, "score": 0.1, "reason": "no_relevant_content_found"}
        assert result == expected
    
    def test_assess_context_quality_no_disclaimers(self, assessor, no_disclaimers_context):
        """Test quality assessment when no disclaimers are found."""
        result = assessor.assess_context_quality(no_disclaimers_context)
        
        expected = {"sufficient": False, "score": 0.4, "reason": "no_disclaimers_found"}
        assert result == expected
    
    def test_assess_context_quality_sufficient(self, assessor, sufficient_context):
        """Test quality assessment when content is sufficient."""
        result = assessor.assess_context_quality(sufficient_context)
        
        # Expected score: (2 marketing * 0.4) + (1 disclaimer * 0.3) + 0.3 = 0.8 + 0.3 + 0.3 = 1.4 -> min(1.0, 1.4) = 1.0
        expected = {"sufficient": True, "score": 1.0, "reason": "sufficient_quality"}
        assert result == expected
    
    def test_assess_context_quality_high_quality(self, assessor, high_quality_context):
        """Test quality assessment with high quality content."""
        result = assessor.assess_context_quality(high_quality_context)
        
        # Expected score: (3 marketing * 0.4) + (2 disclaimers * 0.3) + 0.3 = 1.2 + 0.6 + 0.3 = 2.1 -> min(1.0, 2.1) = 1.0
        expected = {"sufficient": True, "score": 1.0, "reason": "sufficient_quality"}
        assert result == expected
    
    def test_assess_context_quality_minimal_sufficient(self, assessor):
        """Test quality assessment with minimal sufficient content (1 disclaimer only)."""
        context = {
            "marketing_examples": [],
            "disclaimers": [{"id": "disc1"}],
            "vector_available": True
        }
        result = assessor.assess_context_quality(context)
        
        # Expected score: (0 marketing * 0.4) + (1 disclaimer * 0.3) + 0.3 = 0 + 0.3 + 0.3 = 0.6
        expected = {"sufficient": True, "score": 0.6, "reason": "sufficient_quality"}
        assert result == expected
    
    def test_assess_context_quality_missing_fields(self, assessor):
        """Test quality assessment with missing fields in context data."""
        context = {}  # Empty context data
        result = assessor.assess_context_quality(context)
        
        # Should handle missing fields gracefully
        expected = {"sufficient": False, "score": 0.0, "reason": "vector_search_unavailable"}
        assert result == expected
    
    def test_assess_context_quality_scoring_formula(self, assessor):
        """Test quality scoring formula with specific values."""
        # Test case: 1 marketing example, 1 disclaimer
        context = {
            "marketing_examples": [{"id": "ex1"}],
            "disclaimers": [{"id": "disc1"}],
            "vector_available": True
        }
        result = assessor.assess_context_quality(context)
        
        # Expected score: (1 * 0.4) + (1 * 0.3) + 0.3 = 0.4 + 0.3 + 0.3 = 1.0
        assert result["score"] == 1.0
        assert result["sufficient"] == True
        assert result["reason"] == "sufficient_quality"
    
    # Test convenience wrapper methods
    def test_is_context_sufficient_true(self, assessor, sufficient_context):
        """Test is_context_sufficient returns True for sufficient context."""
        result = assessor.is_context_sufficient(sufficient_context)
        assert result == True
    
    def test_is_context_sufficient_false(self, assessor, no_disclaimers_context):
        """Test is_context_sufficient returns False for insufficient context."""
        result = assessor.is_context_sufficient(no_disclaimers_context)
        assert result == False
    
    def test_get_quality_score(self, assessor, sufficient_context):
        """Test get_quality_score returns correct score."""
        result = assessor.get_quality_score(sufficient_context)
        assert result == 1.0
    
    def test_get_quality_score_low_quality(self, assessor, no_disclaimers_context):
        """Test get_quality_score returns correct score for low quality."""
        result = assessor.get_quality_score(no_disclaimers_context)
        assert result == 0.4
    
    def test_get_quality_reason_sufficient(self, assessor, sufficient_context):
        """Test get_quality_reason returns correct reason for sufficient context."""
        result = assessor.get_quality_reason(sufficient_context)
        assert result == "sufficient_quality"
    
    def test_get_quality_reason_insufficient(self, assessor, vector_unavailable_context):
        """Test get_quality_reason returns correct reason for insufficient context."""
        result = assessor.get_quality_reason(vector_unavailable_context)
        assert result == "vector_search_unavailable"
    
    # Test edge cases and boundary conditions
    def test_assess_context_quality_edge_case_scoring(self, assessor):
        """Test edge cases in scoring formula."""
        # Edge case: Large number of examples should cap at 1.0
        context = {
            "marketing_examples": [{"id": f"ex{i}"} for i in range(10)],  # 10 examples
            "disclaimers": [{"id": f"disc{i}"} for i in range(5)],        # 5 disclaimers
            "vector_available": True
        }
        result = assessor.assess_context_quality(context)
        
        # Score should be capped at 1.0 regardless of high counts
        assert result["score"] == 1.0
        assert result["sufficient"] == True
        assert result["reason"] == "sufficient_quality"
    
    def test_assess_context_quality_boundary_conditions(self, assessor):
        """Test boundary conditions in quality assessment."""
        test_cases = [
            # (marketing_count, disclaimer_count, expected_sufficient, expected_reason)
            (0, 0, False, "no_relevant_content_found"),
            (1, 0, False, "no_disclaimers_found"),
            (0, 1, True, "sufficient_quality"),
            (1, 1, True, "sufficient_quality"),
            (5, 0, False, "no_disclaimers_found"),
            (0, 5, True, "sufficient_quality"),
        ]
        
        for marketing_count, disclaimer_count, expected_sufficient, expected_reason in test_cases:
            context = {
                "marketing_examples": [{"id": f"ex{i}"} for i in range(marketing_count)],
                "disclaimers": [{"id": f"disc{i}"} for i in range(disclaimer_count)],
                "vector_available": True
            }
            result = assessor.assess_context_quality(context)
            
            assert result["sufficient"] == expected_sufficient, f"Failed for marketing={marketing_count}, disclaimer={disclaimer_count}"
            assert result["reason"] == expected_reason, f"Failed reason for marketing={marketing_count}, disclaimer={disclaimer_count}"
    
    # Integration test
    def test_all_methods_consistency(self, assessor, sufficient_context):
        """Test that all methods return consistent results."""
        # Get results from main method
        quality_result = assessor.assess_context_quality(sufficient_context)
        
        # Get results from convenience methods
        is_sufficient = assessor.is_context_sufficient(sufficient_context)
        quality_score = assessor.get_quality_score(sufficient_context)
        quality_reason = assessor.get_quality_reason(sufficient_context)
        
        # Verify consistency
        assert is_sufficient == quality_result["sufficient"]
        assert quality_score == quality_result["score"]
        assert quality_reason == quality_result["reason"]
    
    def test_behavioral_compatibility_with_original(self, assessor):
        """Test behavioral compatibility with original enhanced_warren_service implementation."""
        # Test cases that match the original implementation exactly
        original_test_cases = [
            # Vector unavailable
            {
                "input": {"marketing_examples": [], "disclaimers": [], "vector_available": False},
                "expected": {"sufficient": False, "score": 0.0, "reason": "vector_search_unavailable"}
            },
            # No content found
            {
                "input": {"marketing_examples": [], "disclaimers": [], "vector_available": True},
                "expected": {"sufficient": False, "score": 0.1, "reason": "no_relevant_content_found"}
            },
            # No disclaimers
            {
                "input": {"marketing_examples": [{"id": "ex1"}, {"id": "ex2"}], "disclaimers": [], "vector_available": True},
                "expected": {"sufficient": False, "score": 0.4, "reason": "no_disclaimers_found"}
            },
            # Sufficient quality (matches enhanced_warren_service test case)
            {
                "input": {"marketing_examples": [{"id": "ex1"}, {"id": "ex2"}], "disclaimers": [{"id": "disc1"}], "vector_available": True},
                "expected": {"sufficient": True, "score": 1.0, "reason": "sufficient_quality"}
            }
        ]
        
        for test_case in original_test_cases:
            result = assessor.assess_context_quality(test_case["input"])
            assert result == test_case["expected"], f"Failed compatibility test for input: {test_case['input']}"
