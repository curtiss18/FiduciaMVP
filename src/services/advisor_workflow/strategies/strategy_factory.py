# Status Transition Strategy Factory
"""
Factory for creating appropriate status transition strategies based on context.
"""

import logging
from typing import Dict, Optional

from .status_transition_strategy import (
    StatusTransitionStrategy,
    AdvisorTransitionStrategy,
    CCOTransitionStrategy
)

logger = logging.getLogger(__name__)


class StatusTransitionStrategyFactory:
    """Factory for creating status transition strategies."""
    
    def __init__(self):
        """Initialize strategy factory with default strategies."""
        self._strategies = {
            'advisor': AdvisorTransitionStrategy(),
            'cco': CCOTransitionStrategy(),
            'compliance': CCOTransitionStrategy(),
            'admin': CCOTransitionStrategy()
        }
    
    def get_strategy(self, context: Dict) -> Optional[StatusTransitionStrategy]:
        """Get appropriate strategy based on context."""
        user_role = context.get('user_role')
        if not user_role:
            logger.error("No user_role provided in context for strategy selection")
            return None
            
        strategy = self._strategies.get(user_role)
        if not strategy:
            logger.error(f"No strategy found for user_role: {user_role}")
            return None
            
        return strategy
    
    def get_available_strategies(self) -> list:
        """Get list of available strategy types."""
        return list(self._strategies.keys())
    
    def register_strategy(self, user_role: str, strategy: StatusTransitionStrategy):
        """Register a new strategy for a user role."""
        self._strategies[user_role] = strategy
        logger.info(f"Registered new strategy for user_role: {user_role}")
