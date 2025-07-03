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
from src.services.document_manager import DocumentManager
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

# ===== DOCUMENT MANAGEMENT ENDPOINTS =====

class UploadDocumentRequest(BaseModel):
    session_id: str
    title: str
    content_type: str  # 'pdf', 'docx', 'txt', 'video_transcript'
    full_content: str
    original_filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    metadata: Optional[dict] = None

class UpdateDocumentRequest(BaseModel):
    title: Optional[str] = None
    full_content: Optional[str] = None
    summary: Optional[str] = None
    processing_status: Optional[str] = None
    processing_error: Optional[str] = None
    document_metadata: Optional[dict] = None

# Initialize DocumentManager instance
document_manager = DocumentManager()

@advisor_router.post("/documents/upload")
async def upload_document(request: UploadDocumentRequest):
    """
    Upload a document to a Warren session for context use.
    
    Supports PDF, DOCX, TXT, and video transcript content types.
    Documents are stored with metadata and can be used by Warren for content generation.
    """
    try:
        document_data = {
            "title": request.title,
            "content_type": request.content_type,
            "full_content": request.full_content,
            "original_filename": request.original_filename,
            "file_size_bytes": request.file_size_bytes,
            "metadata": request.metadata or {}
        }
        
        document_id = await document_manager.store_document(
            document_data=document_data,
            session_id=request.session_id
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": f"Document '{request.title}' uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advisor_router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get complete document information by ID."""
    try:
        document = await document_manager.retrieve_full_document(document_id)
        return {
            "status": "success",
            "document": document
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@advisor_router.get("/documents/{document_id}/summary")
async def get_document_summary(document_id: str):
    """Get document summary for Warren context use."""
    try:
        summary = await document_manager.get_context_summary(document_id)
        return {
            "status": "success",
            "document_id": document_id,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@advisor_router.get("/documents/{document_id}/relevant-sections")
async def extract_relevant_sections(
    document_id: str,
    query: str = Query(..., description="Search query to find relevant sections"),
    max_length: int = Query(2000, ge=100, le=5000, description="Maximum length of returned text")
):
    """Extract relevant sections from document based on query."""
    try:
        sections = await document_manager.extract_relevant_sections(
            document_id=document_id,
            query=query,
            max_length=max_length
        )
        return {
            "status": "success",
            "document_id": document_id,
            "query": query,
            "relevant_sections": sections
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@advisor_router.get("/sessions/{session_id}/documents")
async def get_session_documents(
    session_id: str,
    include_content: bool = Query(False, description="Whether to include full document content")
):
    """Get all documents for a specific Warren session."""
    try:
        documents = await document_manager.get_session_documents(
            session_id=session_id,
            include_content=include_content
        )
        return {
            "status": "success",
            "session_id": session_id,
            "document_count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advisor_router.put("/documents/{document_id}")
async def update_document(document_id: str, request: UpdateDocumentRequest):
    """Update document metadata or content."""
    try:
        # Build updates dictionary from non-None fields
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.full_content is not None:
            updates["full_content"] = request.full_content
        if request.summary is not None:
            updates["summary"] = request.summary
        if request.processing_status is not None:
            updates["processing_status"] = request.processing_status
        if request.processing_error is not None:
            updates["processing_error"] = request.processing_error
        if request.document_metadata is not None:
            updates["document_metadata"] = request.document_metadata
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")
        
        success = await document_manager.update_document(document_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advisor_router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from storage."""
    try:
        success = await document_manager.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "status": "success",
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advisor_router.get("/documents/statistics")
async def get_document_statistics(
    session_id: Optional[str] = Query(None, description="Optional session ID to filter by")
):
    """Get document statistics for advisor or specific session."""
    try:
        stats = await document_manager.get_document_statistics(session_id)
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
