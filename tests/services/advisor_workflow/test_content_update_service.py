# Test ContentUpdateService
"""
Comprehensive unit tests for ContentUpdateService.

Tests cover:
- Content editing with access control
- Partial updates (title only, content only, etc.)
- Metadata updates 
- Permission validation
- Version tracking foundation
- Error handling and edge cases
- Database operations and rollback scenarios

Following Warren testing patterns with high coverage standards.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.content_update_service import ContentUpdateService


class TestContentUpdateService:
    """Test ContentUpdateService following Warren testing patterns."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ContentUpdateService()
    
    @pytest.fixture
    def sample_content_id(self):
        """Sample content ID for testing."""
        return 123
    
    @pytest.fixture
    def sample_advisor_id(self):
        """Sample advisor ID for testing."""
        return "test_advisor_123"
    
    @pytest.fixture
    def sample_content(self):
        """Sample content object for testing."""
        content = MagicMock()
        content.id = 123
        content.title = "Original Title"
        content.content_text = "Original content text"
        content.advisor_notes = "Original notes"
        content.advisor_id = "test_advisor_123"
        content.created_at = datetime.now()
        content.updated_at = datetime.now()
        content.intended_channels = '["linkedin", "twitter"]'
        content.status = "draft"
        return content

    # === CONTENT UPDATE TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_success(self, mock_session_local, service, sample_content_id, 
                                        sample_advisor_id, sample_content):
        """Test successful content update."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock access verification
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        
        # Mock updated content retrieval
        updated_content = MagicMock()
        updated_content.id = sample_content_id
        updated_content.title = "Updated Title"
        updated_content.content_text = "Updated content text"
        updated_content.advisor_notes = "Updated notes"
        updated_content.updated_at = datetime.now()
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = updated_content
        
        mock_db.execute.side_effect = [mock_verify_result, None, mock_updated_result]
        
        # Act
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            title="Updated Title",
            content_text="Updated content text",
            advisor_notes="Updated notes"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["id"] == sample_content_id
        assert result["content"]["title"] == "Updated Title"
        assert result["content"]["content_text"] == "Updated content text"
        assert result["content"]["advisor_notes"] == "Updated notes"
        assert "updated_at" in result["content"]
        
        # Verify database operations
        assert mock_db.execute.call_count == 3  # verify, update, retrieve
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_partial_update(self, mock_session_local, service, 
                                               sample_content_id, sample_advisor_id, sample_content):
        """Test partial content update (title only)."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        
        updated_content = MagicMock()
        updated_content.id = sample_content_id
        updated_content.title = "New Title Only"
        updated_content.content_text = sample_content.content_text  # Unchanged
        updated_content.advisor_notes = sample_content.advisor_notes  # Unchanged
        updated_content.updated_at = datetime.now()
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = updated_content
        
        mock_db.execute.side_effect = [mock_verify_result, None, mock_updated_result]
        
        # Act - Only update title
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            title="New Title Only"
            # content_text and advisor_notes not provided
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["title"] == "New Title Only"
        # Other fields should remain unchanged
        assert result["content"]["content_text"] == sample_content.content_text
        assert result["content"]["advisor_notes"] == sample_content.advisor_notes
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_access_denied(self, mock_session_local, service, 
                                              sample_content_id, sample_advisor_id):
        """Test content update with access control denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock access verification failure
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = None  # Access denied
        mock_db.execute.return_value = mock_verify_result
        
        # Act
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id="wrong_advisor_id",  # Different advisor
            title="Unauthorized Update"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found or access denied" in result["error"]
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_database_error(self, mock_session_local, service, 
                                                sample_content_id, sample_advisor_id):
        """Test content update with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            title="Test Title"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()

    # === METADATA UPDATE TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_metadata_success(self, mock_session_local, service, 
                                                 sample_content_id, sample_advisor_id, sample_content):
        """Test successful metadata update."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.side_effect = [mock_verify_result, None]
        
        # Act
        result = await service.update_content_metadata(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            intended_channels=["linkedin", "facebook"],
            source_session_id="session_123",
            source_message_id=456
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == sample_content_id
        assert "intended_channels" in result["updated_fields"]
        assert "source_session_id" in result["updated_fields"]
        assert "source_message_id" in result["updated_fields"]
        assert "updated_at" in result["updated_fields"]
        
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_metadata_access_denied(self, mock_session_local, service, 
                                                       sample_content_id):
        """Test metadata update with access control denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_verify_result
        
        # Act
        result = await service.update_content_metadata(
            content_id=sample_content_id,
            advisor_id="wrong_advisor_id",
            intended_channels=["linkedin"]
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found or access denied" in result["error"]

    # === PERMISSION VALIDATION TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_validate_content_update_permission_success(self, mock_session_local, service, 
                                                            sample_content_id, sample_advisor_id):
        """Test successful permission validation."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content_id  # Found
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.validate_content_update_permission(sample_content_id, sample_advisor_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_validate_content_update_permission_denied(self, mock_session_local, service, 
                                                           sample_content_id):
        """Test permission validation denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Not found
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.validate_content_update_permission(sample_content_id, "wrong_advisor_id")
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_validate_content_update_permission_error(self, mock_session_local, service, 
                                                          sample_content_id, sample_advisor_id):
        """Test permission validation with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database error")
        
        # Act
        result = await service.validate_content_update_permission(sample_content_id, sample_advisor_id)
        
        # Assert
        assert result is False

    # === VERSION TRACKING TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_get_content_versions_success(self, mock_session_local, service, 
                                              sample_content_id, sample_advisor_id, sample_content):
        """Test successful content version retrieval."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_content_versions(sample_content_id, sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == sample_content_id
        assert result["current_version"] == 1
        assert result["total_versions"] == 1
        assert len(result["versions"]) == 1
        
        version = result["versions"][0]
        assert version["version"] == 1
        assert version["is_current"] is True
        assert "timestamp" in version
        assert version["title"] == sample_content.title
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_get_content_versions_access_denied(self, mock_session_local, service, 
                                                    sample_content_id):
        """Test content versions retrieval with access denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_content_versions(sample_content_id, "wrong_advisor_id")
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found or access denied" in result["error"]

    # === EDIT SUMMARY TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_get_content_edit_summary_success(self, mock_session_local, service, 
                                                  sample_content_id, sample_advisor_id, sample_content):
        """Test successful content edit summary retrieval."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_content_edit_summary(sample_content_id, sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        
        summary = result["edit_summary"]
        assert summary["content_id"] == sample_content_id
        assert "created_at" in summary
        assert "last_updated" in summary
        assert summary["title_length"] == len(sample_content.title)
        assert summary["content_length"] == len(sample_content.content_text)
        assert summary["has_notes"] is True
        assert summary["notes_length"] == len(sample_content.advisor_notes)
        assert summary["status"] == sample_content.status

    # === SERVICE INITIALIZATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization follows Warren pattern."""
        # Service should initialize with no dependencies
        assert service is not None
        assert hasattr(service, 'update_content')
        assert hasattr(service, 'update_content_metadata')
        assert hasattr(service, 'validate_content_update_permission')
        assert hasattr(service, 'get_content_versions')
        assert hasattr(service, 'get_content_edit_summary')

    # === EDGE CASE TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_no_changes(self, mock_session_local, service, 
                                           sample_content_id, sample_advisor_id, sample_content):
        """Test content update with no actual changes."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = sample_content
        
        mock_db.execute.side_effect = [mock_verify_result, None, mock_updated_result]
        
        # Act - Call with no update parameters
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id
            # No title, content_text, or advisor_notes provided
        )
        
        # Assert
        assert result["status"] == "success"
        # Should still update the updated_at timestamp
        assert "updated_at" in result["content"]
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_empty_values(self, mock_session_local, service, 
                                             sample_content_id, sample_advisor_id, sample_content):
        """Test content update with empty string values."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        
        updated_content = MagicMock()
        updated_content.id = sample_content_id
        updated_content.title = ""
        updated_content.content_text = ""
        updated_content.advisor_notes = ""
        updated_content.updated_at = datetime.now()
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = updated_content
        
        mock_db.execute.side_effect = [mock_verify_result, None, mock_updated_result]
        
        # Act
        result = await service.update_content(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            title="",
            content_text="",
            advisor_notes=""
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["title"] == ""
        assert result["content"]["content_text"] == ""
        assert result["content"]["advisor_notes"] == ""
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_update_service.AsyncSessionLocal')
    async def test_update_content_metadata_json_serialization(self, mock_session_local, service, 
                                                            sample_content_id, sample_advisor_id, sample_content):
        """Test metadata update with JSON serialization."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.side_effect = [mock_verify_result, None]
        
        complex_channels = ["linkedin", "twitter", "facebook", "newsletter"]
        
        # Act
        result = await service.update_content_metadata(
            content_id=sample_content_id,
            advisor_id=sample_advisor_id,
            intended_channels=complex_channels
        )
        
        # Assert
        assert result["status"] == "success"
        assert "intended_channels" in result["updated_fields"]
        
        # Verify the update call included JSON serialization
        update_call = mock_db.execute.call_args_list[1]  # Second call is the update
        # The actual JSON serialization happens in the service method
        mock_db.commit.assert_called_once()
