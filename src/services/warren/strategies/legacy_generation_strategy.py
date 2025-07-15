"""
Legacy Generation Strategy

"""

import logging
import time
from typing import Dict, Any, Optional

from .base_generation_strategy import BaseGenerationStrategy
from .content_generation_strategy import GenerationResult
from src.services.prompt_service import prompt_service
from src.services.claude_service import claude_service
from src.services.warren.youtube_context_service import youtube_context_service

logger = logging.getLogger(__name__)


class LegacyGenerationStrategy(BaseGenerationStrategy):
    """
    Legacy content generation using manual context building.

    """
    
    def __init__(self):
        self.max_transcript_length = 4000
    
    async def generate_content(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str] = None,
        current_content: Optional[str] = None,
        is_refinement: bool = False,
        youtube_context: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Generate content using manual context building."""
        result = GenerationResult()
        result.strategy_used = "legacy"
        start_time = time.time()
        
        try:
            if is_refinement and current_content:
                final_prompt = self._build_refinement_prompt(
                    context_data, user_request, content_type, audience_type, current_content
                )
            else:
                final_prompt = self._build_generation_prompt(
                    context_data, user_request, content_type, audience_type, youtube_context
                )
            
            content = await claude_service.generate_content(final_prompt)
            
            # Use base class method for success result population
            self._populate_success_result(
                result=result,
                content=content,
                strategy_name="legacy",
                start_time=start_time,
                # Legacy-specific metadata
                phase="Legacy_Fallback",
                context_building="manual",
                refinement=is_refinement,
                youtube_context_present=youtube_context is not None
            )
            
            logger.info("✅ Legacy generation strategy completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Legacy generation strategy failed: {e}")
            return self._handle_generation_error(e, "legacy")
        
        return result
    
    def can_handle(self, context_data: Dict[str, Any]) -> bool:
        """
        Legacy strategy can always handle any context - this is the emergency fallback.

        """
        logger.debug("Legacy strategy: Always available as fallback")
        return True
    
    def get_strategy_name(self) -> str:
        return "legacy"
    
    def get_strategy_priority(self) -> int:
        return 100
    
    def requires_advanced_context(self) -> bool:
        return False
    
    def _build_refinement_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        current_content: str
    ) -> str:
        """Build refinement prompt using base class context building."""
        # Use base class method for prompt context
        prompt_context = self._build_base_prompt_context(content_type, audience_type)
        
        refinement_context = {
            'current_content': current_content,
            'refinement_request': user_request,
            **prompt_context  # Include platform, content_type, audience_type
        }
        
        base_system_prompt = prompt_service.get_warren_refinement_prompt(refinement_context)
        
        conversation_context = context_data.get("conversation_context", "")
        conversation_section = ""
        if conversation_context:
            conversation_section = f"""
## CONVERSATION HISTORY:
{conversation_context}

## REFINEMENT CONTEXT:
"""
            logger.info(f"Added conversation context to refinement prompt: {len(conversation_context)} characters")
        
        return f"""{base_system_prompt}
{conversation_section}
CURRENT CONTENT TO REFINE:
##MARKETINGCONTENT##
{current_content}
##MARKETINGCONTENT##

USER'S REFINEMENT REQUEST: {user_request}

Please refine the content based on the user's request while maintaining SEC/FINRA compliance. Consider the conversation history above for additional context about what we've been discussing.
Wrap your refined content in ##MARKETINGCONTENT## delimiters and explain your changes."""
    
    def _build_generation_prompt(
        self,
        context_data: Dict[str, Any],
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        youtube_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build generation prompt using manual context building."""
        # Use base class method for prompt context
        prompt_context = self._build_base_prompt_context(content_type, audience_type)
        
        base_system_prompt = prompt_service.get_warren_system_prompt(prompt_context)
        
        context_parts = ["\nHere is relevant compliance information from our knowledge base:"]
        
        # Add conversation context
        conversation_context = context_data.get("conversation_context", "")
        if conversation_context:
            context_parts.insert(0, "\n## CONVERSATION HISTORY:")
            context_parts.insert(1, f"\n{conversation_context}")
            context_parts.insert(2, "\n## KNOWLEDGE BASE CONTEXT:")
        
        # Add marketing examples
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
        
        # Add YouTube context using shared service
        if youtube_context:
            context_parts = youtube_context_service.add_youtube_context(context_parts, youtube_context)
        
        knowledge_context = "\n".join(context_parts)
        
        return f"""{base_system_prompt}

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
