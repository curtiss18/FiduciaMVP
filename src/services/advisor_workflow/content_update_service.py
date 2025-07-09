# ContentUpdateService
"""
Content editing and modification service following Warren pattern.

Responsibilities:
- Handle content text and metadata editing
- Manage content version tracking and timestamps
- Enforce access control for content modifications
- Support partial content updates (title, content_text, notes)
- Track content revision history
- Handle metadata updates (intended_channels, etc.)

Extracted from advisor_workflow_service.py as part of SCRUM-104.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select, func, and_, update
from src.models.advisor_workflow_models import AdvisorContent
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ContentUpdateService:
    """Content editing and modification following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def update_content(
        self,
        content_id: int,
        advisor_id: str,
        title: Optional[str] = None,
        content_text: Optional[str] = None,
        advisor_notes: Optional[str] = None,
        source_metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Update content with access control and version tracking."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content belongs to advisor (access control)
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    logger.warning(f"Content access denied: {content_id} for advisor {advisor_id}")
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Build update data (excluding source_metadata since column doesn't exist)
                update_data = {"updated_at": func.now()}
                
                # Handle partial updates - only update provided fields
                if title is not None:
                    update_data["title"] = title
                if content_text is not None:
                    update_data["content_text"] = content_text
                if advisor_notes is not None:
                    update_data["advisor_notes"] = advisor_notes
                
                # Perform update
                await db.execute(
                    update(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                    .values(**update_data)
                )
                await db.commit()
                
                # Return updated content
                updated_result = await db.execute(
                    select(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                )
                updated_content = updated_result.scalar_one()
                
                logger.info(f"Updated content {content_id} for advisor {advisor_id}")
                
                return {
                    "status": "success",
                    "content": {
                        "id": updated_content.id,
                        "title": updated_content.title,
                        "content_text": updated_content.content_text,
                        "advisor_notes": updated_content.advisor_notes,
                        "updated_at": updated_content.updated_at.isoformat() if updated_content.updated_at else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Error updating content: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def update_content_metadata(
        self,
        content_id: int,
        advisor_id: str,
        intended_channels: Optional[list] = None,
        source_session_id: Optional[str] = None,
        source_message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update content metadata without changing core content."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content belongs to advisor (access control)
                result = await db.execute(
                    select(AdvisorContent)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    logger.warning(f"Content metadata access denied: {content_id} for advisor {advisor_id}")
                    return {"status": "error", "error": "Content not found or access denied"}
                
                # Build metadata update
                update_data = {"updated_at": func.now()}
                
                if intended_channels is not None:
                    import json
                    update_data["intended_channels"] = json.dumps(intended_channels)
                if source_session_id is not None:
                    update_data["source_session_id"] = source_session_id
                if source_message_id is not None:
                    update_data["source_message_id"] = source_message_id
                
                # Perform metadata update
                await db.execute(
                    update(AdvisorContent)
                    .where(AdvisorContent.id == content_id)
                    .values(**update_data)
                )
                await db.commit()
                
                logger.info(f"Updated content metadata {content_id} for advisor {advisor_id}")
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "updated_fields": list(update_data.keys()),
                    "updated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error updating content metadata: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def validate_content_update_permission(
        self,
        content_id: int,
        advisor_id: str
    ) -> bool:
        """Validate that advisor can update this content."""
        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(AdvisorContent.id)
                    .where(and_(
                        AdvisorContent.id == content_id,
                        AdvisorContent.advisor_id == advisor_id
                    ))
                )
                content = result.scalar_one_or_none()
                
                return content is not None
                
            except Exception as e:
                logger.error(f"Error validating content update permission: {e}")
                return False
    
    async def get_content_versions(
        self,
        content_id: int,
        advisor_id: str
    ) -> Dict[str, Any]:
        """Get content version information (foundation for future enhancement)."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify access and get current content
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
                
                # For now, return current version info
                # Future enhancement: implement proper version tracking
                versions = [{
                    "version": 1,
                    "timestamp": content.updated_at.isoformat() if content.updated_at else content.created_at.isoformat(),
                    "title": content.title,
                    "content_length": len(content.content_text) if content.content_text else 0,
                    "notes": content.advisor_notes,
                    "is_current": True
                }]
                
                return {
                    "status": "success",
                    "content_id": content_id,
                    "current_version": 1,
                    "total_versions": 1,
                    "versions": versions
                }
                
            except Exception as e:
                logger.error(f"Error getting content versions: {e}")
                return {"status": "error", "error": str(e)}
    
    async def get_content_edit_summary(
        self,
        content_id: int,
        advisor_id: str
    ) -> Dict[str, Any]:
        """Get summary of content editing activity."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify access and get content
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
                
                # Calculate edit statistics
                edit_summary = {
                    "content_id": content_id,
                    "created_at": content.created_at.isoformat() if content.created_at else None,
                    "last_updated": content.updated_at.isoformat() if content.updated_at else None,
                    "title_length": len(content.title) if content.title else 0,
                    "content_length": len(content.content_text) if content.content_text else 0,
                    "has_notes": bool(content.advisor_notes),
                    "notes_length": len(content.advisor_notes) if content.advisor_notes else 0,
                    "intended_channels": content.intended_channels,
                    "status": content.status
                }
                
                return {
                    "status": "success",
                    "edit_summary": edit_summary
                }
                
            except Exception as e:
                logger.error(f"Error getting content edit summary: {e}")
                return {"status": "error", "error": str(e)}
