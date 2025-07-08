"""
Tests for ContextRetrievalService

Test Coverage:
- get_vector_search_context (direct port of _get_vector_search_context)
- get_text_search_context (direct port of _get_text_search_context)
- combine_contexts (direct port of _combine_contexts)
- assess_context_quality (direct port of _assess_context_quality)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.context_retrieval_service import ContextRetrievalService
from src.models.refactored_database import ContentType


class TestContextRetrievalService:
    """Test suite for ContextRetrievalService."""
    
    @pytest.fixture
    def mock_vector_search_service(self):
        """Mock vector search service."""
        mock_service = AsyncMock()
        mock_service.check_readiness.return_value = {"ready": True}
        mock_service.search_marketing_content.return_value = []
        mock_service.search_compliance_rules.return_value = []
        return mock_service
    
    @pytest.fixture
    def mock_warren_db_service(self):
        """Mock warren database service."""
        mock_service = AsyncMock()
        mock_service.search_marketing_content.return_value = []
        mock_service.get_disclaimers_for_content_type.return_value = []
        return mock_service
    
    @pytest.fixture
    def service(self, mock_vector_search_service, mock_warren_db_service):
        """Create ContextRetrievalService instance for testing."""
        return ContextRetrievalService(
            vector_search_service=mock_vector_search_service,
            warren_db_service=mock_warren_db_service,
            enable_vector_search=True,
            vector_similarity_threshold=0.1,
            min_results_threshold=1
        )
    
    @pytest.fixture
    def sample_marketing_examples(self):
        """Sample marketing examples for testing."""
        return [
            {
                "id": "example_1",
                "title": "Retirement Planning Post",
                "content_text": "Planning for retirement is crucial...",
                "content_type": "linkedin_post",
                "tags": "retirement, planning",
                "similarity_score": 0.85
            },
            {
                "id": "example_2", 
                "title": "Investment Strategy Newsletter",
                "content_text": "Diversification is key to success...",
                "content_type": "newsletter",
                "tags": "investment, strategy",
                "similarity_score": 0.75
            }
        ]
    
    @pytest.fixture
    def sample_disclaimers(self):
        """Sample disclaimers for testing."""
        return [
            {
                "id": "disclaimer_1",
                "title": "Investment Risk Disclaimer",
                "content_text": "Past performance does not guarantee future results...",
                "tags": "disclaimer, risk, disclosure"
            },
            {
                "id": "disclaimer_2",
                "title": "General Financial Advice Disclaimer", 
                "content_text": "This content is for educational purposes only...",
                "tags": "disclaimer, educational"
            }
        ]
    
    # Test get_vector_search_context method
    @pytest.mark.asyncio
    async def test_get_vector_search_context_success(self, service, mock_vector_search_service, sample_marketing_examples, sample_disclaimers):
        """Test successful vector search context retrieval."""
        # Setup
        mock_vector_search_service.search_marketing_content.return_value = sample_marketing_examples
        mock_vector_search_service.search_compliance_rules.return_value = sample_disclaimers
        
        # Execute
        result = await service.get_vector_search_context(
            user_request="retirement planning post",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST,
            audience_type="retail_investors"
        )
        
        # Verify
        expected = {
            "marketing_examples": sample_marketing_examples,
            "disclaimers": sample_disclaimers,
            "vector_available": True,
            "search_method": "vector",
            "vector_results_count": 2,
            "disclaimer_count": 2,
            "total_sources": 4
        }
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_get_vector_search_context_disabled(self, mock_vector_search_service, mock_warren_db_service):
        """Test vector search context when disabled."""
        # Setup
        service = ContextRetrievalService(
            vector_search_service=mock_vector_search_service,
            warren_db_service=mock_warren_db_service,
            enable_vector_search=False
        )
        
        # Execute
        result = await service.get_vector_search_context(
            user_request="test",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Verify
        expected = {"marketing_examples": [], "disclaimers": [], "vector_available": False}
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_get_vector_search_context_not_ready(self, service, mock_vector_search_service):
        """Test vector search context when not ready."""
        # Setup
        mock_vector_search_service.check_readiness.return_value = {"ready": False, "reason": "Not initialized"}
        
        # Execute
        result = await service.get_vector_search_context(
            user_request="test",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Verify
        assert result["vector_available"] == False
        assert result["marketing_examples"] == []
        assert result["disclaimers"] == []
    
    @pytest.mark.asyncio
    async def test_get_vector_search_context_exception(self, service, mock_vector_search_service):
        """Test vector search context when exception occurs."""
        # Setup
        mock_vector_search_service.search_marketing_content.side_effect = Exception("Vector search failed")
        
        # Execute
        result = await service.get_vector_search_context(
            user_request="test",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Verify
        assert result["vector_available"] == False
        assert "error" in result
    
    # Test get_text_search_context method
    @pytest.mark.asyncio
    async def test_get_text_search_context_success(self, service, mock_warren_db_service, sample_marketing_examples, sample_disclaimers):
        """Test text search context retrieval."""
        # Setup
        mock_warren_db_service.search_marketing_content.return_value = sample_marketing_examples
        mock_warren_db_service.get_disclaimers_for_content_type.return_value = sample_disclaimers
        
        # Execute
        result = await service.get_text_search_context(
            user_request="retirement planning",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Verify
        expected = {
            "marketing_examples": sample_marketing_examples,
            "disclaimers": sample_disclaimers,
            "search_method": "text",
            "text_results_count": 2,
            "disclaimer_count": 2,
            "total_sources": 4
        }
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_get_text_search_context_exception(self, service, mock_warren_db_service):
        """Test text search context when exception occurs."""
        # Setup
        mock_warren_db_service.search_marketing_content.side_effect = Exception("Database error")
        
        # Execute
        result = await service.get_text_search_context(
            user_request="test",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Verify
        assert "error" in result
        assert result["marketing_examples"] == []
        assert result["disclaimers"] == []
    
    # Test combine_contexts method
    def test_combine_contexts_basic_combination(self, service):
        """Test basic combination of vector and text search results."""
        # Setup
        vector_results = {
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
        
        text_results = {
            "marketing_examples": [
                {"id": "text_1", "title": "Text Example 1"},
                {"id": "vector_1", "title": "Duplicate Vector Example"}  # Duplicate
            ],
            "disclaimers": [
                {"id": "text_disclaimer_1", "title": "Text Disclaimer 1"}
            ],
            "search_method": "text"
        }
        
        # Execute
        result = service.combine_contexts(vector_results, text_results)
        
        # Verify
        assert result["search_strategy"] == "hybrid"
        assert len(result["marketing_examples"]) == 3  # 2 vector + 1 unique text
        assert len(result["disclaimers"]) == 2  # 1 vector + 1 text (since vector had < 2)
        assert result["total_sources"] == 5
        assert result["text_results_count"] == 1  # Only unique text results
        
        # Check deduplication
        marketing_ids = [ex["id"] for ex in result["marketing_examples"]]
        assert marketing_ids == ["vector_1", "vector_2", "text_1"]
    
    def test_combine_contexts_sufficient_vector_disclaimers(self, service):
        """Test combination when vector results already have sufficient disclaimers."""
        # Setup
        vector_results = {
            "marketing_examples": [{"id": "vector_1", "title": "Vector Example"}],
            "disclaimers": [
                {"id": "vector_disclaimer_1", "title": "Vector Disclaimer 1"},
                {"id": "vector_disclaimer_2", "title": "Vector Disclaimer 2"}
            ],
            "vector_available": True
        }
        
        text_results = {
            "marketing_examples": [{"id": "text_1", "title": "Text Example"}],
            "disclaimers": [{"id": "text_disclaimer_1", "title": "Text Disclaimer"}]
        }
        
        # Execute
        result = service.combine_contexts(vector_results, text_results)
        
        # Verify - text disclaimers should not be added since vector has >= 2
        assert len(result["disclaimers"]) == 2
        disclaimer_ids = [d["id"] for d in result["disclaimers"]]
        assert "text_disclaimer_1" not in disclaimer_ids
    
    # Test assess_context_quality method
    def test_assess_context_quality_vector_unavailable(self, service):
        """Test quality assessment when vector search is unavailable."""
        # Setup
        results = {
            "marketing_examples": [{"id": "test"}],
            "disclaimers": [{"id": "test"}],
            "vector_available": False
        }
        
        # Execute
        quality = service.assess_context_quality(results)
        
        # Verify
        assert quality["sufficient"] == False
        assert quality["score"] == 0.0
        assert quality["reason"] == "vector_search_unavailable"
    
    def test_assess_context_quality_no_content(self, service):
        """Test quality assessment when no content is found."""
        # Setup
        results = {
            "marketing_examples": [],
            "disclaimers": [],
            "vector_available": True
        }
        
        # Execute
        quality = service.assess_context_quality(results)
        
        # Verify
        assert quality["sufficient"] == False
        assert quality["score"] == 0.1
        assert quality["reason"] == "no_relevant_content_found"
    
    def test_assess_context_quality_no_disclaimers(self, service):
        """Test quality assessment when no disclaimers are found."""
        # Setup
        results = {
            "marketing_examples": [{"id": "test1"}, {"id": "test2"}],
            "disclaimers": [],
            "vector_available": True
        }
        
        # Execute
        quality = service.assess_context_quality(results)
        
        # Verify
        assert quality["sufficient"] == False
        assert quality["score"] == 0.4
        assert quality["reason"] == "no_disclaimers_found"
    
    def test_assess_context_quality_sufficient(self, service):
        """Test quality assessment when content is sufficient."""
        # Setup
        results = {
            "marketing_examples": [{"id": "test1"}, {"id": "test2"}],
            "disclaimers": [{"id": "disclaimer1"}],
            "vector_available": True
        }
        
        # Execute
        quality = service.assess_context_quality(results)
        
        # Verify
        assert quality["sufficient"] == True
        assert quality["score"] == 1.0  # (2 * 0.4) + (1 * 0.3) + 0.3 = 1.0
        assert quality["reason"] == "sufficient_quality"
    
    # Integration test
    @pytest.mark.asyncio
    async def test_full_workflow(self, service, mock_vector_search_service, mock_warren_db_service, sample_marketing_examples, sample_disclaimers):
        """Test complete workflow matching original enhanced_warren_service behavior."""
        # Setup
        mock_vector_search_service.search_marketing_content.return_value = sample_marketing_examples[:1]  # 1 result
        mock_vector_search_service.search_compliance_rules.return_value = sample_disclaimers[:1]  # 1 result
        mock_warren_db_service.search_marketing_content.return_value = sample_marketing_examples[1:]  # 1 different result
        mock_warren_db_service.get_disclaimers_for_content_type.return_value = sample_disclaimers[1:]  # 1 different result
        
        # Execute vector search
        vector_context = await service.get_vector_search_context(
            user_request="retirement planning",
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Execute text search
        text_context = await service.get_text_search_context(
            user_request="retirement planning", 
            content_type="linkedin_post",
            content_type_enum=ContentType.LINKEDIN_POST
        )
        
        # Combine results
        combined = service.combine_contexts(vector_context, text_context)
        
        # Assess quality
        quality = service.assess_context_quality(combined)
        
        # Verify
        assert combined["search_strategy"] == "hybrid"
        assert len(combined["marketing_examples"]) == 2  # 1 vector + 1 text
        assert len(combined["disclaimers"]) == 2  # 1 vector + 1 text (vector had < 2)
        assert quality["sufficient"] == True
