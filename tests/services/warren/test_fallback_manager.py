"""
Tests for FallbackManager

Comprehensive test coverage for error classification, recovery strategy selection,
fallback execution, and emergency scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.services.warren.fallback_manager import (
    FallbackManager,
    ErrorClassification,
    RecoveryStrategy,
    FallbackContext,
    FallbackResult,
    ContentRequest,
    ContentResult
)


class TestFallbackManager:
    """Test suite for FallbackManager."""
    
    @pytest.fixture
    def manager(self):
        return FallbackManager()
    
    @pytest.fixture
    def temp_failure_error(self):
        return Exception("Connection timeout occurred")
    
    @pytest.fixture
    def config_error(self):
        return Exception("Invalid API key provided")
    
    @pytest.fixture
    def data_quality_error(self):
        return Exception("No relevant content found")
    
    @pytest.fixture
    def system_failure_error(self):
        return Exception("Database connection failed")
    
    @pytest.fixture
    def unknown_error(self):
        return Exception("Something unexpected happened")
    
    @pytest.fixture
    def content_request(self):
        return ContentRequest(
            user_request="Create LinkedIn post about retirement planning",
            content_type="linkedin_post",
            audience_type="retail_investors",
            session_id="test-session-123"
        )
    
    @pytest.fixture
    def fallback_context(self):
        return FallbackContext("content_generation", attempt_count=0)
    
    # Error classification tests
    def test_classify_temporary_failure(self, manager, temp_failure_error):
        result = manager.classify_error(temp_failure_error, "vector_search")
        assert result == ErrorClassification.TEMPORARY_FAILURE
    
    def test_classify_configuration_error(self, manager, config_error):
        result = manager.classify_error(config_error, "content_generation")
        assert result == ErrorClassification.CONFIGURATION_ERROR
    
    def test_classify_data_quality_issue(self, manager, data_quality_error):
        result = manager.classify_error(data_quality_error, "vector_search")
        assert result == ErrorClassification.DATA_QUALITY_ISSUE
    
    def test_classify_system_failure(self, manager, system_failure_error):
        result = manager.classify_error(system_failure_error, "content_generation")
        assert result == ErrorClassification.SYSTEM_FAILURE
    
    def test_classify_unknown_error(self, manager, unknown_error):
        result = manager.classify_error(unknown_error, "content_generation")
        assert result == ErrorClassification.UNKNOWN_ERROR
    
    def test_classify_context_specific_errors(self, manager):
        # Vector search with no results
        no_results_error = Exception("no results found")
        result = manager.classify_error(no_results_error, "vector_search")
        assert result == ErrorClassification.DATA_QUALITY_ISSUE
        
        # Session context errors
        session_error = Exception("session not found")
        result = manager.classify_error(session_error, "conversation_context")
        assert result == ErrorClassification.DATA_QUALITY_ISSUE
    
    def test_classify_error_patterns(self, manager):
        test_cases = [
            ("Rate limit exceeded", ErrorClassification.TEMPORARY_FAILURE),
            ("503 Service Unavailable", ErrorClassification.TEMPORARY_FAILURE),
            ("401 Unauthorized", ErrorClassification.CONFIGURATION_ERROR),
            ("Access denied", ErrorClassification.CONFIGURATION_ERROR),
            ("Database connection pool exhausted", ErrorClassification.SYSTEM_FAILURE),
            ("Internal server error", ErrorClassification.SYSTEM_FAILURE),
            ("Empty response received", ErrorClassification.DATA_QUALITY_ISSUE),
        ]
        
        for error_msg, expected_classification in test_cases:
            error = Exception(error_msg)
            result = manager.classify_error(error, "test_operation")
            assert result == expected_classification, f"Failed for: {error_msg}"
    
    # Recovery strategy selection tests
    def test_select_retry_strategy(self, manager, fallback_context):
        strategy = manager.select_recovery_strategy(ErrorClassification.TEMPORARY_FAILURE, fallback_context)
        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
    
    def test_select_fail_fast_strategy(self, manager):
        context = FallbackContext("non_critical_operation", attempt_count=0)
        strategy = manager.select_recovery_strategy(ErrorClassification.CONFIGURATION_ERROR, context)
        assert strategy == RecoveryStrategy.FAIL_FAST
    
    def test_select_graceful_degradation(self, manager, fallback_context):
        strategy = manager.select_recovery_strategy(ErrorClassification.DATA_QUALITY_ISSUE, fallback_context)
        assert strategy == RecoveryStrategy.DEGRADE_GRACEFULLY
    
    def test_select_emergency_fallback(self, manager, fallback_context):
        strategy = manager.select_recovery_strategy(ErrorClassification.SYSTEM_FAILURE, fallback_context)
        assert strategy == RecoveryStrategy.EMERGENCY_FALLBACK
    
    def test_strategy_adjustment_for_max_retries(self, manager):
        context = FallbackContext("test_operation", attempt_count=3)
        strategy = manager.select_recovery_strategy(ErrorClassification.TEMPORARY_FAILURE, context)
        assert strategy == RecoveryStrategy.FALLBACK_TO_ALTERNATIVE
    
    def test_strategy_adjustment_for_critical_operations(self, manager):
        context = FallbackContext("main_workflow", attempt_count=0)
        strategy = manager.select_recovery_strategy(ErrorClassification.CONFIGURATION_ERROR, context)
        assert strategy == RecoveryStrategy.EMERGENCY_FALLBACK
    
    # Fallback attempt decision tests
    def test_should_attempt_under_max_retries(self, manager, temp_failure_error):
        result = manager.should_attempt_fallback(temp_failure_error, 1)
        assert result is True
    
    def test_should_not_attempt_over_max_retries(self, manager, temp_failure_error):
        result = manager.should_attempt_fallback(temp_failure_error, 5)
        assert result is False
    
    def test_should_not_retry_config_errors(self, manager, config_error):
        result = manager.should_attempt_fallback(config_error, 0)
        assert result is False
    
    def test_should_not_retry_system_failures_multiple_times(self, manager):
        system_error = Exception("Database connection pool exhausted")
        
        # First attempt allowed
        result = manager.should_attempt_fallback(system_error, 0)
        assert result is True
        
        # Second attempt not allowed
        result = manager.should_attempt_fallback(system_error, 1)
        assert result is False
    
    # Fallback execution tests
    @pytest.mark.asyncio
    async def test_execute_fallback_success(self, manager, temp_failure_error, fallback_context):
        result = await manager.execute_fallback(temp_failure_error, fallback_context)
        
        assert isinstance(result, FallbackResult)
        assert result.strategy_applied == RecoveryStrategy.RETRY_WITH_BACKOFF.value
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_execute_retry_strategy(self, manager, temp_failure_error):
        context = FallbackContext("test_operation", attempt_count=1)
        result = await manager._execute_retry_strategy(temp_failure_error, context)
        
        assert result.success is True
        assert result.fallback_used is True
        assert result.metadata["retry_attempt"] == 2
        assert result.metadata["backoff_delay"] in manager.retry_backoff_seconds
    
    @pytest.mark.asyncio
    async def test_execute_retry_strategy_max_attempts(self, manager, temp_failure_error):
        context = FallbackContext("test_operation", attempt_count=5)
        result = await manager._execute_retry_strategy(temp_failure_error, context)
        
        assert result.success is False
        assert "Max retry attempts" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_alternative_strategy(self, manager, temp_failure_error):
        context = FallbackContext("vector_search", attempt_count=0)
        result = await manager._execute_alternative_strategy(temp_failure_error, context)
        
        assert result.success is True
        assert result.fallback_used is True
        assert result.metadata["original_method"] == "vector_search"
        assert result.metadata["fallback_method"] == "text_search"
    
    @pytest.mark.asyncio
    async def test_execute_alternative_strategy_no_alternative(self, manager, temp_failure_error):
        context = FallbackContext("unknown_operation", attempt_count=0)
        result = await manager._execute_alternative_strategy(temp_failure_error, context)
        
        assert result.success is False
        assert "No alternative available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_execute_graceful_degradation_success(self, manager, data_quality_error):
        context = FallbackContext("session_documents", attempt_count=0)
        result = await manager._execute_graceful_degradation(data_quality_error, context)
        
        assert result.success is True
        assert result.fallback_used is True
        assert result.result == []
        assert result.metadata["degraded_feature"] == "session_documents"
    
    @pytest.mark.asyncio
    async def test_execute_graceful_degradation_failure(self, manager, data_quality_error):
        context = FallbackContext("critical_operation", attempt_count=0)
        result = await manager._execute_graceful_degradation(data_quality_error, context)
        
        assert result.success is False
        assert "Cannot gracefully degrade" in result.error_message
    
    def test_execute_fail_fast_strategy(self, manager, config_error):
        context = FallbackContext("test_operation", attempt_count=0)
        result = manager._execute_fail_fast_strategy(config_error, context)
        
        assert result.success is False
        assert result.fallback_used is False
        assert str(config_error) in result.error_message
        assert result.metadata["strategy"] == "fail_fast"
    
    # Emergency fallback tests
    @pytest.mark.asyncio
    async def test_execute_emergency_fallback_success(self, manager, content_request):
        mock_response = {"status": "success", "content": "Emergency content", "search_strategy": "text"}
        
        with patch('src.services.warren_database_service.warren_db_service') as mock_service:
            mock_service.generate_content_with_context = AsyncMock(return_value=mock_response)
            
            result = await manager.execute_emergency_fallback(content_request)
            
            assert result.success is True
            assert result.emergency_fallback is True
            assert result.content == "Emergency content"
            assert result.metadata["emergency_fallback"] is True
            
            mock_service.generate_content_with_context.assert_called_once_with(
                user_request=content_request.user_request,
                content_type=content_request.content_type,
                audience_type=content_request.audience_type,
                user_id=content_request.user_id,
                session_id=content_request.session_id
            )
    
    @pytest.mark.asyncio
    async def test_execute_emergency_fallback_failure(self, manager, content_request):
        with patch('src.services.warren_database_service.warren_db_service') as mock_service:
            mock_service.generate_content_with_context = AsyncMock(side_effect=Exception("Service failed"))
            
            result = await manager.execute_emergency_fallback(content_request)
            
            assert result.success is False
            assert "Emergency fallback failed" in result.error
            assert result.metadata["status"] == "error"
            assert result.metadata["content"] is None
    
    @pytest.mark.asyncio
    async def test_execute_emergency_strategy_with_request(self, manager, content_request):
        context = FallbackContext("content_generation", attempt_count=0, request=content_request)
        mock_response = {"status": "success", "content": "Emergency content"}
        
        with patch('src.services.warren_database_service.warren_db_service') as mock_service:
            mock_service.generate_content_with_context = AsyncMock(return_value=mock_response)
            
            result = await manager._execute_emergency_strategy(Exception("System failure"), context)
            
            assert result.success is True
            assert result.fallback_used is True
            assert result.metadata["emergency_fallback"] is True
    
    @pytest.mark.asyncio
    async def test_execute_emergency_strategy_without_request(self, manager):
        context = FallbackContext("content_generation", attempt_count=0)
        result = await manager._execute_emergency_strategy(Exception("System failure"), context)
        
        assert result.success is False
        assert "Emergency fallback requires request context" in result.error_message
    
    # Integration scenario tests
    @pytest.mark.asyncio
    async def test_complete_fallback_chain_vector_to_text(self, manager):
        vector_error = Exception("Vector search timeout")
        context = FallbackContext("vector_search", attempt_count=0)
        
        result = await manager.execute_fallback(vector_error, context)
        
        assert result.strategy_applied == RecoveryStrategy.RETRY_WITH_BACKOFF.value
        assert result.success is True
        assert result.fallback_used is True
    
    @pytest.mark.asyncio
    async def test_complete_fallback_chain_context_assembly(self, manager):
        assembly_error = Exception("Phase 2 context assembly failed")
        context = FallbackContext("phase2_context_assembly", attempt_count=0)
        
        result = await manager.execute_fallback(assembly_error, context)
        
        assert result.strategy_applied == RecoveryStrategy.FALLBACK_TO_ALTERNATIVE.value
        assert result.success is True
        assert result.metadata["fallback_method"] == "phase1_context_assembly"
    
    @pytest.mark.asyncio
    async def test_complete_fallback_emergency_scenario(self, manager, content_request):
        system_error = Exception("Database connection pool exhausted")
        context = FallbackContext("content_generation", attempt_count=0, request=content_request)
        mock_response = {"status": "success", "content": "Emergency content"}
        
        with patch('src.services.warren_database_service.warren_db_service') as mock_service:
            mock_service.generate_content_with_context = AsyncMock(return_value=mock_response)
            
            result = await manager.execute_fallback(system_error, context)
            
            assert result.strategy_applied == RecoveryStrategy.EMERGENCY_FALLBACK.value
            assert result.success is True
            assert result.metadata["emergency_fallback"] is True
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_scenario(self, manager):
        enhancement_error = Exception("Session documents not found")
        context = FallbackContext("session_documents", attempt_count=0)
        
        result = await manager.execute_fallback(enhancement_error, context)
        
        assert result.strategy_applied == RecoveryStrategy.DEGRADE_GRACEFULLY.value
        assert result.success is True
        assert result.result == []
    
    # Error handling tests
    @pytest.mark.asyncio
    async def test_fallback_execution_internal_error(self, manager):
        error = Exception("Test error")
        context = FallbackContext("test_operation", attempt_count=0)
        
        with patch.object(manager, 'select_recovery_strategy', side_effect=Exception("Internal error")):
            result = await manager.execute_fallback(error, context)
            
            assert result.success is False
            assert "Fallback failed" in result.error_message
            assert result.execution_time > 0
    
    def test_get_fallback_statistics(self, manager):
        stats = manager.get_fallback_statistics()
        
        assert "total_fallbacks" in stats
        assert "success_rate" in stats
        assert "most_common_errors" in stats
        assert "average_recovery_time" in stats
