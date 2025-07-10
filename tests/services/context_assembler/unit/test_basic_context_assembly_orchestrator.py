"""Tests for BasicContextAssemblyOrchestrator service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.orchestrator import BasicContextAssemblyOrchestrator
from src.services.context_assembly_service.models import (
    RequestType, 
    ContextType, 
    ContextElement,
    BudgetAllocation
)


class TestBasicContextAssemblyOrchestrator:
    
    def setup_method(self):
        # Create mocks for dependencies
        self.mock_budget_allocator = AsyncMock()
        self.mock_request_analyzer = Mock()
        self.mock_context_gatherer = AsyncMock()
        self.mock_context_builder = Mock()
        self.mock_token_manager = Mock()
        
        # Create orchestrator with mocked dependencies
        self.orchestrator = BasicContextAssemblyOrchestrator(
            budget_allocator=self.mock_budget_allocator,
            request_analyzer=self.mock_request_analyzer,
            context_gatherer=self.mock_context_gatherer,
            context_builder=self.mock_context_builder,
            token_manager=self.mock_token_manager
        )
    
    @pytest.mark.asyncio
    async def test_build_warren_context_basic_workflow(self):
        """Test basic workflow of build_warren_context method."""
        
        # Setup mocks
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.CREATION
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000),
            ContextType.VECTOR_SEARCH_RESULTS: BudgetAllocation(ContextType.VECTOR_SEARCH_RESULTS, 20000)
        }
        self.mock_context_gatherer.gather_all_context.return_value = []
        self.mock_context_builder.build_context_string.return_value = "Final context string"
        self.mock_context_builder.get_context_summary.return_value = {
            'user_input': 50,
            'total_tokens': 50,
            'total_elements': 1
        }
        self.mock_token_manager.count_tokens.side_effect = [50, 100]  # user_input, final_context
        
        # Test parameters
        session_id = "test-session"
        user_input = "Create a LinkedIn post"
        db_session = Mock(spec=AsyncSession)
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id=session_id,
            user_input=user_input,
            db_session=db_session
        )
        
        # Verify calls
        self.mock_request_analyzer.analyze_request_type.assert_called_once_with(
            user_input=user_input,
            current_content=None
        )
        self.mock_budget_allocator.allocate_budget.assert_called_once()
        self.mock_context_gatherer.gather_all_context.assert_called_once()
        self.mock_context_builder.build_context_string.assert_called_once()
        
        # Verify result structure
        assert result["request_type"] == RequestType.CREATION.value
        assert result["context"] == "Final context string"
        assert result["total_tokens"] == 100
        assert "token_budget" in result
        assert "context_breakdown" in result
        assert "optimization_applied" in result
    
    @pytest.mark.asyncio
    async def test_build_warren_context_with_current_content(self):
        """Test workflow with current content (refinement mode)."""
        
        # Setup mocks for refinement
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.REFINEMENT
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000),
            ContextType.CURRENT_CONTENT: BudgetAllocation(ContextType.CURRENT_CONTENT, 15000)
        }
        self.mock_context_gatherer.gather_all_context.return_value = []
        self.mock_context_builder.build_context_string.return_value = "Refinement context"
        self.mock_context_builder.get_context_summary.return_value = {'user_input': 30, 'current_content': 200}
        self.mock_token_manager.count_tokens.side_effect = [30, 200, 250]  # user, current, final
        
        # Execute with current content
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Edit this content",
            current_content="Existing content to edit",
            db_session=Mock(spec=AsyncSession)
        )
        
        # Verify refinement mode was detected
        assert result["request_type"] == RequestType.REFINEMENT.value
        self.mock_request_analyzer.analyze_request_type.assert_called_once_with(
            user_input="Edit this content",
            current_content="Existing content to edit"
        )
    
    @pytest.mark.asyncio
    async def test_build_warren_context_with_youtube_context(self):
        """Test workflow with YouTube context."""
        
        # Setup mocks
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.CREATION
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000),
            ContextType.YOUTUBE_CONTEXT: BudgetAllocation(ContextType.YOUTUBE_CONTEXT, 30000)
        }
        self.mock_context_gatherer.gather_all_context.return_value = []
        self.mock_context_builder.build_context_string.return_value = "Context with YouTube"
        self.mock_context_builder.get_context_summary.return_value = {'user_input': 50, 'youtube_context': 500}
        self.mock_token_manager.count_tokens.side_effect = [50, 500, 600]  # user, youtube, final
        
        # YouTube context data
        youtube_context = {
            'transcript': 'This is a YouTube transcript about financial planning...',
            'video_id': 'abc123'
        }
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content based on this video",
            youtube_context=youtube_context,
            db_session=Mock(spec=AsyncSession)
        )
        
        # Verify YouTube context was processed
        assert result["total_tokens"] == 600
        # Verify that build_context_string was called with elements including YouTube
        call_args = self.mock_context_builder.build_context_string.call_args[0][0]
        youtube_elements = [elem for elem in call_args if elem.context_type == ContextType.YOUTUBE_CONTEXT]
        assert len(youtube_elements) == 1
        assert youtube_elements[0].source_metadata['video_id'] == 'abc123'
    
    @pytest.mark.asyncio
    async def test_build_warren_context_with_vector_search_results(self):
        """Test workflow with vector search results in context_data."""
        
        # Setup mocks
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.CREATION
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000),
            ContextType.VECTOR_SEARCH_RESULTS: BudgetAllocation(ContextType.VECTOR_SEARCH_RESULTS, 20000)
        }
        self.mock_context_gatherer.gather_all_context.return_value = []
        self.mock_context_builder.build_context_string.return_value = "Context with search results"
        self.mock_context_builder.get_context_summary.return_value = {'user_input': 50, 'vector_search_results': 300}
        self.mock_token_manager.count_tokens.side_effect = [50, 100, 100, 100, 400]  # user, result1, result2, result3, final
        
        # Context data with search results
        context_data = {
            'search_results': [
                'First search result about compliance',
                'Second search result about marketing',
                'Third search result about regulations'
            ]
        }
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create compliant content",
            context_data=context_data,
            db_session=Mock(spec=AsyncSession)
        )
        
        # Verify search results were processed
        call_args = self.mock_context_builder.build_context_string.call_args[0][0]
        search_elements = [elem for elem in call_args if elem.context_type == ContextType.VECTOR_SEARCH_RESULTS]
        assert len(search_elements) == 3
        
        # Verify decreasing priority for later results
        priorities = [elem.priority_score for elem in search_elements]
        assert priorities[0] > priorities[1] > priorities[2]
    
    @pytest.mark.asyncio
    async def test_build_warren_context_no_db_session(self):
        """Test graceful handling when no database session provided."""
        
        # Setup mocks
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.CREATION
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000)
        }
        self.mock_context_builder.build_context_string.return_value = "Basic context"
        self.mock_context_builder.get_context_summary.return_value = {'user_input': 50}
        self.mock_token_manager.count_tokens.side_effect = [50, 100]
        
        # Execute without db_session
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content",
            db_session=None  # No session provided
        )
        
        # Should complete successfully but with warning
        assert result["request_type"] == RequestType.CREATION.value
        assert result["context"] == "Basic context"
        
        # Context gatherer should not be called without db_session
        self.mock_context_gatherer.gather_all_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_optimization_applied_flag(self):
        """Test that optimization_applied flag is set correctly."""
        
        # Setup mocks for large context (over TARGET_INPUT_TOKENS)
        self.mock_request_analyzer.analyze_request_type.return_value = RequestType.CREATION
        self.mock_budget_allocator.allocate_budget.return_value = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 2000)
        }
        self.mock_context_gatherer.gather_all_context.return_value = []
        self.mock_context_builder.build_context_string.return_value = "Very large context string" * 1000
        self.mock_context_builder.get_context_summary.return_value = {'user_input': 50}
        
        # Mock large token count (over TARGET_INPUT_TOKENS = 180000)
        self.mock_token_manager.count_tokens.side_effect = [50, 190000]
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content",
            db_session=Mock(spec=AsyncSession)
        )
        
        # Verify optimization flag is set
        assert result["optimization_applied"] is True
        assert result["total_tokens"] == 190000
    
    @pytest.mark.asyncio
    async def test_context_element_optimization(self):
        """Test context element optimization within budget."""
        
        # Create test elements that exceed budget
        test_elements = [
            ContextElement(
                content="High priority content",
                context_type=ContextType.USER_INPUT,
                priority_score=10.0,
                relevance_score=1.0,
                token_count=1000,
                source_metadata={}
            ),
            ContextElement(
                content="Lower priority content",
                context_type=ContextType.USER_INPUT,
                priority_score=5.0,
                relevance_score=0.5,
                token_count=1500,
                source_metadata={}
            )
        ]
        
        # Budget that can only fit first element
        token_budget = {ContextType.USER_INPUT: 1200}
        
        # Execute optimization
        result = await self.orchestrator._optimize_context_elements(
            elements=test_elements,
            token_budget=token_budget,
            request_type=RequestType.CREATION
        )
        
        # Should only include high priority element that fits budget
        assert len(result) == 1
        assert result[0].priority_score == 10.0
        assert result[0].token_count <= 1200
    
    @pytest.mark.asyncio
    async def test_basic_compression(self):
        """Test basic compression of oversized elements."""
        
        # Create element that exceeds budget
        large_element = ContextElement(
            content="This is a very long content that exceeds the token budget" * 100,
            context_type=ContextType.DOCUMENT_SUMMARIES,
            priority_score=8.0,
            relevance_score=0.9,
            token_count=5000,
            source_metadata={}
        )
        
        # Mock token manager for compression
        self.mock_token_manager.count_tokens.return_value = 2000  # Compressed size
        
        # Execute compression
        result = await self.orchestrator._compress_element_basic(large_element, 2500)
        
        # Should return compressed element
        assert result is not None
        assert result.token_count == 2000
        assert result.source_metadata["compressed"] is True
        assert result.compression_level > 0
        assert result.content.endswith("...")
    
    @pytest.mark.asyncio
    async def test_fallback_context_on_error(self):
        """Test fallback context when main workflow fails."""
        
        # Mock request analyzer to raise exception
        self.mock_request_analyzer.analyze_request_type.side_effect = Exception("Test error")
        self.mock_token_manager.count_tokens.return_value = 100
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content",
            context_data={'search_results': ['some context']},
            db_session=Mock(spec=AsyncSession)
        )
        
        # Should return fallback context
        assert "fallback_used" in result
        assert result["fallback_used"] is True
        assert "User Request: Create content" in result["context"]
        assert result["request_type"] == RequestType.CREATION.value
    
    @pytest.mark.asyncio
    async def test_minimal_fallback_on_complete_failure(self):
        """Test minimal fallback when even fallback context fails."""
        
        # Mock everything to fail
        self.mock_request_analyzer.analyze_request_type.side_effect = Exception("Test error")
        self.mock_token_manager.count_tokens.side_effect = Exception("Token counting failed")
        
        # Execute
        result = await self.orchestrator.build_warren_context(
            session_id="test-session",
            user_input="Create content",
            db_session=Mock(spec=AsyncSession)
        )
        
        # Should return absolute minimal fallback
        assert result["fallback_used"] is True
        assert "User Request: Create content" in result["context"]
        assert result["total_tokens"] == 50  # Hardcoded fallback
    
    def test_default_dependency_injection(self):
        """Test that orchestrator creates default dependencies when none provided."""
        
        # Create orchestrator with no dependencies
        orchestrator = BasicContextAssemblyOrchestrator()
        
        # Verify all dependencies are created
        assert orchestrator.budget_allocator is not None
        assert orchestrator.request_analyzer is not None
        assert orchestrator.context_gatherer is not None
        assert orchestrator.context_builder is not None
        assert orchestrator.token_manager is not None
        
        # Verify configuration
        assert orchestrator.MAX_TOTAL_TOKENS == 200000
        assert orchestrator.TARGET_INPUT_TOKENS == 180000
