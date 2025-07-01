# Advisor Workflow API Endpoints
"""
API endpoints for advisor content workflow:
1. Warren conversation management
2. Content library management
3. Compliance submission workflow
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from src.services.advisor_workflow_service import advisor_workflow_service
from src.models.advisor_workflow_models import ContentStatus

# Create router for advisor workflow endpoints
advisor_router = APIRouter(prefix="/advisor", tags=["advisor"])

# ===== REQUEST MODELS =====

class CreateSessionRequest(BaseModel):
    advisor_id: str
    title: Optional[str] = None

class SaveMessageRequest(BaseModel):
    session_id: str
    message_type: str  # 'user' or 'warren'
    content: str
    metadata: Optional[dict] = None

class SaveContentRequest(BaseModel):
    advisor_id: str
    title: str
    content_text: str
    content_type: str
    audience_type: str = "general_education"
    source_session_id: Optional[str] = None
    source_message_id: Optional[int] = None
    advisor_notes: Optional[str] = None
    intended_channels: Optional[List[str]] = None

class UpdateContentStatusRequest(BaseModel):
    new_status: str
    advisor_notes: Optional[str] = None

# ===== WARREN CONVERSATION ENDPOINTS =====

@advisor_router.post("/sessions/create")
async def create_advisor_session(request: CreateSessionRequest):
    """Create a new Warren chat session for an advisor."""
    result = await advisor_workflow_service.create_advisor_session(
        advisor_id=request.advisor_id,
        title=request.title
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.post("/sessions/messages/save")
async def save_warren_message(request: SaveMessageRequest):
    """Save a message to an advisor's Warren conversation."""
    result = await advisor_workflow_service.save_warren_message(
        session_id=request.session_id,
        message_type=request.message_type,
        content=request.content,
        metadata=request.metadata
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.get("/sessions")
async def get_advisor_sessions(
    advisor_id: str = Query(..., description="Advisor ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
):
    """Get advisor's Warren chat sessions."""
    result = await advisor_workflow_service.get_advisor_sessions(
        advisor_id=advisor_id,
        limit=limit,
        offset=offset
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    advisor_id: str = Query(..., description="Advisor ID for access control")
):
    """Get all messages for a specific Warren chat session."""
    result = await advisor_workflow_service.get_session_messages(
        session_id=session_id,
        advisor_id=advisor_id
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

# ===== CONTENT MANAGEMENT ENDPOINTS =====

@advisor_router.post("/content/save")
async def save_advisor_content(request: SaveContentRequest):
    """Save content piece to advisor's library."""
    result = await advisor_workflow_service.save_advisor_content(
        advisor_id=request.advisor_id,
        title=request.title,
        content_text=request.content_text,
        content_type=request.content_type,
        audience_type=request.audience_type,
        source_session_id=request.source_session_id,
        source_message_id=request.source_message_id,
        advisor_notes=request.advisor_notes,
        intended_channels=request.intended_channels
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.get("/content/library")
async def get_content_library(
    advisor_id: str = Query(..., description="Advisor ID"),
    status: Optional[str] = Query(None, description="Filter by content status"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """Get advisor's content library with filtering."""
    result = await advisor_workflow_service.get_advisor_content_library(
        advisor_id=advisor_id,
        status_filter=status,
        content_type_filter=content_type,
        limit=limit,
        offset=offset
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.put("/content/{content_id}/status")
async def update_content_status(
    content_id: int,
    request: UpdateContentStatusRequest,
    advisor_id: str = Query(..., description="Advisor ID for access control")
):
    """Update content status (e.g., submit for review)."""
    result = await advisor_workflow_service.update_content_status(
        content_id=content_id,
        advisor_id=advisor_id,
        new_status=request.new_status,
        advisor_notes=request.advisor_notes
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.put("/content/{content_id}")
async def update_content(
    content_id: int,
    advisor_id: str = Query(..., description="Advisor ID for access control"),
    title: str = None,
    content_text: str = None,
    advisor_notes: str = None,
    source_metadata: dict = None
):
    """Update full content (for session updates)."""
    result = await advisor_workflow_service.update_content(
        content_id=content_id,
        advisor_id=advisor_id,
        title=title,
        content_text=content_text,
        advisor_notes=advisor_notes,
        source_metadata=source_metadata
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@advisor_router.get("/content/statistics")
async def get_content_statistics(
    advisor_id: str = Query(..., description="Advisor ID")
):
    """Get advisor's content statistics."""
    result = await advisor_workflow_service.get_content_statistics(advisor_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

# ===== UTILITY ENDPOINTS =====

@advisor_router.get("/enums")
async def get_advisor_enums():
    """Get available enum values for advisor workflow."""
    from src.models.refactored_database import ContentType, AudienceType
    
    return {
        "status": "success",
        "enums": {
            "content_types": [e.value for e in ContentType],
            "audience_types": [e.value for e in AudienceType],
            "content_statuses": [e.value for e in ContentStatus]
        }
    }
