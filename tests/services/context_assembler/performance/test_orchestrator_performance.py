"""Performance and Load Testing for BasicContextAssemblyOrchestrator."""

import pytest
import asyncio
import time
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.orchestrator import BasicContextAssemblyOrchestrator
from src.services.context_assembly_service.models import RequestType, ContextType


class TestBasicContextAssemblyOrchestratorPerformance:
    """Performance and load testing for the orchestrator."""
    
    def setup_method(self):
        # Create orchestrator for performance testing
        self.orchestrator = BasicContextAssemblyOrchestrator()
        
        # Standard test data for consistent load testing
        self.test_requests = [
            {
                "session_id": f"load-test-session-{i}",
                "user_input": f"Create LinkedIn post about investment strategy {i}",
                "context_data": {"search_results": [f"Investment advice {i}", f"Market analysis {i}"]},
                "current_content": None if i % 2 == 0 else f"Previous content draft {i}",
                "youtube_context": {"transcript": f"Investment video transcript {i}", "video_id": f"vid_{i}"},
                "db_session": AsyncMock(spec=AsyncSession)
            }
            for i in range(50)  # 50 different test scenarios
        ]
    
    @pytest.mark.asyncio
    async def test_single_request_performance(self):
        """Test baseline performance for single request."""
        
        # Measure memory before
        gc.collect()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Time single request
        start_time = time.time()
        
        result = await self.orchestrator.build_warren_context(
            session_id="performance-test-session",
            user_input="Create a comprehensive LinkedIn post about retirement planning strategies",
            context_data={"search_results": ["401k advice", "IRA guidelines", "Social Security optimization"]},
            youtube_context={"transcript": "Retirement planning video content", "video_id": "retirement123"},
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        end_time = time.time()
        
        # Measure memory after
        gc.collect()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Performance assertions
        execution_time = end_time - start_time
        memory_used = memory_after - memory_before
        
        print(f"Single request execution time: {execution_time:.3f} seconds")
        print(f"Memory usage: {memory_used:.2f} MB")
        
        # Performance requirements
        assert execution_time < 5.0, f"Single request took {execution_time:.3f}s, should be < 5.0s"
        assert memory_used < 50.0, f"Memory usage {memory_used:.2f}MB, should be < 50MB per request"
        
        # Verify successful result
        assert result["context"]
        assert result["total_tokens"] > 0
        assert result["request_type"] in [rt.value for rt in RequestType]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_load(self):
        """Test performance with concurrent requests."""
        
        # Measure baseline memory
        gc.collect()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test with 10 concurrent requests
        concurrent_requests = 10
        
        async def execute_request(request_data):
            """Execute a single request and return timing info."""
            start = time.time()
            result = await self.orchestrator.build_warren_context(**request_data)
            end = time.time()
            return {
                "execution_time": end - start,
                "tokens": result["total_tokens"],
                "success": bool(result["context"])
            }
        
        # Execute concurrent requests
        start_time = time.time()
        
        tasks = [
            execute_request(self.test_requests[i % len(self.test_requests)]) 
            for i in range(concurrent_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Measure memory after
        gc.collect()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        # Analyze results
        execution_times = [r["execution_time"] for r in results]
        successful_requests = sum(1 for r in results if r["success"])
        
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Total execution time: {total_time:.3f} seconds")
        print(f"Average request time: {avg_time:.3f} seconds")
        print(f"Max request time: {max_time:.3f} seconds")
        print(f"Successful requests: {successful_requests}/{concurrent_requests}")
        print(f"Memory usage: {memory_used:.2f} MB")
        
        # Performance assertions
        assert successful_requests == concurrent_requests, "All requests should succeed"
        assert avg_time < 10.0, f"Average time {avg_time:.3f}s should be < 10s under load"
        assert max_time < 15.0, f"Max time {max_time:.3f}s should be < 15s under load"
        assert memory_used < 200.0, f"Memory usage {memory_used:.2f}MB should be < 200MB for {concurrent_requests} requests"
        
        # No significant performance degradation under load
        assert total_time < concurrent_requests * 2.0, "Concurrent execution should be faster than sequential"
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_after_requests(self):
        """Test that memory is properly cleaned up after processing multiple requests."""
        
        # Get baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple requests in sequence
        num_requests = 20
        
        for i in range(num_requests):
            await self.orchestrator.build_warren_context(
                session_id=f"memory-test-{i}",
                user_input=f"Create content about financial topic {i}",
                context_data={"search_results": [f"Content {i}" * 100]},  # Larger content
                db_session=AsyncMock(spec=AsyncSession)
            )
            
            # Force garbage collection every 5 requests
            if i % 5 == 0:
                gc.collect()
        
        # Final cleanup and memory check
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - baseline_memory
        
        print(f"Baseline memory: {baseline_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        print(f"Memory per request: {memory_growth / num_requests:.2f} MB")
        
        # Memory cleanup assertions
        assert memory_growth < 100.0, f"Memory growth {memory_growth:.2f}MB should be < 100MB for {num_requests} requests"
        assert memory_growth / num_requests < 5.0, f"Memory per request should be < 5MB, got {memory_growth / num_requests:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_large_context_performance(self):
        """Test performance with large context data."""
        
        # Create large test data
        large_search_results = [f"Large compliance document {i} " + "content " * 1000 for i in range(10)]
        large_youtube_transcript = "Large video transcript " + "financial advice content " * 2000
        
        # Measure performance with large context
        start_time = time.time()
        
        result = await self.orchestrator.build_warren_context(
            session_id="large-context-test",
            user_input="Create comprehensive financial planning guide",
            context_data={"search_results": large_search_results},
            youtube_context={"transcript": large_youtube_transcript, "video_id": "large_vid"},
            db_session=AsyncMock(spec=AsyncSession)
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Large context execution time: {execution_time:.3f} seconds")
        print(f"Result tokens: {result['total_tokens']}")
        print(f"Optimization applied: {result['optimization_applied']}")
        
        # Large context performance requirements
        assert execution_time < 15.0, f"Large context processing took {execution_time:.3f}s, should be < 15s"
        assert result["total_tokens"] > 0, "Should generate context even with large input"
        assert result["context"], "Should produce valid context"
        
        # Verify optimization was likely applied for large context
        # (This depends on the actual content size and token limits)
        if result["total_tokens"] > 180000:  # TARGET_INPUT_TOKENS
            assert result["optimization_applied"], "Optimization should be applied for large contexts"
    
    @pytest.mark.asyncio
    async def test_request_type_distribution_performance(self):
        """Test performance across different request types."""
        
        request_scenarios = [
            # Creation requests
            {"user_input": "Create LinkedIn post", "current_content": None},
            {"user_input": "Write newsletter content", "current_content": None},
            {"user_input": "Generate investment advice", "current_content": None},
            
            # Refinement requests  
            {"user_input": "Edit this content", "current_content": "Previous draft content"},
            {"user_input": "Improve this post", "current_content": "Existing social media post"},
            {"user_input": "Revise this article", "current_content": "Article draft content"},
            
            # Analysis requests
            {"user_input": "Analyze this document", "current_content": None},
            {"user_input": "Review this content", "current_content": None},
            {"user_input": "What do you think about this approach", "current_content": None},
            
            # Conversation requests
            {"user_input": "Hello", "current_content": None},
            {"user_input": "Can you help me?", "current_content": None},
            {"user_input": "Thanks", "current_content": None},
        ]
        
        performance_by_type = {}
        
        for scenario in request_scenarios:
            start_time = time.time()
            
            result = await self.orchestrator.build_warren_context(
                session_id="type-test-session",
                user_input=scenario["user_input"],
                current_content=scenario["current_content"],
                context_data={"search_results": ["Test compliance content"]},
                db_session=AsyncMock(spec=AsyncSession)
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            request_type = result["request_type"]
            if request_type not in performance_by_type:
                performance_by_type[request_type] = []
            performance_by_type[request_type].append(execution_time)
        
        # Analyze performance by request type
        for request_type, times in performance_by_type.items():
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            print(f"{request_type}: avg={avg_time:.3f}s, max={max_time:.3f}s, samples={len(times)}")
            
            # All request types should perform reasonably
            assert avg_time < 8.0, f"{request_type} average time {avg_time:.3f}s should be < 8s"
            assert max_time < 12.0, f"{request_type} max time {max_time:.3f}s should be < 12s"
    
    @pytest.mark.asyncio
    async def test_error_handling_performance(self):
        """Test that error handling doesn't cause performance issues."""
        
        # Test with various error scenarios
        error_scenarios = [
            {"session_id": None, "user_input": "test"},  # Invalid session
            {"session_id": "test", "user_input": ""},    # Empty input
            {"session_id": "test", "user_input": "test", "context_data": {"invalid": "data"}},  # Invalid context
        ]
        
        for scenario in error_scenarios:
            start_time = time.time()
            
            # These should not crash but may return fallback results
            result = await self.orchestrator.build_warren_context(
                db_session=AsyncMock(spec=AsyncSession),
                **scenario
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"Error scenario execution time: {execution_time:.3f}s")
            
            # Error handling should be fast
            assert execution_time < 5.0, f"Error handling took {execution_time:.3f}s, should be < 5s"
            
            # Should still return a result (possibly fallback)
            assert isinstance(result, dict), "Should return dict even on errors"
            assert "context" in result, "Should have context key even on errors"


class TestMemoryProfiling:
    """Detailed memory profiling tests."""
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        
        orchestrator = BasicContextAssemblyOrchestrator()
        
        # Collect baseline
        gc.collect()
        process = psutil.Process()
        
        memory_samples = []
        iterations = 30
        
        for i in range(iterations):
            # Execute request
            await orchestrator.build_warren_context(
                session_id=f"leak-test-{i}",
                user_input=f"Memory test request {i}",
                context_data={"search_results": [f"Test content {i}"]},
                db_session=AsyncMock(spec=AsyncSession)
            )
            
            # Sample memory every 5 iterations
            if i % 5 == 0:
                gc.collect()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
                print(f"Iteration {i}: {memory_mb:.2f} MB")
        
        # Analyze memory trend
        if len(memory_samples) > 2:
            # Check if memory is consistently growing
            memory_growth = memory_samples[-1] - memory_samples[0]
            growth_per_iteration = memory_growth / iterations
            
            print(f"Total memory growth: {memory_growth:.2f} MB over {iterations} iterations")
            print(f"Growth per iteration: {growth_per_iteration:.4f} MB")
            
            # Memory should not grow significantly
            assert growth_per_iteration < 0.5, f"Memory leak detected: {growth_per_iteration:.4f} MB per iteration"
            assert memory_growth < 20.0, f"Total memory growth {memory_growth:.2f} MB is too high"
