# Content Vectorization Service
"""
Service for generating and managing embeddings for existing and new content.
Handles batch processing of existing content and real-time embedding of new content.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, text, func
from sqlalchemy.orm import selectinload

from src.models.refactored_database import MarketingContent, ComplianceRules, ApprovalStatus
from src.core.database import AsyncSessionLocal
from src.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class ContentVectorizationService:
    """Service for generating and managing content embeddings."""
    
    def __init__(self):
        """Initialize the vectorization service."""
        self.batch_size = 10  # Process content in batches
    
    async def vectorize_existing_marketing_content(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Generate embeddings for all existing marketing content.
        
        Args:
            force_update: If True, regenerate embeddings even if they exist
            
        Returns:
            Results summary with counts and any errors
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get content that needs embeddings
                if force_update:
                    # Get all approved content
                    query = select(MarketingContent).where(
                        MarketingContent.approval_status == ApprovalStatus.APPROVED
                    )
                else:
                    # Get only content without embeddings
                    query = select(MarketingContent).where(
                        and_(
                            MarketingContent.approval_status == ApprovalStatus.APPROVED,
                            MarketingContent.embedding.is_(None)
                        )
                    )
                
                result = await db.execute(query)
                content_items = result.scalars().all()
                
                if not content_items:
                    return {
                        "status": "success",
                        "message": "No marketing content needs vectorization",
                        "processed": 0,
                        "skipped": 0,
                        "errors": 0
                    }
                
                logger.info(f"Starting vectorization of {len(content_items)} marketing content items")
                
                processed = 0
                errors = 0
                total_cost = 0.0
                
                # Process in batches
                for i in range(0, len(content_items), self.batch_size):
                    batch = content_items[i:i + self.batch_size]
                    
                    # Prepare texts for embedding
                    texts_to_embed = []
                    for content in batch:
                        prepared_text = embedding_service.prepare_text_for_embedding(
                            title=content.title,
                            content=content.content_text,
                            content_type=content.content_type.value if content.content_type else None,
                            audience_type=content.audience_type.value if content.audience_type else None,
                            tags=content.tags
                        )
                        texts_to_embed.append(prepared_text)
                    
                    # Generate embeddings for batch
                    embeddings = await embedding_service.generate_batch_embeddings(texts_to_embed)
                    
                    # Update content with embeddings
                    for j, (content, embedding) in enumerate(zip(batch, embeddings)):
                        if embedding:
                            content.embedding = embedding
                            processed += 1
                            
                            # Estimate cost for this item
                            token_count = embedding_service.count_tokens(texts_to_embed[j])
                            total_cost += embedding_service.estimate_cost(token_count)
                        else:
                            errors += 1
                            logger.error(f"Failed to generate embedding for content ID {content.id}")
                    
                    # Commit batch
                    await db.commit()
                    logger.info(f"Processed batch {i//self.batch_size + 1}: {len([e for e in embeddings if e])} successful")
                
                return {
                    "status": "success",
                    "message": f"Vectorization completed",
                    "processed": processed,
                    "errors": errors,
                    "total_items": len(content_items),
                    "estimated_cost": total_cost,
                    "batch_count": (len(content_items) + self.batch_size - 1) // self.batch_size
                }
                
            except Exception as e:
                logger.error(f"Error in marketing content vectorization: {str(e)}")
                await db.rollback()
                return {
                    "status": "error",
                    "error": str(e),
                    "processed": 0
                }
    
    async def vectorize_single_content(self, content_id: int) -> Dict[str, Any]:
        """
        Generate embedding for a single marketing content item.
        
        Args:
            content_id: ID of the content to vectorize
            
        Returns:
            Result of the vectorization
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get the content
                result = await db.execute(
                    select(MarketingContent).where(MarketingContent.id == content_id)
                )
                content = result.scalar_one_or_none()
                
                if not content:
                    return {
                        "status": "error",
                        "error": f"Content with ID {content_id} not found"
                    }
                
                # Prepare text for embedding
                prepared_text = embedding_service.prepare_text_for_embedding(
                    title=content.title,
                    content=content.content_text,
                    content_type=content.content_type.value if content.content_type else None,
                    audience_type=content.audience_type.value if content.audience_type else None,
                    tags=content.tags
                )
                
                # Generate embedding
                embedding = await embedding_service.generate_embedding(prepared_text)
                
                if embedding:
                    content.embedding = embedding
                    await db.commit()
                    
                    # Calculate cost
                    token_count = embedding_service.count_tokens(prepared_text)
                    cost = embedding_service.estimate_cost(token_count)
                    
                    return {
                        "status": "success",
                        "content_id": content_id,
                        "title": content.title,
                        "token_count": token_count,
                        "estimated_cost": cost,
                        "embedding_dimensions": len(embedding)
                    }
                else:
                    return {
                        "status": "error",
                        "error": "Failed to generate embedding"
                    }
                    
            except Exception as e:
                logger.error(f"Error vectorizing single content {content_id}: {str(e)}")
                await db.rollback()
                return {
                    "status": "error",
                    "error": str(e)
                }
    
    async def get_vectorization_status(self) -> Dict[str, Any]:
        """Get current status of content vectorization."""
        async with AsyncSessionLocal() as db:
            try:
                # Marketing content stats
                marketing_total = await db.execute(
                    select(func.count(MarketingContent.id)).where(
                        MarketingContent.approval_status == ApprovalStatus.APPROVED
                    )
                )
                marketing_total_count = marketing_total.scalar()
                
                marketing_vectorized = await db.execute(
                    select(func.count(MarketingContent.id)).where(
                        and_(
                            MarketingContent.approval_status == ApprovalStatus.APPROVED,
                            MarketingContent.embedding.isnot(None)
                        )
                    )
                )
                marketing_vectorized_count = marketing_vectorized.scalar()
                
                return {
                    "marketing_content": {
                        "total_approved": marketing_total_count,
                        "vectorized": marketing_vectorized_count,
                        "pending": marketing_total_count - marketing_vectorized_count,
                        "completion_percentage": (marketing_vectorized_count / marketing_total_count * 100) if marketing_total_count > 0 else 0
                    },
                    "overall_status": "ready" if marketing_vectorized_count > 0 else "pending",
                    "vector_search_available": marketing_vectorized_count > 0
                }
                
            except Exception as e:
                logger.error(f"Error getting vectorization status: {str(e)}")
                return {"error": str(e)}
    
    async def estimate_vectorization_cost(self) -> Dict[str, Any]:
        """Estimate the cost of vectorizing all unprocessed content."""
        async with AsyncSessionLocal() as db:
            try:
                # Get unprocessed marketing content
                unprocessed_marketing = await db.execute(
                    select(MarketingContent).where(
                        and_(
                            MarketingContent.approval_status == ApprovalStatus.APPROVED,
                            MarketingContent.embedding.is_(None)
                        )
                    )
                )
                marketing_items = unprocessed_marketing.scalars().all()
                
                # Estimate tokens and cost
                marketing_tokens = 0
                for content in marketing_items:
                    prepared_text = embedding_service.prepare_text_for_embedding(
                        title=content.title,
                        content=content.content_text,
                        content_type=content.content_type.value if content.content_type else None,
                        audience_type=content.audience_type.value if content.audience_type else None,
                        tags=content.tags
                    )
                    marketing_tokens += embedding_service.count_tokens(prepared_text)
                
                total_cost = embedding_service.estimate_cost(marketing_tokens)
                
                return {
                    "marketing_content": {
                        "items": len(marketing_items),
                        "estimated_tokens": marketing_tokens,
                        "estimated_cost": total_cost
                    },
                    "total": {
                        "items": len(marketing_items),
                        "estimated_tokens": marketing_tokens,
                        "estimated_cost": total_cost
                    },
                    "note": f"Estimated cost is approximately ${total_cost:.4f} for {marketing_tokens} tokens"
                }
                
            except Exception as e:
                logger.error(f"Error estimating vectorization cost: {str(e)}")
                return {"error": str(e)}
    
    async def vectorize_existing_compliance_rules(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Generate embeddings for all existing compliance rules.
        
        Args:
            force_update: If True, regenerate embeddings even if they exist
            
        Returns:
            Results summary with counts and any errors
        """
        async with AsyncSessionLocal() as db:
            try:
                # Get compliance rules that need embeddings
                if force_update:
                    # Get all compliance rules
                    query = select(ComplianceRules)
                else:
                    # Get only rules without embeddings
                    query = select(ComplianceRules).where(
                        ComplianceRules.embedding.is_(None)
                    )
                
                result = await db.execute(query)
                compliance_rules = result.scalars().all()
                
                if not compliance_rules:
                    return {
                        "status": "success",
                        "message": "No compliance rules need vectorization",
                        "processed": 0,
                        "total_cost": 0.0
                    }
                
                processed = 0
                failed = 0
                total_cost = 0.0
                errors = []
                
                logger.info(f"Starting vectorization of {len(compliance_rules)} compliance rules")
                
                for rule in compliance_rules:
                    try:
                        # Prepare text for embedding using correct field names and parameters
                        prepared_text = embedding_service.prepare_text_for_embedding(
                            title=rule.regulation_name,  # Use regulation_name as title
                            content=rule.requirement_text,  # Use requirement_text as content
                            content_type=getattr(rule, 'prohibition_type', None),  # Map prohibition_type to content_type
                            audience_type=getattr(rule, 'applicability_scope', None),  # Map applicability_scope to audience_type
                            tags=getattr(rule, 'applies_to_content_types', None)  # Keep tags as is
                        )
                        
                        # Generate embedding
                        embedding = await embedding_service.generate_embedding(prepared_text)
                        
                        if embedding:
                            rule.embedding = embedding
                            processed += 1
                            
                            # Calculate cost
                            token_count = embedding_service.count_tokens(prepared_text)
                            cost = embedding_service.estimate_cost(token_count)
                            total_cost += cost
                            
                            logger.info(f"Vectorized compliance rule: {rule.regulation_name} ({token_count} tokens, ${cost:.6f})")
                        else:
                            failed += 1
                            errors.append(f"Failed to generate embedding for rule: {rule.regulation_name}")
                            
                    except Exception as e:
                        failed += 1
                        error_msg = f"Error processing rule {rule.regulation_name}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # Commit all changes
                await db.commit()
                
                return {
                    "status": "success" if failed == 0 else "partial_success",
                    "processed": processed,
                    "failed": failed,
                    "total_rules": len(compliance_rules),
                    "total_cost": total_cost,
                    "errors": errors,
                    "message": f"Vectorized {processed} compliance rules (${total_cost:.6f} total cost)"
                }
                
            except Exception as e:
                logger.error(f"Error vectorizing compliance rules: {str(e)}")
                await db.rollback()
                return {
                    "status": "error",
                    "error": str(e)
                }


# Service instance
content_vectorization_service = ContentVectorizationService()
