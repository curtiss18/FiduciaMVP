"""
Tests for ContentGenerationOrchestrator
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional

from src.services.warren.content_generation_orchestrator import (
    ContentGenerationOrchestrator, ValidationResult
)
from src.services.warren.strategies.content_generation_strategy import GenerationResult
from src.models.refactored_database import ContentType


class TestContentGenerationOrchestrator:
    """Test suite for ContentGenerationOrchestrator."""
    
    @pytest.fixture
    def mock_search_orchestrator(self):
        """Create mock search orchestrator."""
        mock = AsyncMock()
        mock.execute_search_with_fallback.return_value = {
            "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
            "disclaimers": [{"id": "disc1"}],
            "vector_available": True,
            "search_strategy": "vector",
            "vector_results_count": 2,
            "text_results_count": 0,
            "total_sources": 3,
            "fallback_used": False
        }
        return mock
    
    @pytest.fixture
    def mock_conversation_service(self):
        """Create mock conversation context service."""
        mock = AsyncMock()
        mock.get_session_context.return_value = {
            "conversation_context": "Previous conversation history",
            "session_documents": [
                {"title": "Doc1", "summary": "Summary1", "content_type": "pdf", "word_count": 100, "document_id": "doc1"}
            ],
            "session_id": "test-session",
            "conversation_context_available": True,
            "session_documents_available": True,
            "session_documents_count": 1
        }
        mock.save_conversation_turn.return_value = None
        return mock
    
    @pytest.fixture
    def mock_quality_assessor(self):
        """Create mock context quality assessor."""
        mock = Mock()
        mock.assess_context_quality.return_value = {
            "sufficient": True,
            "score": 0.8,
            "reason": "sufficient_quality"
        }
        return mock
    
    @pytest.fixture
    def mock_prompt_service(self):
        """Create mock prompt construction service."""
        mock = AsyncMock()
        mock.build_generation_prompt.return_value = "Generated prompt"
        return mock
    
    @pytest.fixture
    def mock_strategy_factory(self):
        """Create mock strategy factory."""
        mock = Mock()
        
        # Create mock strategy
        mock_strategy = AsyncMock()
        mock_generation_result = GenerationResult()
        mock_generation_result.success = True
        mock_generation_result.content = "Generated marketing content"
        mock_generation_result.strategy_used = "advanced"
        mock_generation_result.generation_time = 2.5
        mock_generation_result.token_usage = {"prompt_tokens": 100, "completion_tokens": 50}
        mock_strategy.generate_content.return_value = mock_generation_result
        mock_strategy.get_strategy_name.return_value = "advanced"
        
        mock.get_strategy.return_value = mock_strategy
        return mock
    
    @pytest.fixture
    def orchestrator(self, mock_search_orchestrator, mock_conversation_service, 
                    mock_quality_assessor, mock_prompt_service, mock_strategy_factory):
        """Create ContentGenerationOrchestrator with mocked dependencies."""
        return ContentGenerationOrchestrator(
            search_orchestrator=mock_search_orchestrator,
            conversation_service=mock_conversation_service,
            quality_assessor=mock_quality_assessor,
            prompt_service=mock_prompt_service,
            strategy_factory=mock_strategy_factory
        )
    
    @pytest.fixture
    def basic_request_params(self):
        """Basic request parameters for testing."""
        return {
            "user_request": "Create a LinkedIn post about retirement planning",
            "content_type": "linkedin_post",
            "audience_type": "retail_investors",
            "user_id": "user123",
            "session_id": "session123",
            "use_conversation_context": True
        }
    
    class TestGenerateContentWithEnhancedContext:
        """Test the main public interface."""
        
        @pytest.mark.asyncio
        async def test_successful_content_generation(self, orchestrator, basic_request_params):
            """Test successful content generation workflow."""
            result = await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            # Verify response format matches enhanced_warren_service
            assert result["status"] == "success"
            assert result["content"] == "Generated marketing content"
            assert result["content_type"] == "linkedin_post"
            assert result["search_strategy"] == "vector"
            assert result["vector_results_found"] == 2
            assert result["text_results_found"] == 0
            assert result["total_knowledge_sources"] == 3
            assert result["marketing_examples_count"] == 2
            assert result["compliance_rules_count"] == 1
            assert result["session_documents_count"] == 1
            assert result["session_documents_used"] == ["Doc1"]
            assert result["fallback_used"] == False
            assert result["context_quality_score"] == 0.8
            assert result["user_request"] == basic_request_params["user_request"]
            assert result["conversation_context_used"] == True
            assert result["session_documents_available"] == True
            assert result["session_id"] == "session123"
        
        @pytest.mark.asyncio
        async def test_empty_user_request_validation(self, orchestrator):
            """Test validation fails for empty user request."""
            result = await orchestrator.generate_content_with_enhanced_context(
                user_request="",
                content_type="linkedin_post"
            )
            
            assert result["status"] == "error"
            assert "User request cannot be empty" in result["error"]
            assert result["content"] is None
        
        @pytest.mark.asyncio
        async def test_empty_content_type_validation(self, orchestrator):
            """Test validation fails for empty content type."""
            result = await orchestrator.generate_content_with_enhanced_context(
                user_request="Create a post",
                content_type=""
            )
            
            assert result["status"] == "error"
            assert "Content type cannot be empty" in result["error"]
            assert result["content"] is None
        
        @pytest.mark.asyncio
        async def test_without_session_context(self, orchestrator, mock_conversation_service):
            """Test content generation without session context."""
            # Configure conversation service to return empty context
            mock_conversation_service.get_session_context.return_value = {
                "conversation_context": "",
                "session_documents": [],
                "session_id": None,
                "conversation_context_available": False,
                "session_documents_available": False,
                "session_documents_count": 0
            }
            
            result = await orchestrator.generate_content_with_enhanced_context(
                user_request="Create a post",
                content_type="linkedin_post",
                use_conversation_context=False
            )
            
            assert result["status"] == "success"
            assert result["conversation_context_used"] == False
            assert result["session_documents_available"] == False
            assert result["session_documents_count"] == 0
        
        @pytest.mark.asyncio
        async def test_refinement_workflow(self, orchestrator, basic_request_params):
            """Test content refinement workflow."""
            result = await orchestrator.generate_content_with_enhanced_context(
                **basic_request_params,
                current_content="Existing content",
                is_refinement=True
            )
            
            assert result["status"] == "success"
            assert result["content"] == "Generated marketing content"
            
            # Verify strategy was called with refinement parameters
            orchestrator.strategy_factory.get_strategy.assert_called()
            strategy = orchestrator.strategy_factory.get_strategy.return_value
            strategy.generate_content.assert_called_once()
            call_args = strategy.generate_content.call_args[1]
            assert call_args["current_content"] == "Existing content"
            assert call_args["is_refinement"] == True
        
        @patch('src.services.warren_database_service.warren_db_service')
        @pytest.mark.asyncio
        async def test_emergency_fallback_on_exception(self, mock_warren_db, orchestrator, 
                                                      mock_search_orchestrator, basic_request_params):
            """Test emergency fallback when orchestrator fails."""
            # Make search orchestrator fail
            mock_search_orchestrator.execute_search_with_fallback.side_effect = Exception("Search failed")
            
            # Configure warren_db_service mock as async
            mock_warren_db.generate_content_with_context = AsyncMock(return_value={
                "status": "success",
                "content": "Fallback content",
                "content_type": "linkedin_post"
            })
            
            result = await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            assert result["status"] == "success"
            assert result["content"] == "Fallback content"
            assert result["emergency_fallback"] == True
            assert "Search failed" in result["original_error"]
            
            # Verify warren_db_service was called
            mock_warren_db.generate_content_with_context.assert_called_once_with(
                user_request=basic_request_params["user_request"],
                content_type=basic_request_params["content_type"],
                audience_type=basic_request_params["audience_type"],
                user_id=basic_request_params["user_id"],
                session_id=basic_request_params["session_id"]
            )
        
        @patch('src.services.warren_database_service.warren_db_service')
        @pytest.mark.asyncio
        async def test_emergency_fallback_also_fails(self, mock_warren_db, orchestrator, 
                                                    mock_search_orchestrator, basic_request_params):
            """Test behavior when both orchestrator and emergency fallback fail."""
            # Make search orchestrator fail
            mock_search_orchestrator.execute_search_with_fallback.side_effect = Exception("Search failed")
            
            # Make warren_db_service also fail
            mock_warren_db.generate_content_with_context = AsyncMock(side_effect=Exception("Fallback failed"))
            
            result = await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            assert result["status"] == "error"
            assert "Enhanced Warren failed" in result["error"]
            assert "Fallback failed" in result["error"]
            assert result["content"] is None
    
    class TestValidateRequest:
        """Test request validation logic."""
        
        def test_valid_request_with_known_content_type(self, orchestrator):
            """Test validation of valid request with known content type."""
            result = orchestrator._validate_request("Create a post", "linkedin_post")
            
            assert result.valid == True
            assert result.error_message is None
            assert result.processed_params["content_type_enum"] == ContentType.LINKEDIN_POST
            assert result.processed_params["user_request"] == "Create a post"
            assert result.processed_params["content_type"] == "linkedin_post"
        
        def test_valid_request_with_unknown_content_type(self, orchestrator):
            """Test validation handles unknown content types gracefully."""
            result = orchestrator._validate_request("Create content", "unknown_type")
            
            assert result.valid == True
            assert result.error_message is None
            assert result.processed_params["content_type_enum"] is None
            assert result.processed_params["content_type"] == "unknown_type"
        
        def test_empty_user_request(self, orchestrator):
            """Test validation fails for empty user request."""
            result = orchestrator._validate_request("", "linkedin_post")
            
            assert result.valid == False
            assert "User request cannot be empty" in result.error_message
        
        def test_whitespace_user_request(self, orchestrator):
            """Test validation fails for whitespace-only user request."""
            result = orchestrator._validate_request("   ", "linkedin_post")
            
            assert result.valid == False
            assert "User request cannot be empty" in result.error_message
        
        def test_empty_content_type(self, orchestrator):
            """Test validation fails for empty content type."""
            result = orchestrator._validate_request("Create content", "")
            
            assert result.valid == False
            assert "Content type cannot be empty" in result.error_message
        
        def test_whitespace_trimming(self, orchestrator):
            """Test that whitespace is properly trimmed."""
            result = orchestrator._validate_request("  Create content  ", "  linkedin_post  ")
            
            assert result.valid == True
            assert result.processed_params["user_request"] == "Create content"
            assert result.processed_params["content_type"] == "linkedin_post"
    
    class TestAssembleResponse:
        """Test response assembly logic."""
        
        def test_complete_response_assembly(self, orchestrator):
            """Test assembly of complete response with all metadata."""
            content = "Generated content"
            metadata = {
                "context_data": {
                    "search_strategy": "hybrid",
                    "vector_results_count": 5,
                    "text_results_count": 3,
                    "total_sources": 8,
                    "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
                    "disclaimers": [{"id": "disc1"}],
                    "fallback_used": True,
                    "fallback_reason": "poor_vector_quality"
                },
                "session_documents": [
                    {"title": "Doc1"}, {"title": "Doc2"}
                ],
                "conversation_context": "Previous conversation",
                "context_quality": {"score": 0.7},
                "user_request": "Create content",
                "content_type": "linkedin_post",
                "session_id": "session123"
            }
            
            result = orchestrator._assemble_response(content, metadata)
            
            assert result["status"] == "success"
            assert result["content"] == "Generated content"
            assert result["content_type"] == "linkedin_post"
            assert result["search_strategy"] == "hybrid"
            assert result["vector_results_found"] == 5
            assert result["text_results_found"] == 3
            assert result["total_knowledge_sources"] == 8
            assert result["marketing_examples_count"] == 2
            assert result["compliance_rules_count"] == 1
            assert result["session_documents_count"] == 2
            assert result["session_documents_used"] == ["Doc1", "Doc2"]
            assert result["fallback_used"] == True
            assert result["fallback_reason"] == "poor_vector_quality"
            assert result["context_quality_score"] == 0.7
            assert result["user_request"] == "Create content"
            assert result["conversation_context_used"] == True
            assert result["session_documents_available"] == True
            assert result["session_id"] == "session123"
        
        def test_minimal_response_assembly(self, orchestrator):
            """Test assembly with minimal metadata."""
            content = "Simple content"
            metadata = {
                "context_data": {},
                "session_documents": [],
                "conversation_context": "",
                "context_quality": {},
                "user_request": "Simple request",
                "content_type": "email",
                "session_id": None
            }
            
            result = orchestrator._assemble_response(content, metadata)
            
            assert result["status"] == "success"
            assert result["content"] == "Simple content"
            assert result["search_strategy"] == "hybrid"  # default
            assert result["vector_results_found"] == 0
            assert result["text_results_found"] == 0
            assert result["total_knowledge_sources"] == 0
            assert result["marketing_examples_count"] == 0
            assert result["compliance_rules_count"] == 0
            assert result["session_documents_count"] == 0
            assert result["session_documents_used"] == []
            assert result["fallback_used"] == False
            assert result["context_quality_score"] == 0.5  # default
            assert result["conversation_context_used"] == False
            assert result["session_documents_available"] == False
            assert result["session_id"] is None
        
        def test_document_title_handling(self, orchestrator):
            """Test handling of session documents without titles."""
            metadata = {
                "context_data": {},
                "session_documents": [
                    {"title": "Doc1"},
                    {},  # No title
                    {"title": "Doc3"}
                ],
                "conversation_context": "",
                "context_quality": {}
            }
            
            result = orchestrator._assemble_response("content", metadata)
            
            assert result["session_documents_used"] == ["Doc1", "Unknown", "Doc3"]
    
    class TestSelectGenerationStrategy:
        """Test strategy selection logic."""
        
        def test_advanced_strategy_selection(self, orchestrator):
            """Test selection of advanced strategy for high-quality context."""
            context_data = {
                "vector_available": True,
                "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
                "disclaimers": [{"id": "disc1"}]
            }
            context_quality = {"score": 0.8}
            
            strategy = orchestrator._select_generation_strategy(context_data, context_quality)
            
            orchestrator.strategy_factory.get_strategy.assert_called_with("advanced")
        
        def test_standard_strategy_selection_moderate_quality(self, orchestrator):
            """Test selection of standard strategy for moderate quality context."""
            context_data = {
                "vector_available": True,
                "marketing_examples": [{"id": "ex1"}],
                "disclaimers": []
            }
            context_quality = {"score": 0.5}
            
            strategy = orchestrator._select_generation_strategy(context_data, context_quality)
            
            orchestrator.strategy_factory.get_strategy.assert_called_with("standard")
        
        def test_legacy_strategy_selection_poor_quality(self, orchestrator):
            """Test selection of legacy strategy for poor quality context."""
            context_data = {
                "vector_available": True,
                "marketing_examples": [],
                "disclaimers": []
            }
            context_quality = {"score": 0.2}
            
            strategy = orchestrator._select_generation_strategy(context_data, context_quality)
            
            orchestrator.strategy_factory.get_strategy.assert_called_with("legacy")
        
        def test_legacy_strategy_selection_vector_unavailable(self, orchestrator):
            """Test selection of legacy strategy when vector search unavailable."""
            context_data = {
                "vector_available": False,
                "marketing_examples": [{"id": "ex1"}],
                "disclaimers": [{"id": "disc1"}]
            }
            context_quality = {"score": 0.8}
            
            strategy = orchestrator._select_generation_strategy(context_data, context_quality)
            
            orchestrator.strategy_factory.get_strategy.assert_called_with("legacy")
        
        def test_standard_strategy_selection_no_disclaimers(self, orchestrator):
            """Test standard strategy when no disclaimers but good marketing examples."""
            context_data = {
                "vector_available": True,
                "marketing_examples": [{"id": "ex1"}, {"id": "ex2"}],
                "disclaimers": []
            }
            context_quality = {"score": 0.6}
            
            strategy = orchestrator._select_generation_strategy(context_data, context_quality)
            
            orchestrator.strategy_factory.get_strategy.assert_called_with("standard")
    
    class TestTryFallbackGeneration:
        """Test fallback generation logic."""
        
        @pytest.mark.asyncio
        async def test_successful_standard_fallback(self, orchestrator, mock_strategy_factory):
            """Test successful fallback to standard strategy."""
            # Configure successful standard strategy
            standard_strategy = AsyncMock()
            standard_result = GenerationResult()
            standard_result.success = True
            standard_result.content = "Fallback content"
            standard_result.strategy_used = "standard"
            standard_strategy.generate_content.return_value = standard_result
            
            mock_strategy_factory.get_strategy.return_value = standard_strategy
            
            request_params = {
                "context_data": {"test": "data"},
                "user_request": "Create content",
                "content_type": "linkedin_post",
                "audience_type": "retail_investors",
                "current_content": None,
                "is_refinement": False,
                "youtube_context": None
            }
            
            result = await orchestrator._try_fallback_generation(request_params, "Original error")
            
            assert result["content"] == "Fallback content"
            assert result["metadata"]["strategy_used"] == "standard"
            assert result["metadata"]["fallback_used"] == True
            assert result["metadata"]["original_error"] == "Original error"
        
        @pytest.mark.asyncio
        async def test_all_fallback_strategies_fail(self, orchestrator, mock_strategy_factory):
            """Test behavior when all fallback strategies fail."""
            # Configure failing strategies
            failing_strategy = AsyncMock()
            failing_result = GenerationResult()
            failing_result.success = False
            failing_result.error_message = "Strategy failed"
            failing_strategy.generate_content.return_value = failing_result
            
            mock_strategy_factory.get_strategy.return_value = failing_strategy
            
            request_params = {
                "context_data": {"test": "data"},
                "user_request": "Create content",
                "content_type": "linkedin_post",
                "audience_type": "retail_investors",
                "current_content": None,
                "is_refinement": False,
                "youtube_context": None
            }
            
            with pytest.raises(Exception) as exc_info:
                await orchestrator._try_fallback_generation(request_params, "Original error")
            
            assert "All generation strategies failed" in str(exc_info.value)
            assert "Original error" in str(exc_info.value)
    
    class TestEmergencyFallback:
        """Test emergency fallback behavior."""
        
        @patch('src.services.warren_database_service.warren_db_service')
        @pytest.mark.asyncio
        async def test_successful_emergency_fallback(self, mock_warren_db, orchestrator):
            """Test successful emergency fallback to warren_db_service."""
            mock_warren_db.generate_content_with_context = AsyncMock(return_value={
                "status": "success",
                "content": "Emergency content",
                "content_type": "linkedin_post"
            })
            
            result = await orchestrator._execute_emergency_fallback(
                "Create content", "linkedin_post", "retail_investors", 
                "user123", "session123", Exception("Original error")
            )
            
            assert result["status"] == "success"
            assert result["content"] == "Emergency content"
            assert result["emergency_fallback"] == True
            assert result["original_error"] == "Original error"
            
            mock_warren_db.generate_content_with_context.assert_called_once_with(
                user_request="Create content",
                content_type="linkedin_post",
                audience_type="retail_investors",
                user_id="user123",
                session_id="session123"
            )
        
        @patch('src.services.warren_database_service.warren_db_service')
        @pytest.mark.asyncio
        async def test_emergency_fallback_failure(self, mock_warren_db, orchestrator):
            """Test behavior when emergency fallback also fails."""
            mock_warren_db.generate_content_with_context = AsyncMock(side_effect=Exception("Fallback error"))
            
            result = await orchestrator._execute_emergency_fallback(
                "Create content", "linkedin_post", None, None, None, 
                Exception("Original error")
            )
            
            assert result["status"] == "error"
            assert "Enhanced Warren failed: Original error" in result["error"]
            assert "Fallback failed: Fallback error" in result["error"]
            assert result["content"] is None
    
    class TestServiceCoordination:
        """Test coordination between services."""
        
        @pytest.mark.asyncio
        async def test_conversation_turn_saving(self, orchestrator, mock_conversation_service, basic_request_params):
            """Test that conversation turns are saved when session_id provided."""
            await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            mock_conversation_service.save_conversation_turn.assert_called_once()
            call_args = mock_conversation_service.save_conversation_turn.call_args[0]
            assert call_args[0] == "session123"  # session_id
            assert call_args[1] == basic_request_params["user_request"]  # user_input
            assert call_args[2] == "Generated marketing content"  # warren_response
        
        @pytest.mark.asyncio
        async def test_no_conversation_saving_without_session(self, orchestrator, mock_conversation_service):
            """Test that conversation turns are not saved without session_id."""
            await orchestrator.generate_content_with_enhanced_context(
                user_request="Create content",
                content_type="linkedin_post",
                session_id=None
            )
            
            mock_conversation_service.save_conversation_turn.assert_not_called()
        
        @pytest.mark.asyncio
        async def test_search_orchestrator_coordination(self, orchestrator, mock_search_orchestrator, basic_request_params):
            """Test coordination with search orchestrator."""
            await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            mock_search_orchestrator.execute_search_with_fallback.assert_called_once_with(
                basic_request_params["user_request"],
                basic_request_params["content_type"],
                ContentType.LINKEDIN_POST,  # Converted enum
                basic_request_params["audience_type"]
            )
        
        @pytest.mark.asyncio
        async def test_quality_assessment_coordination(self, orchestrator, mock_quality_assessor, basic_request_params):
            """Test coordination with context quality assessor."""
            await orchestrator.generate_content_with_enhanced_context(**basic_request_params)
            
            mock_quality_assessor.assess_context_quality.assert_called_once()
            call_args = mock_quality_assessor.assess_context_quality.call_args[0][0]
            assert "marketing_examples" in call_args
            assert "disclaimers" in call_args
            assert "conversation_context" in call_args
            assert "session_documents" in call_args
