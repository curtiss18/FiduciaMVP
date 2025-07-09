# Test ConversationManagerService
"""
Comprehensive unit tests for ConversationManagerService.

Tests cover:
- Session creation and management
- Message saving with Warren metadata  
- Conversation retrieval with access control
- Session listing with pagination
- Error handling and edge cases
- Warren-specific metadata preservation

Following Warren testing patterns with high coverage standards.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.conversation_manager_service import ConversationManagerService


class TestConversationManagerService:
    """Test ConversationManagerService following Warren testing patterns."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ConversationManagerService()
    
    @pytest.fixture
    def sample_advisor_id(self):
        """Sample advisor ID for testing."""
        return "test_advisor_123"
    
    @pytest.fixture
    def sample_session_id(self):
        """Sample session ID for testing.""" 
        return "session_test_advisor_123_abcd1234"
    
    @pytest.fixture
    def sample_warren_metadata(self):
        """Sample Warren metadata for testing."""
        return {
            "sources_used": ["source1", "source2"],
            "generation_confidence": 0.85,
            "search_strategy": "vector",
            "total_sources": 5,
            "marketing_examples": 3,
            "compliance_rules": 2
        }

    # === SESSION CREATION TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_create_session_success(self, mock_session_local, service, sample_advisor_id):
        """Test successful session creation."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database operations with proper refresh simulation
        async def mock_refresh(obj):
            # Simulate database setting auto-generated fields
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 1
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
            if not hasattr(obj, 'message_count') or obj.message_count is None:
                obj.message_count = 0
        
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh.side_effect = mock_refresh
        
        # Act
        result = await service.create_session(sample_advisor_id, "Test Session")
        
        # Assert
        assert result["status"] == "success"
        assert result["session"]["advisor_id"] == sample_advisor_id
        assert result["session"]["title"] == "Test Session"
        assert f"session_{sample_advisor_id}_" in result["session"]["session_id"]
        assert "created_at" in result["session"]
        assert result["session"]["message_count"] == 0
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_create_session_auto_title(self, mock_session_local, service, sample_advisor_id):
        """Test session creation with auto-generated title."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database operations with proper refresh simulation
        async def mock_refresh(obj):
            # Simulate database setting auto-generated fields
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 1
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
            if not hasattr(obj, 'message_count') or obj.message_count is None:
                obj.message_count = 0
        
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh.side_effect = mock_refresh
        
        # Act - No title provided
        result = await service.create_session(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert "Chat Session" in result["session"]["title"]
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_create_session_database_error(self, mock_session_local, service, sample_advisor_id):
        """Test session creation with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.commit.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.create_session(sample_advisor_id)
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()

    # === MESSAGE SAVING TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_save_message_user_message(self, mock_session_local, service, sample_session_id):
        """Test saving user message (no metadata)."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database operations with proper refresh simulation
        async def mock_refresh(obj):
            # Simulate database setting auto-generated fields
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 1
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
        
        mock_db.add = AsyncMock()
        mock_db.execute = AsyncMock()  # For session update
        mock_db.commit = AsyncMock()
        mock_db.refresh.side_effect = mock_refresh
        
        # Act
        result = await service.save_message(
            session_id=sample_session_id,
            message_type="user",
            content="Create a LinkedIn post"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["message"]["message_type"] == "user"
        assert result["message"]["content"] == "Create a LinkedIn post"
        assert result["message"]["session_id"] == sample_session_id
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.execute.assert_called_once()  # Session update
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_save_message_warren_with_metadata(self, mock_session_local, service, 
                                                   sample_session_id, sample_warren_metadata):
        """Test saving Warren message with complete metadata."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database operations with proper refresh simulation
        async def mock_refresh(obj):
            # Simulate database setting auto-generated fields
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 2
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
        
        mock_db.add = AsyncMock()
        mock_db.execute = AsyncMock()  # For session update
        mock_db.commit = AsyncMock()
        mock_db.refresh.side_effect = mock_refresh
        
        # Act
        result = await service.save_message(
            session_id=sample_session_id,
            message_type="warren",
            content="Here's your LinkedIn post...",
            metadata=sample_warren_metadata
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["message"]["message_type"] == "warren"
        assert result["message"]["content"] == "Here's your LinkedIn post..."
        
        # Verify session activity update was called
        mock_db.execute.assert_called_once()
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_save_message_error_handling(self, mock_session_local, service, sample_session_id):
        """Test message saving with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.commit.side_effect = Exception("Database error")
        
        # Act
        result = await service.save_message(
            session_id=sample_session_id,
            message_type="user",
            content="Test message"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database error" in result["error"]
        mock_db.rollback.assert_called_once()

    # === MESSAGE RETRIEVAL TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_get_session_messages_success(self, mock_session_local, service, 
                                              sample_session_id, sample_advisor_id):
        """Test successful message retrieval with access control."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock session verification
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.session_id = sample_session_id
        mock_session.title = "Test Session"
        mock_session.message_count = 2
        mock_session.created_at = datetime.now()
        
        mock_session_result = MagicMock()
        mock_session_result.scalar_one_or_none.return_value = mock_session
        
        # Mock messages
        mock_user_message = MagicMock()
        mock_user_message.id = 1
        mock_user_message.message_type = "user"
        mock_user_message.content = "Create a LinkedIn post"
        mock_user_message.created_at = datetime.now()
        
        mock_warren_message = MagicMock()
        mock_warren_message.id = 2
        mock_warren_message.message_type = "warren"
        mock_warren_message.content = "Here's your LinkedIn post..."
        mock_warren_message.created_at = datetime.now()
        mock_warren_message.sources_used = '["source1", "source2"]'
        mock_warren_message.generation_confidence = 0.85
        mock_warren_message.search_strategy = "vector"
        mock_warren_message.total_sources = 5
        mock_warren_message.marketing_examples = 3
        mock_warren_message.compliance_rules = 2
        
        mock_messages_result = MagicMock()
        mock_messages_result.scalars.return_value.all.return_value = [
            mock_user_message, mock_warren_message
        ]
        
        # Configure database calls
        mock_db.execute.side_effect = [mock_session_result, mock_messages_result]
        
        # Act
        result = await service.get_session_messages(sample_session_id, sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["session"]["session_id"] == sample_session_id
        assert result["session"]["title"] == "Test Session"
        assert result["session"]["message_count"] == 2
        
        assert len(result["messages"]) == 2
        
        # Check user message
        user_msg = result["messages"][0]
        assert user_msg["message_type"] == "user"
        assert user_msg["content"] == "Create a LinkedIn post"
        assert user_msg["metadata"] is None
        
        # Check Warren message with metadata
        warren_msg = result["messages"][1]
        assert warren_msg["message_type"] == "warren"
        assert warren_msg["content"] == "Here's your LinkedIn post..."
        assert warren_msg["metadata"] is not None
        assert warren_msg["metadata"]["generation_confidence"] == 0.85
        assert warren_msg["metadata"]["search_strategy"] == "vector"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_get_session_messages_access_denied(self, mock_session_local, service, 
                                                    sample_session_id):
        """Test message retrieval with access control denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock session not found (access denied)
        mock_session_result = MagicMock()
        mock_session_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_session_result
        
        # Act
        result = await service.get_session_messages(sample_session_id, "wrong_advisor_id")
        
        # Assert
        assert result["status"] == "error"
        assert "Session not found or access denied" in result["error"]

    # === SESSION LISTING TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_get_advisor_sessions_success(self, mock_session_local, service, sample_advisor_id):
        """Test successful session listing with pagination."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock sessions
        mock_session1 = MagicMock()
        mock_session1.id = 1
        mock_session1.session_id = f"session_{sample_advisor_id}_abcd1234"
        mock_session1.title = "Session 1"
        mock_session1.message_count = 5
        mock_session1.created_at = datetime.now()
        mock_session1.last_activity = datetime.now()
        
        mock_session2 = MagicMock()
        mock_session2.id = 2
        mock_session2.session_id = f"session_{sample_advisor_id}_efgh5678"
        mock_session2.title = "Session 2"
        mock_session2.message_count = 3
        mock_session2.created_at = datetime.now()
        mock_session2.last_activity = datetime.now()
        
        mock_sessions_result = MagicMock()
        mock_sessions_result.scalars.return_value.all.return_value = [mock_session1, mock_session2]
        
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10  # Total sessions
        
        mock_db.execute.side_effect = [mock_sessions_result, mock_count_result]
        
        # Act
        result = await service.get_advisor_sessions(sample_advisor_id, limit=20, offset=0)
        
        # Assert
        assert result["status"] == "success"
        assert len(result["sessions"]) == 2
        assert result["total_count"] == 10
        assert result["has_more"] is False  # (0 + 20) >= 10
        
        # Check session data
        session1 = result["sessions"][0]
        assert session1["session_id"] == f"session_{sample_advisor_id}_abcd1234"
        assert session1["title"] == "Session 1"
        assert session1["message_count"] == 5
        assert "created_at" in session1
        assert "last_activity" in session1
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_get_advisor_sessions_pagination(self, mock_session_local, service, sample_advisor_id):
        """Test session listing pagination logic."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_sessions_result = MagicMock()
        mock_sessions_result.scalars.return_value.all.return_value = []  # No sessions on this page
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100  # Total sessions
        
        mock_db.execute.side_effect = [mock_sessions_result, mock_count_result]
        
        # Act - Request page 3 (offset 40, limit 20)
        result = await service.get_advisor_sessions(sample_advisor_id, limit=20, offset=40)
        
        # Assert
        assert result["status"] == "success"
        assert result["total_count"] == 100
        assert result["has_more"] is True  # (40 + 20) < 100
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_get_advisor_sessions_error(self, mock_session_local, service, sample_advisor_id):
        """Test session listing with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.get_advisor_sessions(sample_advisor_id)
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]

    # === SESSION ACTIVITY UPDATE TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_update_session_activity_success(self, mock_session_local, service, sample_session_id):
        """Test successful session activity update."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.return_value = None
        mock_db.commit.return_value = None
        
        # Act
        await service.update_session_activity(sample_session_id)
        
        # Assert - Should not raise exception
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_update_session_activity_error(self, mock_session_local, service, sample_session_id):
        """Test session activity update with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database error")
        
        # Act - Should not raise exception (graceful error handling)
        await service.update_session_activity(sample_session_id)
        
        # Assert
        mock_db.rollback.assert_called_once()

    # === EDGE CASE TESTS ===
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization follows Warren pattern."""
        # Service should initialize with no dependencies
        assert service is not None
        assert hasattr(service, 'create_session')
        assert hasattr(service, 'save_message')
        assert hasattr(service, 'get_session_messages')
        assert hasattr(service, 'get_advisor_sessions')
        assert hasattr(service, 'update_session_activity')
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_warren_metadata_json_handling(self, mock_session_local, service, 
                                                sample_session_id, sample_warren_metadata):
        """Test Warren metadata JSON serialization/deserialization."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Track what gets added to database
        added_objects = []
        
        def capture_add(message):
            added_objects.append(message)
            return None
        
        async def mock_refresh(obj):
            # Simulate database setting auto-generated fields
            if not hasattr(obj, 'id') or obj.id is None:
                obj.id = 1
            if not hasattr(obj, 'created_at') or obj.created_at is None:
                obj.created_at = datetime.now()
        
        # IMPORTANT: Use MagicMock (not AsyncMock) for db.add since it's synchronous in SQLAlchemy
        mock_db.add = MagicMock(side_effect=capture_add)
        mock_db.commit = AsyncMock()
        mock_db.refresh.side_effect = mock_refresh
        mock_db.execute = AsyncMock()
        
        # Act
        result = await service.save_message(
            session_id=sample_session_id,
            message_type="warren",
            content="Test content",
            metadata=sample_warren_metadata
        )
        
        # Assert
        assert result["status"] == "success"
        
        # Verify db.add was called
        mock_db.add.assert_called_once()
        
        # Verify we captured the message
        assert len(added_objects) == 1
        captured_message = added_objects[0]
        
        # Verify Warren metadata was properly serialized
        assert captured_message.sources_used == json.dumps(sample_warren_metadata["sources_used"])
        assert captured_message.generation_confidence == sample_warren_metadata["generation_confidence"]
        assert captured_message.search_strategy == sample_warren_metadata["search_strategy"]
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_empty_sessions_list(self, mock_session_local, service, sample_advisor_id):
        """Test handling of advisor with no sessions."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_sessions_result = MagicMock()
        mock_sessions_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [mock_sessions_result, mock_count_result]
        
        # Act
        result = await service.get_advisor_sessions(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["sessions"] == []
        assert result["total_count"] == 0
        assert result["has_more"] is False
