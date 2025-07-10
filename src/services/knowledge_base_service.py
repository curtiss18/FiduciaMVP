# Knowledge Base Management Service - Simplified for Testing

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Service for managing knowledge base content and operations."""
    
    def __init__(self):
        self.knowledge_base_path = Path("data/knowledge_base")
        
    def get_available_files(self) -> List[Dict[str, Any]]:
        """Get list of available knowledge base files."""
        files = []
        
        # Get all markdown files in knowledge base
        for root, dirs, file_names in os.walk(self.knowledge_base_path):
            for file in file_names:
                if file.endswith('.md') and not file.startswith('PHASE_') and file != 'CONTENT_COLLECTION_PLAN.md':
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.knowledge_base_path)
                    
                    # Extract basic info
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        metadata = self._extract_metadata(content)
                        
                        files.append({
                            "filename": file,
                            "path": str(relative_path),
                            "full_path": str(file_path),
                            "title": metadata.get('title', file),
                            "content_type": metadata.get('content_type', 'unknown'),
                            "category": metadata.get('content_category', 'general'),
                            "tags": metadata.get('tags', ''),
                            "priority": metadata.get('priority', 'MEDIUM'),
                            "size": len(content),
                            "line_count": len(content.split('\n'))
                        })
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
                        continue
        
        return files
    
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
    
    def get_file_content(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get content of a specific file."""
        try:
            # Find the file
            for root, dirs, files in os.walk(self.knowledge_base_path):
                if filename in files:
                    file_path = Path(root) / filename
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    metadata = self._extract_metadata(content)
                    
                    return {
                        "filename": filename,
                        "content": content,
                        "metadata": metadata,
                        "size": len(content),
                        "line_count": len(content.split('\n'))
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return None
    
    def search_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple text search through all content files."""
        results = []
        query_lower = query.lower()
        
        try:
            files = self.get_available_files()
            
            for file_info in files:
                file_content = self.get_file_content(file_info['filename'])
                if file_content and query_lower in file_content['content'].lower():
                    # Find matching lines
                    lines = file_content['content'].split('\n')
                    matching_lines = []
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            matching_lines.append({
                                "line_number": i + 1,
                                "content": line.strip()
                            })
                    
                    results.append({
                        "file": file_info,
                        "matches": len(matching_lines),
                        "matching_lines": matching_lines[:5]  # First 5 matches
                    })
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            return []
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge base content."""
        try:
            files = self.get_available_files()
            
            # Count by category
            categories = {}
            doc_types = {}
            total_size = 0
            total_lines = 0
            
            for file_info in files:
                category = file_info.get('category', 'unknown')
                doc_type = file_info.get('content_type', 'unknown')
                
                categories[category] = categories.get(category, 0) + 1
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                total_size += file_info.get('size', 0)
                total_lines += file_info.get('line_count', 0)
            
            return {
                "total_files": len(files),
                "by_category": categories,
                "by_type": doc_types,
                "total_size": total_size,
                "total_lines": total_lines,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return {"error": str(e)}

# Utility functions for API endpoints
def get_knowledge_service() -> KnowledgeBaseService:
    """Get knowledge base service instance."""
    return KnowledgeBaseService()
