# Advisor Workflow Services
"""
Modular advisor workflow services following Warren pattern.

Services:
- ConversationManagerService: Warren chat session management
- ContentLibraryService: Advisor content library CRUD
- ComplianceWorkflowService: Review workflow and approval
- ContentStatusManager: Status transitions and business rules
- NotificationCoordinator: Email notifications
- ContentUpdateService: Content editing and modification
- WorkflowOrchestrator: Main coordinator ✅ ACTIVE

Simple Usage:
- from src.services.advisor_workflow import WorkflowOrchestrator
- from src.services.advisor_workflow import get_advisor_workflow_service
"""

from .conversation_manager_service import ConversationManagerService
from .content_library_service import ContentLibraryService
from .compliance_workflow_service import ComplianceWorkflowService
from .content_status_manager import ContentStatusManager
from .notification_coordinator import NotificationCoordinator
from .content_update_service import ContentUpdateService
from .workflow_orchestrator import WorkflowOrchestrator

# Simple singleton function
_orchestrator_instance = None

def get_advisor_workflow_service() -> WorkflowOrchestrator:
    """Get singleton instance of WorkflowOrchestrator."""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator()
    
    return _orchestrator_instance

# Backward compatibility alias
advisor_workflow_service = get_advisor_workflow_service()

__all__ = [
    'ConversationManagerService',
    'ContentLibraryService', 
    'ComplianceWorkflowService',
    'ContentStatusManager',
    'NotificationCoordinator',
    'ContentUpdateService',
    'WorkflowOrchestrator',
    'get_advisor_workflow_service',
    'advisor_workflow_service'
]
