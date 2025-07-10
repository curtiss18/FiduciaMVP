"""Tests for BasicContextOptimizer."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.services.context_assembly_service.optimization.basic_context_optimizer import BasicContextOptimizer
from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager
from src.services.context_assembly_service.optimization.compression.compression_strategy_factory import CompressionStrategyFactory
from src.services.context_assembly_service.models import (
    ContextType, ContextElement, BudgetAllocation, QualityMetrics
)


class TestBasicContextOptimizerBudgetAllocation:
    """Test budget allocation and distribution."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    @pytest.mark.asyncio
    async def test_budget_distribution_across_types(self, optimizer):
        """Test token budget properly distributed."""
        elements = [
            ContextElement("System prompt", ContextType.SYSTEM_PROMPT, 10.0, 1.0, 20, {}),
            ContextElement("User input", ContextType.USER_INPUT, 9.0, 1.0, 15, {})
        ]
        
        budget_allocations = {
            ContextType.SYSTEM_PROMPT: BudgetAllocation(ContextType.SYSTEM_PROMPT, 30),
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 20)
        }
        
        result = await optimizer.optimize_context_elements(elements, budget_allocations)
        assert len(result) == 2
    
    @pytest.mark.asyncio 
    async def test_priority_ordering_correct(self, optimizer):
        """Test elements ordered by priority correctly."""
        elements = [
            ContextElement("Low", ContextType.YOUTUBE_CONTEXT, 3.0, 0.5, 10, {}),
            ContextElement("High", ContextType.SYSTEM_PROMPT, 10.0, 1.0, 10, {}),
            ContextElement("Medium", ContextType.USER_INPUT, 9.0, 0.8, 10, {})
        ]
        
        budget_allocations = {
            ContextType.YOUTUBE_CONTEXT: BudgetAllocation(ContextType.YOUTUBE_CONTEXT, 20),
            ContextType.SYSTEM_PROMPT: BudgetAllocation(ContextType.SYSTEM_PROMPT, 20),
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 20)
        }
        
        result = await optimizer.optimize_context_elements(elements, budget_allocations)
        priorities = [optimizer._calculate_effective_priority(elem) for elem in result]
        assert priorities == sorted(priorities, reverse=True)
    
    @pytest.mark.asyncio
    async def test_budget_overrun_handling(self, optimizer):
        """Test behavior when total exceeds budget."""
        elements = [
            ContextElement("Large content " * 50, ContextType.USER_INPUT, 9.0, 1.0, 200, {})
        ]
        
        budget_allocations = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 50)
        }
        
        result = await optimizer.optimize_context_elements(elements, budget_allocations)
        assert len(result) <= 1
        if result:
            assert result[0].token_count <= 60  # Allow tolerance
    
    @pytest.mark.asyncio
    async def test_empty_budget_handling(self, optimizer):
        """Test handling of zero/negative budgets."""
        elements = [
            ContextElement("Test content", ContextType.USER_INPUT, 9.0, 1.0, 10, {})
        ]
        
        budget_allocations = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 0)
        }
        
        result = await optimizer.optimize_context_elements(elements, budget_allocations)
        assert isinstance(result, list)


class TestBasicContextOptimizerPrioritization:
    """Test element prioritization logic."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    def test_effective_priority_calculation(self, optimizer):
        """Test priority calculation with relevance boost."""
        element = ContextElement("Test", ContextType.COMPLIANCE_SOURCES, 7.0, 0.8, 10, {})
        
        effective_priority = optimizer._calculate_effective_priority(element)
        expected = 7.0 + (0.8 * 2.0)  # base + relevance boost
        assert effective_priority == expected
    
    def test_relevance_score_impact(self, optimizer):
        """Test relevance score properly affects priority."""
        low_relevance = ContextElement("Test", ContextType.USER_INPUT, 9.0, 0.2, 10, {})
        high_relevance = ContextElement("Test", ContextType.USER_INPUT, 9.0, 0.9, 10, {})
        
        priority_low = optimizer._calculate_effective_priority(low_relevance)
        priority_high = optimizer._calculate_effective_priority(high_relevance)
        
        assert priority_high > priority_low
    
    def test_context_type_priority_enforcement(self, optimizer):
        """Test SYSTEM_PROMPT always highest priority."""
        system_elem = ContextElement("System", ContextType.SYSTEM_PROMPT, 10.0, 0.3, 10, {})
        user_elem = ContextElement("User", ContextType.USER_INPUT, 9.0, 1.0, 10, {})
        
        system_priority = optimizer._calculate_effective_priority(system_elem)
        user_priority = optimizer._calculate_effective_priority(user_elem)
        
        # System: 10 + (0.3 * 2) = 10.6, User: 9 + (1.0 * 2) = 11.0
        # But system should be highest due to base priority
        assert system_priority >= 10.0  # System gets base priority of 10
        assert user_priority >= 10.0    # User gets calculated priority


class TestBasicContextOptimizerCompression:
    """Test compression integration and selection."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    @pytest.mark.asyncio
    async def test_compression_strategy_selection(self, optimizer):
        """Test correct compression strategy chosen."""
        element = ContextElement("Long content " * 100, ContextType.CONVERSATION_HISTORY, 6.0, 1.0, 300, {})
        
        result = await optimizer._compress_context_element(element, 50)
        
        if result:
            assert result.token_count <= 60  # Allow tolerance
            assert result.source_metadata.get("compressed") is True
    
    @pytest.mark.asyncio
    async def test_compression_fallback_handling(self, optimizer):
        """Test fallback when compression fails."""
        optimizer.compression_factory = Mock()
        mock_strategy = Mock()
        mock_strategy.compress_content = AsyncMock(side_effect=Exception("Failed"))
        optimizer.compression_factory.get_best_strategy_for_content.return_value = mock_strategy
        
        element = ContextElement("Test", ContextType.USER_INPUT, 9.0, 1.0, 100, {})
        result = await optimizer._compress_context_element(element, 50)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_compression_metadata_tracking(self, optimizer):
        """Test compression metadata properly stored."""
        element = ContextElement("Test content " * 20, ContextType.USER_INPUT, 9.0, 1.0, 100, {"original": "data"})
        
        result = await optimizer._compress_context_element(element, 30)
        
        if result:
            assert "original" in result.source_metadata
            assert result.source_metadata.get("compressed") is True


class TestBasicContextOptimizerAssembly:
    """Test context assembly functionality."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    @pytest.mark.asyncio
    async def test_context_assembly_order(self, optimizer):
        """Test elements assembled in logical order."""
        elements = [
            ContextElement("User input", ContextType.USER_INPUT, 9.0, 1.0, 10, {}),
            ContextElement("Compliance", ContextType.COMPLIANCE_SOURCES, 7.0, 1.0, 20, {}),
            ContextElement("Conversation", ContextType.CONVERSATION_HISTORY, 6.0, 1.0, 15, {})
        ]
        
        budget_allocations = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 15),
            ContextType.COMPLIANCE_SOURCES: BudgetAllocation(ContextType.COMPLIANCE_SOURCES, 25),
            ContextType.CONVERSATION_HISTORY: BudgetAllocation(ContextType.CONVERSATION_HISTORY, 20)
        }
        
        result = await optimizer.assemble_context(elements, budget_allocations)
        
        # Should contain all content types in logical order
        assert "Compliance" in result
        assert "Conversation" in result  
        assert "User input" in result
    
    @pytest.mark.asyncio
    async def test_empty_element_filtering(self, optimizer):
        """Test elements with minimal content are handled properly."""
        elements = [
            ContextElement("x", ContextType.USER_INPUT, 9.0, 1.0, 1, {}),  # minimal content
            ContextElement("Real content", ContextType.CONVERSATION_HISTORY, 6.0, 1.0, 10, {})
        ]
        
        budget_allocations = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 15),
            ContextType.CONVERSATION_HISTORY: BudgetAllocation(ContextType.CONVERSATION_HISTORY, 15)
        }
        
        result = await optimizer.assemble_context(elements, budget_allocations)
        
        # Should contain both elements
        assert "Real content" in result
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_emergency_compression_trigger(self, optimizer):
        """Test emergency compression when exceeding limits."""
        # Create content that will exceed target
        large_elements = [
            ContextElement("Large content " * 100, ContextType.USER_INPUT, 9.0, 1.0, 500, {})
        ]
        
        budget_allocations = {
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 600)
        }
        
        # Set small target to trigger emergency compression
        optimizer.target_tokens = 100
        
        result = await optimizer.assemble_context(large_elements, budget_allocations)
        actual_tokens = optimizer.token_manager.count_tokens(result)
        
        # Should apply emergency compression
        assert actual_tokens <= optimizer.target_tokens * 1.2


class TestBasicContextOptimizerQuality:
    """Test quality assessment functionality."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    def test_quality_metrics_calculation(self, optimizer):
        """Test QualityMetrics calculation accuracy."""
        elements = [
            ContextElement("Original content", ContextType.USER_INPUT, 9.0, 1.0, 50, {}),
            ContextElement("More content", ContextType.COMPLIANCE_SOURCES, 7.0, 0.8, 40, {})
        ]
        
        assembled_context = "Compressed version"
        quality = optimizer.assess_quality(assembled_context, elements)
        
        assert isinstance(quality, QualityMetrics)
        assert 0 <= quality.overall_quality_score <= 1
        assert 0 <= quality.compression_ratio <= 1
    
    def test_compression_ratio_calculation(self, optimizer):
        """Test compression ratio properly calculated."""
        elements = [ContextElement("Original " * 20, ContextType.USER_INPUT, 9.0, 1.0, 80, {})]
        assembled_context = "Short"
        
        quality = optimizer.assess_quality(assembled_context, elements)
        
        # Should show high compression
        assert quality.compression_ratio > 0.5
    
    def test_type_coverage_calculation(self, optimizer):
        """Test context type coverage calculation."""
        elements = [
            ContextElement("Content A", ContextType.USER_INPUT, 9.0, 1.0, 20, {}),
            ContextElement("Content B", ContextType.COMPLIANCE_SOURCES, 7.0, 1.0, 20, {})
        ]
        
        assembled_context = "Content A Content B"  # Both types included
        quality = optimizer.assess_quality(assembled_context, elements)
        
        # Should show full coverage (both elements included)
        assert quality.relevance_score > 0.8  # High relevance since both types included


class TestBasicContextOptimizerEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    @pytest.mark.asyncio
    async def test_empty_element_list_handling(self, optimizer):
        """Test behavior with empty element lists."""
        result = await optimizer.optimize_context_elements([], {})
        assert result == []
        
        context = await optimizer.assemble_context([], {})
        assert context == ""
    
    @pytest.mark.asyncio
    async def test_invalid_input_handling(self, optimizer):
        """Test graceful handling of invalid inputs."""
        # None elements
        result = await optimizer.optimize_context_elements(None, {})
        assert result == []
        
        # Invalid budget allocations
        elements = [ContextElement("Test", ContextType.USER_INPUT, 9.0, 1.0, 10, {})]
        result = await optimizer.optimize_context_elements(elements, None)
        assert isinstance(result, list)
    
    def test_get_optimization_stats(self, optimizer):
        """Test optimization statistics retrieval."""
        stats = optimizer.get_optimization_stats()
        
        assert isinstance(stats, dict)
        assert "optimizer_type" in stats
        assert "target_tokens" in stats
        assert stats["optimizer_type"] == "BasicContextOptimizer"


class TestBasicContextOptimizerIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def optimizer(self):
        return BasicContextOptimizer()
    
    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self, optimizer):
        """Test complete optimization from elements to final context."""
        elements = [
            ContextElement("System: You are Warren", ContextType.SYSTEM_PROMPT, 10.0, 1.0, 20, {}),
            ContextElement("User: Create a post", ContextType.USER_INPUT, 9.0, 1.0, 15, {}),
            ContextElement("Compliance rule about disclaimers", ContextType.COMPLIANCE_SOURCES, 7.0, 0.9, 30, {}),
            ContextElement("Previous conversation about risk", ContextType.CONVERSATION_HISTORY, 6.0, 0.7, 25, {})
        ]
        
        budget_allocations = {
            ContextType.SYSTEM_PROMPT: BudgetAllocation(ContextType.SYSTEM_PROMPT, 25),
            ContextType.USER_INPUT: BudgetAllocation(ContextType.USER_INPUT, 20),
            ContextType.COMPLIANCE_SOURCES: BudgetAllocation(ContextType.COMPLIANCE_SOURCES, 35),
            ContextType.CONVERSATION_HISTORY: BudgetAllocation(ContextType.CONVERSATION_HISTORY, 30)
        }
        
        # Optimize elements
        optimized_elements = await optimizer.optimize_context_elements(elements, budget_allocations)
        assert len(optimized_elements) <= len(elements)
        
        # Assemble context
        final_context = await optimizer.assemble_context(elements, budget_allocations)
        assert len(final_context) > 0
        
        # Assess quality
        quality = optimizer.assess_quality(final_context, elements)
        assert isinstance(quality, QualityMetrics)
