# Test WorkflowOrchestrator
"""
Comprehensive unit tests for WorkflowOrchestrator.

Tests cover:
- Service delegation and coordination
- Public interface backward compatibility
- Cross-cutting concerns (logging, error handling)
- Dependency injection for testing
- Service health monitoring
- Workflow metrics aggregation
- Error handling and fallback strategies

Following Warren testing patterns with high coverage standards.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.advisor_workflow.workflow_orchestrator import WorkflowOrchestrator


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator following Warren testing patterns."""
    
    @pytest.fixture
    def mock_conversation_manager(self):
        """Mock ConversationManagerService for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_content_library(self):
        """Mock ContentLibraryService for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_compliance_workflow(self):
        """Mock ComplianceWorkflowService for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_content_status_manager(self):
        """Mock ContentStatusManager for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_notification_coordinator(self):
        """Mock NotificationCoordinator for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_content_update_service(self):
        """Mock ContentUpdateService for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def orchestrator(self, mock_conversation_manager, mock_content_library, 
                    mock_compliance_workflow, mock_content_status_manager,
                    mock_notification_coordinator, mock_content_update_service):
        """Create WorkflowOrchestrator with all mocked dependencies."""
        return WorkflowOrchestrator(
            conversation_manager=mock_conversation_manager,
            content_library=mock_content_library,
            compliance_workflow=mock_compliance_workflow,
            content_status_manager=mock_content_status_manager,
            notification_coordinator=mock_notification_coordinator,
            content_update_service=mock_content_update_service
        )
    
    @pytest.fixture
    def sample_advisor_id(self):
        """Sample advisor ID for testing."""
        return "test_advisor_123"
    
    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for testing."""
        return {
            "title": "Test LinkedIn Post",
            "content_text": "This is a test post about financial planning...",
            "content_type": "linkedin_post",
            "audience_type": "general_education"
        }
    
    # ===================================================================
    # INITIALIZATION TESTS
    # ===================================================================
    
    def test_orchestrator_initialization_with_mocks(self, orchestrator):
        """Test orchestrator initializes correctly with mocked dependencies."""
        assert orchestrator.conversation_manager is not None
        assert orchestrator.content_library is not None
        assert orchestrator.compliance_workflow is not None
        assert orchestrator.content_status_manager is not None
        assert orchestrator.notification_coordinator is not None
        assert orchestrator.content_update_service is not None
    
    def test_orchestrator_initialization_with_defaults(self):
        """Test orchestrator initializes with default services when no dependencies provided."""
        # This will use the real services, but we're just testing initialization
        orchestrator = WorkflowOrchestrator()
        assert orchestrator.conversation_manager is not None
        assert orchestrator.content_library is not None
        assert orchestrator.compliance_workflow is not None
        assert orchestrator.content_status_manager is not None
        assert orchestrator.notification_coordinator is not None
        assert orchestrator.content_update_service is not None
    
    # ===================================================================
    # CONVERSATION MANAGEMENT DELEGATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_create_advisor_session_success(self, orchestrator, mock_conversation_manager, sample_advisor_id):
        """Test successful session creation delegation."""
        # Arrange
        expected_result = {
            "status": "success",
            "session": {
                "id": 1,
                "session_id": "session_test_advisor_123_abcd1234",
                "advisor_id": sample_advisor_id,
                "title": "Test Session"
            }
        }
        mock_conversation_manager.create_session.return_value = expected_result
        
        # Act
        result = await orchestrator.create_advisor_session(sample_advisor_id, "Test Session")
        
        # Assert
        assert result == expected_result
        mock_conversation_manager.create_session.assert_called_once_with(sample_advisor_id, "Test Session")
    
    @pytest.mark.asyncio
    async def test_create_advisor_session_error_handling(self, orchestrator, mock_conversation_manager, sample_advisor_id):
        """Test session creation error handling."""
        # Arrange
        mock_conversation_manager.create_session.side_effect = Exception("Database connection failed")
        
        # Act
        result = await orchestrator.create_advisor_session(sample_advisor_id)
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_conversation_manager.create_session.assert_called_once_with(sample_advisor_id, None)
    
    @pytest.mark.asyncio
    async def test_save_warren_message_success(self, orchestrator, mock_conversation_manager):
        """Test successful Warren message saving delegation."""
        # Arrange
        session_id = "session_test_123"
        message_type = "warren"
        content = "Here's your compliant content..."
        metadata = {"sources_used": ["source1"], "generation_confidence": 0.85}
        
        expected_result = {
            "status": "success",
            "message": {"id": 1, "content": content}
        }
        mock_conversation_manager.save_message.return_value = expected_result
        
        # Act
        result = await orchestrator.save_warren_message(session_id, message_type, content, metadata)
        
        # Assert
        assert result == expected_result
        mock_conversation_manager.save_message.assert_called_once_with(session_id, message_type, content, metadata)
    
    @pytest.mark.asyncio
    async def test_get_session_messages_success(self, orchestrator, mock_conversation_manager, sample_advisor_id):
        """Test successful session messages retrieval."""
        # Arrange
        session_id = "session_test_123"
        expected_result = {
            "status": "success",
            "messages": [
                {"id": 1, "message_type": "user", "content": "Hello Warren"},
                {"id": 2, "message_type": "warren", "content": "Hello! How can I help?"}
            ]
        }
        mock_conversation_manager.get_session_messages.return_value = expected_result
        
        # Act
        result = await orchestrator.get_session_messages(session_id, sample_advisor_id)
        
        # Assert
        assert result == expected_result
        mock_conversation_manager.get_session_messages.assert_called_once_with(session_id, sample_advisor_id)
    
    @pytest.mark.asyncio
    async def test_get_advisor_sessions_success(self, orchestrator, mock_conversation_manager, sample_advisor_id):
        """Test successful advisor sessions retrieval with pagination."""
        # Arrange
        expected_result = {
            "status": "success",
            "sessions": [{"id": 1, "title": "Session 1"}],
            "total": 1
        }
        mock_conversation_manager.get_advisor_sessions.return_value = expected_result
        
        # Act
        result = await orchestrator.get_advisor_sessions(sample_advisor_id, limit=10, offset=0)
        
        # Assert
        assert result == expected_result
        mock_conversation_manager.get_advisor_sessions.assert_called_once_with(sample_advisor_id, 10, 0)
    
    # ===================================================================
    # CONTENT LIBRARY DELEGATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_save_advisor_content_success(self, orchestrator, mock_content_library, sample_advisor_id, sample_content_data):
        """Test successful content saving delegation."""
        # Arrange
        expected_result = {
            "status": "success",
            "content": {"id": 1, "title": sample_content_data["title"]}
        }
        mock_content_library.save_content.return_value = expected_result
        
        # Act
        result = await orchestrator.save_advisor_content(
            advisor_id=sample_advisor_id,
            **sample_content_data
        )
        
        # Assert
        assert result == expected_result
        mock_content_library.save_content.assert_called_once()
        call_args = mock_content_library.save_content.call_args[1]
        assert call_args["advisor_id"] == sample_advisor_id
        assert call_args["title"] == sample_content_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_advisor_content_library_success(self, orchestrator, mock_content_library, sample_advisor_id):
        """Test successful content library retrieval."""
        # Arrange
        expected_result = {
            "status": "success",
            "content": [
                {"id": 1, "title": "Content 1", "status": "draft"},
                {"id": 2, "title": "Content 2", "status": "approved"}
            ],
            "total": 2
        }
        mock_content_library.get_library.return_value = expected_result
        
        # Act
        result = await orchestrator.get_advisor_content_library(
            advisor_id=sample_advisor_id,
            status_filter="draft",
            content_type_filter="linkedin_post",
            limit=25,
            offset=0
        )
        
        # Assert
        assert result == expected_result
        mock_content_library.get_library.assert_called_once_with(
            advisor_id=sample_advisor_id,
            status_filter="draft",
            content_type_filter="linkedin_post",
            limit=25,
            offset=0
        )
    
    @pytest.mark.asyncio
    async def test_get_content_statistics_success(self, orchestrator, mock_content_library, sample_advisor_id):
        """Test successful content statistics retrieval."""
        # Arrange
        expected_result = {
            "status": "success",
            "statistics": {
                "total_content": 10,
                "draft": 3,
                "approved": 5,
                "archived": 2
            }
        }
        mock_content_library.get_statistics.return_value = expected_result
        
        # Act
        result = await orchestrator.get_content_statistics(sample_advisor_id)
        
        # Assert
        assert result == expected_result
        mock_content_library.get_statistics.assert_called_once_with(sample_advisor_id)
    
    # ===================================================================
    # CONTENT UPDATE DELEGATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_update_content_success(self, orchestrator, mock_content_update_service, sample_advisor_id):
        """Test successful content update delegation."""
        # Arrange
        content_id = 1
        updates = {
            "title": "Updated Title",
            "content_text": "Updated content text...",
            "advisor_notes": "Updated notes"
        }
        expected_result = {
            "status": "success",
            "content": {"id": content_id, **updates}
        }
        mock_content_update_service.update_content.return_value = expected_result
        
        # Act
        result = await orchestrator.update_content(
            content_id=content_id,
            advisor_id=sample_advisor_id,
            **updates
        )
        
        # Assert
        assert result == expected_result
        mock_content_update_service.update_content.assert_called_once_with(
            content_id=content_id,
            advisor_id=sample_advisor_id,
            **updates
        )
    
    # ===================================================================
    # COMPLIANCE WORKFLOW DELEGATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_submit_content_for_review_success(self, orchestrator, mock_compliance_workflow, sample_advisor_id):
        """Test successful content review submission."""
        # Arrange
        content_id = 1
        cco_email = "cco@example.com"
        notes = "Please review for compliance"
        
        expected_result = {
            "status": "success",
            "review": {"content_id": content_id, "review_token": "token123"}
        }
        mock_compliance_workflow.submit_for_review.return_value = expected_result
        
        # Act
        result = await orchestrator.submit_content_for_review(
            content_id=content_id,
            advisor_id=sample_advisor_id,
            cco_email=cco_email,
            notes=notes
        )
        
        # Assert
        assert result == expected_result
        mock_compliance_workflow.submit_for_review.assert_called_once_with(
            content_id=content_id,
            advisor_id=sample_advisor_id,
            cco_email=cco_email,
            notes=notes
        )
    
    # ===================================================================
    # STATUS MANAGEMENT DELEGATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_update_content_status_success(self, orchestrator, mock_content_status_manager, sample_advisor_id):
        """Test successful content status update."""
        # Arrange
        content_id = 1
        new_status = "approved"
        reviewer = "cco@example.com"
        notes = "Content approved with minor suggestions"
        user_role = "cco"
        
        expected_result = {
            "status": "success",
            "content": {"id": content_id, "status": new_status}
        }
        mock_content_status_manager.transition_status.return_value = expected_result
        
        # Act
        result = await orchestrator.update_content_status(
            content_id=content_id,
            advisor_id=sample_advisor_id,
            new_status=new_status,
            reviewer=reviewer,
            notes=notes,
            user_role=user_role
        )
        
        # Assert
        assert result == expected_result
        mock_content_status_manager.transition_status.assert_called_once()
        call_args = mock_content_status_manager.transition_status.call_args
        assert call_args[1]["content_id"] == content_id
        assert call_args[1]["advisor_id"] == sample_advisor_id
        assert call_args[1]["new_status"] == new_status
        
        # Check context was built correctly
        context = call_args[1]["context"]
        assert context["user_role"] == user_role
        assert context["reviewer"] == reviewer
        assert context["notes"] == notes
    
    # ===================================================================
    # UTILITY METHODS TESTS
    # ===================================================================
    
    @patch('src.services.token_manager.token_manager')
    def test_generate_review_token_success(self, mock_token_manager, orchestrator):
        """Test review token generation."""
        # Arrange
        content_id = 1
        cco_email = "cco@example.com"
        expected_token = "review_token_123"
        mock_token_manager.generate_review_token.return_value = expected_token
        
        # Act
        result = orchestrator._generate_review_token(content_id, cco_email)
        
        # Assert
        assert result == expected_token
        mock_token_manager.generate_review_token.assert_called_once_with(
            content_id=content_id,
            cco_email=cco_email,
            expires_hours=24 * 7
        )
    
    @patch('src.services.token_manager.token_manager')
    def test_generate_review_token_error(self, mock_token_manager, orchestrator):
        """Test review token generation error handling."""
        # Arrange
        mock_token_manager.generate_review_token.side_effect = Exception("Token generation failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Token generation failed"):
            orchestrator._generate_review_token(1, "cco@example.com")
    
    # ===================================================================
    # CROSS-CUTTING CONCERNS TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_get_service_health_success(self, orchestrator):
        """Test service health monitoring."""
        # Act
        result = await orchestrator.get_service_health()
        
        # Assert
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "services" in result
        assert len(result["services"]) == 6  # All 6 services
        assert all(status == "healthy" for status in result["services"].values())
    
    @pytest.mark.asyncio
    async def test_get_workflow_metrics_success(self, orchestrator, mock_content_library, mock_conversation_manager, sample_advisor_id):
        """Test workflow metrics aggregation."""
        # Arrange
        mock_content_library.get_statistics.return_value = {
            "status": "success",
            "statistics": {"total_content": 10, "draft": 3}
        }
        mock_conversation_manager.get_advisor_sessions.return_value = {
            "status": "success",
            "total": 5
        }
        
        # Act
        result = await orchestrator.get_workflow_metrics(sample_advisor_id)
        
        # Assert
        assert result["status"] == "success"
        assert result["advisor_id"] == sample_advisor_id
        assert "content_statistics" in result
        assert result["session_count"] == 5
        assert result["workflow_health"] == "operational"
    
    @pytest.mark.asyncio
    async def test_get_workflow_metrics_error_handling(self, orchestrator, sample_advisor_id):
        """Test workflow metrics error handling."""
        # Arrange - Mock the orchestrator's own methods to raise exceptions
        with patch.object(orchestrator, 'get_content_statistics', side_effect=Exception("Database error")):
            # Act
            result = await orchestrator.get_workflow_metrics(sample_advisor_id)
            
            # Assert
            assert result["status"] == "error"
            assert "Database error" in result["error"]
    
    # ===================================================================
    # ERROR HANDLING TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_service_delegation_error_handling(self, orchestrator, mock_content_library, sample_advisor_id):
        """Test error handling when delegated services fail."""
        # Arrange
        mock_content_library.save_content.side_effect = Exception("Service unavailable")
        
        # Act
        result = await orchestrator.save_advisor_content(
            advisor_id=sample_advisor_id,
            title="Test",
            content_text="Test content",
            content_type="linkedin_post"
        )
        
        # Assert
        assert result["status"] == "error"
        assert "Service unavailable" in result["error"]
    
    # ===================================================================
    # BACKWARD COMPATIBILITY TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_all_methods_exist(self, orchestrator):
        """Test that all expected public methods exist for backward compatibility."""
        expected_methods = [
            'create_advisor_session',
            'save_warren_message',
            'get_session_messages',
            'get_advisor_sessions',
            'save_advisor_content',
            'get_advisor_content_library',
            'get_content_statistics',
            'update_content',
            'submit_content_for_review',
            'update_content_status',
            '_generate_review_token'
        ]
        
        for method_name in expected_methods:
            assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"
            assert callable(getattr(orchestrator, method_name)), f"Method not callable: {method_name}"
