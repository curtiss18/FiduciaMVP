# Advisor Workflow Services
"""
Modular advisor workflow services following Warren pattern.

Services:
- ConversationManagerService: Warren chat session management
- ContentLibraryService: Advisor content library CRUD
- ComplianceWorkflowService: Review workflow and approval
- ContentStatusManager: Status transitions and business rules ✅ NEW
- NotificationCoordinator: Email notifications (future)
- WorkflowOrchestrator: Main coordinator (future)
"""

from .conversation_manager_service import ConversationManagerService
from .content_library_service import ContentLibraryService
from .compliance_workflow_service import ComplianceWorkflowService
from .content_status_manager import ContentStatusManager

__all__ = [
    'ConversationManagerService',
    'ContentLibraryService', 
    'ComplianceWorkflowService',
    'ContentStatusManager'
]
