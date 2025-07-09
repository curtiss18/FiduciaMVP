# Status Transition Strategy Pattern
"""
Strategy pattern for content status transitions based on user role and business rules.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class StatusTransitionStrategy(ABC):
    """Abstract base class for status transition strategies."""
    
    @abstractmethod
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """Check if status transition is allowed."""
        pass
    
    @abstractmethod
    def get_allowed_transitions(self, current_status: str, context: Dict) -> List[str]:
        """Get list of allowed transitions from current status."""
        pass
    
    @abstractmethod
    def get_timestamp_updates(self, new_status: str, context: Dict) -> Dict[str, Any]:
        """Get timestamp fields to update for this transition."""
        pass
    
    @abstractmethod
    def validate_transition_context(self, context: Dict) -> Dict[str, Any]:
        """Validate that context has required information for transition."""
        pass


class AdvisorTransitionStrategy(StatusTransitionStrategy):
    """Handle status transitions initiated by advisors."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """Advisors can only perform specific transitions."""
        if context.get('user_role') != 'advisor':
            return False
            
        allowed_transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],
            'rejected': ['draft'],
            'archived': ['draft'],
            'submitted': ['archived'] 
        }
        
        return new_status in allowed_transitions.get(current_status, [])
    
    def get_allowed_transitions(self, current_status: str, context: Dict) -> List[str]:
        """Get allowed transitions for advisors."""
        if context.get('user_role') != 'advisor':
            return []
            
        transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],
            'rejected': ['draft'],
            'archived': ['draft'],
            'submitted': ['archived'] 
        }
        
        return transitions.get(current_status, [])
    
    def get_timestamp_updates(self, new_status: str, context: Dict) -> Dict[str, Any]:
        """Get timestamp updates for advisor transitions."""
        updates = {'updated_at': 'NOW()'}
        
        if new_status == 'submitted':
            updates['submitted_for_review_at'] = 'NOW()'
            
        return updates
    
    def validate_transition_context(self, context: Dict) -> Dict[str, Any]:
        """Validate advisor transition context."""
        required_fields = ['user_role', 'advisor_id', 'content_id']
        
        for field in required_fields:
            if field not in context:
                return {
                    'valid': False, 
                    'error': f"Missing required field: {field}"
                }
        
        if context['user_role'] != 'advisor':
            return {
                'valid': False,
                'error': "AdvisorTransitionStrategy requires user_role=advisor"
            }
            
        return {'valid': True}


class CCOTransitionStrategy(StatusTransitionStrategy):
    """Handle status transitions initiated by CCOs (compliance officers)."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """CCOs have broader permissions for review decisions."""
        user_role = context.get('user_role')
        if user_role not in ['cco', 'compliance', 'admin']:
            return False
        
        # CCOs can approve/reject submitted content
        if current_status == 'submitted' and new_status in ['approved', 'rejected']:
            return True
        
        # Admin override allows any transition
        if context.get('admin_override', False):
            return True
            
        # CCOs can also perform advisor-like transitions
        advisor_transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],
            'rejected': ['draft'],
            'archived': ['draft']
        }
        
        return new_status in advisor_transitions.get(current_status, [])
    
    def get_allowed_transitions(self, current_status: str, context: Dict) -> List[str]:
        """Get allowed transitions for CCOs."""
        user_role = context.get('user_role')
        if user_role not in ['cco', 'compliance', 'admin']:
            return []
        
        transitions = {
            'draft': ['submitted', 'archived'],
            'submitted': ['approved', 'rejected', 'draft'],
            'approved': ['draft', 'archived', 'rejected'],
            'rejected': ['draft', 'approved'],
            'archived': ['draft']
        }
        
        # Admin override allows any transition
        if context.get('admin_override', False):
            all_statuses = ['draft', 'submitted', 'approved', 'rejected', 'archived']
            return [s for s in all_statuses if s != current_status]
        
        return transitions.get(current_status, [])
    
    def get_timestamp_updates(self, new_status: str, context: Dict) -> Dict[str, Any]:
        """Get timestamp updates for CCO transitions."""
        updates = {'updated_at': 'NOW()'}
        
        if new_status == 'submitted':
            updates['submitted_for_review_at'] = 'NOW()'

        return updates
    
    def validate_transition_context(self, context: Dict) -> Dict[str, Any]:
        """Validate CCO transition context."""
        required_fields = ['user_role', 'content_id']
        
        for field in required_fields:
            if field not in context:
                return {
                    'valid': False,
                    'error': f"Missing required field: {field}"
                }
        
        user_role = context['user_role']
        if user_role not in ['cco', 'compliance', 'admin']:
            return {
                'valid': False,
                'error': f"CCOTransitionStrategy requires user_role in [cco, compliance, admin], got: {user_role}"
            }
            
        return {'valid': True}
