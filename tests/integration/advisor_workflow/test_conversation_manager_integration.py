# Integration Test: ConversationManagerService
"""
Integration test for ConversationManagerService with real database.
Tests the extracted service end-to-end with actual database operations.
"""

import pytest
import asyncio
from src.services.advisor_workflow.conversation_manager_service import ConversationManagerService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_manager_service_integration():
    """
    Integration test for ConversationManagerService.
    Requires test database to be running.
    """
    service = ConversationManagerService()
    test_advisor_id = "test_advisor_integration_123"
    
    try:
        # Test 1: Create session
        create_result = await service.create_session(
            advisor_id=test_advisor_id,
            title="Integration Test Session"
        )
        
        assert create_result["status"] == "success"
        session_id = create_result["session"]["session_id"]
        
        # Test 2: Save user message
        user_message_result = await service.save_message(
            session_id=session_id,
            message_type="user",
            content="Create a LinkedIn post about retirement planning"
        )
        
        assert user_message_result["status"] == "success"
        
        # Test 3: Save Warren message with metadata
        warren_metadata = {
            "sources_used": ["source1", "source2"],
            "generation_confidence": 0.85,
            "search_strategy": "vector",
            "total_sources": 5,
            "marketing_examples": 3,
            "compliance_rules": 2
        }
        
        warren_message_result = await service.save_message(
            session_id=session_id,
            message_type="warren",
            content="Here's your LinkedIn post about retirement planning...",
            metadata=warren_metadata
        )
        
        assert warren_message_result["status"] == "success"
        
        # Test 4: Get session messages
        messages_result = await service.get_session_messages(
            session_id=session_id,
            advisor_id=test_advisor_id
        )
        
        assert messages_result["status"] == "success"
        assert len(messages_result["messages"]) == 2
        
        # Verify Warren metadata was preserved
        warren_msg = next(msg for msg in messages_result["messages"] if msg["message_type"] == "warren")
        assert warren_msg["metadata"]["generation_confidence"] == 0.85
        assert warren_msg["metadata"]["search_strategy"] == "vector"
        
        # Test 5: Get advisor sessions
        sessions_result = await service.get_advisor_sessions(test_advisor_id)
        
        assert sessions_result["status"] == "success"
        assert len(sessions_result["sessions"]) >= 1
        
        # Test 6: Update session activity
        await service.update_session_activity(session_id)
        
        print("ConversationManagerService integration test completed successfully")
        
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_manager_service_error_handling():
    """Test ConversationManagerService error handling with real database."""
    service = ConversationManagerService()
    
    # Test access control - try to access another advisor's session
    result = await service.get_session_messages(
        session_id="nonexistent_session",
        advisor_id="wrong_advisor"
    )
    
    assert result["status"] == "error"
    assert "Session not found or access denied" in result["error"]
