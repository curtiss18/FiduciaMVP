# Slim WorkflowOrchestrator
"""
Lightweight coordinator for advisor workflow services.

Responsibilities:
- Delegate operations to specialized services
- Provide backward-compatible interface
- Handle errors gracefully

This is a slim version focusing only on coordination without verbose logging.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Lightweight advisor workflow coordinator."""
    
    def __init__(self,
                 conversation_manager=None,
                 content_library=None,
                 compliance_workflow=None,
                 content_status_manager=None,
                 notification_coordinator=None,
                 content_update_service=None):
        """Initialize with dependency injection for testing."""
        # Lazy imports to prevent circular dependencies
        self.conversation_manager = conversation_manager or self._get_conversation_manager()
        self.content_library = content_library or self._get_content_library()
        self.compliance_workflow = compliance_workflow or self._get_compliance_workflow()
        self.content_status_manager = content_status_manager or self._get_content_status_manager()
        self.notification_coordinator = notification_coordinator or self._get_notification_coordinator()
        self.content_update_service = content_update_service or self._get_content_update_service()
    
    def _get_conversation_manager(self):
        from .conversation_manager_service import ConversationManagerService
        return ConversationManagerService()
    
    def _get_content_library(self):
        from .content_library_service import ContentLibraryService
        return ContentLibraryService()
    
    def _get_compliance_workflow(self):
        from .compliance_workflow_service import ComplianceWorkflowService
        return ComplianceWorkflowService()
    
    def _get_content_status_manager(self):
        from .content_status_manager import ContentStatusManager
        return ContentStatusManager()
    
    def _get_notification_coordinator(self):
        from .notification_coordinator import NotificationCoordinator
        return NotificationCoordinator()
    
    def _get_content_update_service(self):
        from .content_update_service import ContentUpdateService
        return ContentUpdateService()
    
    # ===================================================================
    # CONVERSATION MANAGEMENT - Simple delegation
    # ===================================================================
    
    async def create_advisor_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new Warren chat session."""
        return await self.conversation_manager.create_session(advisor_id, title)
    
    async def save_warren_message(self, session_id: str, message_type: str, content: str, 
                                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Save Warren message."""
        return await self.conversation_manager.save_message(session_id, message_type, content, metadata)
    
    async def get_session_messages(self, session_id: str, advisor_id: str) -> Dict[str, Any]:
        """Get conversation history."""
        return await self.conversation_manager.get_session_messages(session_id, advisor_id)
    
    async def get_advisor_sessions(self, advisor_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get advisor's sessions."""
        return await self.conversation_manager.get_advisor_sessions(advisor_id, limit, offset)
    
    # ===================================================================
    # CONTENT LIBRARY MANAGEMENT - Simple delegation
    # ===================================================================
    
    async def save_advisor_content(self, advisor_id: str, title: str, content_text: str, content_type: str,
                                  audience_type: str = "general_education", source_session_id: Optional[str] = None,
                                  source_message_id: Optional[int] = None, advisor_notes: Optional[str] = None,
                                  intended_channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Save content to advisor's library."""
        return await self.content_library.save_content(
            advisor_id=advisor_id, title=title, content_text=content_text, content_type=content_type,
            audience_type=audience_type, source_session_id=source_session_id,
            source_message_id=source_message_id, advisor_notes=advisor_notes,
            intended_channels=intended_channels
        )
    
    async def get_advisor_content_library(self, advisor_id: str, status_filter: Optional[str] = None,
                                         content_type_filter: Optional[str] = None, limit: int = 50, 
                                         offset: int = 0) -> Dict[str, Any]:
        """Get advisor's content library."""
        return await self.content_library.get_library(
            advisor_id=advisor_id, status_filter=status_filter, 
            content_type_filter=content_type_filter, limit=limit, offset=offset
        )
    
    async def get_content_statistics(self, advisor_id: str) -> Dict[str, Any]:
        """Get content statistics."""
        return await self.content_library.get_statistics(advisor_id)
    
    # ===================================================================
    # CONTENT MODIFICATION - Simple delegation
    # ===================================================================
    
    async def update_content(self, content_id: int, advisor_id: str, title: Optional[str] = None,
                           content_text: Optional[str] = None, advisor_notes: Optional[str] = None) -> Dict[str, Any]:
        """Update existing content."""
        return await self.content_update_service.update_content(
            content_id=content_id, advisor_id=advisor_id, title=title,
            content_text=content_text, advisor_notes=advisor_notes
        )
    
    # ===================================================================
    # COMPLIANCE WORKFLOW - Simple delegation
    # ===================================================================
    
    async def submit_content_for_review(self, content_id: int, advisor_id: str, cco_email: str,
                                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Submit content for compliance review."""
        return await self.compliance_workflow.submit_for_review(
            content_id=content_id, advisor_id=advisor_id, cco_email=cco_email, notes=notes
        )
    
    # ===================================================================
    # STATUS MANAGEMENT - Simple delegation
    # ===================================================================
    
    async def update_content_status(self, content_id: int, advisor_id: str, new_status: str,
                                   advisor_notes: Optional[str] = None, reviewer: Optional[str] = None, 
                                   notes: Optional[str] = None, user_role: str = "advisor") -> Dict[str, Any]:
        """Update content status."""
        # Support both advisor_notes (backward compatibility) and notes (new interface)
        final_notes = advisor_notes or notes
        context = {'user_role': user_role, 'reviewer': reviewer, 'notes': final_notes}
        return await self.content_status_manager.transition_status(
            content_id=content_id, advisor_id=advisor_id, new_status=new_status, context=context
        )
    
    # ===================================================================
    # UTILITY METHODS - For backward compatibility
    # ===================================================================
    
    def _generate_review_token(self, content_id: int, cco_email: str) -> str:
        """Generate review token using centralized token manager."""
        from src.services.token_manager import token_manager
        
        return token_manager.generate_review_token(
            content_id=content_id, cco_email=cco_email, expires_hours=24 * 7
        )
    
    # ===================================================================
    # MONITORING - Minimal implementation
    # ===================================================================
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get basic health status."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "conversation_manager": "healthy",
                "content_library": "healthy", 
                "compliance_workflow": "healthy",
                "content_status_manager": "healthy",
                "notification_coordinator": "healthy",
                "content_update_service": "healthy"
            }
        }
    
    async def get_workflow_metrics(self, advisor_id: str) -> Dict[str, Any]:
        """Get basic workflow metrics."""
        try:
            content_stats = await self.get_content_statistics(advisor_id)
            sessions_result = await self.get_advisor_sessions(advisor_id, limit=1)
            
            return {
                "status": "success",
                "advisor_id": advisor_id,
                "timestamp": datetime.now().isoformat(),
                "content_statistics": content_stats.get("statistics", {}),
                "session_count": sessions_result.get("total", 0),
                "workflow_health": "operational"
            }
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {e}")
            return {"status": "error", "error": str(e)}
