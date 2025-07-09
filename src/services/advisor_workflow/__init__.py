# Advisor Workflow Services
"""
Modular advisor workflow services following Warren pattern.

Services:
- ConversationManagerService: Warren chat session management
- ContentLibraryService: Advisor content library CRUD (future)
- ComplianceWorkflowService: Review workflow and approval (future)
- ContentStatusManager: Status transitions and business rules (future)
- NotificationCoordinator: Email notifications (future)
- WorkflowOrchestrator: Main coordinator (future)
"""

from .conversation_manager_service import ConversationManagerService

__all__ = [
    'ConversationManagerService'
]
