# Test ContentLibraryService
"""
Comprehensive unit tests for ContentLibraryService.

Tests cover:
- Content saving with PostgreSQL enum handling
- Library retrieval with complex filtering and archive logic
- Content updates and modifications
- Statistics calculation with enum casting
- Error handling and access control
- JSON metadata serialization

Following Warren testing patterns with high coverage standards.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.content_library_service import ContentLibraryService
from src.models.advisor_workflow_models import ContentStatus
from src.models.refactored_database import ContentType, AudienceType


class TestContentLibraryService:
    """Test ContentLibraryService following Warren testing patterns."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ContentLibraryService()
    
    @pytest.fixture
    def sample_advisor_id(self):
        """Sample advisor ID for testing."""
        return "test_advisor_123"
    
    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for testing."""
        return {
            "title": "Test LinkedIn Post",
            "content_text": "Sample content for testing...",
            "content_type": "linkedin_post",
            "audience_type": "general_education",
            "source_session_id": "session_test_123",
            "source_message_id": 456,
            "advisor_notes": "Test notes",
            "intended_channels": ["linkedin", "twitter"]
        }
    
    @pytest.fixture
    def sample_content_item(self):
        """Sample content item mock for testing."""
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.title = "Test Content"
        mock_item.content_text = "Sample content..."
        mock_item.content_type = "linkedin_post"
        mock_item.audience_type = "general_education"
        mock_item.status = "draft"
        mock_item.advisor_notes = "Test notes"
        mock_item.intended_channels = '["linkedin", "twitter"]'
        mock_item.source_session_id = "session_test_123"
        mock_item.submitted_for_review_at = None
        mock_item.created_at = datetime.now()
        mock_item.updated_at = datetime.now()
        return mock_item

    # === CONTENT SAVING TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_save_content_success(self, mock_session_local, service, 
                                      sample_advisor_id, sample_content_data):
        """Test successful content saving with raw SQL."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the raw SQL result
        mock_result = MagicMock()
        mock_row = (1, datetime.now(), datetime.now())  # id, created_at, updated_at
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            **sample_content_data
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["id"] == 1
        assert result["content"]["title"] == sample_content_data["title"]
        assert result["content"]["content_type"] == "linkedin_post"
        assert result["content"]["audience_type"] == "general_education"
        assert result["content"]["status"] == "draft"
        assert result["content"]["source_session_id"] == "session_test_123"
        
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_save_content_defaults(self, mock_session_local, service, sample_advisor_id):
        """Test content saving with default values."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the raw SQL result
        mock_result = MagicMock()
        mock_row = (2, datetime.now(), datetime.now())
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Act - Minimal required parameters
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Test Title",
            content_text="Test content",
            content_type="newsletter"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["content_type"] == "newsletter"
        assert result["content"]["audience_type"] == "general_education"  # Default
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_save_content_with_channels(self, mock_session_local, service, sample_advisor_id):
        """Test content saving with intended channels JSON serialization."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Track the execute call to verify JSON serialization
        executed_queries = []
        
        async def capture_execute(query, params):
            executed_queries.append((query, params))
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (3, datetime.now(), datetime.now())
            return mock_result
        
        mock_db.execute.side_effect = capture_execute
        mock_db.commit = AsyncMock()
        
        channels = ["linkedin", "twitter", "facebook"]
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Multi-channel Post",
            content_text="Content for multiple channels",
            content_type="social_post",
            intended_channels=channels
        )
        
        # Assert
        assert result["status"] == "success"
        
        # Verify JSON serialization in SQL params
        assert len(executed_queries) == 1
        query_params = executed_queries[0][1]
        assert query_params['intended_channels'] == json.dumps(channels)
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_save_content_database_error(self, mock_session_local, service, sample_advisor_id):
        """Test content saving with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Test",
            content_text="Test content",
            content_type="linkedin_post"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()

    # === LIBRARY RETRIEVAL TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_success_default_filter(self, mock_session_local, service, 
                                                     sample_advisor_id, sample_content_item):
        """Test successful library retrieval with default filtering (exclude archived)."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock content query result
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = [sample_content_item]
        
        # Mock count query result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act
        result = await service.get_library(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert len(result["content"]) == 1
        assert result["total_count"] == 1
        assert result["has_more"] is False  # (0 + 50) >= 1
        
        content_item = result["content"][0]
        assert content_item["id"] == 1
        assert content_item["title"] == "Test Content"
        assert content_item["content_type"] == "linkedin_post"
        assert content_item["intended_channels"] == ["linkedin", "twitter"]  # JSON parsed
        
        # Should have called execute twice (content query + count query)
        assert mock_db.execute.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_archived_filter(self, mock_session_local, service, 
                                             sample_advisor_id, sample_content_item):
        """Test library retrieval with archived status filter."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Modify sample item to be archived
        sample_content_item.status = "archived"
        
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = [sample_content_item]
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act - Request archived content specifically
        result = await service.get_library(sample_advisor_id, status_filter="archived")
        
        # Assert
        assert result["status"] == "success"
        assert len(result["content"]) == 1
        assert result["content"][0]["status"] == "archived"
        
        # Should have called execute twice
        assert mock_db.execute.call_count == 2
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal') 
    async def test_get_library_specific_status_filter(self, mock_session_local, service, 
                                                    sample_advisor_id, sample_content_item):
        """Test library retrieval with specific status filter (not archived)."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Modify sample item to be approved
        sample_content_item.status = "approved"
        
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = [sample_content_item]
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act - Request approved content specifically
        result = await service.get_library(sample_advisor_id, status_filter="approved")
        
        # Assert
        assert result["status"] == "success"
        assert len(result["content"]) == 1
        assert result["content"][0]["status"] == "approved"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_content_type_filter(self, mock_session_local, service, 
                                                 sample_advisor_id, sample_content_item):
        """Test library retrieval with content type filter."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Modify sample item to be NEWSLETTER (valid ContentType enum)
        sample_content_item.content_type = "NEWSLETTER"
        
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = [sample_content_item]
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act - Use uppercase NEWSLETTER which is valid
        result = await service.get_library(
            sample_advisor_id, 
            content_type_filter="NEWSLETTER"
        )
        
        # Assert
        assert result["status"] == "success"
        assert len(result["content"]) == 1
        assert result["content"][0]["content_type"] == "NEWSLETTER"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_pagination(self, mock_session_local, service, sample_advisor_id):
        """Test library retrieval pagination logic."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = []  # No content on this page
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100  # Total content
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act - Request page 3 (offset 40, limit 20)
        result = await service.get_library(sample_advisor_id, limit=20, offset=40)
        
        # Assert
        assert result["status"] == "success"
        assert result["content"] == []
        assert result["total_count"] == 100
        assert result["has_more"] is True  # (40 + 20) < 100
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_empty_results(self, mock_session_local, service, sample_advisor_id):
        """Test library retrieval with no content."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act
        result = await service.get_library(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["content"] == []
        assert result["total_count"] == 0
        assert result["has_more"] is False
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_library_database_error(self, mock_session_local, service, sample_advisor_id):
        """Test library retrieval with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database query failed")
        
        # Act
        result = await service.get_library(sample_advisor_id)
        
        # Assert
        assert result["status"] == "error"
        assert "Database query failed" in result["error"]

    # === CONTENT UPDATE TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_update_content_success(self, mock_session_local, service, 
                                        sample_advisor_id, sample_content_item):
        """Test successful content update."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock content verification
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content_item
        
        # Mock updated content retrieval
        updated_item = sample_content_item
        updated_item.title = "Updated Title"
        updated_item.content_text = "Updated content text"
        updated_item.advisor_notes = "Updated notes"
        updated_item.updated_at = datetime.now()
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = updated_item
        
        mock_db.execute.side_effect = [
            mock_verify_result,  # Verification query
            None,                # Update query
            mock_updated_result  # Retrieve updated content
        ]
        mock_db.commit = AsyncMock()
        
        # Act
        result = await service.update_content(
            content_id=1,
            advisor_id=sample_advisor_id,
            title="Updated Title",
            content_text="Updated content text",
            advisor_notes="Updated notes"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["id"] == 1
        assert result["content"]["title"] == "Updated Title"
        assert result["content"]["content_text"] == "Updated content text"
        assert result["content"]["advisor_notes"] == "Updated notes"
        assert "updated_at" in result["content"]
        
        # Should have called execute 3 times + commit
        assert mock_db.execute.call_count == 3
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_update_content_access_denied(self, mock_session_local, service):
        """Test content update with access control denial."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock content not found (access denied)
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_verify_result
        
        # Act
        result = await service.update_content(
            content_id=999,
            advisor_id="wrong_advisor_id",
            title="Hacked Title"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Content not found or access denied" in result["error"]
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_update_content_partial_update(self, mock_session_local, service, 
                                                sample_advisor_id, sample_content_item):
        """Test content update with only some fields."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content_item
        
        # Only update title, keep other fields
        updated_item = sample_content_item
        updated_item.title = "New Title Only"
        
        mock_updated_result = MagicMock()
        mock_updated_result.scalar_one.return_value = updated_item
        
        mock_db.execute.side_effect = [mock_verify_result, None, mock_updated_result]
        mock_db.commit = AsyncMock()
        
        # Act - Only update title
        result = await service.update_content(
            content_id=1,
            advisor_id=sample_advisor_id,
            title="New Title Only"
            # No content_text or advisor_notes provided
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content"]["title"] == "New Title Only"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_update_content_database_error(self, mock_session_local, service, 
                                               sample_advisor_id, sample_content_item):
        """Test content update with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_verify_result = MagicMock()
        mock_verify_result.scalar_one_or_none.return_value = sample_content_item
        
        mock_db.execute.side_effect = [
            mock_verify_result,  # Verification succeeds
            Exception("Update failed")  # Update fails
        ]
        
        # Act
        result = await service.update_content(
            content_id=1,
            advisor_id=sample_advisor_id,
            title="Should Fail"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Update failed" in result["error"]
        mock_db.rollback.assert_called_once()

    # === STATISTICS TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_statistics_success(self, mock_session_local, service, sample_advisor_id):
        """Test successful statistics generation with enum casting."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock status count queries (one for each ContentStatus enum)
        status_counts = {
            "draft": 5,
            "ready_for_review": 1,
            "submitted": 2,
            "in_review": 1,
            "needs_revision": 1,
            "approved": 8,
            "rejected": 1,
            "distributed": 2,
            "archived": 3
        }
        
        # Mock the raw SQL queries for status counts
        mock_status_results = []
        for status in ContentStatus:
            mock_result = MagicMock()
            mock_result.scalar.return_value = status_counts.get(status.value, 0)
            mock_status_results.append(mock_result)
        
        # Mock total count query
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 24  # Sum of all status counts
        
        # Configure execute calls: 9 status queries + 1 total query = 10
        mock_db.execute.side_effect = mock_status_results + [mock_total_result]
        
        # Act
        result = await service.get_statistics(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["statistics"]["total_content"] == 24
        assert "content_by_status" in result["statistics"]
        assert "generated_at" in result["statistics"]
        
        # Check status counts
        status_data = result["statistics"]["content_by_status"]
        assert status_data["draft"] == 5
        assert status_data["submitted"] == 2
        assert status_data["approved"] == 8
        assert status_data["rejected"] == 1
        assert status_data["archived"] == 3
        
        # Should have called execute 10 times (9 status + 1 total)
        assert mock_db.execute.call_count == 10
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_statistics_empty_advisor(self, mock_session_local, service, sample_advisor_id):
        """Test statistics for advisor with no content."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock all status counts as 0
        mock_status_results = []
        for status in ContentStatus:
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0
            mock_status_results.append(mock_result)
        
        # Mock total count as 0
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = mock_status_results + [mock_total_result]
        
        # Act
        result = await service.get_statistics(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["statistics"]["total_content"] == 0
        
        # All status counts should be 0
        status_data = result["statistics"]["content_by_status"]
        for status in ContentStatus:
            assert status_data[status.value] == 0
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_get_statistics_database_error(self, mock_session_local, service, sample_advisor_id):
        """Test statistics generation with database error."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.get_statistics(sample_advisor_id)
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]

    # === EDGE CASE AND INTEGRATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization follows Warren pattern."""
        # Service should initialize with no dependencies
        assert service is not None
        assert hasattr(service, 'save_content')
        assert hasattr(service, 'get_library')
        assert hasattr(service, 'update_content')
        assert hasattr(service, 'get_statistics')
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_json_metadata_handling(self, mock_session_local, service, sample_advisor_id):
        """Test JSON serialization/deserialization for intended_channels."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Track the execute call to verify JSON handling
        executed_queries = []
        
        async def capture_execute(query, params):
            executed_queries.append((query, params))
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (1, datetime.now(), datetime.now())
            return mock_result
        
        mock_db.execute.side_effect = capture_execute
        mock_db.commit = AsyncMock()
        
        test_channels = ["linkedin", "twitter", "facebook", "newsletter"]
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Multi-channel Test",
            content_text="Content for testing JSON handling",
            content_type="social_post",
            intended_channels=test_channels
        )
        
        # Assert
        assert result["status"] == "success"
        
        # Verify JSON serialization
        assert len(executed_queries) == 1
        query_params = executed_queries[0][1]
        assert query_params['intended_channels'] == json.dumps(test_channels)
        
        # Verify correct JSON structure
        parsed_channels = json.loads(query_params['intended_channels'])
        assert parsed_channels == test_channels
        assert len(parsed_channels) == 4
        assert "linkedin" in parsed_channels
        assert "newsletter" in parsed_channels
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_enum_fallback_handling(self, mock_session_local, service, sample_advisor_id):
        """Test enum handling with fallback for invalid values."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock library query that should handle enum fallback
        mock_content_result = MagicMock()
        mock_content_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [mock_content_result, mock_count_result]
        
        # Act - Use an invalid status that should trigger fallback
        result = await service.get_library(
            sample_advisor_id, 
            status_filter="invalid_status"
        )
        
        # Assert - Should not crash, should use fallback logic
        assert result["status"] == "success"
        assert result["content"] == []
        assert result["total_count"] == 0
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_large_content_handling(self, mock_session_local, service, sample_advisor_id):
        """Test handling of large content text."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1, datetime.now(), datetime.now())
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Create large content (10KB+)
        large_content = "This is a very long piece of content. " * 300
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Large Content Test",
            content_text=large_content,
            content_type="blog_post"
        )
        
        # Assert
        assert result["status"] == "success"
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_special_characters_handling(self, mock_session_local, service, sample_advisor_id):
        """Test handling of special characters in content."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1, datetime.now(), datetime.now())
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Content with special characters
        special_content = "Content with émojis 🚀, quotes \"test\", and symbols & < > %"
        
        # Act
        result = await service.save_content(
            advisor_id=sample_advisor_id,
            title="Special Characters Test",
            content_text=special_content,
            content_type="social_post"
        )
        
        # Assert
        assert result["status"] == "success"
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.content_library_service.AsyncSessionLocal')
    async def test_concurrent_access_simulation(self, mock_session_local, service, sample_advisor_id):
        """Test simulation of concurrent content operations."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1, datetime.now(), datetime.now())
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Act - Simulate concurrent saves
        import asyncio
        
        async def save_content_task(title_suffix):
            return await service.save_content(
                advisor_id=sample_advisor_id,
                title=f"Concurrent Test {title_suffix}",
                content_text=f"Content {title_suffix}",
                content_type="linkedin_post"
            )
        
        # Run multiple save operations concurrently
        tasks = [save_content_task(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        # Assert - All should succeed
        for result in results:
            assert result["status"] == "success"
        
        # Should have called execute 3 times (once per task)
        assert mock_db.execute.call_count == 3
        assert mock_db.commit.call_count == 3
