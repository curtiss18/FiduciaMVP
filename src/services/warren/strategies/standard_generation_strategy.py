"""
Standard Generation Strategy

Uses Phase 1 ContextAssembler when advanced generation fails.
"""

import logging
import time
from typing import Dict, Any, Optional

from .content_generation_strategy import ContentGenerationStrategy, GenerationResult
from src.services.context_assembly_service import ContextAssembler
from src.services.prompt_service import prompt_service
from src.services.claude_service import claude_service
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class StandardGenerationStrategy(ContentGenerationStrategy):
    """Standard content generation using ContextAssembler."""
    
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
        """Generate content using Phase 1 ContextAssembler."""
        result = GenerationResult()
        result.strategy_used = "standard"
        start_time = time.time()
        
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
                
                context_data["token_management"] = {
                    **assembly_result,
                    "phase": "Phase_1_Standard"
                }
                
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
                
                content = await claude_service.generate_content(final_prompt)
                
                result.content = content
                result.success = True
                result.metadata = {
                    "assembly_result": assembly_result,
                    "token_management": context_data["token_management"],
                    "phase": "Phase_1_Standard"
                }
                
                logger.info("✅ Standard generation strategy completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Standard generation strategy failed: {e}")
            result.success = False
            result.error_message = str(e)
            result.metadata = {"error_type": "standard_generation_failure"}
        
        finally:
            result.generation_time = time.time() - start_time
        
        return result
    
    def can_handle(self, context_data: Dict[str, Any]) -> bool:
        """Standard strategy can handle any context."""
        return True
    
    def get_strategy_name(self) -> str:
        return "standard"
    
    def get_strategy_priority(self) -> int:
        return 50
    
    def requires_advanced_context(self) -> bool:
        return False
    
    def _extract_platform_from_content_type(self, content_type: str) -> str:
        """Extract platform from content type."""
        platform_mapping = {
            'linkedin_post': 'linkedin',
            'email_template': 'email',
            'website_content': 'website',
            'newsletter': 'newsletter',
            'social_media': 'twitter',
            'blog_post': 'website'
        }
        return platform_mapping.get(content_type.lower(), 'general')
