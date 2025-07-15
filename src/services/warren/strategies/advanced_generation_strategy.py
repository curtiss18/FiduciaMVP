"""
Advanced Generation Strategy

Uses the new context assembly service for sophisticated context optimization.
Inherits common functionality from BaseGenerationStrategy to eliminate code duplication.
"""

import logging
import time
from typing import Dict, Any, Optional

from .base_generation_strategy import BaseGenerationStrategy
from .content_generation_strategy import GenerationResult
from src.services.context_assembly_service.orchestrator import BasicContextAssemblyOrchestrator
from src.services.prompt_service import prompt_service
from src.services.claude_service import claude_service
from src.services.warren.youtube_context_service import youtube_context_service
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AdvancedGenerationStrategy(BaseGenerationStrategy):
    """
    Advanced content generation using sophisticated context assembly.
    """
    
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
        """Generate content using the new context assembly service."""
        result = GenerationResult()
        result.strategy_used = "advanced"
        start_time = time.time()
        
        try:
            async with AsyncSessionLocal() as db_session:
                context_assembler = BasicContextAssemblyOrchestrator()
                session_id = context_data.get("session_id")
                
                assembly_result = await context_assembler.build_warren_context(
                    session_id=session_id or "no-session",
                    user_input=user_request,
                    context_data=context_data,
                    current_content=current_content,
                    youtube_context=youtube_context,
                    db_session=db_session  # Pass session as parameter
                )
                
                # Use base class method for platform extraction and context building
                prompt_context = self._build_base_prompt_context(content_type, audience_type)
                
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
                
                # Populate success result using base class method
                self._populate_success_result(
                    result=result,
                    content=content,
                    strategy_name="advanced",
                    start_time=start_time,
                    # Enhanced metadata specific to Advanced strategy
                    assembly_result=assembly_result,
                    token_management=context_data["token_management"],
                    phase="Phase_2_Advanced",
                    document_count=len(session_documents),
                    has_documents=has_documents,
                    quality_metrics=assembly_result.get("quality_metrics", {}),
                    relevance_scores=assembly_result.get("relevance_scores", {}),
                    priority_scores=assembly_result.get("priority_scores", {})
                )
                
                logger.info("✅ Advanced generation strategy completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Advanced generation strategy failed: {e}")
            return self._handle_generation_error(e, "advanced")
        
        return result
    
    def can_handle(self, context_data: Dict[str, Any]) -> bool:
        """
        Advanced context validation with sophisticated type checking.
        """
        try:
            # Validate that context_data is a dict and has the expected structure
            if not isinstance(context_data, dict):
                logger.debug("Advanced strategy: context_data is not a dictionary")
                return False
            
            # Check for the presence of key context elements
            marketing_examples = context_data.get("marketing_examples")
            disclaimers = context_data.get("disclaimers")
            conversation_context = context_data.get("conversation_context")
            session_documents = context_data.get("session_documents")
            
            # Validate that lists are actually lists (not strings or other types)
            if marketing_examples is not None and not isinstance(marketing_examples, list):
                logger.debug("Advanced strategy: marketing_examples is not a list")
                return False
            if disclaimers is not None and not isinstance(disclaimers, list):
                logger.debug("Advanced strategy: disclaimers is not a list")
                return False
            if session_documents is not None and not isinstance(session_documents, list):
                logger.debug("Advanced strategy: session_documents is not a list")
                return False
            
            # Check if we have any valid context (this is the core capability check)
            has_context = bool(
                marketing_examples or 
                disclaimers or
                conversation_context or
                session_documents
            )
            
            if has_context:
                logger.debug("Advanced strategy: Can handle context with rich data")
            else:
                logger.debug("Advanced strategy: No sufficient context available")
                
            return has_context
            
        except Exception as e:
            logger.warning(f"Advanced strategy can_handle() failed: {e}")
            return False
    
    def get_strategy_name(self) -> str:
        return "advanced"
    
    def get_strategy_priority(self) -> int:
        return 10
    
    def requires_advanced_context(self) -> bool:
        return True
