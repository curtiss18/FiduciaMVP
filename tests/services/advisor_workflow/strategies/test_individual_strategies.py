# Test Individual Status Transition Strategies
"""
Tests for individual status transition strategy implementations.
"""

import pytest
from unittest.mock import MagicMock

from src.services.advisor_workflow.strategies.status_transition_strategy import (
    AdvisorTransitionStrategy,
    CCOTransitionStrategy
)


class TestAdvisorTransitionStrategy:
    
    @pytest.fixture
    def strategy(self):
        return AdvisorTransitionStrategy()
    
    @pytest.fixture
    def advisor_context(self):
        return {
            'user_role': 'advisor',
            'advisor_id': 'test_advisor_123',
            'content_id': 1
        }

    def test_can_transition_draft_to_submitted(self, strategy, advisor_context):
        result = strategy.can_transition("draft", "submitted", advisor_context)
        assert result is True
    
    def test_can_transition_draft_to_archived(self, strategy, advisor_context):
        result = strategy.can_transition("draft", "archived", advisor_context)
        assert result is True
    
    def test_cannot_transition_draft_to_approved(self, strategy, advisor_context):
        result = strategy.can_transition("draft", "approved", advisor_context)
        assert result is False
    
    def test_cannot_transition_submitted_to_approved(self, strategy, advisor_context):
        result = strategy.can_transition("submitted", "approved", advisor_context)
        assert result is False
    
    def test_can_transition_approved_to_draft(self, strategy, advisor_context):
        result = strategy.can_transition("approved", "draft", advisor_context)
        assert result is True
    
    def test_can_transition_rejected_to_draft(self, strategy, advisor_context):
        result = strategy.can_transition("rejected", "draft", advisor_context)
        assert result is True
    
    def test_can_transition_archived_to_draft(self, strategy, advisor_context):
        result = strategy.can_transition("archived", "draft", advisor_context)
        assert result is True
    
    def test_cannot_transition_wrong_user_role(self, strategy):
        context = {'user_role': 'cco', 'advisor_id': 'test', 'content_id': 1}
        result = strategy.can_transition("draft", "submitted", context)
        assert result is False

    def test_get_allowed_transitions_draft(self, strategy, advisor_context):
        result = strategy.get_allowed_transitions("draft", advisor_context)
        assert "submitted" in result
        assert "archived" in result
        assert len(result) == 2
    
    def test_get_allowed_transitions_approved(self, strategy, advisor_context):
        result = strategy.get_allowed_transitions("approved", advisor_context)
        assert "draft" in result
        assert "archived" in result
        assert len(result) == 2
    
    def test_get_allowed_transitions_rejected(self, strategy, advisor_context):
        result = strategy.get_allowed_transitions("rejected", advisor_context)
        assert result == ["draft"]
    
    def test_get_allowed_transitions_submitted(self, strategy, advisor_context):
        result = strategy.get_allowed_transitions("submitted", advisor_context)
        assert result == ['archived']
    
    def test_get_allowed_transitions_wrong_role(self, strategy):
        context = {'user_role': 'cco'}
        result = strategy.get_allowed_transitions("draft", context)
        assert result == []

    def test_timestamp_updates_submitted(self, strategy, advisor_context):
        result = strategy.get_timestamp_updates("submitted", advisor_context)
        assert result['updated_at'] == 'NOW()'
        assert result['submitted_for_review_at'] == 'NOW()'
    
    def test_timestamp_updates_archived(self, strategy, advisor_context):
        result = strategy.get_timestamp_updates("archived", advisor_context)
        assert result['updated_at'] == 'NOW()'
        # archived_at column doesn't exist in database
    
    def test_timestamp_updates_restore_from_archive(self, strategy, advisor_context):
        advisor_context['previous_status'] = 'archived'
        result = strategy.get_timestamp_updates("draft", advisor_context)
        assert result['updated_at'] == 'NOW()'
        # archived_at column doesn't exist in database

    def test_validate_context_success(self, strategy, advisor_context):
        result = strategy.validate_transition_context(advisor_context)
        assert result['valid'] is True
    
    def test_validate_context_missing_user_role(self, strategy):
        context = {'advisor_id': 'test', 'content_id': 1}
        result = strategy.validate_transition_context(context)
        assert result['valid'] is False
        assert 'user_role' in result['error']
    
    def test_validate_context_wrong_user_role(self, strategy):
        context = {'user_role': 'cco', 'advisor_id': 'test', 'content_id': 1}
        result = strategy.validate_transition_context(context)
        assert result['valid'] is False
        assert 'advisor' in result['error']


class TestCCOTransitionStrategy:
    
    @pytest.fixture
    def strategy(self):
        return CCOTransitionStrategy()
    
    @pytest.fixture
    def cco_context(self):
        return {
            'user_role': 'cco',
            'cco_email': 'cco@example.com',
            'content_id': 1
        }

    def test_can_transition_submitted_to_approved(self, strategy, cco_context):
        result = strategy.can_transition("submitted", "approved", cco_context)
        assert result is True
    
    def test_can_transition_submitted_to_rejected(self, strategy, cco_context):
        result = strategy.can_transition("submitted", "rejected", cco_context)
        assert result is True
    
    def test_can_transition_with_admin_override(self, strategy, cco_context):
        cco_context['admin_override'] = True
        result = strategy.can_transition("approved", "rejected", cco_context)
        assert result is True
    
    def test_compliance_role_allowed(self, strategy):
        context = {'user_role': 'compliance', 'content_id': 1}
        result = strategy.can_transition("submitted", "approved", context)
        assert result is True
    
    def test_admin_role_allowed(self, strategy):
        context = {'user_role': 'admin', 'content_id': 1}
        result = strategy.can_transition("submitted", "approved", context)
        assert result is True
    
    def test_cannot_transition_wrong_user_role(self, strategy):
        context = {'user_role': 'advisor', 'content_id': 1}
        result = strategy.can_transition("submitted", "approved", context)
        assert result is False

    def test_get_allowed_transitions_submitted(self, strategy, cco_context):
        result = strategy.get_allowed_transitions("submitted", cco_context)
        assert "approved" in result
        assert "rejected" in result
        assert "draft" in result
    
    def test_get_allowed_transitions_with_admin_override(self, strategy, cco_context):
        cco_context['admin_override'] = True
        result = strategy.get_allowed_transitions("approved", cco_context)
        assert "draft" in result
        assert "submitted" in result
        assert "rejected" in result
        assert "archived" in result
        assert "approved" not in result

    def test_timestamp_updates_approved(self, strategy, cco_context):
        result = strategy.get_timestamp_updates("approved", cco_context)
        assert result['updated_at'] == 'NOW()'
        # approved_at and reviewed_by columns don't exist in database
    
    def test_timestamp_updates_rejected(self, strategy, cco_context):
        result = strategy.get_timestamp_updates("rejected", cco_context)
        assert result['updated_at'] == 'NOW()'
        # rejected_at and reviewed_by columns don't exist in database
    
    def test_timestamp_updates_clear_review_data(self, strategy, cco_context):
        cco_context['previous_status'] = 'approved'
        result = strategy.get_timestamp_updates("draft", cco_context)
        assert result['updated_at'] == 'NOW()'
        # approved_at, rejected_at, and reviewed_by columns don't exist in database

    def test_validate_context_success(self, strategy, cco_context):
        result = strategy.validate_transition_context(cco_context)
        assert result['valid'] is True
    
    def test_validate_context_missing_content_id(self, strategy):
        context = {'user_role': 'cco'}
        result = strategy.validate_transition_context(context)
        assert result['valid'] is False
        assert 'content_id' in result['error']
    
    def test_validate_context_wrong_user_role(self, strategy):
        context = {'user_role': 'advisor', 'content_id': 1}
        result = strategy.validate_transition_context(context)
        assert result['valid'] is False
        assert 'cco, compliance, admin' in result['error']
