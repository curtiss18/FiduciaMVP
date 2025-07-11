"""Basic Context Assembly Orchestrator - Main coordinator for context assembly workflow"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from .models import RequestType, ContextType, ContextElement
from .budget import BudgetAllocator, RequestTypeAnalyzer
from .gathering import ContextGatherer
from .assembly import ContextBuilder
from .optimization import TextTokenManager

logger = logging.getLogger(__name__)


class BasicContextAssemblyOrchestrator:
    """
    Main orchestrator for basic context assembly workflow.
    
    Replaces the original ContextAssembler with dependency injection and SRP.
    Maintains exact same interface for backward compatibility.
    """
    
    def __init__(self,
                 budget_allocator: Optional[BudgetAllocator] = None,
                 request_analyzer: Optional[RequestTypeAnalyzer] = None,
                 context_gatherer: Optional[ContextGatherer] = None,
                 context_builder: Optional[ContextBuilder] = None,
                 token_manager: Optional[TextTokenManager] = None):
        """Initialize with dependency injection for testing."""
        
        # Use dependency injection or create defaults
        self.token_manager = token_manager or TextTokenManager()
        self.budget_allocator = budget_allocator or BudgetAllocator(self.token_manager)
        self.request_analyzer = request_analyzer or RequestTypeAnalyzer()
        self.context_gatherer = context_gatherer or ContextGatherer()
        self.context_builder = context_builder or ContextBuilder(self.token_manager)
        
        # Configuration matching original ContextAssembler
        self.MAX_TOTAL_TOKENS = 200000
        self.TARGET_INPUT_TOKENS = 180000  # Leave 20K for output
    
    async def build_warren_context(
        self,
        session_id: str,
        user_input: str,
        context_data: Optional[Dict] = None,
        current_content: Optional[str] = None,
        youtube_context: Optional[Dict] = None,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Build optimized context for Warren based on intelligent token allocation.
        
        MAINTAINS EXACT SAME INTERFACE as original ContextAssembler.build_warren_context()
        
        Args:
            session_id: Session identifier for conversation history
            user_input: Current user request
            context_data: Vector search results and compliance sources
            current_content: Existing content for refinement scenarios
            youtube_context: YouTube video transcript context
            db_session: Database session for data access
            
        Returns:
            Dict containing optimized context and metadata
        """
        try:
            if not db_session:
                logger.warning("No database session provided, context gathering may be limited")
            
            # Step 1: Analyze request type
            request_type = self.request_analyzer.analyze_request_type(
                user_input=user_input, 
                current_content=current_content
            )
            
            logger.info(f"Request type determined: {request_type.value}")
            
            # Step 2: Allocate token budget
            budget_allocations = await self.budget_allocator.allocate_budget(
                request_type=request_type,
                user_input=user_input,
                available_tokens=self.MAX_TOTAL_TOKENS
            )
            
            # Convert budget allocations to simple dict for compatibility
            token_budget = {
                context_type: allocation.allocated_tokens 
                for context_type, allocation in budget_allocations.items()
            }
            
            logger.info(f"Token budget allocated: {sum(token_budget.values())} total tokens")
            
            # Step 3: Gather context elements
            context_elements = await self._gather_all_context_elements(
                session_id=session_id,
                user_input=user_input,
                context_data=context_data,
                current_content=current_content,
                youtube_context=youtube_context,
                db_session=db_session,
                token_budget=token_budget
            )
            
            logger.info(f"Gathered {len(context_elements)} context elements")
            
            # Step 4: Optimize context within budget
            optimized_elements = await self._optimize_context_elements(
                elements=context_elements,
                token_budget=token_budget,
                request_type=request_type
            )
            
            # Step 5: Build final context string
            final_context = self.context_builder.build_context_string(optimized_elements)
            
            # Step 6: Validate and return results
            total_tokens = self.token_manager.count_tokens(final_context)
            context_breakdown = self.context_builder.get_context_summary(optimized_elements)
            
            logger.info(f"Context assembled: {total_tokens} tokens for {request_type.value}")
            
            return {
                "context": final_context,
                "request_type": request_type.value,
                "total_tokens": total_tokens,
                "token_budget": token_budget,
                "context_breakdown": {k: v for k, v in context_breakdown.items() if k != 'total_tokens' and k != 'total_elements'},
                "optimization_applied": total_tokens > self.TARGET_INPUT_TOKENS
            }
            
        except Exception as e:
            logger.error(f"Error building Warren context: {e}")
            return await self._build_fallback_context(user_input, context_data)
    
    async def _gather_all_context_elements(
        self,
        session_id: str,
        user_input: str,
        context_data: Optional[Dict],
        current_content: Optional[str],
        youtube_context: Optional[Dict],
        db_session: Optional[AsyncSession],
        token_budget: Dict[ContextType, int]
    ) -> List[ContextElement]:
        """Gather all available context elements from various sources."""
        
        all_elements = []
        
        # Add user input as context element
        user_input_tokens = self.token_manager.count_tokens(user_input)
        user_element = ContextElement(
            content=user_input,
            context_type=ContextType.USER_INPUT,
            priority_score=10.0,  # Highest priority
            relevance_score=1.0,
            token_count=user_input_tokens,
            source_metadata={"source_type": "user_input"}
        )
        all_elements.append(user_element)
        
        # Add current content if provided (refinement mode)
        if current_content:
            current_content_tokens = self.token_manager.count_tokens(current_content)
            current_element = ContextElement(
                content=current_content,
                context_type=ContextType.CURRENT_CONTENT,
                priority_score=9.5,  # Very high priority for refinement
                relevance_score=1.0,
                token_count=current_content_tokens,
                source_metadata={"source_type": "current_content"}
            )
            all_elements.append(current_element)
        
        # Gather context using ContextGatherer service
        if db_session:
            try:
                gathered_elements = await self.context_gatherer.gather_all_context(
                    session_id=session_id,
                    db_session=db_session,
                    context_data=context_data
                )
                all_elements.extend(gathered_elements)
            except Exception as e:
                logger.warning(f"Failed to gather context elements: {e}")
        
        # Add YouTube context if provided
        if youtube_context and youtube_context.get('transcript'):
            youtube_content = youtube_context['transcript']
            youtube_tokens = self.token_manager.count_tokens(youtube_content)
            youtube_element = ContextElement(
                content=youtube_content,
                context_type=ContextType.YOUTUBE_CONTEXT,
                priority_score=7.0,
                relevance_score=0.8,
                token_count=youtube_tokens,
                source_metadata={"source_type": "youtube_transcript", "video_id": youtube_context.get('video_id')}
            )
            all_elements.append(youtube_element)
        
        # Add vector search results from context_data
        if context_data and context_data.get('search_results'):
            search_results = context_data['search_results']
            if isinstance(search_results, list):
                for i, result in enumerate(search_results):
                    result_content = str(result)
                    result_tokens = self.token_manager.count_tokens(result_content)
                    result_element = ContextElement(
                        content=result_content,
                        context_type=ContextType.VECTOR_SEARCH_RESULTS,
                        priority_score=6.0 - (i * 0.1),  # Decreasing priority for later results
                        relevance_score=0.7,
                        token_count=result_tokens,
                        source_metadata={"source_type": "vector_search", "result_index": i}
                    )
                    all_elements.append(result_element)
        
        return all_elements
    
    async def _optimize_context_elements(
        self,
        elements: List[ContextElement],
        token_budget: Dict[ContextType, int],
        request_type: RequestType
    ) -> List[ContextElement]:
        """Optimize context elements to fit within token budget."""
        
        optimized_elements = []
        
        # Group elements by type
        elements_by_type = {}
        for element in elements:
            if element.context_type not in elements_by_type:
                elements_by_type[element.context_type] = []
            elements_by_type[element.context_type].append(element)
        
        # Process each context type within its budget
        for context_type, type_elements in elements_by_type.items():
            budget = token_budget.get(context_type, 0)
            
            if budget <= 0:
                continue
            
            # Sort by effective priority (priority * relevance)
            type_elements.sort(key=lambda x: x.effective_priority, reverse=True)
            
            # Select elements that fit within budget
            current_tokens = 0
            for element in type_elements:
                if current_tokens + element.token_count <= budget:
                    optimized_elements.append(element)
                    current_tokens += element.token_count
                else:
                    # If single element exceeds budget, try basic compression
                    if not optimized_elements:  # No elements yet for this type
                        compressed_element = await self._compress_element_basic(element, budget)
                        if compressed_element:
                            optimized_elements.append(compressed_element)
                    break
        
        return optimized_elements
    
    async def _compress_element_basic(self, element: ContextElement, target_tokens: int) -> Optional[ContextElement]:
        """Apply basic compression to fit element within target tokens."""
        
        if element.token_count <= target_tokens:
            return element
        
        try:
            # Simple truncation strategy for basic compression
            content = element.content
            
            # Calculate truncation ratio
            ratio = target_tokens / element.token_count
            
            # Truncate content
            target_chars = int(len(content) * ratio * 0.9)  # Leave some buffer
            compressed_content = content[:target_chars] + "..." if target_chars < len(content) else content
            
            # Create compressed element
            compressed_tokens = self.token_manager.count_tokens(compressed_content)
            
            return ContextElement(
                content=compressed_content,
                context_type=element.context_type,
                priority_score=element.priority_score,
                relevance_score=element.relevance_score,
                token_count=compressed_tokens,
                source_metadata={**element.source_metadata, "compressed": True},
                compression_level=1.0 - (compressed_tokens / element.token_count)
            )
            
        except Exception as e:
            logger.warning(f"Failed to compress element: {e}")
            return None
    
    async def _build_fallback_context(self, user_input: str, context_data: Optional[Dict]) -> Dict[str, Any]:
        """Build minimal fallback context if main assembly fails."""
        
        try:
            fallback_parts = [f"User Request: {user_input}"]
            
            if context_data and context_data.get('search_results'):
                fallback_parts.append("Relevant Context:")
                fallback_parts.append(str(context_data['search_results'])[:1000])
            
            fallback_context = "\n\n".join(fallback_parts)
            fallback_tokens = self.token_manager.count_tokens(fallback_context)
            
            return {
                "context": fallback_context,
                "request_type": RequestType.CREATION.value,
                "total_tokens": fallback_tokens,
                "token_budget": {},
                "context_breakdown": {"fallback": fallback_tokens},
                "optimization_applied": False,
                "fallback_used": True
            }
            
        except Exception as e:
            logger.error(f"Fallback context creation failed: {e}")
            return {
                "context": f"User Request: {user_input}",
                "request_type": RequestType.CREATION.value,
                "total_tokens": 50,
                "token_budget": {},
                "context_breakdown": {},
                "optimization_applied": False,
                "fallback_used": True
            }
