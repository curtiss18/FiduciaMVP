"""
Advanced Generation Strategy

Uses Phase 2 AdvancedContextAssembler for sophisticated context optimization.
"""

import logging
import time
from typing import Dict, Any, Optional

from .content_generation_strategy import ContentGenerationStrategy, GenerationResult
from src.services.advanced_context_assembler import AdvancedContextAssembler
from src.services.prompt_service import prompt_service
from src.services.claude_service import claude_service
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AdvancedGenerationStrategy(ContentGenerationStrategy):
    """Advanced content generation using AdvancedContextAssembler."""
    
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
        """Generate content using Phase 2 AdvancedContextAssembler."""
        result = GenerationResult()
        result.strategy_used = "advanced"
        start_time = time.time()
        
        try:
            async with AsyncSessionLocal() as db_session:
                context_assembler = AdvancedContextAssembler(db_session)
                session_id = context_data.get("session_id")
                
                assembly_result = await context_assembler.build_warren_context(
                    session_id=session_id or "no-session",
                    user_input=user_request,
                    context_data=context_data,
                    current_content=current_content,
                    youtube_context=youtube_context
                )
                
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
                
                optimized_context = assembly_result["context"]
                session_documents = context_data.get("session_documents", [])
                has_documents = len(session_documents) > 0
                
                document_instruction = ""
                if has_documents:
                    document_titles = [doc['title'] for doc in session_documents]
                    document_instruction = f"""

IMPORTANT: You have access to the following uploaded documents in this session:
{', '.join(document_titles)}

Please reference and incorporate information from these documents when creating content."""

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
                
                content = await claude_service.generate_content(final_prompt)
                
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
                
                result.content = content
                result.success = True
                result.metadata = {
                    "assembly_result": assembly_result,
                    "token_management": context_data["token_management"],
                    "phase": "Phase_2_Advanced",
                    "document_count": len(session_documents),
                    "has_documents": has_documents
                }
                
                logger.info("✅ Advanced generation strategy completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Advanced generation strategy failed: {e}")
            result.success = False
            result.error_message = str(e)
            result.metadata = {"error_type": "advanced_generation_failure"}
        
        finally:
            result.generation_time = time.time() - start_time
        
        return result
    
    def can_handle(self, context_data: Dict[str, Any]) -> bool:
        """Check if advanced strategy can handle the given context."""
        try:
            # Validate that context_data is a dict and has the expected structure
            if not isinstance(context_data, dict):
                return False
            
            # Check for the presence of key context elements
            marketing_examples = context_data.get("marketing_examples")
            disclaimers = context_data.get("disclaimers")
            conversation_context = context_data.get("conversation_context")
            session_documents = context_data.get("session_documents")
            
            # Validate that lists are actually lists (not strings or other types)
            if marketing_examples is not None and not isinstance(marketing_examples, list):
                return False
            if disclaimers is not None and not isinstance(disclaimers, list):
                return False
            if session_documents is not None and not isinstance(session_documents, list):
                return False
            
            # Check if we have any valid context
            has_context = bool(
                marketing_examples or 
                disclaimers or
                conversation_context or
                session_documents
            )
            return has_context
        except Exception:
            return False
    
    def get_strategy_name(self) -> str:
        return "advanced"
    
    def get_strategy_priority(self) -> int:
        return 10
    
    def requires_advanced_context(self) -> bool:
        return True
    
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
