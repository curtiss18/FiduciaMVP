"""
Content Generation Orchestrator - Main workflow coordinator for Warren.
Replaces enhanced_warren_service.py using refactored services.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.services.warren.search_orchestrator import SearchOrchestrator
from src.services.warren.conversation_context_service import ConversationContextService
from src.services.warren.context_quality_assessor import ContextQualityAssessor
from src.services.warren.prompt_construction_service import PromptConstructionService
from src.services.warren.strategies.strategy_factory import StrategyFactory
from src.models.refactored_database import ContentType

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of request validation."""
    def __init__(self):
        self.valid = False
        self.error_message = None
        self.processed_params = {}


class ContentGenerationOrchestrator:
    """Main orchestrator for Warren content generation workflow."""
    
    def __init__(self,
                 search_orchestrator=None,
                 conversation_service=None,
                 quality_assessor=None,
                 prompt_service=None,
                 strategy_factory=None):
        """Initialize with dependency injection for testing."""
        self.search_orchestrator = search_orchestrator or SearchOrchestrator()
        self.conversation_service = conversation_service or ConversationContextService()
        self.quality_assessor = quality_assessor or ContextQualityAssessor()
        self.prompt_service = prompt_service or PromptConstructionService()
        self.strategy_factory = strategy_factory or StrategyFactory()
        
        # Configuration matching enhanced_warren_service defaults
        self.vector_similarity_threshold = 0.1
        self.min_results_threshold = 1
        self.enable_vector_search = True
    
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
        use_conversation_context: bool = True,
        conversation_history: Optional[list] = None,
        session_documents: Optional[list] = None
    ) -> Dict[str, Any]:
        """Generate content maintaining exact interface compatibility with enhanced_warren_service."""
        try:
            # Validate and preprocess request
            validation_result = self._validate_request(user_request, content_type)
            if not validation_result.valid:
                return {
                    "status": "error",
                    "error": validation_result.error_message,
                    "content": None
                }
            
            content_type_enum = validation_result.processed_params.get("content_type_enum")
            
            # Get session context (conversation + documents) - use provided params if available
            if conversation_history is not None or session_documents is not None:
                # Use provided parameters directly
                conversation_context = ""
                if conversation_history:
                    # Convert conversation history to string format
                    conversation_context = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                                                     for msg in conversation_history])
                session_docs = session_documents or []
            else:
                # Use existing session context service
                session_context = await self.conversation_service.get_session_context(
                    session_id, use_conversation_context
                )
                conversation_context = session_context.get("conversation_context", "")
                session_docs = session_context.get("session_documents", [])
            
            # Execute search with fallback logic
            context_data = await self.search_orchestrator.execute_search_with_fallback(
                user_request, content_type, content_type_enum, audience_type
            )
            
            # Add session context to search results
            context_data["conversation_context"] = conversation_context
            context_data["session_documents"] = session_docs
            context_data["session_id"] = session_id
            
            # Assess context quality for strategy selection
            context_quality = self.quality_assessor.assess_context_quality(context_data)
            
            # Select and execute content generation strategy
            generation_result = await self._coordinate_generation_workflow({
                "context_data": context_data,
                "user_request": user_request,
                "content_type": content_type,
                "audience_type": audience_type,
                "current_content": current_content,
                "is_refinement": is_refinement,
                "youtube_context": youtube_context,
                "context_quality": context_quality
            })
            
            # Save conversation turn if applicable
            if session_id and use_conversation_context and generation_result.get("content"):
                await self.conversation_service.save_conversation_turn(
                    session_id, user_request, generation_result["content"], context_data
                )
            
            # Assemble final response with all metadata
            return self._assemble_response(
                generation_result["content"],
                {
                    "context_data": context_data,
                    "session_documents": session_documents,
                    "conversation_context": conversation_context,
                    "context_quality": context_quality,
                    "generation_metadata": generation_result.get("metadata", {}),
                    "user_request": user_request,
                    "content_type": content_type,
                    "session_id": session_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced Warren generation: {str(e)}")
            return await self._execute_emergency_fallback(
                user_request, content_type, audience_type, user_id, session_id, e
            )
    
    def _validate_request(self, user_request: str, content_type: str) -> ValidationResult:
        """Validate and preprocess the content generation request."""
        result = ValidationResult()
        
        if not user_request or not user_request.strip():
            result.error_message = "User request cannot be empty"
            return result
        
        if not content_type or not content_type.strip():
            result.error_message = "Content type cannot be empty"
            return result
        
        # Convert string content type to enum if possible
        content_type_enum = None
        try:
            # Handle common aliases for content types
            content_type_normalized = content_type.upper()
            if content_type_normalized == "BLOG_POST":
                content_type_normalized = "WEBSITE_BLOG"
            elif content_type_normalized == "TWITTER_POST":
                content_type_normalized = "X_POST"
            
            content_type_enum = ContentType(content_type_normalized)
        except ValueError:
            logger.warning(f"Unknown content type: {content_type}")
            # Don't fail - let it continue with None content_type_enum
        
        result.processed_params = {
            "content_type_enum": content_type_enum,
            "user_request": user_request.strip(),
            "content_type": content_type.strip()
        }
        result.valid = True
        return result
    
    def _assemble_response(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble final response in the expected format for backward compatibility."""
        context_data = metadata.get("context_data", {})
        session_documents = metadata.get("session_documents", []) or []  # Ensure it's a list
        conversation_context = metadata.get("conversation_context", "") or ""  # Ensure it's a string
        context_quality = metadata.get("context_quality", {})
        
        # Ensure all list fields have default empty lists to prevent None errors
        marketing_examples = context_data.get("marketing_examples", []) or []
        disclaimers = context_data.get("disclaimers", []) or []
        
        context_used = {
            "marketing_examples": marketing_examples,
            "compliance_rules": disclaimers,
            "conversation_context": conversation_context,
            "session_documents": session_documents,
            "search_strategy": context_data.get("search_strategy", "hybrid")
        }
        
        detailed_metadata = {
            "context_quality": context_quality,
            "search_details": {
                "vector_results_found": context_data.get("vector_results_count", 0),
                "text_results_found": context_data.get("text_results_count", 0),
                "total_knowledge_sources": context_data.get("total_sources", 0)
            },
            "session_info": {
                "session_id": metadata.get("session_id"),
                "conversation_context_used": bool(conversation_context),
                "session_documents_available": bool(session_documents)
            }
        }
        
        return {
            "status": "success",
            "content": content,
            "content_type": metadata.get("content_type"),
            "search_strategy": context_data.get("search_strategy", "hybrid"),
            "vector_results_found": context_data.get("vector_results_count", 0),
            "text_results_found": context_data.get("text_results_count", 0),
            "total_knowledge_sources": context_data.get("total_sources", 0),
            "marketing_examples_count": len(marketing_examples),
            "compliance_rules_count": len(disclaimers),
            "session_documents_count": len(session_documents),
            "session_documents_used": [doc.get('title', 'Unknown') for doc in session_documents],
            "fallback_used": context_data.get("fallback_used", False),
            "fallback_reason": context_data.get("fallback_reason"),
            "context_quality_score": context_quality.get("score", 0.5),
            "user_request": metadata.get("user_request"),
            "conversation_context_used": bool(conversation_context),
            "session_documents_available": bool(session_documents),
            "session_id": metadata.get("session_id"),
            "generated_content": content,
            "context_used": context_used,
            "metadata": detailed_metadata
        }
    
    async def _coordinate_generation_workflow(self, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate the complete content generation workflow."""
        context_data = request_params["context_data"]
        context_quality = request_params["context_quality"]
        
        # Select appropriate generation strategy
        strategy = self._select_generation_strategy(context_data, context_quality)
        logger.info(f"Selected generation strategy: {strategy.get_strategy_name()}")
        
        # Execute content generation
        generation_result = await strategy.generate_content(
            context_data=context_data,
            user_request=request_params["user_request"],
            content_type=request_params["content_type"],
            audience_type=request_params["audience_type"],
            current_content=request_params["current_content"],
            is_refinement=request_params["is_refinement"],
            youtube_context=request_params["youtube_context"]
        )
        
        if generation_result.success:
            return {
                "content": generation_result.content,
                "metadata": {
                    "strategy_used": generation_result.strategy_used,
                    "generation_time": generation_result.generation_time,
                    "token_usage": generation_result.token_usage
                }
            }
        else:
            return await self._try_fallback_generation(request_params, generation_result.error_message)
    
    def _select_generation_strategy(self, context_data: Dict[str, Any], context_quality: Dict[str, Any]):
        """Select the appropriate content generation strategy based on context quality."""
        quality_score = context_quality.get("score", 0.0)
        vector_available = context_data.get("vector_available", False)
        has_marketing_examples = len(context_data.get("marketing_examples", [])) > 0
        has_disclaimers = len(context_data.get("disclaimers", [])) > 0
        
        # Advanced: High quality context with vector search
        if (vector_available and quality_score > 0.7 and 
            has_marketing_examples and has_disclaimers):
            return self.strategy_factory.get_strategy("advanced")
        
        # Standard: Moderate quality context
        elif (vector_available and quality_score > 0.4 and 
              (has_marketing_examples or has_disclaimers)):
            return self.strategy_factory.get_strategy("standard")
        
        # Legacy: Fallback case
        else:
            logger.info(f"Using legacy strategy: quality_score={quality_score}, "
                       f"vector_available={vector_available}")
            return self.strategy_factory.get_strategy("legacy")
    
    async def _try_fallback_generation(self, request_params: Dict[str, Any], original_error: str) -> Dict[str, Any]:
        """Try fallback generation strategies if primary strategy fails."""
        context_data = request_params["context_data"]
        fallback_strategies = ["standard", "legacy"]
        
        for strategy_name in fallback_strategies:
            try:
                logger.info(f"Trying fallback strategy: {strategy_name}")
                strategy = self.strategy_factory.get_strategy(strategy_name)
                
                generation_result = await strategy.generate_content(
                    context_data=context_data,
                    user_request=request_params["user_request"],
                    content_type=request_params["content_type"],
                    audience_type=request_params["audience_type"],
                    current_content=request_params["current_content"],
                    is_refinement=request_params["is_refinement"],
                    youtube_context=request_params["youtube_context"]
                )
                
                if generation_result.success:
                    logger.info(f"Fallback strategy {strategy_name} succeeded")
                    return {
                        "content": generation_result.content,
                        "metadata": {
                            "strategy_used": generation_result.strategy_used,
                            "generation_time": generation_result.generation_time,
                            "token_usage": generation_result.token_usage,
                            "fallback_used": True,
                            "original_error": original_error
                        }
                    }
                
            except Exception as e:
                logger.warning(f"Fallback strategy {strategy_name} failed: {e}")
                continue
        
        raise Exception(f"All generation strategies failed. Original error: {original_error}")
    
    async def _execute_emergency_fallback(
        self,
        user_request: str,
        content_type: str,
        audience_type: Optional[str],
        user_id: Optional[str],
        session_id: Optional[str],
        original_error: Exception
    ) -> Dict[str, Any]:
        """Execute emergency fallback to original Warren database service."""
        try:
            from src.services.warren_database_service import warren_db_service
            
            logger.info("Attempting emergency fallback to original Warren service")
            fallback_result = await warren_db_service.generate_content_with_context(
                user_request=user_request,
                content_type=content_type,
                audience_type=audience_type,
                user_id=user_id,
                session_id=session_id
            )
            fallback_result["emergency_fallback"] = True
            fallback_result["original_error"] = str(original_error)
            return fallback_result
            
        except Exception as fallback_error:
            logger.error(f"Emergency fallback also failed: {str(fallback_error)}")
            return {
                "status": "error",
                "error": f"Enhanced Warren failed: {str(original_error)}. Fallback failed: {str(fallback_error)}",
                "content": None
            }


# Service instance for import compatibility
content_generation_orchestrator = ContentGenerationOrchestrator()
