"""Basic context optimization service for budget-aware element prioritization."""

import logging
from typing import Dict, List, Optional

from ..interfaces import ContextAssemblyStrategy
from ..models import ContextType, ContextElement, BudgetAllocation, QualityMetrics
from .text_token_manager import TextTokenManager
from .compression import CompressionStrategyFactory

logger = logging.getLogger(__name__)


class BasicContextOptimizer(ContextAssemblyStrategy):
    """Budget-aware context optimization with priority-based element selection."""
    
    # Context priority order (higher number = higher priority)
    CONTEXT_PRIORITIES = {
        ContextType.SYSTEM_PROMPT: 10,  # Always highest priority
        ContextType.USER_INPUT: 9,      # Current request always included
        ContextType.CURRENT_CONTENT: 8, # For refinement tasks
        ContextType.COMPLIANCE_SOURCES: 7,  # Critical for compliance
        ContextType.CONVERSATION_HISTORY: 6,  # Important for context
        ContextType.VECTOR_SEARCH_RESULTS: 5,  # Supporting evidence
        ContextType.DOCUMENT_SUMMARIES: 4,   # User-provided context
        ContextType.YOUTUBE_CONTEXT: 3       # Additional context
    }
    
    def __init__(self, 
                 token_manager: Optional[TextTokenManager] = None,
                 compression_factory: Optional[CompressionStrategyFactory] = None,
                 target_tokens: int = 180000):
        self.token_manager = token_manager or TextTokenManager()
        self.compression_factory = compression_factory or CompressionStrategyFactory(self.token_manager)
        self.target_tokens = target_tokens
    
    async def assemble_context(
        self, 
        elements: List[ContextElement], 
        budget_allocations: Dict[ContextType, BudgetAllocation]
    ) -> str:
        if not elements:
            return ""
        
        # Optimize elements within budget
        optimized_elements = await self.optimize_context_elements(elements, budget_allocations)
        
        # Build final context string
        context_parts = []
        
        # Assemble in logical order
        ordered_types = [
            ContextType.COMPLIANCE_SOURCES,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.CONVERSATION_HISTORY,
            ContextType.CURRENT_CONTENT,
            ContextType.DOCUMENT_SUMMARIES,
            ContextType.YOUTUBE_CONTEXT,
            ContextType.USER_INPUT
        ]
        
        for context_type in ordered_types:
            type_elements = [elem for elem in optimized_elements if elem.context_type == context_type]
            
            for element in type_elements:
                if element.content.strip():
                    context_parts.append(element.content)
        
        final_context = "\n\n".join(context_parts)
        
        # Final emergency compression if needed
        if self.token_manager.count_tokens(final_context) > self.target_tokens:
            logger.warning("Applying emergency compression to assembled context")
            final_context = await self._apply_emergency_compression(final_context)
        
        return final_context
    
    async def optimize_context_elements(
        self,
        elements: List[ContextElement], 
        budget_allocations: Dict[ContextType, BudgetAllocation]
    ) -> List[ContextElement]:
        if not elements:
            return []
        
        if not budget_allocations:
            logger.warning("No budget allocations provided, returning elements as-is")
            return elements
        
        optimized_elements = []
        total_used_tokens = 0
        
        # Sort elements by priority
        sorted_elements = sorted(
            elements,
            key=lambda x: self._calculate_effective_priority(x),
            reverse=True
        )
        
        for element in sorted_elements:
            if not element.content:
                continue
            
            # Get budget allocation for this context type
            allocation = budget_allocations.get(element.context_type)
            if not allocation or allocation.allocated_tokens <= 0:
                logger.debug(f"No budget for {element.context_type.value}, skipping")
                continue
            
            current_tokens = element.token_count
            allocated_budget = allocation.allocated_tokens
            
            if current_tokens <= allocated_budget:
                # Content fits within budget
                optimized_elements.append(element)
                total_used_tokens += current_tokens
                logger.debug(f"{element.context_type.value}: {current_tokens} tokens (within budget)")
                
            else:
                # Need to compress content
                compressed_element = await self._compress_context_element(
                    element, allocated_budget
                )
                
                if compressed_element:
                    optimized_elements.append(compressed_element)
                    total_used_tokens += compressed_element.token_count
                    logger.debug(
                        f"{element.context_type.value}: {current_tokens} → "
                        f"{compressed_element.token_count} tokens (compressed)"
                    )
                else:
                    logger.warning(f"Could not compress {element.context_type.value} to fit budget")
        
        logger.info(f"Context optimization complete: {total_used_tokens} total tokens")
        return optimized_elements
    
    def _calculate_effective_priority(self, element: ContextElement) -> float:
        base_priority = self.CONTEXT_PRIORITIES.get(element.context_type, 5.0)
        relevance_boost = element.relevance_score * 2.0  # Scale relevance impact
        
        return base_priority + relevance_boost
    
    async def _compress_context_element(
        self, 
        element: ContextElement, 
        target_tokens: int
    ) -> Optional[ContextElement]:
        try:
            # Get appropriate compression strategy
            strategy = self.compression_factory.get_best_strategy_for_content(
                element.content, element.context_type
            )
            
            # Compress content
            compressed_content = await strategy.compress_content(
                element.content, target_tokens, element.context_type
            )
            
            if not compressed_content or len(compressed_content.strip()) < 10:
                return None
            
            # Calculate compression metrics
            original_tokens = element.token_count
            compressed_tokens = self.token_manager.count_tokens(compressed_content)
            compression_ratio = 1.0 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0.0
            
            # Create compressed element
            compressed_element = ContextElement(
                content=compressed_content,
                context_type=element.context_type,
                priority_score=element.priority_score,
                relevance_score=element.relevance_score,
                token_count=compressed_tokens,
                source_metadata={
                    **element.source_metadata,
                    "compressed": True,
                    "original_tokens": original_tokens,
                    "compression_ratio": compression_ratio,
                    "compression_strategy": strategy.__class__.__name__
                },
                compression_level=compression_ratio
            )
            
            return compressed_element
            
        except Exception as e:
            logger.error(f"Error compressing context element: {e}")
            return None
    
    async def _apply_emergency_compression(self, context: str) -> str:
        current_tokens = self.token_manager.count_tokens(context)
        reduction_needed = current_tokens - self.target_tokens
        
        if reduction_needed <= 0:
            return context
        
        logger.warning(f"Emergency compression: reducing {reduction_needed} tokens")
        
        # Use generic compression as fallback
        generic_strategy = self.compression_factory.create_strategy(ContextType.USER_INPUT)
        
        try:
            compressed_context = await generic_strategy.compress_content(
                context, self.target_tokens, ContextType.USER_INPUT
            )
            
            final_tokens = self.token_manager.count_tokens(compressed_context)
            logger.warning(f"Emergency compression complete: {current_tokens} → {final_tokens} tokens")
            
            return compressed_context
            
        except Exception as e:
            logger.error(f"Emergency compression failed: {e}")
            # Fallback to simple truncation
            return self._simple_truncate(context, self.target_tokens)
    
    def _simple_truncate(self, text: str, token_limit: int) -> str:
        if self.token_manager.count_tokens(text) <= token_limit:
            return text
        
        # Estimate character limit based on token limit
        estimated_chars = self.token_manager.estimate_chars_from_tokens(token_limit)
        
        if len(text) <= estimated_chars:
            return text
        
        # Truncate with some buffer
        truncated = text[:int(estimated_chars * 0.9)]
        return truncated.rstrip() + "\n\n[Content truncated due to length]"
    
    def assess_quality(
        self, 
        assembled_context: str, 
        elements: List[ContextElement]
    ) -> QualityMetrics:
        total_original_tokens = sum(elem.token_count for elem in elements)
        final_tokens = self.token_manager.count_tokens(assembled_context)
        
        # Calculate compression ratio
        compression_ratio = 1.0 - (final_tokens / total_original_tokens) if total_original_tokens > 0 else 0.0
        
        # Calculate coverage (how many element types included)
        original_types = set(elem.context_type for elem in elements)
        included_types = set()
        
        for elem in elements:
            if elem.content.strip() and elem.content[:100] in assembled_context:
                included_types.add(elem.context_type)
        
        coverage = len(included_types) / len(original_types) if original_types else 0.0
        
        # Calculate priority preservation
        high_priority_elements = [elem for elem in elements if elem.priority_score >= 8.0]
        high_priority_preserved = sum(
            1 for elem in high_priority_elements
            if elem.content.strip() and elem.content[:100] in assembled_context
        )
        
        priority_preservation = (
            high_priority_preserved / len(high_priority_elements) 
            if high_priority_elements else 1.0
        )
        
        # Calculate overall quality score
        quality_score = (
            (1.0 - compression_ratio) * 0.3 +  # Less compression = higher quality
            coverage * 0.4 +  # More types included = higher quality
            priority_preservation * 0.3  # High priority preserved = higher quality
        )
        
        return QualityMetrics(
            relevance_score=coverage,  # How well context matches requirements
            completeness_score=priority_preservation,  # How complete the context is
            coherence_score=0.8,  # Assume good coherence (could be enhanced)
            diversity_score=coverage,  # Type diversity
            token_efficiency=(final_tokens / total_original_tokens) if total_original_tokens > 0 else 1.0,
            compression_ratio=compression_ratio
        )
    
    def get_optimization_stats(self) -> Dict[str, any]:
        token_stats = self.token_manager.get_cache_stats()
        
        return {
            "optimizer_type": "BasicContextOptimizer",
            "target_tokens": self.target_tokens,
            "token_manager_stats": token_stats,
            "available_strategies": [
                "StructurePreservingCompressor",
                "ConversationCompressor", 
                "GenericCompressor"
            ]
        }
