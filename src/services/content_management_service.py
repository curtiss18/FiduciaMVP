# Content Management Service for CRUD operations
# Handles Create, Read, Update, Delete operations for marketing content

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select
from src.models.refactored_database import MarketingContent, ContentType, AudienceType, ApprovalStatus, SourceType
from src.core.database import AsyncSessionLocal
from src.services.embedding_service import embedding_service
import logging

logger = logging.getLogger(__name__)


class ContentManagementService:
    """Service for managing marketing content CRUD operations with auto-vectorization."""
    
    async def get_all_content(
        self,
        skip: int = 0,
        limit: int = 100,
        content_type: Optional[ContentType] = None,
        audience_type: Optional[AudienceType] = None,
        approval_status: Optional[ApprovalStatus] = None,
        search_query: Optional[str] = None,
        source_type: Optional[SourceType] = None
    ) -> Dict[str, Any]:
        """
        Get all marketing content with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            content_type: Filter by content type
            audience_type: Filter by audience type  
            approval_status: Filter by approval status
            search_query: Search in title and content_text
            source_type: Filter by source type
            
        Returns:
            Dict with content list, total count, and metadata
        """
        try:
            async with AsyncSessionLocal() as db:
                # Build query with filters
                query = select(MarketingContent)
                
                # Apply filters
                if content_type:
                    query = query.where(MarketingContent.content_type == content_type)
                if audience_type:
                    query = query.where(MarketingContent.audience_type == audience_type)
                if approval_status:
                    query = query.where(MarketingContent.approval_status == approval_status)
                if source_type:
                    query = query.where(MarketingContent.source_type == source_type)
                if search_query:
                    search_filter = or_(
                        MarketingContent.title.ilike(f"%{search_query}%"),
                        MarketingContent.content_text.ilike(f"%{search_query}%"),
                        MarketingContent.tags.ilike(f"%{search_query}%")
                    )
                    query = query.where(search_filter)
                
                # Get total count
                count_query = select(func.count()).select_from(query.subquery())
                count_result = await db.execute(count_query)
                total_count = count_result.scalar()
                
                # Apply pagination and ordering
                query = query.order_by(MarketingContent.updated_at.desc()).offset(skip).limit(limit)
                result = await db.execute(query)
                content_items = result.scalars().all()
                
                # Convert to dict format
                content_list = []
                for item in content_items:
                    content_dict = {
                        "id": item.id,
                        "title": item.title,
                        "content_text": item.content_text,
                        "content_type": item.content_type.value if item.content_type else None,
                        "audience_type": item.audience_type.value if item.audience_type else None,
                        "tone": item.tone,
                        "topic_focus": item.topic_focus,
                        "target_demographics": item.target_demographics,
                        "approval_status": item.approval_status.value if item.approval_status else None,
                        "compliance_score": item.compliance_score,
                        "source_type": item.source_type.value if item.source_type else None,
                        "original_source": item.original_source,
                        "usage_count": item.usage_count,
                        "effectiveness_score": item.effectiveness_score,
                        "tags": item.tags.split(",") if item.tags else [],
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                        "has_embedding": item.embedding is not None
                    }
                    content_list.append(content_dict)
                
                return {
                    "status": "success",
                    "content": content_list,
                    "pagination": {
                        "total_count": total_count,
                        "returned_count": len(content_list),
                        "skip": skip,
                        "limit": limit,
                        "has_more": (skip + len(content_list)) < total_count
                    },
                    "filters_applied": {
                        "content_type": content_type.value if content_type else None,
                        "audience_type": audience_type.value if audience_type else None,
                        "approval_status": approval_status.value if approval_status else None,
                        "source_type": source_type.value if source_type else None,
                        "search_query": search_query
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting content: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_content_by_id(self, content_id: int) -> Dict[str, Any]:
        """Get a specific content item by ID."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(MarketingContent).where(MarketingContent.id == content_id)
                result = await db.execute(query)
                content_item = result.scalar_one_or_none()
                
                if not content_item:
                    return {"status": "error", "error": "Content not found"}
                
                content_dict = {
                    "id": content_item.id,
                    "title": content_item.title,
                    "content_text": content_item.content_text,
                    "content_type": content_item.content_type.value if content_item.content_type else None,
                    "audience_type": content_item.audience_type.value if content_item.audience_type else None,
                    "tone": content_item.tone,
                    "topic_focus": content_item.topic_focus,
                    "target_demographics": content_item.target_demographics,
                    "approval_status": content_item.approval_status.value if content_item.approval_status else None,
                    "compliance_score": content_item.compliance_score,
                    "fiducia_approved_by": content_item.fiducia_approved_by,
                    "fiducia_approved_at": content_item.fiducia_approved_at.isoformat() if content_item.fiducia_approved_at else None,
                    "source_type": content_item.source_type.value if content_item.source_type else None,
                    "original_source": content_item.original_source,
                    "contributed_by_user_id": content_item.contributed_by_user_id,
                    "usage_count": content_item.usage_count,
                    "effectiveness_score": content_item.effectiveness_score,
                    "tags": content_item.tags.split(",") if content_item.tags else [],
                    "created_at": content_item.created_at.isoformat() if content_item.created_at else None,
                    "updated_at": content_item.updated_at.isoformat() if content_item.updated_at else None,
                    "has_embedding": content_item.embedding is not None
                }
                
                return {"status": "success", "content": content_dict}
                
        except Exception as e:
            logger.error(f"Error getting content by ID {content_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def create_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new marketing content with automatic vectorization.
        
        Args:
            content_data: Dictionary containing content fields
            
        Returns:
            Dict with created content and vectorization status
        """
        try:
            # Validate required fields
            required_fields = ["title", "content_text", "content_type", "audience_type"]
            for field in required_fields:
                if field not in content_data or not content_data[field]:
                    return {"status": "error", "error": f"Required field '{field}' is missing"}
            
            async with AsyncSessionLocal() as db:
                # Create new content item with explicit timestamps
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                
                new_content = MarketingContent(
                    title=content_data["title"],
                    content_text=content_data["content_text"],
                    content_type=ContentType(content_data["content_type"]),
                    audience_type=AudienceType(content_data["audience_type"]),
                    tone=content_data.get("tone"),
                    topic_focus=content_data.get("topic_focus"),
                    target_demographics=content_data.get("target_demographics"),
                    approval_status=ApprovalStatus(content_data.get("approval_status", "approved")),
                    compliance_score=content_data.get("compliance_score", 1.0),
                    source_type=SourceType(content_data.get("source_type", "fiducia_created")),
                    original_source=content_data.get("original_source"),
                    contributed_by_user_id=content_data.get("contributed_by_user_id"),
                    tags=content_data.get("tags") if content_data.get("tags") else None,
                    created_at=now,
                    updated_at=now
                )
                
                db.add(new_content)
                await db.commit()
                await db.refresh(new_content)
                
                # Auto-generate embedding
                vectorization_result = await self._generate_embedding_for_content(new_content)
                
                return {
                    "status": "success",
                    "content": {
                        "id": new_content.id,
                        "title": new_content.title,
                        "content_type": new_content.content_type.value,
                        "created_at": new_content.created_at.isoformat() if new_content.created_at else None
                    },
                    "vectorization": vectorization_result
                }
                
        except ValueError as e:
            return {"status": "error", "error": f"Invalid enum value: {str(e)}"}
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def update_content(self, content_id: int, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing marketing content with automatic re-vectorization.
        
        Args:
            content_id: ID of content to update
            content_data: Dictionary containing updated fields
            
        Returns:
            Dict with updated content and vectorization status
        """
        try:
            async with AsyncSessionLocal() as db:
                # Use async query operations (fixed from sync)
                query = select(MarketingContent).where(MarketingContent.id == content_id)
                result = await db.execute(query)
                content_item = result.scalar_one_or_none()
                
                if not content_item:
                    return {"status": "error", "error": "Content not found"}
                
                # Track if content changed (affects vectorization)
                content_changed = False
                
                # Update fields if provided
                if "title" in content_data:
                    if content_item.title != content_data["title"]:
                        content_changed = True
                    content_item.title = content_data["title"]
                
                if "content_text" in content_data:
                    if content_item.content_text != content_data["content_text"]:
                        content_changed = True
                    content_item.content_text = content_data["content_text"]
                
                if "content_type" in content_data:
                    content_item.content_type = ContentType(content_data["content_type"])
                
                if "audience_type" in content_data:
                    content_item.audience_type = AudienceType(content_data["audience_type"])
                
                if "tone" in content_data:
                    content_item.tone = content_data["tone"]
                
                if "topic_focus" in content_data:
                    content_item.topic_focus = content_data["topic_focus"]
                
                if "target_demographics" in content_data:
                    content_item.target_demographics = content_data["target_demographics"]
                
                if "approval_status" in content_data:
                    content_item.approval_status = ApprovalStatus(content_data["approval_status"])
                
                if "compliance_score" in content_data:
                    content_item.compliance_score = content_data["compliance_score"]
                
                if "tags" in content_data:
                    content_item.tags = content_data["tags"] if content_data["tags"] else None
                
                if "original_source" in content_data:
                    content_item.original_source = content_data["original_source"] if content_data["original_source"] else None
                
                # Update timestamps (use datetime.now instead of func.now for async)
                from datetime import datetime, timezone
                content_item.updated_at = datetime.now(timezone.utc)
                
                await db.commit()
                await db.refresh(content_item)
                
                # Re-vectorize if content changed
                vectorization_result = None
                if content_changed:
                    vectorization_result = await self._generate_embedding_for_content(content_item)
                
                return {
                    "status": "success",
                    "content": {
                        "id": content_item.id,
                        "title": content_item.title,
                        "content_type": content_item.content_type.value,
                        "updated_at": content_item.updated_at.isoformat()
                    },
                    "content_changed": content_changed,
                    "vectorization": vectorization_result
                }
                
        except ValueError as e:
            return {"status": "error", "error": f"Invalid enum value: {str(e)}"}
        except Exception as e:
            logger.error(f"Error updating content {content_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def delete_content(self, content_id: int) -> Dict[str, Any]:
        """
        Delete marketing content and its embedding.
        
        Args:
            content_id: ID of content to delete
            
        Returns:
            Dict with deletion status
        """
        try:
            async with AsyncSessionLocal() as db:
                # Use async query operations
                from sqlalchemy import select
                result = await db.execute(select(MarketingContent).where(MarketingContent.id == content_id))
                content_item = result.scalar_one_or_none()
                
                if not content_item:
                    return {"status": "error", "error": "Content not found"}
                
                # Store info for response
                deleted_info = {
                    "id": content_item.id,
                    "title": content_item.title,
                    "content_type": content_item.content_type.value,
                    "had_embedding": content_item.embedding is not None
                }
                
                # Delete the content (this also deletes the embedding)
                await db.delete(content_item)
                await db.commit()
                
                return {
                    "status": "success",
                    "message": "Content deleted successfully",
                    "deleted_content": deleted_info
                }
                
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_embedding_for_content(self, content_item: MarketingContent) -> Dict[str, Any]:
        """
        Generate embedding for a content item and update the database.
        
        Args:
            content_item: MarketingContent instance
            
        Returns:
            Dict with vectorization result
        """
        try:
            # Generate embedding
            embedding = await embedding_service.generate_embedding(content_item.content_text)
            
            if embedding:
                # Update content with embedding using async operations
                async with AsyncSessionLocal() as db:
                    # Re-query to get fresh session with async operations
                    query = select(MarketingContent).where(MarketingContent.id == content_item.id)
                    result = await db.execute(query)
                    fresh_content = result.scalar_one_or_none()
                    
                    if fresh_content:
                        fresh_content.embedding = embedding
                        await db.commit()
                
                return {
                    "status": "success",
                    "embedding_generated": True,
                    "embedding_dimensions": len(embedding)
                }
            else:
                return {
                    "status": "error",
                    "embedding_generated": False,
                    "error": "Failed to generate embedding"
                }
                
        except Exception as e:
            logger.error(f"Error generating embedding for content {content_item.id}: {str(e)}")
            return {
                "status": "error",
                "embedding_generated": False,
                "error": str(e)
            }
    
    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get statistics about the content database."""
        try:
            async with AsyncSessionLocal() as db:
                # Total counts
                total_query = select(func.count()).select_from(MarketingContent)
                total_result = await db.execute(total_query)
                total_content = total_result.scalar()
                
                vectorized_query = select(func.count()).select_from(MarketingContent).where(MarketingContent.embedding.isnot(None))
                vectorized_result = await db.execute(vectorized_query)
                vectorized_content = vectorized_result.scalar()
                
                # Content type breakdown
                content_type_stats = {}
                for content_type in ContentType:
                    type_query = select(func.count()).select_from(MarketingContent).where(MarketingContent.content_type == content_type)
                    type_result = await db.execute(type_query)
                    content_type_stats[content_type.value] = type_result.scalar()
                
                # Source type breakdown
                source_type_stats = {}
                for source_type in SourceType:
                    source_query = select(func.count()).select_from(MarketingContent).where(MarketingContent.source_type == source_type)
                    source_result = await db.execute(source_query)
                    source_type_stats[source_type.value] = source_result.scalar()
                
                # Approval status breakdown
                approval_stats = {}
                for status in ApprovalStatus:
                    approval_query = select(func.count()).select_from(MarketingContent).where(MarketingContent.approval_status == status)
                    approval_result = await db.execute(approval_query)
                    approval_stats[status.value] = approval_result.scalar()
                
                return {
                    "status": "success",
                    "statistics": {
                        "total_content": total_content,
                        "vectorized_content": vectorized_content,
                        "vectorization_percentage": round((vectorized_content / total_content * 100), 2) if total_content > 0 else 0,
                        "content_by_type": content_type_stats,
                        "content_by_source": source_type_stats,
                        "content_by_approval": approval_stats
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting content statistics: {str(e)}")
            return {"status": "error", "error": str(e)}


# Create global instance
content_management_service = ContentManagementService()
