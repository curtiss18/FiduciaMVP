import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from src.services.advisor_workflow.compliance_workflow_service import ComplianceWorkflowService


class TestComplianceWorkflowService:
    """Comprehensive tests for ComplianceWorkflowService following Warren pattern."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ComplianceWorkflowService()
    
    @pytest.fixture
    def sample_content(self):
        """Create sample advisor content for testing."""
        content = MagicMock()
        content.id = 1
        content.advisor_id = "advisor_123"
        content.title = "Test LinkedIn Post"
        content.content_text = "Sample LinkedIn content for compliance review"
        content.content_type = "linkedin_post"
        content.status = MagicMock()
        content.status.value = "draft"
        content.cco_review_status = None
        content.cco_email = None
        content.submitted_for_review_at = None
        content.reviewed_by = None
        content.reviewed_at = None
        content.cco_review_notes = None
        content.created_at = datetime.now()
        content.updated_at = datetime.now()
        return content
    
    # ===== SUBMIT FOR REVIEW TESTS =====
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_submit_for_review_success(self, mock_session_local, service, sample_content):
        """Test successful content submission for review."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        with patch.object(service, 'generate_review_token', return_value="test_token_123") as mock_token, \
             patch.object(service, '_send_review_notification', return_value=True) as mock_email:
            
            # Act
            result = await service.submit_for_review(
                content_id=1,
                advisor_id="advisor_123",
                cco_email="cco@example.com",
                notes="Please review this content"
            )
            
            # Assert
            assert result["status"] == "success"
            assert result["content_id"] == 1
            assert result["review_token"] == "test_token_123"
            assert result["cco_email"] == "cco@example.com"
            assert result["email_sent"] is True
            assert "submitted_at" in result
            
            # Verify database operations
            assert mock_db.execute.call_count == 2  # SELECT + UPDATE
            mock_db.commit.assert_called_once()
            
            # Verify token generation and email sending
            mock_token.assert_called_once_with(1, "cco@example.com")
            mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_submit_for_review_content_not_found(self, mock_session_local, service):
        """Test submission fails when content not found."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database result to return None (content not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.submit_for_review(
            content_id=999,
            advisor_id="advisor_123",
            cco_email="cco@example.com"
        )
        
        # Assert
        assert result["status"] == "error"
        assert result["error"] == "Content not found or access denied"
        
        # Verify no database updates
        assert mock_db.execute.call_count == 1  # Only SELECT
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_submit_for_review_database_error(self, mock_session_local, service):
        """Test submission handles database errors gracefully."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.submit_for_review(
            content_id=1,
            advisor_id="advisor_123",
            cco_email="cco@example.com"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_submit_for_review_email_failure(self, mock_session_local, service, sample_content):
        """Test submission handles email sending failures gracefully."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        with patch.object(service, 'generate_review_token', return_value="test_token_123"), \
             patch.object(service, '_send_review_notification', return_value=False) as mock_email:
            
            # Act
            result = await service.submit_for_review(
                content_id=1,
                advisor_id="advisor_123",
                cco_email="cco@example.com"
            )
            
            # Assert
            assert result["status"] == "success"  # Submission succeeds even if email fails
            assert result["email_sent"] is False
            assert result["content_id"] == 1
            
            # Database should still be updated
            mock_db.commit.assert_called_once()
    
    # ===== UPDATE REVIEW STATUS TESTS =====
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_update_review_status_success(self, mock_session_local, service, sample_content):
        """Test successful review status update."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.update_review_status(
            content_id=1,
            new_status="approved",
            reviewer="cco@example.com",
            notes="Content approved for distribution"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == 1
        assert result["new_status"] == "approved"
        assert result["reviewer"] == "cco@example.com"
        assert "reviewed_at" in result
        
        # Verify database operations
        assert mock_db.execute.call_count == 2  # SELECT + UPDATE
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_update_review_status_without_notes(self, mock_session_local, service, sample_content):
        """Test review status update without notes."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.update_review_status(
            content_id=1,
            new_status="rejected",
            reviewer="cco@example.com"
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["content_id"] == 1
        assert result["new_status"] == "rejected"
        assert result["reviewer"] == "cco@example.com"
        
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_update_review_status_content_not_found(self, mock_session_local, service):
        """Test review status update fails when content not found."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Mock the database result to return None (content not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.update_review_status(
            content_id=999,
            new_status="approved",
            reviewer="cco@example.com"
        )
        
        # Assert
        assert result["status"] == "error"
        assert result["error"] == "Content not found"
        
        # Verify no database updates
        assert mock_db.execute.call_count == 1  # Only SELECT
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_update_review_status_database_error(self, mock_session_local, service):
        """Test review status update handles database errors."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database update failed")
        
        # Act
        result = await service.update_review_status(
            content_id=1,
            new_status="approved",
            reviewer="cco@example.com"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Database update failed" in result["error"]
        mock_db.rollback.assert_called_once()
    
    # ===== GET REVIEW HISTORY TESTS =====
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_get_review_history_success(self, mock_session_local, service, sample_content):
        """Test successful review history retrieval."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Set up reviewed content
        sample_content.cco_review_status = "approved"
        sample_content.cco_email = "cco@example.com"
        sample_content.submitted_for_review_at = datetime.now()
        sample_content.reviewed_by = "cco@example.com"
        sample_content.reviewed_at = datetime.now()
        sample_content.cco_review_notes = "Content looks good"
        
        # Use MagicMock for the result to avoid coroutine issues
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_review_history(content_id=1)
        
        # Assert
        assert result["status"] == "success"
        history = result["review_history"]
        assert history["content_id"] == 1
        assert history["current_status"] == "draft"
        assert history["cco_review_status"] == "approved"
        assert history["cco_email"] == "cco@example.com"
        assert history["reviewed_by"] == "cco@example.com"
        assert history["cco_review_notes"] == "Content looks good"
        assert "submitted_for_review_at" in history
        assert "reviewed_at" in history
        assert "created_at" in history
        assert "updated_at" in history
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_get_review_history_content_not_found(self, mock_session_local, service):
        """Test review history retrieval fails when content not found."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Use MagicMock for the result to avoid coroutine issues
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_review_history(content_id=999)
        
        # Assert
        assert result["status"] == "error"
        assert result["error"] == "Content not found"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_get_review_history_with_null_values(self, mock_session_local, service, sample_content):
        """Test review history with null/None values."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Set up content with null review fields
        sample_content.cco_review_status = None
        sample_content.cco_email = None
        sample_content.submitted_for_review_at = None
        sample_content.reviewed_by = None
        sample_content.reviewed_at = None
        sample_content.cco_review_notes = None
        
        # Use MagicMock for the result to avoid coroutine issues
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        # Act
        result = await service.get_review_history(content_id=1)
        
        # Assert
        assert result["status"] == "success"
        history = result["review_history"]
        assert history["content_id"] == 1
        assert history["cco_review_status"] is None
        assert history["cco_email"] is None
        assert history["submitted_for_review_at"] is None
        assert history["reviewed_by"] is None
        assert history["reviewed_at"] is None
        assert history["cco_review_notes"] is None
    
    # ===== TOKEN GENERATION TESTS =====
    
    def test_generate_review_token_success(self, service):
        """Test successful review token generation."""
        # Arrange & Act
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.generate_review_token.return_value = "secure_token_abc123"
            
            token = service.generate_review_token(content_id=1, cco_email="cco@example.com")
            
            # Assert
            assert token == "secure_token_abc123"
            mock_token_manager.generate_review_token.assert_called_once_with(
                content_id=1,
                cco_email="cco@example.com",
                expires_hours=24 * 7
            )
    
    def test_generate_review_token_fallback(self, service):
        """Test token generation fallback when token_manager fails."""
        # Arrange & Act
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.generate_review_token.side_effect = Exception("Token service unavailable")
            
            token = service.generate_review_token(content_id=1, cco_email="cco@example.com")
            
            # Assert
            assert token.startswith("review_1_")
            assert len(token) == 17  # "review_1_" + 8 hex chars
    
    # ===== TOKEN VALIDATION TESTS =====
    
    def test_validate_review_access_success(self, service):
        """Test successful token validation."""
        # Arrange & Act
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.validate_review_token.return_value = {
                "valid": True,
                "content_id": 1,
                "cco_email": "cco@example.com",
                "expires_at": "2025-07-16T12:00:00"
            }
            
            result = service.validate_review_access("valid_token_123")
            
            # Assert
            assert result["status"] == "success"
            assert result["valid"] is True
            assert result["content_id"] == 1
            assert result["cco_email"] == "cco@example.com"
            assert result["expires_at"] == "2025-07-16T12:00:00"
    
    def test_validate_review_access_invalid_token(self, service):
        """Test validation with invalid token."""
        # Arrange & Act
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.validate_review_token.return_value = {
                "valid": False,
                "error": "Token expired"
            }
            
            result = service.validate_review_access("expired_token_123")
            
            # Assert
            assert result["status"] == "error"
            assert result["valid"] is False
            assert result["error"] == "Token expired"
    
    def test_validate_review_access_service_error(self, service):
        """Test validation when token service fails."""
        # Arrange & Act
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.validate_review_token.side_effect = Exception("Token service down")
            
            result = service.validate_review_access("any_token")
            
            # Assert
            assert result["status"] == "error"
            assert result["valid"] is False
            assert result["error"] == "Token validation failed"
    
    # ===== EMAIL NOTIFICATION TESTS =====
    
    @pytest.mark.asyncio
    async def test_send_review_notification_success(self, service, sample_content):
        """Test successful email notification sending."""
        # Arrange & Act
        with patch('src.services.email_service.email_service') as mock_email_service:
            # Make the mock return a coroutine that resolves to True
            mock_email_service.send_review_notification = AsyncMock(return_value=True)
            
            result = await service._send_review_notification(
                cco_email="cco@example.com",
                content=sample_content,
                review_token="test_token_123",
                notes="Please review this content"
            )
            
            # Assert
            assert result is True
            mock_email_service.send_review_notification.assert_called_once_with(
                to_email="cco@example.com",
                content_title="Test LinkedIn Post",
                content_type="linkedin_post",
                advisor_id="advisor_123",
                review_url="http://localhost:3003/review/test_token_123",
                notes="Please review this content"
            )
    
    @pytest.mark.asyncio
    async def test_send_review_notification_without_notes(self, service, sample_content):
        """Test email notification without notes."""
        # Arrange & Act
        with patch('src.services.email_service.email_service') as mock_email_service:
            # Make the mock return a coroutine that resolves to True
            mock_email_service.send_review_notification = AsyncMock(return_value=True)
            
            result = await service._send_review_notification(
                cco_email="cco@example.com",
                content=sample_content,
                review_token="test_token_123"
            )
            
            # Assert
            assert result is True
            mock_email_service.send_review_notification.assert_called_once_with(
                to_email="cco@example.com",
                content_title="Test LinkedIn Post",
                content_type="linkedin_post",
                advisor_id="advisor_123",
                review_url="http://localhost:3003/review/test_token_123",
                notes=None
            )
    
    @pytest.mark.asyncio
    async def test_send_review_notification_email_failure(self, service, sample_content):
        """Test email notification handles sending failures."""
        # Arrange & Act
        with patch('src.services.email_service.email_service') as mock_email_service:
            mock_email_service.send_review_notification.return_value = False
            
            result = await service._send_review_notification(
                cco_email="cco@example.com",
                content=sample_content,
                review_token="test_token_123"
            )
            
            # Assert
            assert result is False
    @pytest.mark.asyncio
    async def test_send_review_notification_service_exception(self, service, sample_content):
        """Test email notification handles service exceptions."""
        # Arrange & Act
        with patch('src.services.email_service.email_service') as mock_email_service:
            mock_email_service.send_review_notification.side_effect = Exception("Email service unavailable")
            
            result = await service._send_review_notification(
                cco_email="cco@example.com",
                content=sample_content,
                review_token="test_token_123"
            )
            
            # Assert
            assert result is False
    
    # ===== EDGE CASE AND ERROR HANDLING TESTS =====
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_get_review_history_database_error(self, mock_session_local, service):
        """Test review history handles database errors."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database query failed")
        
        # Act
        result = await service.get_review_history(content_id=1)
        
        # Assert
        assert result["status"] == "error"
        assert "Database query failed" in result["error"]
    
    def test_validate_review_access_sync_method(self, service):
        """Test that validate_review_access is a sync method (not async)."""
        # This test ensures the method signature is correct
        # The actual validation is tested in other token validation tests
        
        with patch('src.services.token_manager.token_manager') as mock_token_manager:
            mock_token_manager.validate_review_token.return_value = {"valid": True, "content_id": 1}
            
            # Act - should not need await
            result = service.validate_review_access("test_token")
            
            # Assert - method should return immediately
            assert result["status"] == "success"
    
    def test_service_initialization(self, service):
        """Test service initializes correctly with Warren pattern."""
        # Service should initialize without dependencies
        assert service is not None
        assert hasattr(service, 'submit_for_review')
        assert hasattr(service, 'update_review_status')
        assert hasattr(service, 'get_review_history')
        assert hasattr(service, 'generate_review_token')
        assert hasattr(service, 'validate_review_access')
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_submit_for_review_access_control(self, mock_session_local, service):
        """Test submission enforces access control (content belongs to advisor)."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # The WHERE clause with advisor_id AND content_id will return None
        # when advisor tries to access content that doesn't belong to them
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Access denied
        mock_db.execute.return_value = mock_result
        
        # Act - try to submit content as wrong advisor
        result = await service.submit_for_review(
            content_id=1,
            advisor_id="advisor_123",  # Different from content.advisor_id
            cco_email="cco@example.com"
        )
        
        # Assert - should fail due to access control
        assert result["status"] == "error"
        assert result["error"] == "Content not found or access denied"
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.compliance_workflow_service.AsyncSessionLocal')
    async def test_complex_review_workflow_integration(self, mock_session_local, service, sample_content):
        """Test complete review workflow: submit -> update status -> get history."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        # Use MagicMock for the result to avoid coroutine issues
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        mock_db.execute.return_value = mock_result
        
        with patch.object(service, 'generate_review_token', return_value="workflow_token_123"), \
             patch.object(service, '_send_review_notification', return_value=True):
            
            # Act 1: Submit for review
            submit_result = await service.submit_for_review(
                content_id=1,
                advisor_id="advisor_123",
                cco_email="cco@example.com",
                notes="Initial submission"
            )
            
            # Act 2: Update review status
            update_result = await service.update_review_status(
                content_id=1,
                new_status="approved",
                reviewer="cco@example.com",
                notes="Approved after review"
            )
            
            # Act 3: Get review history
            history_result = await service.get_review_history(content_id=1)
            
            # Assert all operations succeeded
            assert submit_result["status"] == "success"
            assert update_result["status"] == "success"
            assert history_result["status"] == "success"
            
            # Verify database was called multiple times
            assert mock_db.execute.call_count >= 5  # Multiple operations across 3 methods
            assert mock_db.commit.call_count == 2   # submit and update operations
