# Test ContentStatusManager
"""
Unit tests for ContentStatusManager service following Warren testing patterns.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.content_status_manager import ContentStatusManager
from src.services.advisor_workflow.strategies.status_transition_strategy import (
    AdvisorTransitionStrategy, CCOTransitionStrategy
)
from src.services.advisor_workflow.strategies.strategy_factory import StatusTransitionStrategyFactory


class TestContentStatusManager:
    
    @pytest.fixture
    def service(self):
        return ContentStatusManager()
    
    @pytest.fixture
    def mock_strategy_factory(self):
        factory = MagicMock()
        factory.get_strategy.return_value = MagicMock()
        return factory
    
    @pytest.fixture
    def service_with_mock_factory(self, mock_strategy_factory):
        return ContentStatusManager(strategy_factory=mock_strategy_factory)
    
    @pytest.fixture
    def sample_content_item(self):
        mock_content = MagicMock()
        mock_content.id = 1
        mock_content.advisor_id = "test_advisor_123"
        mock_content.status = "draft"
        mock_content.title = "Test Content"
        mock_content.submitted_for_review_at = None
        mock_content.updated_at = datetime.now()
        return mock_content
    
    @pytest.fixture
    def advisor_context(self):
        return {
            'user_role': 'advisor',
            'advisor_id': 'test_advisor_123',
            'content_id': 1
        }
    
    @pytest.fixture
    def cco_context(self):
        return {
            'user_role': 'cco',
            'cco_email': 'cco@example.com',
            'content_id': 1,
            'advisor_id': 'test_advisor_123'
        }

    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_success(self, mock_session_local, service, 
                                           sample_content_item, advisor_context):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_item
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None
        
        # Act
        result = await service.transition_status(
            content_id=1,
            advisor_id="test_advisor_123", 
            new_status="submitted",
            context=advisor_context
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == 1
        assert result["previous_status"] == "draft"
        assert result["new_status"] == "submitted"
        assert result["user_role"] == "advisor"
        
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_content_not_found(self, mock_session_local, service):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.transition_status(
            content_id=999,
            advisor_id="test_advisor_123",
            new_status="submitted"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found or access denied" in result["error"]
    
    @pytest.mark.asyncio
    async def test_transition_status_invalid_user_role(self, service_with_mock_factory, 
                                                     mock_strategy_factory):
        # Arrange
        mock_strategy_factory.get_strategy.return_value = None
        
        # Act
        result = await service_with_mock_factory.transition_status(
            content_id=1,
            advisor_id="test_advisor_123",
            new_status="submitted",
            context={'user_role': 'invalid_role'}
        )
        
        # Assert
        assert result["status"] == "error"
        assert "No strategy found" in result["error"]
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_not_allowed(self, mock_session_local, service,
                                                sample_content_item):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        sample_content_item.status = "submitted"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_item
        mock_db.execute.return_value = mock_result
        
        # Act - advisor trying to change submitted content
        result = await service.transition_status(
            content_id=1,
            advisor_id="test_advisor_123",
            new_status="approved",
            context={'user_role': 'advisor'}
        )
        
        # Assert
        assert result["status"] == "error"
        assert "not allowed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_validate_transition_advisor_valid(self, service):
        result = await service.validate_transition(
            current_status="draft",
            new_status="submitted", 
            user_role="advisor"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_transition_advisor_invalid(self, service):
        result = await service.validate_transition(
            current_status="submitted",
            new_status="approved",
            user_role="advisor"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_transition_cco_valid(self, service):
        result = await service.validate_transition(
            current_status="submitted",
            new_status="approved",
            user_role="cco"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_transition_invalid_role(self, service):
        result = await service.validate_transition(
            current_status="draft",
            new_status="submitted",
            user_role="invalid_role"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_get_allowed_transitions_advisor_draft(self, service):
        result = await service.get_allowed_transitions(
            current_status="draft",
            user_role="advisor"
        )
        assert "submitted" in result
        assert "archived" in result
        assert "approved" not in result
    
    @pytest.mark.asyncio
    async def test_get_allowed_transitions_advisor_submitted(self, service):
        result = await service.get_allowed_transitions(
            current_status="submitted",
            user_role="advisor"
        )
        assert result == ['archived']
    
    @pytest.mark.asyncio
    async def test_get_allowed_transitions_cco_submitted(self, service):
        result = await service.get_allowed_transitions(
            current_status="submitted",
            user_role="cco"
        )
        assert "approved" in result
        assert "rejected" in result
        assert "draft" in result
    
    @pytest.mark.asyncio
    async def test_get_allowed_transitions_invalid_role(self, service):
        result = await service.get_allowed_transitions(
            current_status="draft",
            user_role="invalid_role"
        )
        assert result == []

    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_get_status_history_success(self, mock_session_local, service,
                                            sample_content_item):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        sample_content_item.submitted_for_review_at = datetime.now()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_item
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_status_history(
            content_id=1,
            advisor_id="test_advisor_123"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == 1
        assert result["current_status"] == "draft"
        assert len(result["history"]) >= 1
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_get_status_history_not_found(self, mock_session_local, service):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_status_history(
            content_id=999,
            advisor_id="test_advisor_123"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found" in result["error"]

    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_database_error(self, mock_session_local, service):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.transition_status(
            content_id=1,
            advisor_id="test_advisor_123",
            new_status="submitted"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_default_advisor_role(self, mock_session_local, service,
                                                         sample_content_item):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_item
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None
        
        # Act - no context provided, should default to advisor
        result = await service.transition_status(
            content_id=1,
            advisor_id="test_advisor_123",
            new_status="submitted"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["user_role"] == "advisor"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_status_manager.AsyncSessionLocal')
    async def test_transition_status_with_advisor_notes(self, mock_session_local, service,
                                                       sample_content_item):
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_item
        mock_db.execute.return_value = mock_result
        mock_db.commit.return_value = None
        
        # Act
        result = await service.transition_status(
            content_id=1,
            advisor_id="test_advisor_123",
            new_status="submitted",
            context={'advisor_notes': 'Ready for review'}
        )
        
        # Assert
        assert result["status"] == "success"
