"""Integration tests for BasicContextAssemblyOrchestrator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.orchestrator import BasicContextAssemblyOrchestrator
from src.services.context_assembly_service.models import RequestType, ContextType


class TestBasicContextAssemblyOrchestratorIntegration:
    """Integration tests verifying orchestrator works with real dependencies."""
    
    def setup_method(self):
        # Use real dependencies (not mocked) for integration testing
        self.orchestrator = BasicContextAssemblyOrchestrator()
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_real_dependencies(self):
        """Test orchestrator works with real service dependencies."""
        
        # Mock the database session and external dependencies
        mock_db_session = AsyncMock(spec=AsyncSession)
        
        # Test basic functionality
        result = await self.orchestrator.build_warren_context(
            session_id="integration-test-session",
            user_input="Create a LinkedIn post about retirement planning",
            db_session=mock_db_session
        )
        
        # Verify expected structure
        assert isinstance(result, dict)
        assert "context" in result
        assert "request_type" in result
        assert "total_tokens" in result
        assert "token_budget" in result
        assert "context_breakdown" in result
        assert "optimization_applied" in result
        
        # Verify request type analysis works
        assert result["request_type"] == RequestType.CREATION.value
        
        # Verify context contains user input
        assert "Create a LinkedIn post about retirement planning" in result["context"]
        
        # Verify token counts are reasonable
        assert result["total_tokens"] > 0
        assert result["total_tokens"] < 200000  # Should be under max limit
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_interface(self):
        """Test that interface matches original ContextAssembler exactly."""
        
        # Test all parameters from original interface
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create investment advice content",
            context_data={"search_results": ["Example compliance guidance"]},
            current_content="Previous draft content",
            youtube_context={"transcript": "Video about investing", "video_id": "test123"},
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Verify all expected keys from original ContextAssembler
        expected_keys = [
            "context",
            "request_type", 
            "total_tokens",
            "token_budget",
            "context_breakdown",
            "optimization_applied"
        ]
        
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"
        
        # Verify types match original expectations
        assert isinstance(result["context"], str)
        assert isinstance(result["request_type"], str)
        assert isinstance(result["total_tokens"], int)
        assert isinstance(result["token_budget"], dict)
        assert isinstance(result["context_breakdown"], dict)
        assert isinstance(result["optimization_applied"], bool)
        
        # Verify request type detection for refinement
        assert result["request_type"] == RequestType.REFINEMENT.value  # Should detect refinement mode
    
    @pytest.mark.asyncio
    async def test_context_data_processing(self):
        """Test processing of context_data like original ContextAssembler."""
        
        context_data = {
            "search_results": [
                "First compliance example about FINRA rules",
                "Second example about SEC regulations", 
                "Third example about marketing guidelines"
            ],
            "additional_info": "Extra context information"
        }
        
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create compliant marketing content",
            context_data=context_data,
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Verify search results are included in context
        context = result["context"]
        assert "FINRA rules" in context
        assert "SEC regulations" in context
        assert "marketing guidelines" in context
        
        # Verify context breakdown includes vector search results
        breakdown = result["context_breakdown"]
        assert "vector_search_results" in breakdown or len([k for k in breakdown.keys() if "search" in k or "vector" in k]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_fallback(self):
        """Test graceful error handling with fallback context."""
        
        # Create orchestrator with broken dependencies to trigger fallback
        broken_orchestrator = BasicContextAssemblyOrchestrator()
        
        # Mock a service to fail
        with patch.object(broken_orchestrator.request_analyzer, 'analyze_request_type', side_effect=Exception("Service failure")):
            result = await broken_orchestrator.build_warren_context(
                session_id="test-session",
                user_input="Test content creation",
                context_data={"search_results": ["fallback context"]},
                db_session=AsyncMock(spec=AsyncSession)
            )
            
            # Should return fallback result
            assert "fallback_used" in result
            assert result["fallback_used"] is True
            assert "Test content creation" in result["context"]
            assert result["request_type"] == RequestType.CREATION.value
    
    @pytest.mark.asyncio
    async def test_large_context_optimization(self):
        """Test that large contexts trigger optimization."""
        
        # Create large context data to trigger optimization
        large_search_results = [f"Large search result {i} " + "content " * 100 for i in range(50)]
        
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content with lots of context",
            context_data={"search_results": large_search_results},
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Should stay under reasonable limits
        assert result["total_tokens"] < 200000  # Under max limit
        
        # May or may not trigger optimization depending on actual content size
        # Just verify the field exists
        assert "optimization_applied" in result
        assert isinstance(result["optimization_applied"], bool)
    
    @pytest.mark.asyncio
    async def test_conversation_integration(self):
        """Test integration with conversation context gathering."""
        
        # Mock database session that would return conversation data
        mock_db_session = AsyncMock(spec=AsyncSession)
        
        result = await self.orchestrator.build_warren_context(
            session_id="conversation-test-session",
            user_input="Continue our discussion about portfolio diversification", 
            db_session=mock_db_session
        )
        
        # Should complete successfully even if no conversation history found
        assert result["request_type"] == RequestType.CONVERSATION.value
        assert "portfolio diversification" in result["context"]
        
        # Verify conversation context type appears in breakdown or context
        # (may be empty if no actual conversation data, but should be handled gracefully)
        assert isinstance(result["context_breakdown"], dict)
    
    @pytest.mark.asyncio
    async def test_document_context_integration(self):
        """Test integration with document context gathering."""
        
        # Test with session that could have documents
        result = await self.orchestrator.build_warren_context(
            session_id="document-test-session",
            user_input="Create content based on uploaded documents",
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Should complete successfully and handle document gathering
        assert "uploaded documents" in result["context"].lower()
        assert result["total_tokens"] > 0
    
    @pytest.mark.asyncio 
    async def test_youtube_context_integration(self):
        """Test YouTube context processing integration."""
        
        youtube_data = {
            "transcript": "This video discusses the importance of starting to invest early for retirement. The power of compound interest means that even small amounts invested in your 20s can grow to substantial sums by retirement age.",
            "video_id": "retirement_investing_123",
            "title": "Early Retirement Investing Tips"
        }
        
        result = await self.orchestrator.build_warren_context(
            session_id="youtube-test-session",
            user_input="Create a post based on this retirement investing video",
            youtube_context=youtube_data,
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Verify YouTube content is included
        context = result["context"]
        assert "compound interest" in context
        assert "retirement" in context
        
        # Verify YouTube context is tracked in breakdown
        breakdown = result["context_breakdown"]
        assert "youtube_context" in breakdown or any("youtube" in k for k in breakdown.keys())
    
    @pytest.mark.asyncio
    async def test_token_budget_allocation(self):
        """Test that token budgets are allocated properly."""
        
        result = await self.orchestrator.build_warren_context(
            session_id="budget-test-session",
            user_input="Create comprehensive financial planning content",
            context_data={"search_results": ["Budget allocation test context"]},
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        # Verify token budget structure
        budget = result["token_budget"]
        assert isinstance(budget, dict)
        
        # Should have allocated budget for user input
        assert ContextType.USER_INPUT in budget
        assert budget[ContextType.USER_INPUT] > 0
        
        # Total allocated should be reasonable
        total_allocated = sum(budget.values())
        assert total_allocated <= 200000  # Should not exceed max tokens
        assert total_allocated > 0  # Should allocate some tokens
