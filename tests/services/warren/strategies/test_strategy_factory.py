"""
Tests for Content Generation Strategy Interface and Factory

Test Coverage:
- ContentGenerationStrategy interface contract
- StrategyFactory strategy selection logic
- Strategy fallback chains
- Strategy instantiation and management
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.strategies import (
    ContentGenerationStrategy, 
    GenerationResult,
    AdvancedGenerationStrategy,
    StandardGenerationStrategy,
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
            StandardGenerationStrategy(),
            LegacyGenerationStrategy()
        ]
        
        for strategy in strategies:
            assert isinstance(strategy, ContentGenerationStrategy)
            assert hasattr(strategy, 'generate_content')
            assert hasattr(strategy, 'can_handle')
            assert hasattr(strategy, 'get_strategy_name')
            assert hasattr(strategy, 'get_strategy_priority')
            assert hasattr(strategy, 'requires_advanced_context')


class TestStrategyFactory:
    """Test StrategyFactory functionality."""
    
    @pytest.fixture
    def factory(self):
        """Create a fresh strategy factory for testing."""
        return StrategyFactory()
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
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
        """Test factory initializes with all strategies."""
        strategies = factory.get_all_strategies()
        
        assert "advanced" in strategies
        assert "standard" in strategies
        assert "legacy" in strategies
        assert len(strategies) == 3
        
        assert isinstance(strategies["advanced"], AdvancedGenerationStrategy)
        assert isinstance(strategies["standard"], StandardGenerationStrategy)
        assert isinstance(strategies["legacy"], LegacyGenerationStrategy)
    
    def test_get_strategy_by_name(self, factory):
        """Test retrieving specific strategies by name."""
        advanced = factory.get_strategy("advanced")
        standard = factory.get_strategy("standard")
        legacy = factory.get_strategy("legacy")
        none_strategy = factory.get_strategy("nonexistent")
        
        assert isinstance(advanced, AdvancedGenerationStrategy)
        assert isinstance(standard, StandardGenerationStrategy)
        assert isinstance(legacy, LegacyGenerationStrategy)
        assert none_strategy is None
    
    def test_get_best_strategy_rich_context(self, factory, sample_context_data):
        """Test strategy selection with rich context data."""
        # Mock strategy can_handle methods
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=True):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=True):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=True):
                    
                    strategy = factory.get_best_strategy(sample_context_data)
                    
                    # Should select advanced strategy (highest priority)
                    assert isinstance(strategy, AdvancedGenerationStrategy)
                    assert strategy.get_strategy_name() == "advanced"
    
    def test_get_best_strategy_no_advanced_context(self, factory):
        """Test strategy selection when advanced strategy can't handle context."""
        minimal_context = {"session_id": "test-123"}
        
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=False):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=True):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=True):
                    
                    strategy = factory.get_best_strategy(minimal_context)
                    
                    # Should select standard strategy (next highest priority)
                    assert isinstance(strategy, StandardGenerationStrategy)
                    assert strategy.get_strategy_name() == "standard"
    
    def test_get_best_strategy_only_legacy_available(self, factory):
        """Test strategy selection when only legacy can handle context."""
        empty_context = {}
        
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=False):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=False):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=True):
                    
                    strategy = factory.get_best_strategy(empty_context)
                    
                    # Should select legacy strategy (only available)
                    assert isinstance(strategy, LegacyGenerationStrategy)
                    assert strategy.get_strategy_name() == "legacy"
    
    def test_get_best_strategy_no_strategies_available(self, factory):
        """Test strategy selection when no strategies can handle context."""
        problematic_context = {"error": "Invalid context"}
        
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=False):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=False):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=False):
                    
                    strategy = factory.get_best_strategy(problematic_context)
                    
                    # Should fallback to legacy strategy
                    assert isinstance(strategy, LegacyGenerationStrategy)
                    assert strategy.get_strategy_name() == "legacy"
    
    def test_get_fallback_chain_all_available(self, factory, sample_context_data):
        """Test fallback chain when all strategies are available."""
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=True):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=True):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=True):
                    
                    chain = factory.get_fallback_chain(sample_context_data)
                    
                    assert len(chain) == 3
                    assert isinstance(chain[0], AdvancedGenerationStrategy)  # Highest priority
                    assert isinstance(chain[1], StandardGenerationStrategy)  # Medium priority
                    assert isinstance(chain[2], LegacyGenerationStrategy)    # Lowest priority
    
    def test_get_fallback_chain_partial_availability(self, factory):
        """Test fallback chain when only some strategies are available."""
        context = {"minimal": True}
        
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=False):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=True):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=False):
                    
                    chain = factory.get_fallback_chain(context)
                    
                    # Should include standard + legacy fallback
                    assert len(chain) == 2
                    assert isinstance(chain[0], StandardGenerationStrategy)
                    assert isinstance(chain[1], LegacyGenerationStrategy)  # Always included as final fallback
    
    def test_get_fallback_chain_ensures_legacy_fallback(self, factory):
        """Test that fallback chain always includes legacy strategy."""
        context = {"test": True}
        
        with patch.object(AdvancedGenerationStrategy, 'can_handle', return_value=True):
            with patch.object(StandardGenerationStrategy, 'can_handle', return_value=False):
                with patch.object(LegacyGenerationStrategy, 'can_handle', return_value=False):
                    
                    chain = factory.get_fallback_chain(context)
                    
                    # Should include advanced + legacy fallback (even though legacy.can_handle=False)
                    assert len(chain) == 2
                    assert isinstance(chain[0], AdvancedGenerationStrategy)
                    assert isinstance(chain[1], LegacyGenerationStrategy)


class TestStrategiesIntegration:
    """Test strategy priority and behavior integration."""
    
    def test_strategy_priorities_are_correct(self):
        """Test that strategy priorities are set correctly."""
        advanced = AdvancedGenerationStrategy()
        standard = StandardGenerationStrategy()
        legacy = LegacyGenerationStrategy()
        
        assert advanced.get_strategy_priority() < standard.get_strategy_priority()
        assert standard.get_strategy_priority() < legacy.get_strategy_priority()
        
        # Specific values
        assert advanced.get_strategy_priority() == 10  # Highest priority
        assert standard.get_strategy_priority() == 50  # Medium priority  
        assert legacy.get_strategy_priority() == 100   # Lowest priority
    
    def test_strategy_names_are_unique(self):
        """Test that all strategies have unique names."""
        strategies = [
            AdvancedGenerationStrategy(),
            StandardGenerationStrategy(),
            LegacyGenerationStrategy()
        ]
        
        names = [s.get_strategy_name() for s in strategies]
        assert len(names) == len(set(names))  # All names should be unique
        assert "advanced" in names
        assert "standard" in names
        assert "legacy" in names
    
    def test_advanced_context_requirements(self):
        """Test advanced context requirements are set correctly."""
        advanced = AdvancedGenerationStrategy()
        standard = StandardGenerationStrategy()
        legacy = LegacyGenerationStrategy()
        
        assert advanced.requires_advanced_context() is True
        assert standard.requires_advanced_context() is False
        assert legacy.requires_advanced_context() is False


class TestGlobalStrategyFactory:
    """Test the global strategy factory instance."""
    
    def test_global_factory_is_initialized(self):
        """Test that global strategy_factory is properly initialized."""
        assert strategy_factory is not None
        assert isinstance(strategy_factory, StrategyFactory)
        
        strategies = strategy_factory.get_all_strategies()
        assert len(strategies) == 3
        assert "advanced" in strategies
        assert "standard" in strategies
        assert "legacy" in strategies
    
    def test_global_factory_strategies_work(self):
        """Test that strategies from global factory are functional."""
        context_data = {"test": True}
        
        # Should be able to get a strategy
        strategy = strategy_factory.get_best_strategy(context_data)
        assert strategy is not None
        assert isinstance(strategy, ContentGenerationStrategy)
        
        # Should be able to get fallback chain
        chain = strategy_factory.get_fallback_chain(context_data)
        assert len(chain) > 0
        assert all(isinstance(s, ContentGenerationStrategy) for s in chain)

