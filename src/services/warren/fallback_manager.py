"""
Fallback Manager - Centralized error recovery for Warren service.
Replaces scattered fallback logic from enhanced_warren_service.py.
"""

import logging
import asyncio
from typing import Dict, Any
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ErrorClassification(Enum):
    TEMPORARY_FAILURE = "temporary_failure"
    CONFIGURATION_ERROR = "configuration_error"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    SYSTEM_FAILURE = "system_failure"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_TO_ALTERNATIVE = "fallback_to_alternative"
    DEGRADE_GRACEFULLY = "degrade_gracefully"
    EMERGENCY_FALLBACK = "emergency_fallback"
    FAIL_FAST = "fail_fast"


class FallbackContext:
    def __init__(self, operation_type: str, attempt_count: int = 0, **kwargs):
        self.operation_type = operation_type
        self.attempt_count = attempt_count
        self.additional_context = kwargs
        self.start_time = time.time()


class FallbackResult:
    def __init__(self):
        self.success = False
        self.result = None
        self.fallback_used = False
        self.strategy_applied = None
        self.error_message = None
        self.metadata = {}
        self.execution_time = 0.0


class ContentRequest:
    def __init__(self, user_request: str, content_type: str, **kwargs):
        self.user_request = user_request
        self.content_type = content_type
        self.audience_type = kwargs.get('audience_type')
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id')
        self.current_content = kwargs.get('current_content')
        self.is_refinement = kwargs.get('is_refinement', False)
        self.youtube_context = kwargs.get('youtube_context')
        self.use_conversation_context = kwargs.get('use_conversation_context', True)


class ContentResult:
    def __init__(self):
        self.content = None
        self.metadata = {}
        self.success = False
        self.error = None
        self.emergency_fallback = False
        self.original_error = None


class FallbackManager:
    """Coordinates fallback strategies and error recovery for Warren."""
    
    def __init__(self):
        self.max_retry_attempts = 3
        self.retry_backoff_seconds = [1, 2, 4]
        
        self.error_patterns = {
            ErrorClassification.TEMPORARY_FAILURE: [
                "timeout", "rate limit", "503", "502", "504", "temporary", "unavailable", "network", "dns"
            ],
            ErrorClassification.CONFIGURATION_ERROR: [
                "api key", "invalid key", "authentication", "unauthorized", "permission", "access denied", "401", "403"
            ],
            ErrorClassification.DATA_QUALITY_ISSUE: [
                "no relevant content", "no content found", "insufficient context", "poor quality", "no results", "empty response", "invalid format"
            ],
            ErrorClassification.SYSTEM_FAILURE: [
                "database connection", "connection pool", "out of memory", "crash", "internal server error", "500", "service down"
            ]
        }
        
        self.strategy_mapping = {
            ErrorClassification.TEMPORARY_FAILURE: RecoveryStrategy.RETRY_WITH_BACKOFF,
            ErrorClassification.CONFIGURATION_ERROR: RecoveryStrategy.FAIL_FAST,
            ErrorClassification.DATA_QUALITY_ISSUE: RecoveryStrategy.DEGRADE_GRACEFULLY,
            ErrorClassification.SYSTEM_FAILURE: RecoveryStrategy.EMERGENCY_FALLBACK,
            ErrorClassification.UNKNOWN_ERROR: RecoveryStrategy.FALLBACK_TO_ALTERNATIVE
        }
    
    async def execute_fallback(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute appropriate fallback strategy for the given error."""
        start_time = time.time()
        result = FallbackResult()
        
        try:
            error_class = self.classify_error(original_error, context.operation_type)
            recovery_strategy = self.select_recovery_strategy(error_class, context)
            
            strategy_methods = {
                RecoveryStrategy.RETRY_WITH_BACKOFF: self._execute_retry_strategy,
                RecoveryStrategy.FALLBACK_TO_ALTERNATIVE: self._execute_alternative_strategy,
                RecoveryStrategy.DEGRADE_GRACEFULLY: self._execute_graceful_degradation,
                RecoveryStrategy.EMERGENCY_FALLBACK: self._execute_emergency_strategy,
                RecoveryStrategy.FAIL_FAST: self._execute_fail_fast_strategy
            }
            
            method = strategy_methods[recovery_strategy]
            if asyncio.iscoroutinefunction(method):
                result = await method(original_error, context)
            else:
                result = method(original_error, context)
            
            result.strategy_applied = recovery_strategy.value
            result.execution_time = time.time() - start_time
            
            logger.info(f"Fallback {recovery_strategy.value}: {result.success} ({result.execution_time:.2f}s)")
            return result
            
        except Exception as fallback_error:
            logger.error(f"Fallback execution failed: {fallback_error}")
            result.success = False
            result.error_message = f"Fallback failed: {str(fallback_error)}"
            result.execution_time = time.time() - start_time
            return result
    
    def classify_error(self, error: Exception, operation_type: str) -> ErrorClassification:
        """Classify error type for appropriate recovery strategy selection."""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        for classification, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_message or pattern in error_type:
                    return classification
        
        # Operation-specific classification
        if operation_type in ["vector_search", "text_search"] and ("no results" in error_message or "empty" in error_message):
            return ErrorClassification.DATA_QUALITY_ISSUE
        
        if operation_type in ["conversation_context", "session_documents"]:
            return ErrorClassification.DATA_QUALITY_ISSUE
        
        logger.warning(f"Could not classify error: {error_message}")
        return ErrorClassification.UNKNOWN_ERROR
    
    def select_recovery_strategy(self, error_class: ErrorClassification, context: FallbackContext) -> RecoveryStrategy:
        """Select appropriate recovery strategy based on error classification."""
        base_strategy = self.strategy_mapping.get(error_class, RecoveryStrategy.FAIL_FAST)
        
        # Adjust based on context
        if context.attempt_count >= self.max_retry_attempts and base_strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return RecoveryStrategy.FALLBACK_TO_ALTERNATIVE
        
        # Only truly critical operations get emergency fallback for config errors
        if context.operation_type in ["main_workflow"] and base_strategy == RecoveryStrategy.FAIL_FAST:
            return RecoveryStrategy.EMERGENCY_FALLBACK
        
        return base_strategy
    
    async def execute_emergency_fallback(self, request: ContentRequest) -> ContentResult:
        """Execute emergency fallback to original Warren service."""
        result = ContentResult()
        
        try:
            from src.services.warren_database_service import warren_db_service
            
            logger.info("Attempting emergency fallback to original Warren service")
            
            fallback_result = await warren_db_service.generate_content_with_context(
                user_request=request.user_request,
                content_type=request.content_type,
                audience_type=request.audience_type,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            fallback_result["emergency_fallback"] = True
            result.success = True
            result.content = fallback_result.get("content")
            result.metadata = fallback_result
            result.emergency_fallback = True
            
            logger.info("Emergency fallback succeeded")
            return result
            
        except Exception as fallback_error:
            logger.error(f"Emergency fallback failed: {fallback_error}")
            result.success = False
            result.error = f"Emergency fallback failed: {str(fallback_error)}"
            result.metadata = {"status": "error", "error": result.error, "content": None}
            return result
    
    def should_attempt_fallback(self, error: Exception, attempt_count: int) -> bool:
        """Determine if fallback should be attempted for this error."""
        if attempt_count >= self.max_retry_attempts:
            return False
        
        error_class = self.classify_error(error, "unknown")
        
        if error_class == ErrorClassification.CONFIGURATION_ERROR:
            return False
        
        if error_class == ErrorClassification.SYSTEM_FAILURE and attempt_count > 0:
            return False
        
        return True
    
    async def _execute_retry_strategy(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute retry with exponential backoff."""
        result = FallbackResult()
        
        if context.attempt_count >= self.max_retry_attempts:
            result.success = False
            result.error_message = f"Max retry attempts ({self.max_retry_attempts}) exceeded"
            return result
        
        delay = self.retry_backoff_seconds[min(context.attempt_count, len(self.retry_backoff_seconds) - 1)]
        logger.info(f"Retrying {context.operation_type} after {delay}s (attempt {context.attempt_count + 1})")
        await asyncio.sleep(delay)
        
        result.success = True
        result.fallback_used = True
        result.metadata = {
            "retry_attempt": context.attempt_count + 1,
            "backoff_delay": delay,
            "original_error": str(original_error)
        }
        return result
    
    async def _execute_alternative_strategy(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute fallback to alternative method."""
        result = FallbackResult()
        
        alternatives = {
            "vector_search": "text_search",
            "phase2_context_assembly": "phase1_context_assembly",
            "phase1_context_assembly": "legacy_context_assembly",
            "advanced_generation": "legacy_generation"
        }
        
        alternative = alternatives.get(context.operation_type)
        if alternative:
            logger.info(f"Falling back from {context.operation_type} to {alternative}")
            result.success = True
            result.fallback_used = True
            result.metadata = {
                "original_method": context.operation_type,
                "fallback_method": alternative,
                "original_error": str(original_error)
            }
        else:
            result.success = False
            result.error_message = f"No alternative available for {context.operation_type}"
        
        return result
    
    async def _execute_graceful_degradation(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute graceful degradation - continue with reduced functionality."""
        result = FallbackResult()
        
        enhancement_operations = ["session_documents", "conversation_context", "compliance_rules_search"]
        
        if context.operation_type in enhancement_operations:
            logger.info(f"Gracefully degrading: continuing without {context.operation_type}")
            result.success = True
            result.fallback_used = True
            result.result = []
            result.metadata = {
                "degraded_feature": context.operation_type,
                "reason": str(original_error),
                "impact": "reduced_functionality"
            }
        else:
            result.success = False
            result.error_message = f"Cannot gracefully degrade operation: {context.operation_type}"
        
        return result
    
    async def _execute_emergency_strategy(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute emergency fallback strategy."""
        result = FallbackResult()
        
        if context.operation_type in ["content_generation", "main_workflow"]:
            if "request" in context.additional_context:
                request = context.additional_context["request"]
                content_result = await self.execute_emergency_fallback(request)
                
                result.success = content_result.success
                result.result = content_result.metadata
                result.fallback_used = True
                result.metadata = {"emergency_fallback": True, "original_error": str(original_error)}
            else:
                result.success = False
                result.error_message = "Emergency fallback requires request context"
        else:
            result.success = False
            result.error_message = f"No emergency strategy for {context.operation_type}"
        
        return result
    
    def _execute_fail_fast_strategy(self, original_error: Exception, context: FallbackContext) -> FallbackResult:
        """Execute fail fast strategy - don't attempt recovery."""
        result = FallbackResult()
        result.success = False
        result.fallback_used = False
        result.error_message = f"Fail fast: {str(original_error)}"
        result.metadata = {"strategy": "fail_fast", "reason": "configuration_error_or_critical_failure"}
        
        logger.warning(f"Failing fast for {context.operation_type}: {original_error}")
        return result
    
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get statistics about fallback usage (for monitoring)."""
        return {
            "total_fallbacks": 0,
            "success_rate": 0.0,
            "most_common_errors": [],
            "average_recovery_time": 0.0
        }
