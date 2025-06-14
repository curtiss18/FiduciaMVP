# Vector Search Service
"""
Service for performing semantic similarity search using PostgreSQL + pgvector.
Handles vector similarity queries and hybrid search strategies.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, or_
from sqlalchemy.sql import func

from src.models.refactored_database import MarketingContent, ComplianceRules, ContentType, ApprovalStatus
from src.core.database import AsyncSessionLocal
from src.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for semantic similarity search using vector embeddings."""
    
    def __init__(self):
        """Initialize vector search service."""
        self.default_similarity_threshold = 0.4  # Lowered from 0.7 to 0.4 for better discovery
        self.max_results = 10
    
    async def search_marketing_content(
        self,
        query_text: str,
        content_type: Optional[ContentType] = None,
        audience_type: Optional[str] = None,
        similarity_threshold: float = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search marketing content using vector similarity.
        
        Args:
            query_text: User query text
            content_type: Filter by content type
            audience_type: Filter by audience type  
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum results to return
            
        Returns:
            List of similar marketing content with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await embedding_service.generate_embedding(query_text)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []
            
            threshold = similarity_threshold or self.default_similarity_threshold
            
            async with AsyncSessionLocal() as db:
                # Build base query
                query = select(
                    MarketingContent.id,
                    MarketingContent.title,
                    MarketingContent.content_text,
                    MarketingContent.content_type,
                    MarketingContent.audience_type,
                    MarketingContent.tags,
                    MarketingContent.usage_count,
                    MarketingContent.compliance_score,
                    MarketingContent.source_type,
                    # Calculate cosine similarity using pgvector
                    (1 - MarketingContent.embedding.cosine_distance(query_embedding)).label('similarity_score')
                ).where(
                    and_(
                        MarketingContent.embedding.isnot(None),  # Has embedding
                        MarketingContent.approval_status == ApprovalStatus.APPROVED,  # Approved content
                        (1 - MarketingContent.embedding.cosine_distance(query_embedding)) > threshold  # Above threshold
                    )
                )
                
                # Add content type filter
                if content_type:
                    query = query.where(MarketingContent.content_type == content_type)
                
                # Add audience type filter  
                if audience_type:
                    query = query.where(MarketingContent.audience_type == audience_type)
                
                # Order by similarity score descending, then by usage count
                query = query.order_by(
                    text('similarity_score DESC'),
                    MarketingContent.usage_count.desc()
                ).limit(limit)
                
                result = await db.execute(query)
                rows = result.all()
                
                # Convert to dictionaries with similarity scores
                results = []
                for row in rows:
                    results.append({
                        "id": row.id,
                        "title": row.title,
                        "content_text": row.content_text,
                        "content_type": row.content_type.value,
                        "audience_type": row.audience_type.value,
                        "tags": row.tags,
                        "usage_count": row.usage_count,
                        "compliance_score": row.compliance_score,
                        "source_type": row.source_type.value,
                        "similarity_score": float(row.similarity_score),
                        "search_method": "vector"
                    })
                
                logger.info(f"Vector search found {len(results)} marketing content results")
                return results
                
        except Exception as e:
            logger.error(f"Error in vector marketing content search: {str(e)}")
            return []
    
    async def search_compliance_rules(
        self,
        query_text: str,
        content_type: Optional[str] = None,
        similarity_threshold: float = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search compliance rules using vector similarity.
        
        Args:
            query_text: User query text
            content_type: Filter by applicable content types
            similarity_threshold: Minimum similarity score
            limit: Maximum results to return
            
        Returns:
            List of similar compliance rules with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await embedding_service.generate_embedding(query_text)
            if not query_embedding:
                logger.warning("Failed to generate query embedding for compliance rules")
                return []
            
            threshold = similarity_threshold or self.default_similarity_threshold
            
            async with AsyncSessionLocal() as db:
                # Build compliance rules query
                query = select(
                    ComplianceRules.id,
                    ComplianceRules.regulation_name,
                    ComplianceRules.rule_section,
                    ComplianceRules.requirement_text,
                    ComplianceRules.required_disclaimers,
                    ComplianceRules.prohibition_type,
                    ComplianceRules.applies_to_content_types,
                    ComplianceRules.applicability_scope,
                    # Calculate similarity - assume compliance rules will have embeddings too
                    text(f"1 - (embedding <=> '{query_embedding}') as similarity_score")
                ).where(
                    and_(
                        text("embedding IS NOT NULL"),  # Has embedding
                        text(f"1 - (embedding <=> '{query_embedding}') > {threshold}")  # Above threshold
                    )
                )
                
                # Filter by content type applicability
                if content_type:
                    query = query.where(
                        or_(
                            ComplianceRules.applies_to_content_types.contains(content_type),
                            ComplianceRules.applies_to_content_types.is_(None)  # Universal rules
                        )
                    )
                
                query = query.order_by(text('similarity_score DESC')).limit(limit)
                
                result = await db.execute(query)
                rows = result.all()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row.id,
                        "regulation_name": row.regulation_name,
                        "rule_section": row.rule_section,
                        "requirement_text": row.requirement_text,
                        "required_disclaimers": row.required_disclaimers,
                        "prohibition_type": row.prohibition_type,
                        "applies_to_content_types": row.applies_to_content_types,
                        "applicability_scope": row.applicability_scope,
                        "similarity_score": float(row.similarity_score),
                        "search_method": "vector"
                    })
                
                logger.info(f"Vector search found {len(results)} compliance rules")
                return results
                
        except Exception as e:
            logger.error(f"Error in vector compliance rules search: {str(e)}")
            return []
    
    async def hybrid_search_marketing_content(
        self,
        query_text: str,
        content_type: Optional[ContentType] = None,
        similarity_threshold: float = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and keyword search for marketing content.
        
        Args:
            query_text: User query text
            content_type: Filter by content type
            similarity_threshold: Minimum similarity score for vector search
            limit: Maximum results to return
            
        Returns:
            Combined and deduplicated results from both search methods
        """
        try:
            # 1. Try vector search first
            vector_results = await self.search_marketing_content(
                query_text=query_text,
                content_type=content_type,
                similarity_threshold=similarity_threshold,
                limit=max(3, limit // 2)  # Get fewer from vector to leave room for keyword
            )
            
            # 2. Keyword search as supplement/fallback
            keyword_results = await self._keyword_search_marketing_content(
                query_text=query_text,
                content_type=content_type,
                limit=max(2, limit - len(vector_results))
            )
            
            # 3. Combine and deduplicate results
            combined_results = self._combine_search_results(
                vector_results, keyword_results, max_results=limit
            )
            
            logger.info(f"Hybrid search: {len(vector_results)} vector + {len(keyword_results)} keyword = {len(combined_results)} combined")
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            return []
    
    async def _keyword_search_marketing_content(
        self,
        query_text: str,
        content_type: Optional[ContentType] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search for marketing content."""
        async with AsyncSessionLocal() as db:
            try:
                query_lower = query_text.lower()
                
                search_query = select(MarketingContent).where(
                    and_(
                        MarketingContent.approval_status == ApprovalStatus.APPROVED,
                        or_(
                            MarketingContent.content_text.contains(query_text),
                            MarketingContent.title.contains(query_text),
                            MarketingContent.tags.contains(query_text)
                        )
                    )
                )
                
                if content_type:
                    search_query = search_query.where(MarketingContent.content_type == content_type)
                
                search_query = search_query.order_by(
                    MarketingContent.usage_count.desc(),
                    MarketingContent.compliance_score.desc()
                ).limit(limit)
                
                result = await db.execute(search_query)
                contents = result.scalars().all()
                
                return [
                    {
                        "id": content.id,
                        "title": content.title,
                        "content_text": content.content_text,
                        "content_type": content.content_type.value,
                        "audience_type": content.audience_type.value,
                        "tags": content.tags,
                        "usage_count": content.usage_count,
                        "compliance_score": content.compliance_score,
                        "source_type": content.source_type.value,
                        "similarity_score": 0.5,  # Default score for keyword matches
                        "search_method": "keyword"
                    }
                    for content in contents
                ]
                
            except Exception as e:
                logger.error(f"Error in keyword search: {str(e)}")
                return []
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate search results from multiple methods."""
        seen_ids = set()
        combined = []
        
        # Add vector results first (higher priority)
        for result in vector_results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                combined.append(result)
        
        # Add keyword results if not already included
        for result in keyword_results:
            if result["id"] not in seen_ids and len(combined) < max_results:
                seen_ids.add(result["id"])
                combined.append(result)
        
        return combined[:max_results]
    
    async def get_vector_search_stats(self) -> Dict[str, Any]:
        """Get statistics about vector search readiness."""
        async with AsyncSessionLocal() as db:
            try:
                # Count content with embeddings
                marketing_with_embeddings = await db.execute(
                    select(func.count(MarketingContent.id)).where(
                        MarketingContent.embedding.isnot(None)
                    )
                )
                marketing_embedded_count = marketing_with_embeddings.scalar()
                
                marketing_total = await db.execute(
                    select(func.count(MarketingContent.id))
                )
                marketing_total_count = marketing_total.scalar()
                
                # Check compliance rules embeddings (may not exist yet)
                compliance_embedded_count = 0
                try:
                    compliance_with_embeddings = await db.execute(
                        text("SELECT COUNT(*) FROM compliance_rules WHERE embedding IS NOT NULL")
                    )
                    compliance_embedded_count = compliance_with_embeddings.scalar()
                except Exception as e:
                    logger.warning(f"Could not count compliance rules embeddings: {e}")
                    compliance_embedded_count = 0
                
                compliance_total = await db.execute(
                    select(func.count(ComplianceRules.id))
                )
                compliance_total_count = compliance_total.scalar()
                
                return {
                    "marketing_content": {
                        "total": marketing_total_count,
                        "with_embeddings": marketing_embedded_count,
                        "embedding_percentage": (marketing_embedded_count / marketing_total_count * 100) if marketing_total_count > 0 else 0
                    },
                    "compliance_rules": {
                        "total": compliance_total_count,
                        "with_embeddings": compliance_embedded_count,
                        "embedding_percentage": (compliance_embedded_count / compliance_total_count * 100) if compliance_total_count > 0 else 0
                    },
                    "vector_search_ready": marketing_embedded_count > 0
                }
                
            except Exception as e:
                logger.error(f"Error getting vector search stats: {str(e)}")
                return {"error": str(e)}
    
    async def check_readiness(self) -> Dict[str, Any]:
        """
        Check if vector search is ready for use.
        
        Returns:
            Dict with ready status and reason if not ready
        """
        async with AsyncSessionLocal() as db:
            try:
                # Simple check: count marketing content with embeddings
                marketing_with_embeddings = await db.execute(
                    select(func.count(MarketingContent.id)).where(
                        MarketingContent.embedding.isnot(None)
                    )
                )
                marketing_embedded_count = marketing_with_embeddings.scalar()
                
                if marketing_embedded_count > 0:
                    return {
                        "ready": True,
                        "reason": "vector_search_operational",
                        "marketing_content_count": marketing_embedded_count
                    }
                else:
                    return {
                        "ready": False,
                        "reason": "no_vectorized_content",
                        "marketing_content_count": 0
                    }
                    
            except Exception as e:
                logger.error(f"Error checking vector search readiness: {str(e)}")
                # If there's a database error, assume vector search is not ready
                return {
                    "ready": False,
                    "reason": f"database_error: {str(e)}"
                }
            finally:
                # Ensure clean transaction state
                await db.rollback()


# Service instance
vector_search_service = VectorSearchService()
