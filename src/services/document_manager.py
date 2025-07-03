# Document Manager Service
"""
Service for managing advisor uploaded documents:
1. Store documents with metadata
2. Retrieve documents and summaries
3. Extract relevant sections for Warren context
4. Manage document lifecycle (CRUD operations)

SCRUM-39: DocumentManager Class with CRUD Operations
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update, desc, delete
from sqlalchemy.orm import selectinload

from src.models.advisor_workflow_models import SessionDocuments
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DocumentManager:
    """Service for managing advisor document storage and retrieval."""
    
    def __init__(self):
        """Initialize the document manager service."""
        pass
    
    # ===== CORE CRUD OPERATIONS =====
    
    async def store_document(
        self,
        document_data: Dict[str, Any],
        session_id: str
    ) -> str:
        """
        Store a document with metadata.
        
        Args:
            document_data: Dictionary containing document information
                - title: Document title
                - content_type: Type ('pdf', 'docx', 'txt', 'video_transcript')
                - full_content: Complete extracted text
                - original_filename: Original file name (optional)
                - file_size_bytes: File size (optional)
                - metadata: Additional processing metadata (optional)
            session_id: Associated advisor session ID
            
        Returns:
            str: Document ID of stored document
        """
        async with AsyncSessionLocal() as db:
            try:
                # Generate unique document ID
                document_id = f"doc_{uuid.uuid4().hex[:12]}"
                
                # Calculate word count
                word_count = len(document_data.get('full_content', '').split())
                
                # Create document record
                document = SessionDocuments(
                    id=document_id,
                    session_id=session_id,
                    title=document_data.get('title', 'Untitled Document'),
                    content_type=document_data.get('content_type', 'txt'),
                    original_filename=document_data.get('original_filename'),
                    file_size_bytes=document_data.get('file_size_bytes'),
                    full_content=document_data.get('full_content', ''),
                    word_count=word_count,
                    document_metadata=json.dumps(document_data.get('metadata', {})),
                    processing_status='pending'
                )
                
                db.add(document)
                await db.commit()
                await db.refresh(document)
                
                logger.info(f"Document stored successfully: {document_id}")
                return document_id
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error storing document: {str(e)}")
                raise Exception(f"Failed to store document: {str(e)}")
    
    async def retrieve_full_document(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve complete document information.
        
        Args:
            document_id: ID of document to retrieve
            
        Returns:
            Dict containing full document data
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(SessionDocuments).where(SessionDocuments.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document not found: {document_id}")
                
                return {
                    "id": document.id,
                    "session_id": document.session_id,
                    "title": document.title,
                    "content_type": document.content_type,
                    "original_filename": document.original_filename,
                    "file_size_bytes": document.file_size_bytes,
                    "full_content": document.full_content,
                    "summary": document.summary,
                    "word_count": document.word_count,
                    "metadata": json.loads(document.document_metadata or '{}'),
                    "processing_status": document.processing_status,
                    "processing_error": document.processing_error,
                    "times_referenced": document.times_referenced,
                    "last_referenced_at": document.last_referenced_at,
                    "created_at": document.created_at.isoformat(),
                    "updated_at": document.updated_at.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error retrieving document {document_id}: {str(e)}")
                raise Exception(f"Failed to retrieve document: {str(e)}")
    
    async def get_context_summary(self, document_id: str) -> str:
        """
        Get document summary for Warren context use.
        
        Args:
            document_id: ID of document
            
        Returns:
            str: Document summary text (or first 1000 chars if no summary)
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(SessionDocuments.summary, SessionDocuments.full_content).where(
                    SessionDocuments.id == document_id
                )
                result = await db.execute(stmt)
                row = result.first()
                
                if not row:
                    raise ValueError(f"Document not found: {document_id}")
                
                # Return summary if available, otherwise first 1000 characters
                if row.summary:
                    return row.summary
                else:
                    return row.full_content[:1000] + "..." if len(row.full_content) > 1000 else row.full_content
                
            except Exception as e:
                logger.error(f"Error getting summary for document {document_id}: {str(e)}")
                raise Exception(f"Failed to get document summary: {str(e)}")
    
    async def extract_relevant_sections(
        self,
        document_id: str,
        query: str,
        max_length: int = 2000
    ) -> str:
        """
        Extract relevant sections from document based on query.
        
        Args:
            document_id: ID of document
            query: Search query to find relevant sections
            max_length: Maximum length of returned text
            
        Returns:
            str: Relevant sections of document
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(SessionDocuments.full_content, SessionDocuments.title).where(
                    SessionDocuments.id == document_id
                )
                result = await db.execute(stmt)
                row = result.first()
                
                if not row:
                    raise ValueError(f"Document not found: {document_id}")
                
                full_content = row.full_content
                title = row.title
                
                # Simple keyword-based extraction (can be enhanced with semantic search later)
                query_terms = query.lower().split()
                paragraphs = full_content.split('\n\n')
                
                # Score paragraphs based on query term matches
                scored_paragraphs = []
                for paragraph in paragraphs:
                    if len(paragraph.strip()) < 50:  # Skip very short paragraphs
                        continue
                    
                    score = 0
                    paragraph_lower = paragraph.lower()
                    for term in query_terms:
                        score += paragraph_lower.count(term)
                    
                    if score > 0:
                        scored_paragraphs.append((score, paragraph))
                
                # Sort by relevance and combine top paragraphs
                scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
                
                relevant_text = f"Relevant sections from '{title}':\n\n"
                current_length = len(relevant_text)
                
                for score, paragraph in scored_paragraphs:
                    if current_length + len(paragraph) > max_length:
                        break
                    relevant_text += paragraph + "\n\n"
                    current_length += len(paragraph) + 2
                
                # Update reference tracking
                await self._update_reference_count(db, document_id)
                
                return relevant_text.strip()
                
            except Exception as e:
                logger.error(f"Error extracting sections from document {document_id}: {str(e)}")
                raise Exception(f"Failed to extract relevant sections: {str(e)}")
    
    async def get_session_documents(
        self,
        session_id: str,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for a specific session.
        
        Args:
            session_id: Session ID to filter by
            include_content: Whether to include full content in response
            
        Returns:
            List of document dictionaries
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(SessionDocuments).where(
                    SessionDocuments.session_id == session_id
                ).order_by(desc(SessionDocuments.created_at))
                
                result = await db.execute(stmt)
                documents = result.scalars().all()
                
                document_list = []
                for doc in documents:
                    doc_dict = {
                        "id": doc.id,
                        "title": doc.title,
                        "content_type": doc.content_type,
                        "original_filename": doc.original_filename,
                        "file_size_bytes": doc.file_size_bytes,
                        "word_count": doc.word_count,
                        "processing_status": doc.processing_status,
                        "times_referenced": doc.times_referenced,
                        "created_at": doc.created_at.isoformat()
                    }
                    
                    if include_content:
                        doc_dict["full_content"] = doc.full_content
                        doc_dict["summary"] = doc.summary
                    
                    document_list.append(doc_dict)
                
                return document_list
                
            except Exception as e:
                logger.error(f"Error getting session documents for {session_id}: {str(e)}")
                raise Exception(f"Failed to get session documents: {str(e)}")
    
    async def update_document(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update document metadata or content.
        
        Args:
            document_id: ID of document to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: Success status
        """
        async with AsyncSessionLocal() as db:
            try:
                # Build update statement
                update_data = {}
                
                # Map allowed update fields
                allowed_fields = [
                    'title', 'full_content', 'summary', 'processing_status', 'processing_error',
                    'document_metadata'
                ]
                
                for field in allowed_fields:
                    if field in updates:
                        if field == 'document_metadata' and isinstance(updates[field], dict):
                            update_data[field] = json.dumps(updates[field])
                        else:
                            update_data[field] = updates[field]
                
                # If full_content is being updated, recalculate word count
                if 'full_content' in updates:
                    update_data['word_count'] = len(updates['full_content'].split())
                
                if not update_data:
                    logger.warning(f"No valid fields to update for document {document_id}")
                    return False
                
                update_data['updated_at'] = func.now()
                
                stmt = update(SessionDocuments).where(
                    SessionDocuments.id == document_id
                ).values(**update_data)
                
                result = await db.execute(stmt)
                await db.commit()
                
                if result.rowcount == 0:
                    raise ValueError(f"Document not found: {document_id}")
                
                logger.info(f"Document updated successfully: {document_id}")
                return True
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error updating document {document_id}: {str(e)}")
                raise Exception(f"Failed to update document: {str(e)}")
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            bool: Success status
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = delete(SessionDocuments).where(SessionDocuments.id == document_id)
                result = await db.execute(stmt)
                await db.commit()
                
                if result.rowcount == 0:
                    raise ValueError(f"Document not found: {document_id}")
                
                logger.info(f"Document deleted successfully: {document_id}")
                return True
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error deleting document {document_id}: {str(e)}")
                raise Exception(f"Failed to delete document: {str(e)}")
    
    # ===== HELPER METHODS =====
    
    async def _update_reference_count(self, db: AsyncSession, document_id: str):
        """Update the reference count when document is accessed."""
        try:
            await db.execute(
                update(SessionDocuments)
                .where(SessionDocuments.id == document_id)
                .values(
                    times_referenced=SessionDocuments.times_referenced + 1,
                    last_referenced_at=func.now()
                )
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to update reference count for {document_id}: {str(e)}")
    
    # ===== UTILITY METHODS =====
    
    async def get_document_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about stored documents.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            Dict containing document statistics
        """
        async with AsyncSessionLocal() as db:
            try:
                base_stmt = select(SessionDocuments)
                if session_id:
                    base_stmt = base_stmt.where(SessionDocuments.session_id == session_id)
                
                result = await db.execute(base_stmt)
                documents = result.scalars().all()
                
                total_documents = len(documents)
                total_words = sum(doc.word_count for doc in documents)
                
                # Count by content type
                content_types = {}
                processing_statuses = {}
                
                for doc in documents:
                    content_types[doc.content_type] = content_types.get(doc.content_type, 0) + 1
                    processing_statuses[doc.processing_status] = processing_statuses.get(doc.processing_status, 0) + 1
                
                return {
                    "total_documents": total_documents,
                    "total_word_count": total_words,
                    "content_types": content_types,
                    "processing_statuses": processing_statuses,
                    "session_id": session_id
                }
                
            except Exception as e:
                logger.error(f"Error getting document statistics: {str(e)}")
                raise Exception(f"Failed to get document statistics: {str(e)}")
