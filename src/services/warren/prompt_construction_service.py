"""
Prompt Construction Service

Builds prompts for different content generation scenarios.

Responsibilities:
- Build prompts for new content generation
- Build prompts for content refinement scenarios
- Manage token limits and context optimization
- Handle different prompt types (advanced, standard, legacy)
- Context prioritization and assembly

Extracted from enhanced_warren_service.py:
- _generate_with_enhanced_context() prompt building (lines 400-470)
- _generate_with_legacy_context() prompt building (lines 550-720)
- Platform extraction logic (line 730)
"""

import logging
from typing import Dict, Any, List, Optional

from src.services.prompt_service import prompt_service
from src.services.context_assembler import ContextAssembler
from src.services.advanced_context_assembler import AdvancedContextAssembler
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class PromptType:
    """Constants for different prompt types."""
    ADVANCED_GENERATION = "advanced_generation"
    STANDARD_GENERATION = "standard_generation"
    LEGACY_GENERATION = "legacy_generation"
    REFINEMENT = "refinement"
    EMERGENCY = "emergency"


class PromptConstructionService:
    """
    Service for constructing prompts for Warren content generation.
    
    Direct extraction from enhanced_warren_service.py prompt building logic.
    Supports all existing prompt types and scenarios.
    """
    
    def __init__(self):
        """Initialize the prompt construction service."""
        # Configuration (matching enhanced_warren_service defaults)
        self.max_transcript_length = 4000
    
    async def build_generation_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str] = None,
        prompt_type: str = PromptType.ADVANCED_GENERATION
    ) -> str:
        """
        Build prompt for new content generation.
        
        Extracted from enhanced_warren_service._generate_with_enhanced_context()
        and _generate_with_legacy_context() new content generation paths.
        
        Args:
            context_data: Retrieved context and metadata
            user_request: User's content generation request
            content_type: Type of content to generate
            audience_type: Target audience for content
            prompt_type: Type of prompt to construct
            
        Returns:
            Complete prompt ready for AI generation
        """
        if prompt_type == PromptType.ADVANCED_GENERATION:
            return await self._build_advanced_generation_prompt(
                context_data, user_request, content_type, audience_type
            )
        elif prompt_type == PromptType.STANDARD_GENERATION:
            return await self._build_standard_generation_prompt(
                context_data, user_request, content_type, audience_type
            )
        elif prompt_type == PromptType.LEGACY_GENERATION:
            return await self._build_legacy_generation_prompt(
                context_data, user_request, content_type, audience_type
            )
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    async def build_refinement_prompt(
        self,
        current_content: str,
        refinement_request: str,
        context_data: Dict[str, Any],
        content_type: str,
        audience_type: Optional[str] = None
    ) -> str:
        """
        Build prompt for content refinement scenarios.
        
        Extracted from enhanced_warren_service._generate_with_legacy_context()
        refinement path.
        
        Args:
            current_content: Existing content to refine
            refinement_request: User's refinement instructions
            context_data: Additional context for refinement
            content_type: Type of content being refined
            audience_type: Target audience
            
        Returns:
            Complete refinement prompt
        """
        # Use refinement prompt with current content context
        refinement_context = {
            'current_content': current_content,
            'refinement_request': refinement_request,
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

USER'S REFINEMENT REQUEST: {refinement_request}

Please refine the content based on the user's request while maintaining SEC/FINRA compliance. Consider the conversation history above for additional context about what we've been discussing.
Wrap your refined content in ##MARKETINGCONTENT## delimiters and explain your changes."""

        return final_prompt
    
    def optimize_context_tokens(
        self,
        context_parts: List[str],
        max_tokens: int
    ) -> List[str]:
        """
        Optimize context to fit within token limits while preserving quality.
        
        Note: This is a placeholder for token optimization logic.
        In the existing enhanced_warren_service, this is handled by ContextAssembler
        and AdvancedContextAssembler services.
        
        Args:
            context_parts: List of context sections to optimize
            max_tokens: Maximum tokens allowed for context
            
        Returns:
            Optimized context parts that fit within limits
        """
        # Simple implementation - join and return as-is
        # Token optimization is handled by ContextAssembler services
        return context_parts
    
    def assemble_context_sections(self, context_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Assemble different types of context into organized sections.
        
        Extracted from enhanced_warren_service._generate_with_legacy_context()
        context assembly logic.
        
        Args:
            context_data: Raw context data from various sources
            
        Returns:
            Organized context sections with labels
        """
        sections = {}
        
        # Add conversation context if available
        conversation_context = context_data.get("conversation_context", "")
        if conversation_context:
            sections["conversation_history"] = f"\n## CONVERSATION HISTORY:\n{conversation_context}"
            logger.info(f"Added conversation context: {len(conversation_context)} characters")
        
        # Add marketing examples with similarity scores if available
        marketing_examples = context_data.get("marketing_examples", [])
        if marketing_examples:
            content_type = context_data.get("content_type", "content")
            sections["marketing_examples"] = f"\n## APPROVED {content_type.upper()} EXAMPLES:"
            
            for example in marketing_examples[:2]:
                similarity_info = ""
                if "similarity_score" in example:
                    similarity_info = f" (relevance: {example['similarity_score']:.2f})"
                
                sections["marketing_examples"] += f"\n**Example{similarity_info}**: {example['title']}"
                sections["marketing_examples"] += f"\nContent: {example['content_text'][:300]}..."
                if example.get('tags'):
                    sections["marketing_examples"] += f"\nTags: {example['tags']}"
        
        # Add disclaimers
        disclaimers = context_data.get("disclaimers", [])
        if disclaimers:
            sections["disclaimers"] = f"\n## REQUIRED DISCLAIMERS:"
            for disclaimer in disclaimers[:2]:
                sections["disclaimers"] += f"\n**{disclaimer['title']}**: {disclaimer['content_text'][:200]}..."
        
        return sections
    
    def add_document_instructions(self, context_data: Dict[str, Any]) -> str:
        """
        Add instructions for using uploaded documents in content generation.
        
        Extracted from enhanced_warren_service._generate_with_enhanced_context()
        document instruction logic.
        
        Args:
            context_data: Context containing session documents
            
        Returns:
            Document instruction text for prompt
        """
        session_documents = context_data.get("session_documents", [])
        has_documents = len(session_documents) > 0
        
        if not has_documents:
            return ""
        
        document_titles = [doc['title'] for doc in session_documents]
        
        document_instruction = f"""

IMPORTANT: You have access to the following uploaded documents in this session:
{', '.join(document_titles)}

Please reference and incorporate information from these documents when creating content. These documents contain specific information about the advisor's services, strategies, and expertise that should inform your content generation."""
        
        return document_instruction
    
    def add_youtube_context(self, context_parts: List[str], youtube_context: Dict[str, Any]) -> List[str]:
        """
        Add YouTube video context to context parts.
        
        Extracted from enhanced_warren_service._generate_with_legacy_context()
        YouTube context handling.
        
        Args:
            context_parts: Existing context parts list
            youtube_context: YouTube context data
            
        Returns:
            Updated context parts with YouTube context
        """
        if not youtube_context:
            logger.info("No YouTube context provided to Warren")
            return context_parts
        
        logger.info("Processing YouTube context for Warren")
        context_parts.append("\n## VIDEO CONTEXT:")
        video_info = youtube_context.get("metadata", {})
        stats = youtube_context.get("stats", {})
        
        context_parts.append("\nYou are creating content based on a YouTube video:")
        if video_info.get("url"):
            context_parts.append(f"Video URL: {video_info['url']}")
        if stats.get("word_count"):
            context_parts.append(f"Transcript length: ~{stats['word_count']} words")
        
        # Add transcript (truncated if too long)
        transcript = youtube_context.get("transcript", "")
        if transcript:
            logger.info(f"Adding transcript to Warren prompt: {len(transcript)} characters")
            context_parts.append("\n**VIDEO TRANSCRIPT PROVIDED BELOW:**")
            
            # Limit transcript to reasonable length for prompt
            if len(transcript) > self.max_transcript_length:
                transcript_preview = transcript[:self.max_transcript_length] + "..."
                context_parts.append(f"\n{transcript_preview}")
                context_parts.append(f"\n[Note: This is a preview of the full {len(transcript)}-character transcript]")
                logger.info(f"Transcript truncated to {self.max_transcript_length} characters for prompt")
            else:
                context_parts.append(f"\n{transcript}")
                logger.info("Full transcript included in prompt")
        else:
            logger.warning("No transcript found in YouTube context!")
        
        context_parts.append("\n**IMPORTANT**: You have been provided with the actual video transcript above. Please create content that references, summarizes, or analyzes the key points from this video transcript while maintaining SEC/FINRA compliance. Do NOT say you haven't seen the video - you have the transcript content.")
        
        return context_parts
    
    def _extract_platform_from_content_type(self, content_type: str) -> str:
        """
        Extract platform information from content type for prompt context.
        
        Direct extraction from enhanced_warren_service._extract_platform_from_content_type()
        
        Args:
            content_type: Content type string
            
        Returns:
            Platform identifier for prompt customization
        """
        platform_mapping = {
            'linkedin_post': 'linkedin',
            'email_template': 'email',
            'website_content': 'website',
            'newsletter': 'newsletter',
            'social_media': 'twitter',
            'blog_post': 'website'
        }
        return platform_mapping.get(content_type.lower(), 'general')
    
    async def _build_advanced_generation_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str]
    ) -> str:
        """
        Build advanced generation prompt using Phase 2 AdvancedContextAssembler.
        
        Extracted from enhanced_warren_service._generate_with_enhanced_context()
        advanced context assembly path.
        """
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
                current_content=None,  # New generation, no current content
                youtube_context=context_data.get("youtube_context")
            )
            
            # Get the appropriate system prompt
            prompt_context = {
                'platform': self._extract_platform_from_content_type(content_type),
                'content_type': content_type,
                'audience_type': audience_type
            }
            
            base_system_prompt = prompt_service.get_warren_system_prompt(prompt_context)
            
            # Build final prompt with Phase 2 optimized context and document awareness
            optimized_context = assembly_result["context"]
            
            # Check if we have session documents to reference
            has_documents = len(context_data.get("session_documents", [])) > 0
            document_instruction = self.add_document_instructions(context_data)
            
            document_titles = []
            if has_documents:
                document_titles = [doc['title'] for doc in context_data.get("session_documents", [])]
            
            final_prompt = f"""{base_system_prompt}

{optimized_context}{document_instruction}

Based on the above information{" and uploaded documents" if has_documents else ""}, please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type
6. References the style and structure of the approved examples
{f"7. Incorporates relevant information from the uploaded documents: {', '.join(document_titles)}" if has_documents else ""}

Remember to wrap your final marketing content in ##MARKETINGCONTENT## delimiters.

Generate the content now:"""
            
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
            
            return final_prompt
    
    async def _build_standard_generation_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str]
    ) -> str:
        """
        Build standard generation prompt using Phase 1 ContextAssembler.
        
        Extracted from enhanced_warren_service._generate_with_enhanced_context()
        Phase 1 fallback path.
        """
        async with AsyncSessionLocal() as db_session:
            context_assembler = ContextAssembler(db_session)
            
            assembly_result = await context_assembler.build_warren_context(
                session_id=context_data.get("session_id", "no-session"),
                user_input=user_request,
                context_data=context_data,
                current_content=None,  # New generation, no current content
                youtube_context=context_data.get("youtube_context")
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
            
            return final_prompt
    
    async def _build_legacy_generation_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str]
    ) -> str:
        """
        Build legacy generation prompt using original context building method.
        
        Extracted from enhanced_warren_service._generate_with_legacy_context()
        new content generation path.
        """
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
        youtube_context = context_data.get("youtube_context")
        if youtube_context:
            context_parts = self.add_youtube_context(context_parts, youtube_context)
        
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

        return final_prompt
