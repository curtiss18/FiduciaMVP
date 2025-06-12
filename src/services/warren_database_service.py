# Warren Database Service - Uses Refactored Database
"""
Enhanced Warren service that uses the new granular content management database
instead of file-based knowledge system.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from src.models.refactored_database import (
    MarketingContent, ComplianceRules, WarrenInteractions, 
    ContentType, AudienceType, SourceType, ApprovalStatus
)
from src.core.database import AsyncSessionLocal
from src.services.claude_service import claude_service

logger = logging.getLogger(__name__)


class WarrenDatabaseService:
    """Enhanced Warren service using the refactored database for knowledge retrieval."""
    
    def __init__(self):
        """Initialize the Warren database service."""
        pass
    
    async def search_marketing_content(
        self, 
        query: str, 
        content_type: Optional[ContentType] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search marketing content using text search (will be enhanced with vector search)."""
        async with AsyncSessionLocal() as db:
            try:
                # Build search query
                search_query = select(MarketingContent).where(
                    and_(
                        MarketingContent.approval_status == ApprovalStatus.APPROVED,
                        or_(
                            MarketingContent.content_text.contains(query),
                            MarketingContent.title.contains(query),
                            MarketingContent.tags.contains(query)
                        )
                    )
                )
                
                # Filter by content type if specified
                if content_type:
                    search_query = search_query.where(MarketingContent.content_type == content_type)
                
                # Order by usage count and compliance score
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
                        "compliance_score": content.compliance_score,
                        "tags": content.tags,
                        "usage_count": content.usage_count,
                        "source_type": content.source_type.value
                    }
                    for content in contents
                ]
                
            except Exception as e:
                logger.error(f"Error searching marketing content: {str(e)}")
                return []
    
    async def search_compliance_rules(
        self, 
        query: str, 
        content_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search compliance rules relevant to the query."""
        async with AsyncSessionLocal() as db:
            try:
                # Build search query
                search_query = select(ComplianceRules).where(
                    or_(
                        ComplianceRules.requirement_text.contains(query),
                        ComplianceRules.regulation_name.contains(query),
                        ComplianceRules.required_disclaimers.contains(query)
                    )
                )
                
                # Filter by content type applicability if specified
                if content_type:
                    search_query = search_query.where(
                        or_(
                            ComplianceRules.applies_to_content_types.contains(content_type),
                            ComplianceRules.applies_to_content_types.is_(None)  # Universal rules
                        )
                    )
                
                search_query = search_query.limit(limit)
                
                result = await db.execute(search_query)
                rules = result.scalars().all()
                
                return [
                    {
                        "id": rule.id,
                        "regulation_name": rule.regulation_name,
                        "rule_section": rule.rule_section,
                        "requirement_text": rule.requirement_text,
                        "required_disclaimers": rule.required_disclaimers,
                        "prohibition_type": rule.prohibition_type,
                        "applies_to_content_types": rule.applies_to_content_types
                    }
                    for rule in rules
                ]
                
            except Exception as e:
                logger.error(f"Error searching compliance rules: {str(e)}")
                return []
    
    async def get_disclaimers_for_content_type(
        self, 
        content_type: str
    ) -> List[Dict[str, Any]]:
        """Get required disclaimers for a specific content type."""
        async with AsyncSessionLocal() as db:
            try:
                # Search for disclaimer-related marketing content
                disclaimer_query = select(MarketingContent).where(
                    and_(
                        MarketingContent.approval_status == ApprovalStatus.APPROVED,
                        or_(
                            MarketingContent.tags.contains("disclaimer"),
                            MarketingContent.title.contains("disclaimer"),
                            MarketingContent.title.contains("risk disclosure")
                        )
                    )
                ).limit(3)
                
                result = await db.execute(disclaimer_query)
                disclaimers = result.scalars().all()
                
                return [
                    {
                        "id": disclaimer.id,
                        "title": disclaimer.title,
                        "content_text": disclaimer.content_text,
                        "content_type": disclaimer.content_type.value,
                        "tags": disclaimer.tags
                    }
                    for disclaimer in disclaimers
                ]
                
            except Exception as e:
                logger.error(f"Error getting disclaimers: {str(e)}")
                return []
    
    async def generate_content_with_context(
        self,
        user_request: str,
        content_type: str,
        audience_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate content using Warren with database-driven context."""
        try:
            # Convert string content type to enum if possible
            try:
                content_type_enum = ContentType(content_type.lower())
            except ValueError:
                content_type_enum = None
                logger.warning(f"Unknown content type: {content_type}")
            
            # 1. Search for relevant marketing content examples
            marketing_examples = await self.search_marketing_content(
                query=user_request,
                content_type=content_type_enum,
                limit=3
            )
            
            # 2. Search for relevant compliance rules
            compliance_rules = await self.search_compliance_rules(
                query=content_type,
                content_type=content_type,
                limit=3
            )
            
            # 3. Get required disclaimers
            disclaimers = await self.get_disclaimers_for_content_type(content_type)
            
            # 4. Build enhanced context for Warren
            context_parts = [
                "You are Warren, an AI assistant specialized in creating SEC and FINRA compliant marketing content for financial advisors.",
                "\nHere is relevant compliance information from our knowledge base:"
            ]
            
            # Add compliance rules
            if compliance_rules:
                context_parts.append(f"\n## REGULATORY REQUIREMENTS:")
                for rule in compliance_rules[:2]:
                    context_parts.append(f"\n**{rule['regulation_name']}**: {rule['requirement_text'][:300]}...")
                    if rule['required_disclaimers']:
                        context_parts.append(f"Required disclaimers: {rule['required_disclaimers'][:200]}...")
            
            # Add marketing examples
            if marketing_examples:
                context_parts.append(f"\n## APPROVED {content_type.upper()} EXAMPLES:")
                for example in marketing_examples[:2]:
                    context_parts.append(f"\n**Example**: {example['title']}")
                    context_parts.append(f"Content: {example['content_text'][:200]}...")
                    if example['tags']:
                        context_parts.append(f"Tags: {example['tags']}")
            
            # Add disclaimers
            if disclaimers:
                context_parts.append(f"\n## REQUIRED DISCLAIMERS:")
                for disclaimer in disclaimers[:2]:
                    context_parts.append(f"\n**{disclaimer['title']}**: {disclaimer['content_text'][:200]}...")
            
            context = "\n".join(context_parts)
            
            # 5. Create enhanced prompt for Warren
            warren_prompt = f"""{context}

USER REQUEST: {user_request}
CONTENT TYPE: {content_type}
TARGET AUDIENCE: {audience_type or 'general'}

Please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements shown above
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type
6. References the style and structure of the approved examples above

Generate the content now:"""

            # 6. Generate content with Warren
            warren_content = await claude_service.generate_content(warren_prompt)
            
            # 7. Log the interaction for tracking
            await self._log_warren_interaction(
                user_id=user_id,
                session_id=session_id,
                user_request=user_request,
                content_type=content_type,
                audience_type=audience_type,
                generated_content=warren_content,
                content_sources_used=[
                    *[str(ex['id']) for ex in marketing_examples],
                    *[str(rule['id']) for rule in compliance_rules],
                    *[str(disc['id']) for disc in disclaimers]
                ]
            )
            
            # 8. Update usage counts for retrieved content
            await self._update_content_usage_counts(
                [ex['id'] for ex in marketing_examples]
            )
            
            return {
                "status": "success",
                "content": warren_content,
                "content_type": content_type,
                "knowledge_sources_used": len(marketing_examples) + len(compliance_rules) + len(disclaimers),
                "marketing_examples_found": len(marketing_examples),
                "compliance_rules_found": len(compliance_rules),
                "disclaimers_found": len(disclaimers),
                "context_provided": bool(context_parts),
                "user_request": user_request
            }
            
        except Exception as e:
            logger.error(f"Error generating content with Warren: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "content": None
            }
    
    async def _log_warren_interaction(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        generated_content: str,
        content_sources_used: List[str]
    ) -> None:
        """Log Warren interaction to database for analytics."""
        async with AsyncSessionLocal() as db:
            try:
                # Convert content_type string to enum
                try:
                    content_type_enum = ContentType(content_type.lower())
                except ValueError:
                    content_type_enum = None
                
                # Convert audience_type string to enum if provided
                audience_type_enum = None
                if audience_type:
                    try:
                        audience_type_enum = AudienceType(audience_type.lower())
                    except ValueError:
                        pass
                
                interaction = WarrenInteractions(
                    user_id=user_id or "anonymous",
                    session_id=session_id,
                    user_request=user_request,
                    requested_content_type=content_type_enum,
                    requested_audience=audience_type_enum,
                    generated_content=generated_content,
                    content_sources_used=",".join(content_sources_used),
                    generation_confidence=0.95  # Default high confidence
                )
                
                db.add(interaction)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error logging Warren interaction: {str(e)}")
                await db.rollback()
    
    async def _update_content_usage_counts(self, content_ids: List[int]) -> None:
        """Update usage counts for marketing content that was retrieved."""
        async with AsyncSessionLocal() as db:
            try:
                for content_id in content_ids:
                    # Get the content
                    result = await db.execute(
                        select(MarketingContent).where(MarketingContent.id == content_id)
                    )
                    content = result.scalar_one_or_none()
                    
                    if content:
                        content.usage_count = (content.usage_count or 0) + 1
                
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error updating content usage counts: {str(e)}")
                await db.rollback()
    
    async def get_database_summary(self) -> Dict[str, Any]:
        """Get summary of the refactored database content."""
        async with AsyncSessionLocal() as db:
            try:
                # Count marketing content
                marketing_count = await db.execute(
                    select(func.count(MarketingContent.id))
                )
                marketing_total = marketing_count.scalar()
                
                # Count by content type
                content_type_counts = {}
                for content_type in ContentType:
                    count_result = await db.execute(
                        select(func.count(MarketingContent.id)).where(
                            MarketingContent.content_type == content_type
                        )
                    )
                    content_type_counts[content_type.value] = count_result.scalar()
                
                # Count compliance rules
                rules_count = await db.execute(
                    select(func.count(ComplianceRules.id))
                )
                rules_total = rules_count.scalar()
                
                # Count Warren interactions
                interactions_count = await db.execute(
                    select(func.count(WarrenInteractions.id))
                )
                interactions_total = interactions_count.scalar()
                
                # Get most used content
                popular_content = await db.execute(
                    select(MarketingContent.title, MarketingContent.usage_count)
                    .where(MarketingContent.usage_count > 0)
                    .order_by(MarketingContent.usage_count.desc())
                    .limit(5)
                )
                popular_list = [
                    {"title": title, "usage_count": count} 
                    for title, count in popular_content.all()
                ]
                
                return {
                    "database_type": "refactored_granular",
                    "marketing_content_total": marketing_total,
                    "content_by_type": content_type_counts,
                    "compliance_rules_total": rules_total,
                    "warren_interactions_total": interactions_total,
                    "most_popular_content": popular_list,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting database summary: {str(e)}")
                return {"error": str(e)}


# Service instance
warren_db_service = WarrenDatabaseService()
