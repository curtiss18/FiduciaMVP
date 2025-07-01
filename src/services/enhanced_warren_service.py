# Enhanced Warren Service with Vector Search
"""
Enhanced Warren service implementing Hybrid MVP+ approach:
- Primary: Vector search for semantic content matching
- Fallback: Text search if vector search fails or returns poor results
- Safety: Automatic degradation to ensure Warren always works
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.services.embedding_service import embedding_service
from src.services.vector_search_service import vector_search_service
from src.services.warren_database_service import warren_db_service
from src.services.content_vectorization_service import content_vectorization_service
from src.services.claude_service import claude_service
from src.services.prompt_service import prompt_service
from src.models.refactored_database import ContentType, AudienceType

logger = logging.getLogger(__name__)


class EnhancedWarrenService:
    """Enhanced Warren with vector search and automatic fallbacks."""
    
    def __init__(self):
        """Initialize the enhanced Warren service."""
        self.vector_similarity_threshold = 0.1  # Very low for debugging - see what scores we get
        self.min_results_threshold = 1  # Minimum results before falling back
        self.enable_vector_search = True  # Feature flag
    
    async def generate_content_with_enhanced_context(
        self,
        user_request: str,
        content_type: str,
        audience_type: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        current_content: Optional[str] = None,
        is_refinement: bool = False,
        youtube_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate content using enhanced vector search with automatic fallbacks.
        """
        try:
            # Convert string content type to enum if possible
            try:
                content_type_enum = ContentType(content_type.lower())
            except ValueError:
                content_type_enum = None
                logger.warning(f"Unknown content type: {content_type}")
            
            # Try vector search first (primary method)
            context_data = await self._get_vector_search_context(
                user_request, content_type, content_type_enum, audience_type
            )
            
            # Validate context quality
            context_quality = self._assess_context_quality(context_data)
            
            # Fall back to text search if vector search results are poor
            if not context_quality["sufficient"]:
                fallback_context = await self._get_text_search_context(
                    user_request, content_type, content_type_enum
                )
                
                # Combine vector and text results
                context_data = self._combine_contexts(context_data, fallback_context)
                context_data["fallback_used"] = True
                context_data["fallback_reason"] = context_quality["reason"]
            else:
                context_data["fallback_used"] = False
                context_data["search_strategy"] = "vector"  # Explicitly set vector strategy
            
            # Generate content with Warren using the assembled context
            warren_content = await self._generate_with_enhanced_context(
                context_data, user_request, content_type, audience_type, 
                current_content, is_refinement, youtube_context
            )
            
            return {
                "status": "success",
                "content": warren_content,
                "content_type": content_type,
                "search_strategy": context_data.get("search_strategy", "hybrid"),
                "vector_results_found": context_data.get("vector_results_count", 0),
                "text_results_found": context_data.get("text_results_count", 0),
                "total_knowledge_sources": context_data.get("total_sources", 0),
                "marketing_examples_count": len(context_data.get("marketing_examples", [])),
                "compliance_rules_count": len(context_data.get("disclaimers", [])),
                "fallback_used": context_data.get("fallback_used", False),
                "fallback_reason": context_data.get("fallback_reason"),
                "context_quality_score": context_quality.get("score", 0.5),
                "user_request": user_request
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced Warren generation: {str(e)}")
            
            # Emergency fallback to original Warren database service
            try:
                logger.info("Attempting emergency fallback to original Warren service")
                fallback_result = await warren_db_service.generate_content_with_context(
                    user_request=user_request,
                    content_type=content_type,
                    audience_type=audience_type,
                    user_id=user_id,
                    session_id=session_id
                )
                fallback_result["emergency_fallback"] = True
                fallback_result["original_error"] = str(e)
                return fallback_result
                
            except Exception as fallback_error:
                logger.error(f"Emergency fallback also failed: {str(fallback_error)}")
                return {
                    "status": "error",
                    "error": f"Enhanced Warren failed: {str(e)}. Fallback failed: {str(fallback_error)}",
                    "content": None
                }
    
    async def _get_vector_search_context(
        self,
        user_request: str,
        content_type: str,
        content_type_enum: Optional[ContentType],
        audience_type: Optional[str]
    ) -> Dict[str, Any]:
        """Get context using vector similarity search."""
        try:
            if not self.enable_vector_search:
                return {"marketing_examples": [], "disclaimers": [], "vector_available": False}
            
            # Check if vector search is available
            readiness_check = await vector_search_service.check_readiness()
            if not readiness_check.get("ready", False):
                logger.warning(f"Vector search not ready: {readiness_check.get('reason', 'Unknown')}")
                return {"marketing_examples": [], "disclaimers": [], "vector_available": False}
            
            # Search for relevant marketing content examples
            marketing_examples = await vector_search_service.search_marketing_content(
                query_text=user_request,
                content_type=content_type_enum,
                similarity_threshold=self.vector_similarity_threshold,
                limit=3
            )
            
            # Try to search compliance rules, but fall back gracefully if it fails
            compliance_rules = []
            try:
                compliance_rules = await vector_search_service.search_compliance_rules(
                    query_text=f"{content_type} compliance rules disclaimer",
                    content_type=content_type,
                    similarity_threshold=0.1,
                    limit=3
                )
            except Exception as e:
                logger.warning(f"Compliance rules vector search failed: {e}, continuing with marketing examples only")
                compliance_rules = []
            
            # If no compliance rules found via vector search, try marketing content for disclaimers as backup
            disclaimers = compliance_rules
            if not disclaimers:
                disclaimer_query = f"{content_type} disclaimer risk disclosure"
                potential_disclaimers = await vector_search_service.search_marketing_content(
                    query_text=disclaimer_query,
                    similarity_threshold=0.1,
                    limit=3
                )
                
                # Filter for disclaimer-like content
                disclaimers = [
                    d for d in potential_disclaimers 
                    if any(keyword in d.get("title", "").lower() or keyword in d.get("tags", "").lower() 
                           for keyword in ["disclaimer", "risk", "disclosure"])
                ]
            
            return {
                "marketing_examples": marketing_examples,
                "disclaimers": disclaimers,
                "vector_available": True,
                "search_method": "vector",
                "vector_results_count": len(marketing_examples),
                "disclaimer_count": len(disclaimers),
                "total_sources": len(marketing_examples) + len(disclaimers)
            }
            
        except Exception as e:
            logger.error(f"Error in vector search context: {str(e)}")
            return {"marketing_examples": [], "disclaimers": [], "vector_available": False, "error": str(e)}
    
    async def _get_text_search_context(
        self,
        user_request: str,
        content_type: str,
        content_type_enum: Optional[ContentType]
    ) -> Dict[str, Any]:
        """Get context using traditional text search (fallback method)."""
        try:
            # Use the original Warren database service text search logic
            marketing_examples = await warren_db_service.search_marketing_content(
                query=user_request,
                content_type=content_type_enum,
                limit=3
            )
            
            disclaimers = await warren_db_service.get_disclaimers_for_content_type(content_type)
            
            return {
                "marketing_examples": marketing_examples,
                "disclaimers": disclaimers,
                "search_method": "text",
                "text_results_count": len(marketing_examples),
                "disclaimer_count": len(disclaimers),
                "total_sources": len(marketing_examples) + len(disclaimers)
            }
            
        except Exception as e:
            logger.error(f"Error in text search context: {str(e)}")
            return {"marketing_examples": [], "disclaimers": [], "error": str(e)}
    
    def _assess_context_quality(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of retrieved context and determine if it's sufficient."""
        marketing_count = len(context_data.get("marketing_examples", []))
        disclaimer_count = len(context_data.get("disclaimers", []))
        vector_available = context_data.get("vector_available", False)
        
        # Quality assessment logic
        if not vector_available:
            return {"sufficient": False, "score": 0.0, "reason": "vector_search_unavailable"}
        
        if marketing_count == 0 and disclaimer_count == 0:
            return {"sufficient": False, "score": 0.1, "reason": "no_relevant_content_found"}
        
        if disclaimer_count == 0:
            return {"sufficient": False, "score": 0.4, "reason": "no_disclaimers_found"}
        
        # Context is sufficient if we have disclaimers (minimum requirement)
        total_sources = marketing_count + disclaimer_count
        quality_score = min(1.0, (marketing_count * 0.4) + (disclaimer_count * 0.3) + 0.3)
        
        return {"sufficient": True, "score": quality_score, "reason": "sufficient_quality"}
    
    def _combine_contexts(
        self, 
        vector_context: Dict[str, Any], 
        text_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine vector and text search contexts intelligently."""
        # Start with vector context
        combined = vector_context.copy()
        
        # Add text results that aren't already included
        vector_ids = {ex.get("id") for ex in vector_context.get("marketing_examples", [])}
        text_examples = [
            ex for ex in text_context.get("marketing_examples", [])
            if ex.get("id") not in vector_ids
        ]
        
        # Combine marketing examples (vector first, then unique text results)
        combined["marketing_examples"] = (
            vector_context.get("marketing_examples", []) + text_examples[:2]
        )
        
        # For disclaimers, prefer vector results but supplement with text if needed
        if len(vector_context.get("disclaimers", [])) < 2:
            vector_disclaimer_ids = {d.get("id") for d in vector_context.get("disclaimers", [])}
            text_disclaimers = [
                d for d in text_context.get("disclaimers", [])
                if d.get("id") not in vector_disclaimer_ids
            ]
            combined["disclaimers"] = (
                vector_context.get("disclaimers", []) + text_disclaimers[:2]
            )
        
        # Update metadata
        combined["search_strategy"] = "hybrid"
        combined["text_results_count"] = len(text_examples)
        combined["total_sources"] = (
            len(combined.get("marketing_examples", [])) + 
            len(combined.get("disclaimers", []))
        )
        
        return combined
    
    async def _generate_with_enhanced_context(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        current_content: Optional[str] = None,
        is_refinement: bool = False,
        youtube_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content using Warren with enhanced context and smart prompt selection."""
        
        # Determine which prompt to use based on whether this is a refinement
        if is_refinement and current_content:
            # Use refinement prompt with current content context
            refinement_context = {
                'current_content': current_content,
                'refinement_request': user_request,
                'platform': self._extract_platform_from_content_type(content_type),
                'content_type': content_type,
                'audience_type': audience_type
            }
            
            base_system_prompt = prompt_service.get_warren_refinement_prompt(refinement_context)
            
            # For refinement, we primarily focus on the current content and user's request
            final_prompt = f"""{base_system_prompt}

CURRENT CONTENT TO REFINE:
##MARKETINGCONTENT##
{current_content}
##MARKETINGCONTENT##

USER'S REFINEMENT REQUEST: {user_request}

Please refine the content based on the user's request while maintaining SEC/FINRA compliance.
Wrap your refined content in ##MARKETINGCONTENT## delimiters and explain your changes."""

        else:
            # Use main system prompt for new content generation
            prompt_context = {
                'platform': self._extract_platform_from_content_type(content_type),
                'content_type': content_type,
                'audience_type': audience_type
            }
            
            base_system_prompt = prompt_service.get_warren_system_prompt(prompt_context)
            
            # Build enhanced context from knowledge base for new content
            context_parts = ["\nHere is relevant compliance information from our knowledge base:"]
            
            # Add marketing examples with similarity scores if available
            marketing_examples = context_data.get("marketing_examples", [])
            if marketing_examples:
                context_parts.append(f"\n## APPROVED {content_type.upper()} EXAMPLES:")
                for example in marketing_examples[:2]:
                    similarity_info = ""
                    if "similarity_score" in example:
                        similarity_info = f" (relevance: {example['similarity_score']:.2f})"
                    
                    context_parts.append(f"\n**Example{similarity_info}**: {example['title']}")
                    context_parts.append(f"Content: {example['content_text'][:300]}...")
                    if example.get('tags'):
                        context_parts.append(f"Tags: {example['tags']}")
            
            # Add disclaimers
            disclaimers = context_data.get("disclaimers", [])
            if disclaimers:
                context_parts.append(f"\n## REQUIRED DISCLAIMERS:")
                for disclaimer in disclaimers[:2]:
                    context_parts.append(f"\n**{disclaimer['title']}**: {disclaimer['content_text'][:200]}...")
            
            # NEW: Add YouTube video context if provided
            if youtube_context:
                logger.info(f"Processing YouTube context for Warren")
                context_parts.append(f"\n## VIDEO CONTEXT:")
                video_info = youtube_context.get("metadata", {})
                stats = youtube_context.get("stats", {})
                
                context_parts.append(f"\nYou are creating content based on a YouTube video:")
                if video_info.get("url"):
                    context_parts.append(f"Video URL: {video_info['url']}")
                if stats.get("word_count"):
                    context_parts.append(f"Transcript length: ~{stats['word_count']} words")
                
                # Add transcript (truncated if too long)
                transcript = youtube_context.get("transcript", "")
                if transcript:
                    logger.info(f"Adding transcript to Warren prompt: {len(transcript)} characters")
                    context_parts.append(f"\n**VIDEO TRANSCRIPT PROVIDED BELOW:**")
                    
                    # Limit transcript to reasonable length for prompt
                    max_transcript_length = 4000  # Increased from 3000 for more context
                    if len(transcript) > max_transcript_length:
                        transcript_preview = transcript[:max_transcript_length] + "..."
                        context_parts.append(f"\n{transcript_preview}")
                        context_parts.append(f"\n[Note: This is a preview of the full {len(transcript)}-character transcript]")
                        logger.info(f"Transcript truncated to {max_transcript_length} characters for prompt")
                    else:
                        context_parts.append(f"\n{transcript}")
                        logger.info(f"Full transcript included in prompt")
                else:
                    logger.warning(f"No transcript found in YouTube context!")
                
                context_parts.append(f"\n**IMPORTANT**: You have been provided with the actual video transcript above. Please create content that references, summarizes, or analyzes the key points from this video transcript while maintaining SEC/FINRA compliance. Do NOT say you haven't seen the video - you have the transcript content.")
            else:
                logger.info(f"No YouTube context provided to Warren")
            
            knowledge_context = "\n".join(context_parts)
            
            # Create final prompt combining system prompt with specific context
            final_prompt = f"""{base_system_prompt}

{knowledge_context}

USER REQUEST: {user_request}
CONTENT TYPE: {content_type}
TARGET AUDIENCE: {audience_type or 'general'}

Based on the compliance examples and requirements shown above, please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type
6. References the style and structure of the approved examples

Remember to wrap your final marketing content in ##MARKETINGCONTENT## delimiters.

Generate the content now:"""

        # Generate content with Warren using the appropriate prompt
        return await claude_service.generate_content(final_prompt)
    
    def _extract_platform_from_content_type(self, content_type: str) -> str:
        """Extract platform information from content type for prompt context."""
        platform_mapping = {
            'linkedin_post': 'linkedin',
            'email_template': 'email',
            'website_content': 'website',
            'newsletter': 'newsletter',
            'social_media': 'twitter',
            'blog_post': 'website'
        }
        return platform_mapping.get(content_type.lower(), 'general')


# Service instance
enhanced_warren_service = EnhancedWarrenService()
