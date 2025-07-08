"""
Integration tests for ContextRetrievalService behavioral compatibility.

Epic: [SCRUM-76] Refactor Enhanced Warren Service
Task: [SCRUM-77] Extract ContextRetrievalService

Purpose: Validate that the new ContextRetrievalService produces identical results
to the current enhanced_warren_service context retrieval methods.

These tests ensure zero functional regressions during the refactoring process.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.services.enhanced_warren_service import EnhancedWarrenService
from src.services.warren.context_retrieval_service import ContextRetrievalService
from src.models.refactored_database import ContentType


class TestContextRetrievalBehavioralCompatibility:
    """
    Test suite to ensure new ContextRetrievalService produces identical results
    to the original enhanced_warren_service methods.
    """
    
    @pytest.fixture
    def sample_vector_results(self):
        """Sample vector search results for consistent testing."""
        return [
            {
                "id": "vector_example_1",
                "title": "Retirement Planning LinkedIn Post",
                "content_text": "Start planning for retirement early to secure your financial future...",
                "content_type": "linkedin_post",
                "tags": "retirement, planning, linkedin",
                "similarity_score": 0.85
            },
            {
                "id": "vector_example_2",
                "title": "Investment Strategy Newsletter",
                "content_text": "Diversification is key to successful long-term investing...",
                "content_type": "newsletter",
                "tags": "investment, strategy, diversification",
                "similarity_score": 0.73
            }
        ]
    
    @pytest.fixture
    def sample_compliance_results(self):
        """Sample compliance search results for testing."""
        return [
            {
                "id": "compliance_1",
                "title": "Investment Risk Disclaimer",
                "content_text": "Past performance does not guarantee future results. All investments carry risk...",
                "tags": "disclaimer, risk, investment"
            },
            {
                "id": "compliance_2",
                "title": "General Financial Advice Disclaimer",
                "content_text": "This content is for educational purposes only and should not be considered...",
                "tags": "disclaimer, educational, advice"
            }
        ]
    
    @pytest.fixture
    def sample_text_results(self):
        """Sample text search results for testing."""
        return [
            {
                "id": "text_example_1",
                "title": "Retirement Savings Tips",
                "content_text": "Here are some practical tips for building your retirement savings...",
                "content_type": "blog_post",
                "tags": "retirement, savings, tips"
            }
        ]
    
    @pytest.fixture
    def mock_services(self, sample_vector_results, sample_compliance_results, sample_text_results):
        """Mock external services with consistent test data."""
        with patch('src.services.vector_search_service.vector_search_service') as mock_vector, \
             patch('src.services.warren_database_service.warren_db_service') as mock_warren:
            
            # Setup vector search service
            mock_vector.check_readiness.return_value = {"ready": True}
            mock_vector.search_marketing_content.return_value = sample_vector_results
            mock_vector.search_compliance_rules.return_value = sample_compliance_results
            
            # Setup warren database service
            mock_warren.search_marketing_content.return_value = sample_text_results
            mock_warren.get_disclaimers_for_content_type.return_value = sample_compliance_results
            
            yield {
                'vector_search': mock_vector,
                'warren_db': mock_warren
            }
    
    async def test_vector_search_context_compatibility(self, mock_services, sample_vector_results, sample_compliance_results):
        """
        Test that new ContextRetrievalService.get_vector_search_context produces
        identical results to enhanced_warren_service._get_vector_search_context.
        """
        # Setup
        original_service = EnhancedWarrenService()
        new_service = ContextRetrievalService()
        
        test_params = {
            "user_request": "retirement planning linkedin post",
            "content_type": "linkedin_post",
            "content_type_enum": ContentType.LINKEDIN_POST,
            "audience_type": "retail_investors"
        }
        
        # Execute both implementations
        original_result = await original_service._get_vector_search_context(**test_params)
        new_result = await new_service.get_vector_search_context(**test_params)
        
        # Verify identical results
        assert original_result == new_result
        assert original_result["marketing_examples"] == sample_vector_results
        assert original_result["disclaimers"] == sample_compliance_results
        assert original_result["vector_available"] == True
        assert original_result["search_method"] == "vector"
        assert original_result["vector_results_count"] == len(sample_vector_results)
        assert original_result["disclaimer_count"] == len(sample_compliance_results)
    
    async def test_text_search_context_compatibility(self, mock_services, sample_text_results, sample_compliance_results):
        """
        Test that new ContextRetrievalService.get_text_search_context produces
        identical results to enhanced_warren_service._get_text_search_context.
        """
        # Setup
        original_service = EnhancedWarrenService()
        new_service = ContextRetrievalService()
        
        test_params = {
            "user_request": "retirement planning",
            "content_type": "linkedin_post",
            "content_type_enum": ContentType.LINKEDIN_POST
        }
        
        # Execute both implementations
        original_result = await original_service._get_text_search_context(**test_params)
        new_result = await new_service.get_text_search_context(**test_params)
        
        # Verify identical results
        assert original_result == new_result
        assert original_result["marketing_examples"] == sample_text_results
        assert original_result["disclaimers"] == sample_compliance_results
        assert original_result["search_method"] == "text"
        assert original_result["text_results_count"] == len(sample_text_results)
        assert original_result["disclaimer_count"] == len(sample_compliance_results)
    
    async def test_combine_contexts_compatibility(self, mock_services):
        """
        Test that new ContextRetrievalService.combine_search_results produces
        identical results to enhanced_warren_service._combine_contexts.
        """
        # Setup
        original_service = EnhancedWarrenService()
        new_service = ContextRetrievalService()
        
        vector_context = {
            "marketing_examples": [
                {"id": "vector_1", "title": "Vector Example 1"},
                {"id": "vector_2", "title": "Vector Example 2"}
            ],
            "disclaimers": [
                {"id": "vector_disclaimer_1", "title": "Vector Disclaimer 1"}
            ],
            "vector_available": True,
            "search_method": "vector"
        }
        
        text_context = {
            "marketing_examples": [
                {"id": "text_1", "title": "Text Example 1"},
                {"id": "vector_1", "title": "Duplicate Example"}  # Should be deduplicated
            ],
            "disclaimers": [
                {"id": "text_disclaimer_1", "title": "Text Disclaimer 1"}
            ],
            "search_method": "text"
        }
        
        # Execute both implementations
        original_result = original_service._combine_contexts(vector_context, text_context)
        new_result = await new_service.combine_search_results(vector_context, text_context)
        
        # Verify identical results
        assert original_result == new_result
        assert original_result["search_strategy"] == "hybrid"
        assert len(original_result["marketing_examples"]) == 3  # 2 vector + 1 unique text
        assert len(original_result["disclaimers"]) == 2  # 1 vector + 1 text (since vector had < 2)
        
        # Verify deduplication works identically
        marketing_ids = [ex["id"] for ex in original_result["marketing_examples"]]
        assert "vector_1" in marketing_ids  # Should appear only once despite being in both
        assert marketing_ids.count("vector_1") == 1
    
    async def test_quality_assessment_compatibility(self, mock_services):
        """
        Test that new ContextRetrievalService.assess_retrieval_quality produces
        identical results to enhanced_warren_service._assess_context_quality.
        """
        # Setup
        original_service = EnhancedWarrenService()
        new_service = ContextRetrievalService()
        
        test_cases = [
            # Case 1: Vector search unavailable
            {
                "marketing_examples": [{"id": "test"}],
                "disclaimers": [{"id": "test"}],
                "vector_available": False
            },
            # Case 2: No content found
            {
                "marketing_examples": [],
                "disclaimers": [],
                "vector_available": True
            },
            # Case 3: No disclaimers
            {
                "marketing_examples": [{"id": "test1"}, {"id": "test2"}],
                "disclaimers": [],
                "vector_available": True
            },
            # Case 4: Sufficient content
            {
                "marketing_examples": [{"id": "test1"}, {"id": "test2"}],
                "disclaimers": [{"id": "disclaimer1"}],
                "vector_available": True
            }
        ]
        
        for test_case in test_cases:
            # Execute both implementations
            original_result = original_service._assess_context_quality(test_case)
            new_result = new_service.assess_retrieval_quality(test_case)
            
            # Verify identical results
            assert original_result == new_result
            assert original_result["sufficient"] == new_result["sufficient"]
            assert original_result["score"] == new_result["score"]
            assert original_result["reason"] == new_result["reason"]
    
    async def test_error_handling_compatibility(self, mock_services):
        """
        Test that error handling behavior is identical between implementations.
        """
        # Setup services with vector search failure
        with patch('src.services.vector_search_service.vector_search_service') as mock_vector:
            mock_vector.check_readiness.return_value = {"ready": True}
            mock_vector.search_marketing_content.side_effect = Exception("Vector search failed")
            
            original_service = EnhancedWarrenService()
            new_service = ContextRetrievalService()
            
            test_params = {
                "user_request": "test query",
                "content_type": "linkedin_post",
                "content_type_enum": ContentType.LINKEDIN_POST
            }
            
            # Execute both implementations
            original_result = await original_service._get_vector_search_context(**test_params)
            new_result = await new_service.get_vector_search_context(**test_params)
            
            # Verify identical error handling
            assert original_result == new_result
            assert original_result["vector_available"] == False
            assert "error" in original_result
            assert original_result["marketing_examples"] == []
            assert original_result["disclaimers"] == []
    
    async def test_configuration_compatibility(self, mock_services):
        """
        Test that configuration parameters work identically in both implementations.
        """
        # Test with vector search disabled
        original_service = EnhancedWarrenService()
        original_service.enable_vector_search = False
        
        new_service = ContextRetrievalService(enable_vector_search=False)
        
        test_params = {
            "user_request": "test query",
            "content_type": "linkedin_post", 
            "content_type_enum": ContentType.LINKEDIN_POST
        }
        
        # Execute both implementations
        original_result = await original_service._get_vector_search_context(**test_params)
        new_result = await new_service.get_vector_search_context(**test_params)
        
        # Verify identical behavior when vector search is disabled
        assert original_result == new_result
        assert original_result["vector_available"] == False
        assert original_result["marketing_examples"] == []
        assert original_result["disclaimers"] == []
    
    async def test_comprehensive_workflow_compatibility(self, mock_services, sample_vector_results, sample_compliance_results, sample_text_results):
        """
        Test complete workflow compatibility across all methods.
        """
        # Setup
        original_service = EnhancedWarrenService()
        new_service = ContextRetrievalService()
        
        # Test complete vector search workflow
        vector_params = {
            "user_request": "retirement planning post",
            "content_type": "linkedin_post",
            "content_type_enum": ContentType.LINKEDIN_POST,
            "audience_type": "retail_investors"
        }
        
        original_vector = await original_service._get_vector_search_context(**vector_params)
        new_vector = await new_service.get_vector_search_context(**vector_params)
        
        # Test complete text search workflow
        text_params = {
            "user_request": "retirement planning post",
            "content_type": "linkedin_post",
            "content_type_enum": ContentType.LINKEDIN_POST
        }
        
        original_text = await original_service._get_text_search_context(**text_params)
        new_text = await new_service.get_text_search_context(**text_params)
        
        # Test combination
        original_combined = original_service._combine_contexts(original_vector, original_text)
        new_combined = await new_service.combine_search_results(new_vector, new_text)
        
        # Test quality assessment
        original_quality = original_service._assess_context_quality(original_combined)
        new_quality = new_service.assess_retrieval_quality(new_combined)
        
        # Verify all results are identical
        assert original_vector == new_vector
        assert original_text == new_text
        assert original_combined == new_combined
        assert original_quality == new_quality
        
        # Verify workflow produces expected results
        assert original_combined["search_strategy"] == "hybrid"
        assert original_combined["total_sources"] > 0
        assert original_quality["sufficient"] == True
        assert original_quality["score"] > 0.5

