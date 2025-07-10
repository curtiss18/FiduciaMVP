# Async Knowledge Base Database Service

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.database import KnowledgeBaseDocument
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class AsyncKnowledgeBaseService:
    """Async service for loading knowledge base content into database."""
    
    def __init__(self):
        self.knowledge_base_path = Path("data/knowledge_base")
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from document markdown headers."""
        metadata = {}
        lines = content.split('\n')
        
        in_metadata = False
        for line in lines:
            line = line.strip()
            
            if line == "## Document Metadata":
                in_metadata = True
                continue
            elif line.startswith("##") and in_metadata:
                break
            elif in_metadata and line.startswith("- **"):
                # Parse metadata lines like: - **Title**: SEC Marketing Rule
                try:
                    key_part = line.split("**")[1].lower().replace(" ", "_")
                    value_part = line.split(": ", 1)[1] if ": " in line else ""
                    metadata[key_part] = value_part
                except:
                    continue
        
        return metadata
    
    def _determine_category(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Determine document category based on file path and metadata."""
        path_str = str(file_path).lower()
        
        if 'regulations' in path_str:
            return 'regulation'
        elif 'approved_examples' in path_str:
            return 'approved_example'
        elif 'disclaimers' in path_str:
            return 'disclaimer'
        elif 'violations' in path_str:
            return 'violation'
        elif 'platform_guidelines' in path_str:
            return 'platform_guideline'
        else:
            return metadata.get('content_category', 'general')
    
    async def load_document_from_file(self, file_path: Path, db: AsyncSession) -> Optional[KnowledgeBaseDocument]:
        """Load a single document from file into the database."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from document header
            metadata = self._extract_metadata(content)
            category = self._determine_category(file_path, metadata)
            
            # Determine document type from path
            if 'regulations' in str(file_path):
                doc_type = 'regulation'
            elif 'approved_examples' in str(file_path):
                doc_type = 'approved_example'
            elif 'disclaimers' in str(file_path):
                doc_type = 'disclaimer'
            elif 'violations' in str(file_path):
                doc_type = 'violation'
            elif 'platform_guidelines' in str(file_path):
                doc_type = 'platform_guideline'
            else:
                doc_type = 'general'
            
            # Determine platform from metadata or filename
            platform = None
            if 'linkedin' in str(file_path).lower():
                platform = 'linkedin'
            elif 'twitter' in str(file_path).lower():
                platform = 'twitter'
            elif 'social' in str(file_path).lower():
                platform = 'social_media'
            
            # Create document record
            document = KnowledgeBaseDocument(
                title=metadata.get('title', file_path.stem),
                content=content,
                document_type=doc_type,
                source=str(file_path),
                platform=platform,
                compliance_score=1.0,  # All our documents are pre-approved
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add to database
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            logger.info(f"Loaded document: {document.title} (ID: {document.id})")
            return document
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            await db.rollback()
            return None
    
    async def load_all_documents(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load all documents from the knowledge base directory into database."""
        async with AsyncSessionLocal() as db:
            try:
                # Check if documents already exist (unless force reload)
                if not force_reload:
                    result = await db.execute(select(func.count(KnowledgeBaseDocument.id)))
                    existing_count = result.scalar()
                    if existing_count > 0:
                        return {
                            "status": "skipped",
                            "message": f"Database already contains {existing_count} documents. Use force_reload=true to reload.",
                            "existing_documents": existing_count
                        }
                
                # Clear existing documents if force reload
                if force_reload:
                    await db.execute("DELETE FROM knowledge_base_documents")
                    await db.commit()
                    logger.info("Cleared existing documents for reload")
                
                loaded_documents = []
                
                # Get all markdown files in knowledge base
                for root, dirs, files in os.walk(self.knowledge_base_path):
                    for file in files:
                        # Skip certain files
                        if (file.endswith('.md') and 
                            not file.startswith('PHASE_') and 
                            file != 'CONTENT_COLLECTION_PLAN.md'):
                            
                            file_path = Path(root) / file
                            document = await self.load_document_from_file(file_path, db)
                            if document:
                                loaded_documents.append({
                                    "id": document.id,
                                    "title": document.title,
                                    "document_type": document.document_type,
                                    "source": document.source
                                })
                
                return {
                    "status": "success",
                    "loaded_documents": len(loaded_documents),
                    "documents": loaded_documents
                }
                
            except Exception as e:
                logger.error(f"Error loading documents: {str(e)}")
                await db.rollback()
                return {
                    "status": "error",
                    "error": str(e)
                }
    
    async def get_document_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the knowledge base."""
        async with AsyncSessionLocal() as db:
            try:
                # Count total documents
                result = await db.execute(select(func.count(KnowledgeBaseDocument.id)))
                total_docs = result.scalar()
                
                # Count by document type
                result = await db.execute(select(KnowledgeBaseDocument.document_type).distinct())
                doc_types = result.scalars().all()
                type_counts = {}
                for doc_type in doc_types:
                    result = await db.execute(
                        select(func.count(KnowledgeBaseDocument.id)).where(
                            KnowledgeBaseDocument.document_type == doc_type
                        )
                    )
                    type_counts[doc_type] = result.scalar()
                
                # Count by platform
                result = await db.execute(
                    select(KnowledgeBaseDocument.platform, func.count(KnowledgeBaseDocument.id))
                    .group_by(KnowledgeBaseDocument.platform)
                )
                platform_counts = {platform or 'general': count for platform, count in result.all()}
                
                return {
                    "total_documents": total_docs,
                    "by_type": type_counts,
                    "by_platform": platform_counts,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting document summary: {str(e)}")
                return {"error": str(e)}
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents in database by content."""
        async with AsyncSessionLocal() as db:
            try:
                # Simple text search for now - will be replaced with vector search later
                result = await db.execute(
                    select(KnowledgeBaseDocument)
                    .where(KnowledgeBaseDocument.content.contains(query))
                    .limit(limit)
                )
                documents = result.scalars().all()
                
                return [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "platform": doc.platform,
                        "source": doc.source,
                        "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        "compliance_score": doc.compliance_score
                    }
                    for doc in documents
                ]
                
            except Exception as e:
                logger.error(f"Error searching documents: {str(e)}")
                return []

# Service instance
async_kb_service = AsyncKnowledgeBaseService()
