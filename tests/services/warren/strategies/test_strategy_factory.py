"""
Updated Tests for Content Generation Strategy Interface and Factory (2-Strategy Model)

Test Coverage:
- ContentGenerationStrategy interface contract
- StrategyFactory strategy selection logic for Advanced + Legacy
- Strategy fallback chains
- Strategy instantiation and management
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.strategies import (
    ContentGenerationStrategy, 
    GenerationResult,
    AdvancedGenerationStrategy,
    LegacyGenerationStrategy,
    StrategyFactory,
    strategy_factory
)


class TestGenerationResult:
    """Test GenerationResult container."""
    
    def test_generation_result_initialization(self):
        """Test GenerationResult default initialization."""
        result = GenerationResult()
        
        assert result.content is None
        assert result.success is False
        assert result.error_message is None
        assert result.metadata == {}
        assert result.strategy_used is None
        assert result.generation_time == 0.0
        assert result.token_usage == {}


class TestContentGenerationStrategy:
    """Test ContentGenerationStrategy interface contract."""
    
    def test_interface_is_abstract(self):
        """Test that ContentGenerationStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ContentGenerationStrategy()
    
    def test_all_strategies_implement_interface(self):
        """Test that all strategies properly implement the interface."""
        strategies = [
            AdvancedGenerationStrategy(),
            LegacyGenerationStrategy()
        ]
        
        for strategy in strategies:
            assert isinstance(strategy, ContentGenerationStrategy)
            assert hasattr(strategy, 'generate_content')
            assert hasattr(strategy, 'can_handle')
            assert hasattr(strategy, 'get_strategy_name')
            assert hasattr(strategy, 'get_strategy_priority')


class TestStrategyFactory:
    """Test StrategyFactory for 2-strategy model."""
    
    @pytest.fixture
    def factory(self):
        """Create fresh StrategyFactory for testing."""
        return StrategyFactory()
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample rich context data."""
        return {
            "session_id": "test-session-123",
            "marketing_examples": [
                {"title": "Example 1", "content_text": "Sample content..."}
            ],
            "disclaimers": [
                {"title": "Risk Disclaimer", "content_text": "Past performance..."}
            ],
            "conversation_context": "Previous conversation...",
            "session_documents": [
                {"title": "Investment Philosophy", "summary": "Our approach..."}
            ]
        }
    
    def test_factory_initialization(self, factory):
        """Test StrategyFactory initialization with 2 strategies."""
        strategies = factory.get_all_strategies()
        
        assert "advanced" in strategies
        assert "legacy" in strategies
        assert len(strategies) == 2
        
        assert isinstance(strategies["advanced"], AdvancedGenerationStrategy)
        assert isinstance(strategies["legacy"], LegacyGenerationStrategy)
    
    def test_get_strategy_by_name(self, factory):
        """Test retrieving specific strategies by name."""
        advanced = factory.get_strategy("advanced")
        legacy = factory.get_strategy("legacy")
        none_strategy = factory.get_strategy("nonexistent")
        
        assert isinstance(advanced, AdvancedGenerationStrategy)
        assert isinstance(legacy, LegacyGenerationStrategy)
        assert none_strategy is None
    
    def test_get_best_strategy_advanced_context(self, factory, sample_context_data):
        """Test strategy selection with rich context that Advanced can handle."""
        strategy = factory.get_best_strategy(sample_context_data)
        
        # Advanced strategy should be selected for rich context
        assert isinstance(strategy, AdvancedGenerationStrategy)
        assert strategy.get_strategy_name() == "advanced"
    
    def test_get_best_strategy_fallback_to_legacy(self, factory):
        """Test strategy selection falls back to legacy when advanced can't handle."""
        # Empty context that Advanced strategy cannot handle
        minimal_context = {}
        
        strategy = factory.get_best_strategy(minimal_context)
        
        # Should fallback to legacy strategy
        assert isinstance(strategy, LegacyGenerationStrategy)
        assert strategy.get_strategy_name() == "legacy"
    
    def test_get_fallback_chain(self, factory, sample_context_data):
        """Test fallback chain creation."""
        fallback_chain = factory.get_fallback_chain(sample_context_data)
        
        # Should have both strategies in priority order
        assert len(fallback_chain) == 2
        assert isinstance(fallback_chain[0], AdvancedGenerationStrategy)  # Highest priority
        assert isinstance(fallback_chain[1], LegacyGenerationStrategy)    # Fallback


class TestStrategiesIntegration:
    """Integration tests for 2-strategy model."""
    
    def test_strategy_priorities_are_correct(self):
        """Test that strategy priorities are properly ordered."""
        advanced = AdvancedGenerationStrategy()
        legacy = LegacyGenerationStrategy()
        
        assert advanced.get_strategy_priority() < legacy.get_strategy_priority()
        
        # Specific values
        assert advanced.get_strategy_priority() == 10  # Highest priority
        assert legacy.get_strategy_priority() == 100   # Lowest priority
    
    def test_strategy_names_are_unique(self):
        """Test that all strategies have unique names."""
        strategies = [
            AdvancedGenerationStrategy(),
            LegacyGenerationStrategy()
        ]
        
        names = [s.get_strategy_name() for s in strategies]
        assert len(names) == len(set(names))  # All names should be unique
        assert "advanced" in names
        assert "legacy" in names
    
    def test_advanced_context_requirements(self):
        """Test advanced context requirements are set correctly."""
        advanced = AdvancedGenerationStrategy()
        legacy = LegacyGenerationStrategy()
        
        assert advanced.requires_advanced_context() is True
        assert legacy.requires_advanced_context() is False


class TestGlobalStrategyFactory:
    """Test the global strategy factory instance."""
    
    def test_global_factory_is_initialized(self):
        """Test that global strategy_factory is properly initialized."""
        assert strategy_factory is not None
        assert isinstance(strategy_factory, StrategyFactory)
        
        strategies = strategy_factory.get_all_strategies()
        assert len(strategies) == 2  # Advanced + Legacy
        assert "advanced" in strategies
        assert "legacy" in strategies
    
    def test_global_factory_strategies_work(self):
        """Test that strategies from global factory are functional."""
        advanced = strategy_factory.get_strategy("advanced")
        legacy = strategy_factory.get_strategy("legacy")
        
        assert advanced is not None
        assert legacy is not None
        assert advanced.get_strategy_name() == "advanced"
        assert legacy.get_strategy_name() == "legacy"


class TestStrategyFactoryEnhancements:
    """Test enhanced features added in SCRUM-122."""
    
    @pytest.fixture
    def factory(self):
        """Create StrategyFactory instance for testing."""
        return StrategyFactory()
    
    def test_context_summarization(self, factory):
        """Test context summarization for logging."""
        # Test rich context
        rich_context = {
            "marketing_examples": ["ex1", "ex2"],
            "disclaimers": ["disc1"],
            "session_documents": [{"title": "doc1"}],
            "conversation_context": "previous chat"
        }
        summary = factory._summarize_context(rich_context)
        assert "marketing_examples(2)" in summary
        assert "disclaimers(1)" in summary
        assert "documents(1)" in summary
        assert "conversation" in summary
        
        # Test empty context
        empty_context = {}
        summary = factory._summarize_context(empty_context)
        assert "minimal/empty" in summary
        
        # Test invalid context
        invalid_context = "not a dict"
        summary = factory._summarize_context(invalid_context)
        assert "Invalid context type" in summary
    
    def test_2_strategy_architecture(self, factory):
        """Test that factory has exactly 2 strategies."""
        strategies = factory.get_all_strategies()
        assert len(strategies) == 2
        assert "advanced" in strategies
        assert "legacy" in strategies
        assert "standard" not in strategies  # Ensure removed strategy is not present
    
    def test_strategy_selection_logging(self, factory):
        """Test that strategy selection includes proper logging."""
        with patch('src.services.warren.strategies.strategy_factory.logger') as mock_logger:
            # Test Advanced selection
            rich_context = {"marketing_examples": ["ex1"]}
            strategy = factory.get_best_strategy(rich_context)
            assert strategy.get_strategy_name() == "advanced"
            mock_logger.info.assert_called_with("🎯 Selected Advanced strategy (sophisticated context handling)")
            
            # Test Legacy fallback
            empty_context = {}
            strategy = factory.get_best_strategy(empty_context)
            assert strategy.get_strategy_name() == "legacy"
            mock_logger.info.assert_called_with("🔄 Selected Legacy strategy (emergency fallback - always works)")
    
    def test_fallback_chain_logging(self, factory):
        """Test that fallback chain generation includes proper logging."""
        with patch('src.services.warren.strategies.strategy_factory.logger') as mock_logger:
            # Test chain with Advanced strategy
            rich_context = {"marketing_examples": ["ex1"]}
            chain = factory.get_fallback_chain(rich_context)
            assert len(chain) == 2
            assert chain[0].get_strategy_name() == "advanced"
            assert chain[1].get_strategy_name() == "legacy"
            mock_logger.info.assert_called_with("📋 Fallback chain: advanced → legacy")
            
            # Test chain with only Legacy
            empty_context = {}
            chain = factory.get_fallback_chain(empty_context)
            assert len(chain) == 1
            assert chain[0].get_strategy_name() == "legacy"
            mock_logger.info.assert_called_with("📋 Fallback chain: legacy")
    
    def test_get_strategy_error_handling(self, factory):
        """Test get_strategy handles invalid strategy names."""
        with patch('src.services.warren.strategies.strategy_factory.logger') as mock_logger:
            strategy = factory.get_strategy("nonexistent")
            assert strategy is None
            mock_logger.warning.assert_called_with("Strategy 'nonexistent' not found. Available: ['advanced', 'legacy']")
    
    def test_advanced_strategy_priority_over_legacy(self, factory):
        """Test that Advanced strategy is always chosen when it can handle context."""
        # Context that both can handle (Legacy always can, Advanced needs validation)
        valid_context = {"marketing_examples": ["example"]}
        
        # Advanced should be selected due to higher priority (lower number)
        strategy = factory.get_best_strategy(valid_context)
        assert strategy.get_strategy_name() == "advanced"
        
        # Verify priorities are correct
        advanced = factory.get_strategy("advanced")
        legacy = factory.get_strategy("legacy")
        assert advanced.get_strategy_priority() < legacy.get_strategy_priority()
    
    def test_legacy_as_guaranteed_fallback(self, factory):
        """Test that Legacy strategy always works as intended."""
        # Legacy should handle any context type
        test_contexts = [
            {},
            None,
            "invalid",
            [],
            {"malformed": "data"},
            {"marketing_examples": "not a list"}
        ]
        
        for context in test_contexts:
            strategy = factory.get_best_strategy(context)
            # Should always get a strategy (never None due to Legacy fallback)
            assert strategy is not None
            # For invalid contexts, should get Legacy
            if context not in [{"marketing_examples": ["valid"]}]:
                assert strategy.get_strategy_name() == "legacy"


class TestStrategyFactoryBackwardCompatibility:
    """Test that SCRUM-122 changes maintain backward compatibility."""
    
    @pytest.fixture
    def factory(self):
        """Create StrategyFactory instance for testing."""
        return StrategyFactory()
    
    def test_public_api_unchanged(self, factory):
        """Test that all public API methods still exist and work."""
        # All these methods should exist and work as before
        assert hasattr(factory, 'get_strategy')
        assert hasattr(factory, 'get_best_strategy')
        assert hasattr(factory, 'get_fallback_chain')
        assert hasattr(factory, 'get_all_strategies')
        
        # Test they return expected types
        context = {"marketing_examples": ["ex1"]}
        
        strategy = factory.get_strategy("advanced")
        assert isinstance(strategy, AdvancedGenerationStrategy)
        
        best_strategy = factory.get_best_strategy(context)
        assert hasattr(best_strategy, 'get_strategy_name')
        
        chain = factory.get_fallback_chain(context)
        assert isinstance(chain, list)
        assert all(hasattr(s, 'get_strategy_name') for s in chain)
        
        all_strategies = factory.get_all_strategies()
        assert isinstance(all_strategies, dict)
    
    def test_existing_usage_patterns_work(self, factory):
        """Test existing code patterns still work after refactoring."""
        # Pattern 1: Get specific strategy by name
        advanced = factory.get_strategy("advanced")
        legacy = factory.get_strategy("legacy")
        assert advanced is not None
        assert legacy is not None
        
        # Pattern 2: Get best strategy for context
        context = {"marketing_examples": ["example"]}
        best = factory.get_best_strategy(context)
        assert best.get_strategy_name() in ["advanced", "legacy"]
        
        # Pattern 3: Get fallback chain
        chain = factory.get_fallback_chain(context)
        assert len(chain) >= 1  # At least Legacy should be in chain
        
        # Pattern 4: Iterate through all strategies
        all_strategies = factory.get_all_strategies()
        for name, strategy in all_strategies.items():
            assert name in ["advanced", "legacy"]
            assert strategy.get_strategy_name() == name
