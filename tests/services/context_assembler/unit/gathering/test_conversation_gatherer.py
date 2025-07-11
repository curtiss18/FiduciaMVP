"""Unit tests for ConversationGatherer"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.gathering.conversation_gatherer import ConversationGatherer
from src.services.context_assembly_service.models import ContextType


@pytest.mark.asyncio
async def test_conversation_gatherer_success():
    """Test successful conversation context retrieval"""
    gatherer = ConversationGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.return_value = "Previous conversation content"
        
        elements = await gatherer.gather_context("test-session", mock_session)
        
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.CONVERSATION_HISTORY
        assert elements[0].content == "Previous conversation content"
        assert elements[0].source_metadata["session_id"] == "test-session"


@pytest.mark.asyncio
async def test_conversation_gatherer_no_context():
    """Test when no conversation context exists"""
    gatherer = ConversationGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.return_value = None
        
        elements = await gatherer.gather_context("test-session", mock_session)
        
        assert len(elements) == 0


@pytest.mark.asyncio
async def test_conversation_gatherer_error_handling():
    """Test error handling when conversation manager fails"""
    gatherer = ConversationGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.side_effect = Exception("Database error")
        
        elements = await gatherer.gather_context("test-session", mock_session)
        
        assert len(elements) == 0


def test_supported_context_types():
    """Test supported context types"""
    gatherer = ConversationGatherer()
    supported = gatherer.get_supported_context_types()
    
    assert supported == [ContextType.CONVERSATION_HISTORY]
