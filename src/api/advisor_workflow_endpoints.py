# Advisor Workflow API Endpoints
"""
API endpoints for advisor content workflow:
1. Warren conversation management
2. Content library management
3. Compliance submission workflow
"""

import logging
from fastapi import APIRouter, Query, HTTPException, File, UploadFile, Form
from typing import Optional, List
from pydantic import BaseModel

from src.services.advisor_workflow_service import advisor_workflow_service
from src.services.document_manager import DocumentManager
from src.services.document_processor import DocumentProcessor
from src.models.advisor_workflow_models import ContentStatus

logger = logging.getLogger(__name__)

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

# Initialize service instances
document_manager = DocumentManager()
document_processor = DocumentProcessor()

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

@advisor_router.post("/documents/upload-file")
async def upload_file_with_processing(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    titles: Optional[str] = Form(None)
):
    """
    Enhanced multi-file upload with full multi-modal processing.
    
    Supports multiple PDF, DOCX, TXT files with comprehensive:
    - Text extraction
    - Image and chart detection  
    - Table extraction with structured data
    - Visual element descriptions
    - Warren-optimized context generation
    - AI-powered summarization
    - Security validation
    - Batch processing with partial success handling
    
    SCRUM-40: Enhanced Multi-Modal Document Processing
    SCRUM-41: AI-Powered Document Summarization  
    SCRUM-42: Multiple File Upload Support
    """
    try:
        # Initialize processing results
        successful_uploads = []
        failed_uploads = []
        total_files = len(files)
        
        # Parse titles if provided (comma-separated or individual titles)
        file_titles = []
        if titles:
            # Split by comma and strip whitespace
            title_list = [title.strip() for title in titles.split(',')]
            file_titles = title_list
        
        # Process each file individually
        for idx, file in enumerate(files):
            file_result = {
                "filename": file.filename,
                "index": idx,
                "status": "processing"
            }
            
            try:
                # Get title for this file
                if idx < len(file_titles) and file_titles[idx]:
                    file_title = file_titles[idx]
                else:
                    # Generate title from filename
                    base_name = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
                    file_title = base_name.replace('_', ' ').replace('-', ' ').title()
                
                # Read file content
                file_content = await file.read()
                
                # Determine content type from filename
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                if file_ext not in ['pdf', 'docx', 'txt']:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                
                # Process file with DocumentProcessor
                processed_data = await document_processor.process_uploaded_file(
                    file_content=file_content,
                    filename=file.filename,
                    content_type=file_ext
                )
                
                # Prepare document data for storage
                document_data = {
                    "title": file_title,
                    "content_type": file_ext,
                    "full_content": processed_data["text"],
                    "original_filename": file.filename,
                    "file_size_bytes": len(file_content),
                    "metadata": {
                        # Core metadata
                        **processed_data["metadata"],
                        # Multi-modal content
                        "images": processed_data["images"],
                        "tables": processed_data["tables"],
                        "visual_summary": processed_data["visual_summary"],
                        "warren_context": processed_data["warren_context"],
                        # Processing info
                        "multi_modal_processed": True,
                        "processor_version": "1.0.0",
                        # Batch info
                        "batch_upload": True,
                        "batch_index": idx,
                        "batch_total": total_files
                    }
                }
                
                # Store processed document
                document_id = await document_manager.store_document(
                    document_data=document_data,
                    session_id=session_id
                )
                
                # Generate AI summary automatically (SCRUM-41 Phase 1.3)
                summary_success = False
                summary_info = {}
                try:
                    summary_success = await document_manager.update_document_with_summary(document_id)
                    if summary_success:
                        # Get summary info for response
                        updated_doc = await document_manager.retrieve_full_document(document_id)
                        if updated_doc and updated_doc.get('summary'):
                            from src.services.context_assembler import TokenManager
                            token_manager = TokenManager()
                            summary_tokens = token_manager.count_tokens(updated_doc['summary'])
                            summary_info = {
                                "summary_generated": True,
                                "summary_tokens": summary_tokens,
                                "summary_preview": updated_doc['summary'][:150] + "..." if len(updated_doc['summary']) > 150 else updated_doc['summary']
                            }
                except Exception as e:
                    logger.warning(f"AI summarization failed for document {document_id}: {str(e)}")
                    summary_info = {
                        "summary_generated": False,
                        "summary_error": "AI summarization failed but document was processed successfully"
                    }
                
                # Update file result with success
                file_result.update({
                    "status": "success",
                    "document_id": document_id,
                    "title": file_title,
                    "processing_results": {
                        "text_extracted": True,
                        "word_count": processed_data["metadata"]["word_count"],
                        "images_detected": processed_data["metadata"]["total_images"],
                        "tables_detected": processed_data["metadata"]["total_tables"],
                        "visual_summary": processed_data["visual_summary"],
                        "processing_time_ms": processed_data["metadata"]["processing_time_ms"],
                        # AI Summarization results (SCRUM-41)
                        **summary_info
                    }
                })
                
                successful_uploads.append(file_result)
                
            except Exception as file_error:
                # Handle individual file failure
                file_result.update({
                    "status": "failed",
                    "error": str(file_error),
                    "error_type": type(file_error).__name__
                })
                failed_uploads.append(file_result)
                logger.error(f"Failed to process file {file.filename}: {str(file_error)}")
        
        # Prepare batch response
        batch_success = len(successful_uploads) > 0
        response = {
            "status": "success" if batch_success else "failed",
            "message": f"Batch upload complete: {len(successful_uploads)}/{total_files} files processed successfully",
            "batch_results": {
                "total_files": total_files,
                "successful_count": len(successful_uploads),
                "failed_count": len(failed_uploads),
                "success_rate": len(successful_uploads) / total_files if total_files > 0 else 0,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads
            }
        }
        
        # Return appropriate status code
        if not batch_success:
            raise HTTPException(status_code=400, detail=response)
        elif failed_uploads:
            # Partial success - return 207 Multi-Status if possible, otherwise 200 with warnings
            response["status"] = "partial_success"
            response["message"] = f"Partial success: {len(successful_uploads)}/{total_files} files processed"
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch file processing failed: {str(e)}")

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
