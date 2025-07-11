# ContentStatusManager
"""
Content status transition management service following Warren pattern.
Extracted from advisor_workflow_service.py as part of SCRUM-101.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select, text, and_
from src.models.advisor_workflow_models import AdvisorContent, ContentStatus
from src.core.database import AsyncSessionLocal
from .strategies.strategy_factory import StatusTransitionStrategyFactory

logger = logging.getLogger(__name__)


class ContentStatusManager:
    """Content status management following Warren pattern."""
    
    def __init__(self, strategy_factory=None):
        """Initialize with dependency injection for testing."""
        self.strategy_factory = strategy_factory or StatusTransitionStrategyFactory()
    
    async def transition_status(
        self,
        content_id: int,
        advisor_id: str,
        new_status: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Transition content status with business rules validation."""
        if context is None:
            context = {}
            
        # Set default user role if not provided
        if 'user_role' not in context:
            context['user_role'] = 'advisor'
            
        context.update({
            'content_id': content_id,
            'advisor_id': advisor_id
        })
        
        # Get appropriate strategy first
        strategy = self.strategy_factory.get_strategy(context)
        if not strategy:
            return {
                "status": "error", 
                "error": f"No strategy found for user_role: {context.get('user_role')}"
            }
        
        # Validate strategy context
        validation = strategy.validate_transition_context(context)
        if not validation['valid']:
            return {"status": "error", "error": validation['error']}
        
        async with AsyncSessionLocal() as db:
            try:
                # Get current content and status
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"status": "error", "error": "Content not found or access denied"}
                
                current_status = content.status
                context['previous_status'] = current_status
                
                # Validate strategy context
                validation = strategy.validate_transition_context(context)
                if not validation['valid']:
                    return {"status": "error", "error": validation['error']}
                
                # Check if transition is allowed
                if not strategy.can_transition(current_status, new_status, context):
                    allowed = strategy.get_allowed_transitions(current_status, context)
                    return {
                        "status": "error",
                        "error": f"Transition from '{current_status}' to '{new_status}' not allowed. Allowed: {allowed}"
                    }
                
                # Get timestamp updates
                timestamp_updates = strategy.get_timestamp_updates(new_status, context)
                
                # Execute the transition
                update_result = await self._execute_status_update(
                    db, content_id, new_status, timestamp_updates, context
                )
                
                if update_result['status'] == 'error':
                    return update_result
                
                await db.commit()
                
                logger.info(f"Transitioned content {content_id} from '{current_status}' to '{new_status}'")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "previous_status": current_status,
                    "new_status": new_status,
                    "user_role": context['user_role'],
                    "updated_at": datetime.now().isoformat(),
                    "timestamp_updates": timestamp_updates
                }
                
            except Exception as e:
                logger.error(f"Error transitioning status: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def validate_transition(
        self,
        current_status: str,
        new_status: str,
        user_role: str,
        content_id: Optional[int] = None,
        advisor_id: Optional[str] = None
    ) -> bool:
        """Validate if a status transition is allowed without executing it."""
        context = {
            'user_role': user_role,
            'content_id': content_id,
            'advisor_id': advisor_id
        }
        
        strategy = self.strategy_factory.get_strategy(context)
        if not strategy:
            return False
        
        validation = strategy.validate_transition_context(context)
        if not validation['valid']:
            return False
            
        return strategy.can_transition(current_status, new_status, context)
    
    async def get_allowed_transitions(
        self,
        current_status: str,
        user_role: str,
        content_id: Optional[int] = None,
        advisor_id: Optional[str] = None
    ) -> List[str]:
        """Get list of allowed status transitions for current context."""
        context = {
            'user_role': user_role,
            'content_id': content_id,
            'advisor_id': advisor_id
        }
        
        strategy = self.strategy_factory.get_strategy(context)
        if not strategy:
            return []
        
        validation = strategy.validate_transition_context(context)
        if not validation['valid']:
            return []
            
        return strategy.get_allowed_transitions(current_status, context)
    
    async def get_status_history(self, content_id: int, advisor_id: str) -> Dict[str, Any]:
        """Get status history for content."""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {"status": "error", "error": "Content not found or access denied"}
                
                history = [{
                    "status": content.status,
                    "timestamp": content.updated_at.isoformat() if content.updated_at else None,
                    "notes": "Current status"
                }]
                
                # Add submission timestamp if available
                if content.submitted_for_review_at:
                    history.append({
                        "status": "submitted",
                        "timestamp": content.submitted_for_review_at.isoformat(),
                        "notes": "Submitted for review"
                    })
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "current_status": content.status,
                    "history": history
                }
                
            except Exception as e:
                logger.error(f"Error getting status history: {e}")
                return {"status": "error", "error": str(e)}
    
    async def _execute_status_update(
        self,
        db,
        content_id: int,
        new_status: str,
        timestamp_updates: Dict[str, Any],
        context: Dict
    ) -> Dict[str, Any]:
        """Execute the database update with PostgreSQL enum handling."""
        try:
            # Build dynamic SQL based on what needs to be updated
            set_clauses = ["status = :status"]
            query_params = {
                "status": new_status.lower(),
                "content_id": content_id
            }
            
            # Add timestamp updates
            for field, value in timestamp_updates.items():
                if value == 'NOW()':
                    set_clauses.append(f"{field} = NOW()")
                elif value is None:
                    set_clauses.append(f"{field} = NULL")
                else:
                    param_name = f"ts_{field}"
                    set_clauses.append(f"{field} = :{param_name}")
                    query_params[param_name] = value
            
            # Add advisor notes if provided
            if context.get('advisor_notes'):
                set_clauses.append("advisor_notes = :advisor_notes")
                query_params['advisor_notes'] = context['advisor_notes']
            
            # Add CCO information for review transitions
            if new_status.lower() == 'submitted' and context.get('cco_email'):
                set_clauses.append("cco_email = :cco_email")
                set_clauses.append("cco_review_status = 'submitted'")
                query_params['cco_email'] = context['cco_email']
            
            # Build final query
            query_sql = f"""
                UPDATE advisor_content 
                SET {', '.join(set_clauses)}
                WHERE id = :content_id
            """
            
            query = text(query_sql)
            await db.execute(query, query_params)
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error executing status update: {e}")
            return {"status": "error", "error": str(e)}
