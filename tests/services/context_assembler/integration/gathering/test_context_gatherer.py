"""Unit tests for ContextGatherer coordinator"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.gathering.context_gatherer import ContextGatherer
from src.services.context_assembly_service.models import ContextType, ContextElement


@pytest.mark.asyncio
async def test_context_gatherer_all_context():
    """Test gathering all context types"""
    gatherer = ContextGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    context_data = {
        "rules": [{"title": "Test Rule", "content_text": "Test content"}]
    }
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.return_value = "Previous conversation"
        
        elements = await gatherer.gather_all_context(
            session_id="test-session",
            db_session=mock_session,
            context_data=context_data
        )
        
        assert len(elements) == 2  # One conversation, one compliance
        
        # Check we have both types
        types = [elem.context_type for elem in elements]
        assert ContextType.CONVERSATION_HISTORY in types
        assert ContextType.COMPLIANCE_SOURCES in types


@pytest.mark.asyncio
async def test_context_gatherer_conversation_only():
    """Test gathering only conversation context"""
    gatherer = ContextGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.return_value = "Previous conversation"
        
        elements = await gatherer.gather_conversation_only(
            session_id="test-session",
            db_session=mock_session
        )
        
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.CONVERSATION_HISTORY


@pytest.mark.asyncio
async def test_context_gatherer_compliance_only():
    """Test gathering only compliance context"""
    gatherer = ContextGatherer()
    
    context_data = {
        "rules": [{"title": "Test Rule", "content_text": "Test content"}]
    }
    
    elements = await gatherer.gather_compliance_only(context_data=context_data)
    
    assert len(elements) == 1
    assert elements[0].context_type == ContextType.COMPLIANCE_SOURCES


@pytest.mark.asyncio
async def test_context_gatherer_partial_failure():
    """Test handling when one gatherer fails but other succeeds"""
    gatherer = ContextGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    context_data = {
        "rules": [{"title": "Test Rule", "content_text": "Test content"}]
    }
    
    # Mock conversation gatherer to fail
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.side_effect = Exception("Database error")
        
        elements = await gatherer.gather_all_context(
            session_id="test-session",
            db_session=mock_session,
            context_data=context_data
        )
        
        # Should still get compliance context even if conversation fails
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.COMPLIANCE_SOURCES


@pytest.mark.asyncio
async def test_context_gatherer_no_context():
    """Test when no context is available"""
    gatherer = ContextGatherer()
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch('src.services.context_assembly_service.gathering.conversation_gatherer.ConversationManager') as mock_cm:
        mock_manager = AsyncMock()
        mock_cm.return_value = mock_manager
        mock_manager.get_conversation_context.return_value = None
        
        elements = await gatherer.gather_all_context(
            session_id="test-session",
            db_session=mock_session,
            context_data=None
        )
        
        assert len(elements) == 0
