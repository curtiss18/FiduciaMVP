# Test NotificationCoordinator
"""
Comprehensive unit tests for NotificationCoordinator.

Tests cover:
- Review notification sending with email service integration
- Status update notifications for all status types
- Approval and rejection notifications
- Template management and formatting
- URL generation and validation
- Error handling and edge cases
- Email validation and data validation

Following Warren testing patterns with high coverage standards.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.notification_coordinator import NotificationCoordinator


class TestNotificationCoordinator:
    """Test NotificationCoordinator following Warren testing patterns."""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return NotificationCoordinator()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        content = MagicMock()
        content.id = 1
        content.title = "Test LinkedIn Post"
        content.content_type = "linkedin_post"
        content.advisor_id = "advisor_123"
        content.status = "submitted"
        return content
    
    @pytest.fixture
    def sample_cco_email(self):
        """Sample CCO email for testing."""
        return "cco@example.com"
    
    @pytest.fixture
    def sample_advisor_email(self):
        """Sample advisor email for testing."""
        return "advisor@example.com"
    
    @pytest.fixture
    def sample_review_token(self):
        """Sample review token for testing."""
        return "review_token_abc123"

    # === REVIEW NOTIFICATION TESTS ===
    
    @pytest.mark.asyncio
    @patch('src.services.email_service.email_service')
    async def test_send_review_notification_success(self, mock_email_service, service, 
                                                   sample_content, sample_cco_email, sample_review_token):
        """Test successful review notification sending."""
        # Arrange
        mock_email_service.send_review_notification = AsyncMock(return_value=True)
        
        # Act
        result = await service.send_review_notification(
            cco_email=sample_cco_email,
            content=sample_content,
            review_token=sample_review_token,
            notes="Please review urgently"
        )
        
        # Assert
        assert result is True
        mock_email_service.send_review_notification.assert_called_once_with(
            to_email=sample_cco_email,
            content_title=sample_content.title,
            content_type=sample_content.content_type,
            advisor_id=sample_content.advisor_id,
            review_url=f"http://localhost:3003/review/{sample_review_token}",
            notes="Please review urgently"
        )
    
    @pytest.mark.asyncio
    @patch('src.services.email_service.email_service')
    async def test_send_review_notification_email_failure(self, mock_email_service, service,
                                                         sample_content, sample_cco_email, sample_review_token):
        """Test review notification when email service fails."""
        # Arrange
        mock_email_service.send_review_notification = AsyncMock(return_value=False)
        
        # Act
        result = await service.send_review_notification(
            cco_email=sample_cco_email,
            content=sample_content,
            review_token=sample_review_token
        )
        
        # Assert
        assert result is False
        mock_email_service.send_review_notification.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.email_service.email_service')
    async def test_send_review_notification_exception(self, mock_email_service, service,
                                                     sample_content, sample_cco_email, sample_review_token):
        """Test review notification with exception handling."""
        # Arrange
        mock_email_service.send_review_notification = AsyncMock(
            side_effect=Exception("Email service unavailable")
        )
        
        # Act
        result = await service.send_review_notification(
            cco_email=sample_cco_email,
            content=sample_content,
            review_token=sample_review_token
        )
        
        # Assert
        assert result is False

    # === STATUS UPDATE NOTIFICATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_send_status_update_notification_approved(self, service, sample_content, sample_advisor_email):
        """Test status update notification for approved content."""
        # Arrange
        sample_content.status = "approved"
        
        # Act
        result = await service.send_status_update_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            new_status="approved",
            reviewer_notes="Great work!"
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_status_update_notification_rejected(self, service, sample_content, sample_advisor_email):
        """Test status update notification for rejected content."""
        # Arrange
        sample_content.status = "rejected"
        
        # Act
        result = await service.send_status_update_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            new_status="rejected",
            reviewer_notes="Please revise the disclaimer language."
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_status_update_notification_generic(self, service, sample_content, sample_advisor_email):
        """Test status update notification for generic status change."""
        # Arrange
        sample_content.status = "draft"
        
        # Act
        result = await service.send_status_update_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            new_status="draft",
            reviewer_notes="Returned to draft for editing"
        )
        
        # Assert
        assert result is True

    # === APPROVAL NOTIFICATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_send_approval_notification_success(self, service, sample_content, sample_advisor_email):
        """Test successful approval notification."""
        # Act
        result = await service.send_approval_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            approval_notes="Excellent content, approved for all channels."
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_approval_notification_no_notes(self, service, sample_content, sample_advisor_email):
        """Test approval notification without approval notes."""
        # Act
        result = await service.send_approval_notification(
            advisor_email=sample_advisor_email,
            content=sample_content
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_approval_notification_exception(self, service, sample_advisor_email):
        """Test approval notification with exception handling."""
        # Arrange - Invalid content object
        invalid_content = None
        
        # Act
        result = await service.send_approval_notification(
            advisor_email=sample_advisor_email,
            content=invalid_content
        )
        
        # Assert
        assert result is False

    # === REJECTION NOTIFICATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_send_rejection_notification_success(self, service, sample_content, sample_advisor_email):
        """Test successful rejection notification."""
        # Act
        result = await service.send_rejection_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            rejection_reason="Content contains prohibited language. Please revise section 2."
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_rejection_notification_empty_reason(self, service, sample_content, sample_advisor_email):
        """Test rejection notification with empty reason."""
        # Act
        result = await service.send_rejection_notification(
            advisor_email=sample_advisor_email,
            content=sample_content,
            rejection_reason=""
        )
        
        # Assert
        assert result is True

    # === URL GENERATION TESTS ===
    
    def test_build_review_url(self, service, sample_review_token):
        """Test review URL generation."""
        # Act
        url = service.build_review_url(sample_review_token)
        
        # Assert
        expected_url = f"http://localhost:3003/review/{sample_review_token}"
        assert url == expected_url
    
    def test_build_review_url_special_characters(self, service):
        """Test review URL generation with special characters."""
        # Arrange
        special_token = "token_with_special-chars_123"
        
        # Act
        url = service.build_review_url(special_token)
        
        # Assert
        expected_url = f"http://localhost:3003/review/{special_token}"
        assert url == expected_url

    # === TEMPLATE MANAGEMENT TESTS ===
    
    def test_get_notification_template_review_request(self, service):
        """Test getting review request template."""
        # Act
        template = service.get_notification_template('review_request')
        
        # Assert
        assert 'subject' in template
        assert 'body' in template
        assert 'Content Review Required' in template['subject']
        assert '{content_title}' in template['subject']
        assert '{review_url}' in template['body']
    
    def test_get_notification_template_approval(self, service):
        """Test getting approval notification template."""
        # Act
        template = service.get_notification_template('approval_notification')
        
        # Assert
        assert 'subject' in template
        assert 'body' in template
        assert 'Content Approved' in template['subject']
        assert '{advisor_name}' in template['body']
        assert '{approval_notes}' in template['body']
    
    def test_get_notification_template_rejection(self, service):
        """Test getting rejection notification template."""
        # Act
        template = service.get_notification_template('rejection_notification')
        
        # Assert
        assert 'subject' in template
        assert 'body' in template
        assert 'Requires Revision' in template['subject']
        assert '{rejection_reason}' in template['body']
    
    def test_get_notification_template_status_update(self, service):
        """Test getting status update templates."""
        # Test submitted status
        submitted_template = service.get_notification_template('status_update_submitted')
        assert 'Submitted for Review' in submitted_template['subject']
        
        # Test draft status
        draft_template = service.get_notification_template('status_update_draft')
        assert 'Returned to Draft' in draft_template['subject']
        
        # Test archived status
        archived_template = service.get_notification_template('status_update_archived')
        assert 'Archived' in archived_template['subject']
    
    def test_get_notification_template_unknown_type(self, service):
        """Test getting template for unknown notification type."""
        # Act
        template = service.get_notification_template('unknown_type')
        
        # Assert
        assert 'subject' in template
        assert 'body' in template
        assert template['subject'] == 'Fiducia Platform Notification'

    # === REMINDER NOTIFICATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_send_reminder_notification_success(self, service, sample_content, 
                                                     sample_cco_email, sample_review_token):
        """Test successful reminder notification."""
        # Act
        result = await service.send_reminder_notification(
            cco_email=sample_cco_email,
            content=sample_content,
            review_token=sample_review_token,
            days_pending=3
        )
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_reminder_notification_exception(self, service, sample_cco_email, sample_review_token):
        """Test reminder notification with exception handling."""
        # Arrange - Invalid content
        invalid_content = None
        
        # Act
        result = await service.send_reminder_notification(
            cco_email=sample_cco_email,
            content=invalid_content,
            review_token=sample_review_token,
            days_pending=7
        )
        
        # Assert
        assert result is False

    # === VALIDATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_validate_notification_data_success(self, service, sample_content):
        """Test successful notification data validation."""
        # Act
        result = await service.validate_notification_data(
            notification_type='review_request',
            recipient_email='valid@example.com',
            content=sample_content
        )
        
        # Assert
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_notification_data_invalid_email(self, service, sample_content):
        """Test validation with invalid email address."""
        # Act
        result = await service.validate_notification_data(
            notification_type='review_request',
            recipient_email='invalid-email',
            content=sample_content
        )
        
        # Assert
        assert result['valid'] is False
        assert 'Invalid recipient email address' in result['errors']
    
    @pytest.mark.asyncio
    async def test_validate_notification_data_missing_content(self, service):
        """Test validation with missing content."""
        # Act
        result = await service.validate_notification_data(
            notification_type='review_request',
            recipient_email='valid@example.com',
            content=None
        )
        
        # Assert
        assert result['valid'] is False
        assert 'Content object is required' in result['errors']
    
    @pytest.mark.asyncio
    async def test_validate_notification_data_invalid_type(self, service, sample_content):
        """Test validation with invalid notification type."""
        # Act
        result = await service.validate_notification_data(
            notification_type='invalid_type',
            recipient_email='valid@example.com',
            content=sample_content
        )
        
        # Assert
        assert result['valid'] is False
        assert any('Invalid notification type' in error for error in result['errors'])
    
    @pytest.mark.asyncio
    async def test_validate_notification_data_multiple_errors(self, service):
        """Test validation with multiple errors."""
        # Act
        result = await service.validate_notification_data(
            notification_type='invalid_type',
            recipient_email='invalid-email',
            content=None
        )
        
        # Assert
        assert result['valid'] is False
        assert len(result['errors']) == 3
        assert 'Invalid recipient email address' in result['errors']
        assert 'Content object is required' in result['errors']
        assert any('Invalid notification type' in error for error in result['errors'])

    # === EDGE CASE TESTS ===
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization follows Warren pattern."""
        # Service should initialize with no dependencies
        assert service is not None
        assert hasattr(service, 'send_review_notification')
        assert hasattr(service, 'send_status_update_notification')
        assert hasattr(service, 'send_approval_notification')
        assert hasattr(service, 'send_rejection_notification')
        assert hasattr(service, 'build_review_url')
        assert hasattr(service, 'get_notification_template')
    
    def test_template_formatting_placeholders(self, service):
        """Test that all templates have consistent placeholder formatting."""
        templates = [
            'review_request', 'approval_notification', 'rejection_notification',
            'status_update_submitted', 'status_update_draft', 'status_update_archived'
        ]
        
        for template_type in templates:
            template = service.get_notification_template(template_type)
            
            # All templates should have subject and body
            assert 'subject' in template
            assert 'body' in template
            
            # Templates should contain proper placeholder formatting
            assert '{' in template['subject'] or '{' in template['body']
    
    @pytest.mark.asyncio
    async def test_notification_methods_handle_none_content(self, service, sample_advisor_email):
        """Test all notification methods handle None content gracefully."""
        # Test approval notification
        result1 = await service.send_approval_notification(sample_advisor_email, None)
        assert result1 is False
        
        # Test rejection notification
        result2 = await service.send_rejection_notification(sample_advisor_email, None, "test reason")
        assert result2 is False
        
        # Test status update notification
        result3 = await service.send_status_update_notification(sample_advisor_email, None, "approved")
        assert result3 is False
    
    def test_build_review_url_empty_token(self, service):
        """Test review URL generation with empty token."""
        # Act
        url = service.build_review_url("")
        
        # Assert
        expected_url = "http://localhost:3003/review/"
        assert url == expected_url
