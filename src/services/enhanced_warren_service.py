# Enhanced Warren Service with Vector Search
"""
Enhanced Warren service implementing Hybrid MVP+ approach:
- Primary: Vector search for semantic content matching
- Fallback: Text search if vector search fails or returns poor results
- Safety: Automatic degradation to ensure Warren always works
- NEW: Conversation memory and context management
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
from src.services.conversation_manager import ConversationManager
from src.services.context_assembler import ContextAssembler, TokenManager
from src.services.advanced_context_assembler import AdvancedContextAssembler
from src.core.database import AsyncSessionLocal
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
        youtube_context: Optional[Dict[str, Any]] = None,
        use_conversation_context: bool = True  # NEW: Enable conversation memory
    ) -> Dict[str, Any]:
        """
        Generate content using enhanced vector search with automatic fallbacks.
        NEW: Includes conversation memory and context management.
        """
        try:
            # Convert string content type to enum if possible
            try:
                content_type_enum = ContentType(content_type.lower())
            except ValueError:
                content_type_enum = None
                logger.warning(f"Unknown content type: {content_type}")
            
            # NEW: Get conversation context if enabled and session_id provided
            conversation_context = ""
            if use_conversation_context and session_id:
                logger.info(f"🔍 Getting conversation context for session {session_id}")
                conversation_context = await self._get_conversation_context(session_id)
                if conversation_context:
                    logger.info(f"✅ Retrieved conversation context: {len(conversation_context)} characters")
                    logger.info(f"📝 Context preview: {conversation_context[:200]}...")
                else:
                    logger.info(f"❌ No conversation context found for session {session_id}")
            else:
                if not use_conversation_context:
                    logger.info(f"🔄 Conversation context disabled (use_conversation_context=False)")
                if not session_id:
                    logger.info(f"🔄 No session_id provided, skipping conversation context")
            
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
            
            # NEW: Add conversation context and session info to context_data
            context_data["conversation_context"] = conversation_context
            context_data["session_id"] = session_id  # Pass session_id to ContextAssembler
            
            # Generate content with Warren using the assembled context
            warren_content = await self._generate_with_enhanced_context(
                context_data, user_request, content_type, audience_type, 
                current_content, is_refinement, youtube_context
            )
            
            # NEW: Save conversation turn if session_id provided
            if session_id and use_conversation_context:
                await self._save_conversation_turn(
                    session_id, user_request, warren_content, context_data
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
                "user_request": user_request,
                "conversation_context_used": bool(conversation_context),  # NEW: Track context usage
                "session_id": session_id  # NEW: Include session_id in response
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
        """
        Generate content using Warren with intelligent context assembly and token management.
        NEW: Uses ContextAssembler for sophisticated token allocation and context optimization.
        """
        try:
            # Initialize Phase 2 advanced context assembly system
            async with AsyncSessionLocal() as db_session:
                # Use Phase 2 Advanced Context Assembler for sophisticated prioritization
                context_assembler = AdvancedContextAssembler(db_session)
                
                # Get session_id from context_data if available
                session_id = context_data.get("session_id")
                
                # Use Phase 2 AdvancedContextAssembler for intelligent context building
                assembly_result = await context_assembler.build_warren_context(
                    session_id=session_id or "no-session",
                    user_input=user_request,
                    context_data=context_data,
                    current_content=current_content,
                    youtube_context=youtube_context
                )
                
                # Get the appropriate system prompt based on request type
                prompt_context = {
                    'platform': self._extract_platform_from_content_type(content_type),
                    'content_type': content_type,
                    'audience_type': audience_type
                }
                
                if is_refinement and current_content:
                    # Use refinement prompt
                    refinement_context = {
                        'current_content': current_content,
                        'refinement_request': user_request,
                        **prompt_context
                    }
                    base_system_prompt = prompt_service.get_warren_refinement_prompt(refinement_context)
                else:
                    # Use main system prompt
                    base_system_prompt = prompt_service.get_warren_system_prompt(prompt_context)
                
                # Build final prompt with Phase 2 optimized context
                optimized_context = assembly_result["context"]
                final_prompt = f"""{base_system_prompt}

{optimized_context}

Based on the above information, please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type
6. References the style and structure of the approved examples

Remember to wrap your final marketing content in ##MARKETINGCONTENT## delimiters.

Generate the content now:"""
                
                # Log Phase 2 enhanced context assembly details
                logger.info(f"Phase 2 Advanced Context Assembly Complete:")
                logger.info(f"   Request Type: {assembly_result['request_type']}")
                logger.info(f"   Total Tokens: {assembly_result['total_tokens']}")
                logger.info(f"   Quality Score: {assembly_result.get('quality_metrics', {}).get('overall_quality', 'N/A')}")
                logger.info(f"   Average Relevance: {assembly_result.get('quality_metrics', {}).get('avg_relevance', 'N/A')}")
                logger.info(f"   High Priority Sources: {assembly_result.get('quality_metrics', {}).get('high_priority_count', 'N/A')}")
                logger.info(f"   Context Diversity: {assembly_result.get('quality_metrics', {}).get('context_diversity', 'N/A')}")
                logger.info(f"   Phase: {assembly_result.get('phase', 'Phase_2_Advanced')}")
                
                # Add Phase 2 assembly metadata to context_data for response
                context_data["token_management"] = {
                    "total_tokens": assembly_result["total_tokens"],
                    "request_type": assembly_result["request_type"],
                    "optimization_applied": assembly_result["optimization_applied"],
                    "context_breakdown": assembly_result["context_breakdown"],
                    "quality_metrics": assembly_result.get("quality_metrics", {}),
                    "relevance_scores": assembly_result.get("relevance_scores", {}),
                    "priority_scores": assembly_result.get("priority_scores", {}),
                    "phase": "Phase_2_Advanced"
                }
                
        except Exception as e:
            logger.error(f"Error in Phase 2 advanced context assembly: {e}")
            # Fallback to Phase 1 context assembler
            logger.info("Falling back to Phase 1 context assembler")
            try:
                async with AsyncSessionLocal() as db_session:
                    context_assembler = ContextAssembler(db_session)
                    
                    assembly_result = await context_assembler.build_warren_context(
                        session_id=context_data.get("session_id", "no-session"),
                        user_input=user_request,
                        context_data=context_data,
                        current_content=current_content,
                        youtube_context=youtube_context
                    )
                    
                    optimized_context = assembly_result["context"]
                    
                    # Add Phase 1 fallback metadata
                    context_data["token_management"] = {
                        **assembly_result,
                        "phase": "Phase_1_Fallback"
                    }
                    
                    # Build Phase 1 prompt
                    prompt_context = {
                        'platform': self._extract_platform_from_content_type(content_type),
                        'content_type': content_type,
                        'audience_type': audience_type
                    }
                    
                    if is_refinement and current_content:
                        refinement_context = {
                            'current_content': current_content,
                            'refinement_request': user_request,
                            **prompt_context
                        }
                        base_system_prompt = prompt_service.get_warren_refinement_prompt(refinement_context)
                    else:
                        base_system_prompt = prompt_service.get_warren_system_prompt(prompt_context)
                    
                    final_prompt = f"""{base_system_prompt}

{optimized_context}

Based on the above information, please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type
6. References the style and structure of the approved examples

Remember to wrap your final marketing content in ##MARKETINGCONTENT## delimiters.

Generate the content now:"""
                    
                    logger.info("Phase 1 fallback context assembly completed successfully")
                    
            except Exception as fallback_error:
                logger.error(f"Error in Phase 1 fallback context assembly: {fallback_error}")
                # Final fallback to legacy context building
                logger.info("Falling back to legacy context building")
                return await self._generate_with_legacy_context(
                    context_data, user_request, content_type, audience_type, 
                    current_content, is_refinement, youtube_context
                )
        
        # Generate content with Warren using the intelligently assembled context
        return await claude_service.generate_content(final_prompt)
    
    async def _generate_with_legacy_context(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        current_content: Optional[str] = None,
        is_refinement: bool = False,
        youtube_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Legacy context building method as fallback.
        Preserves original functionality when intelligent assembly fails.
        """
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
            
            # Include conversation context for refinements
            conversation_context = context_data.get("conversation_context", "")
            conversation_section = ""
            if conversation_context:
                conversation_section = f"""
## CONVERSATION HISTORY:
{conversation_context}

## REFINEMENT CONTEXT:
"""
                logger.info(f"Added conversation context to refinement prompt: {len(conversation_context)} characters")
            
            # For refinement, we focus on current content and user's request, but also include conversation context
            final_prompt = f"""{base_system_prompt}
{conversation_section}
CURRENT CONTENT TO REFINE:
##MARKETINGCONTENT##
{current_content}
##MARKETINGCONTENT##

USER'S REFINEMENT REQUEST: {user_request}

Please refine the content based on the user's request while maintaining SEC/FINRA compliance. Consider the conversation history above for additional context about what we've been discussing.
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
            
            # Add conversation context if available
            conversation_context = context_data.get("conversation_context", "")
            if conversation_context:
                context_parts.insert(0, "\n## CONVERSATION HISTORY:")
                context_parts.insert(1, f"\n{conversation_context}")
                context_parts.insert(2, "\n## KNOWLEDGE BASE CONTEXT:")
                logger.info(f"Added conversation context to Warren prompt: {len(conversation_context)} characters")
            
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
            
            # Add YouTube video context if provided
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
                    max_transcript_length = 4000
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
    
    async def _get_conversation_context(self, session_id: str) -> str:
        """
        Get conversation context for a session using ConversationManager.
        """
        try:
            async with AsyncSessionLocal() as db_session:
                conversation_manager = ConversationManager(db_session)
                return await conversation_manager.get_conversation_context(session_id)
        except Exception as e:
            logger.error(f"Error getting conversation context for session {session_id}: {e}")
            return ""
    
    async def _save_conversation_turn(
        self, 
        session_id: str, 
        user_input: str, 
        warren_response: str, 
        context_data: Dict[str, Any]
    ):
        """
        Save a conversation turn using ConversationManager.
        """
        try:
            # Prepare Warren metadata for storage
            warren_metadata = {
                'sources_used': context_data.get('marketing_examples', []) + context_data.get('disclaimers', []),
                'generation_confidence': context_data.get('context_quality_score', 0.5),
                'search_strategy': context_data.get('search_strategy', 'unknown'),
                'total_sources': context_data.get('total_sources', 0),
                'marketing_examples': context_data.get('marketing_examples_count', 0),
                'compliance_rules': context_data.get('compliance_rules_count', 0)
            }
            
            async with AsyncSessionLocal() as db_session:
                conversation_manager = ConversationManager(db_session)
                await conversation_manager.save_conversation_turn(
                    session_id=session_id,
                    user_input=user_input,
                    warren_response=warren_response,
                    warren_metadata=warren_metadata
                )
                logger.info(f"Saved conversation turn for session {session_id}")
        except Exception as e:
            logger.error(f"Error saving conversation turn for session {session_id}: {e}")
            # Don't raise the exception - conversation saving shouldn't break content generation


# Service instance
enhanced_warren_service = EnhancedWarrenService()
