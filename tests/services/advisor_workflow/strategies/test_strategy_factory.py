# Test Status Transition Strategy Factory
"""
Tests for status transition strategy factory.
"""

import pytest
from unittest.mock import MagicMock

from src.services.advisor_workflow.strategies.status_transition_strategy import (
    StatusTransitionStrategy,
    AdvisorTransitionStrategy,
    CCOTransitionStrategy
)
from src.services.advisor_workflow.strategies.strategy_factory import StatusTransitionStrategyFactory


class TestStatusTransitionStrategyFactory:
    
    @pytest.fixture
    def factory(self):
        return StatusTransitionStrategyFactory()

    def test_get_strategy_advisor(self, factory):
        context = {'user_role': 'advisor'}
        strategy = factory.get_strategy(context)
        assert isinstance(strategy, AdvisorTransitionStrategy)
    
    def test_get_strategy_cco(self, factory):
        context = {'user_role': 'cco'}
        strategy = factory.get_strategy(context)
        assert isinstance(strategy, CCOTransitionStrategy)
    
    def test_get_strategy_compliance(self, factory):
        context = {'user_role': 'compliance'}
        strategy = factory.get_strategy(context)
        assert isinstance(strategy, CCOTransitionStrategy)
    
    def test_get_strategy_admin(self, factory):
        context = {'user_role': 'admin'}
        strategy = factory.get_strategy(context)
        assert isinstance(strategy, CCOTransitionStrategy)
    
    def test_get_strategy_invalid_role(self, factory):
        context = {'user_role': 'invalid_role'}
        strategy = factory.get_strategy(context)
        assert strategy is None
    
    def test_get_strategy_no_role(self, factory):
        context = {}
        strategy = factory.get_strategy(context)
        assert strategy is None

    def test_get_available_strategies(self, factory):
        strategies = factory.get_available_strategies()
        assert 'advisor' in strategies
        assert 'cco' in strategies
        assert 'compliance' in strategies
        assert 'admin' in strategies
    
    def test_register_new_strategy(self, factory):
        mock_strategy = MagicMock()
        factory.register_strategy('custom_role', mock_strategy)
        
        context = {'user_role': 'custom_role'}
        result = factory.get_strategy(context)
        assert result == mock_strategy
