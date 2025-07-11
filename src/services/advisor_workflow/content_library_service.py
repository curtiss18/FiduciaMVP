# ContentLibraryService
"""
Advisor content library management service following Warren pattern.

Responsibilities:
- Save Warren-generated content to advisor's personal library
- Content retrieval with filtering (status, type, date) and pagination
- Content updates and modifications
- Content statistics and analytics
- Status filtering with archive handling
- Channel and metadata management

Extracted from advisor_workflow_service.py as part of SCRUM-99.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlalchemy import select, func, and_, update, desc, text
from src.models.advisor_workflow_models import AdvisorContent, ContentStatus
from src.models.refactored_database import ContentType, AudienceType
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ContentLibraryService:
    """Advisor content library management following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def save_content(
        self,
        advisor_id: str,
        title: str,
        content_text: str,
        content_type: str,
        audience_type: str = "general_education",
        source_session_id: Optional[str] = None,
        source_message_id: Optional[int] = None,
        advisor_notes: Optional[str] = None,
        intended_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save content piece to advisor's library."""
        async with AsyncSessionLocal() as db:
            try:
                # Force string values and ensure lowercase
                content_type_str = str(content_type).lower() if content_type else "linkedin_post"
                audience_type_str = str(audience_type).lower() if audience_type else "general_education"
                status_str = "draft"
                
                # Use raw SQL insert without enum casting for advisor_content table
                query = text("""
                    INSERT INTO advisor_content 
                    (advisor_id, title, content_text, content_type, audience_type, 
                     source_session_id, source_message_id, advisor_notes, 
                     intended_channels, status, created_at, updated_at)
                    VALUES 
                    (:advisor_id, :title, :content_text, :content_type, 
                     :audience_type, :source_session_id, :source_message_id, 
                     :advisor_notes, :intended_channels, :status, NOW(), NOW())
                    RETURNING id, created_at, updated_at
                """)
                
                result = await db.execute(query, {
                    'advisor_id': advisor_id,
                    'title': title,
                    'content_text': content_text,
                    'content_type': content_type_str,
                    'audience_type': audience_type_str,
                    'source_session_id': source_session_id,
                    'source_message_id': source_message_id,
                    'advisor_notes': advisor_notes,
                    'intended_channels': json.dumps(intended_channels) if intended_channels else None,
                    'status': status_str
                })
                
                row = result.fetchone()
                content_id = row[0]
                created_at = row[1]
                updated_at = row[2]
                
                await db.commit()
                
                logger.info(f"Saved advisor content: {content_id} for advisor {advisor_id}")
                
                return {
                    "status": "success",
                    "content": {
                        "id": content_id,
                        "title": title,
                        "content_type": content_type_str,
                        "audience_type": audience_type_str,
                        "status": status_str,
                        "created_at": created_at.isoformat(),
                        "source_session_id": source_session_id,
                        "source_message_id": source_message_id
                    }
                }
                
            except Exception as e:
                logger.error(f"Error saving advisor content: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
    
    async def get_library(
        self,
        advisor_id: str,
        status_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get advisor's content library with filtering."""
        async with AsyncSessionLocal() as db:
            try:
                # Build query with filters
                query = select(AdvisorContent).where(
                    AdvisorContent.advisor_id == advisor_id
                )
                
                # Filter logic
                if status_filter:
                    # If specific status requested, show only that status
                    print(f"DEBUG: Filtering by status: {status_filter}")
                    try:
                        # Try both the raw value and lowercase
                        if status_filter.lower() == 'archived':
                            query = query.where(AdvisorContent.status == 'archived')
                        else:
                            status_enum = ContentStatus(status_filter.lower())
                            query = query.where(AdvisorContent.status == status_enum.value)
                        print(f"DEBUG: Status filter applied successfully")
                    except ValueError as e:
                        print(f"DEBUG: Status enum error: {e}")
                        # Fallback to raw string comparison
                        query = query.where(AdvisorContent.status == status_filter.lower())
                else:
                    # Default: exclude archived content from results
                    query = query.where(AdvisorContent.status != ContentStatus.ARCHIVED.value)
                
                if content_type_filter:
                    content_type_enum = ContentType(content_type_filter.upper())
                    query = query.where(AdvisorContent.content_type == content_type_enum)
                
                # Get content with pagination
                result = await db.execute(
                    query.order_by(desc(AdvisorContent.updated_at))
                    .limit(limit)
                    .offset(offset)
                )
                content_items = result.scalars().all()
                
                # Get total count with same filtering logic
                count_query = select(func.count(AdvisorContent.id)).where(
                    AdvisorContent.advisor_id == advisor_id
                )
                
                if status_filter:
                    # If specific status requested, count only that status
                    print(f"DEBUG: Count filtering by status: {status_filter}")
                    try:
                        if status_filter.lower() == 'archived':
                            count_query = count_query.where(AdvisorContent.status == 'archived')
                        else:
                            count_query = count_query.where(AdvisorContent.status == ContentStatus(status_filter.lower()).value)
                    except ValueError:
                        # Fallback to raw string comparison
                        count_query = count_query.where(AdvisorContent.status == status_filter.lower())
                else:
                    # Default: exclude archived content from count
                    count_query = count_query.where(AdvisorContent.status != ContentStatus.ARCHIVED.value)
                    
                if content_type_filter:
                    count_query = count_query.where(AdvisorContent.content_type == ContentType(content_type_filter.upper()))
                
                count_result = await db.execute(count_query)
                total_count = count_result.scalar()
                
                logger.info(f"Retrieved {len(content_items)} content items for advisor {advisor_id}")
                
                return {
                    "status": "success",
                    "content": [
                        {
                            "id": item.id,
                            "title": item.title,
                            "content_text": item.content_text,
                            "content_type": item.content_type,
                            "audience_type": item.audience_type,
                            "status": item.status,
                            "advisor_notes": item.advisor_notes,
                            "intended_channels": json.loads(item.intended_channels) if item.intended_channels else None,
                            "source_session_id": item.source_session_id,
                            "submitted_for_review_at": item.submitted_for_review_at.isoformat() if item.submitted_for_review_at else None,
                            "created_at": item.created_at.isoformat(),
                            "updated_at": item.updated_at.isoformat()
                        }
                        for item in content_items
                    ],
                    "total_count": total_count,
                    "has_more": (offset + limit) < total_count
                }
                
            except Exception as e:
                logger.error(f"Error getting advisor content library: {e}")
                return {"status": "error", "error": str(e)}
    
    async def update_content(
        self,
        content_id: int,
        advisor_id: str,
        title: Optional[str] = None,
        content_text: Optional[str] = None,
        advisor_notes: Optional[str] = None,
        source_metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """Update full content (for session updates)."""
        async with AsyncSessionLocal() as db:
            try:
                # Verify content belongs to advisor
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
                await db.rollback()
                logger.error(f"Error updating content: {e}")
                return {"status": "error", "error": str(e)}
    
    async def get_statistics(self, advisor_id: str) -> Dict[str, Any]:
        """Get advisor's content statistics."""
        async with AsyncSessionLocal() as db:
            try:
                # Count by status using raw SQL with proper enum casting
                status_counts = {}
                for status in ContentStatus:
                    query = text("""
                        SELECT COUNT(id) 
                        FROM advisor_content 
                        WHERE advisor_id = :advisor_id 
                        AND status = :status
                    """)
                    result = await db.execute(query, {
                        "advisor_id": advisor_id,
                        "status": status.value
                    })
                    status_counts[status.value] = result.scalar()
                
                # Total content count
                total_result = await db.execute(
                    select(func.count(AdvisorContent.id))
                    .where(AdvisorContent.advisor_id == advisor_id)
                )
                total_count = total_result.scalar()
                
                logger.info(f"Generated statistics for advisor {advisor_id}: {total_count} total content")
                
                return {
                    "status": "success",
                    "statistics": {
                        "total_content": total_count,
                        "content_by_status": status_counts,
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting content statistics: {e}")
                return {"status": "error", "error": str(e)}
