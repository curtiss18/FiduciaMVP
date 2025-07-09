# Advisor Workflow Services
"""
Modular advisor workflow services following Warren pattern.

Services:
- ConversationManagerService: Warren chat session management
- ContentLibraryService: Advisor content library CRUD
- ComplianceWorkflowService: Review workflow and approval
- ContentStatusManager: Status transitions and business rules
- NotificationCoordinator: Email notifications ✅ NEW
- WorkflowOrchestrator: Main coordinator (future)
"""

from .conversation_manager_service import ConversationManagerService
from .content_library_service import ContentLibraryService
from .compliance_workflow_service import ComplianceWorkflowService
from .content_status_manager import ContentStatusManager
from .notification_coordinator import NotificationCoordinator

__all__ = [
    'ConversationManagerService',
    'ContentLibraryService', 
    'ComplianceWorkflowService',
    'ContentStatusManager',
    'NotificationCoordinator'
]
