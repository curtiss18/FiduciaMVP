"""
Context Assembler for Intelligent Token Management

"""

import asyncio
import json
import logging
import tiktoken
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum

from src.models.advisor_workflow_models import AdvisorMessages
from src.services.conversation_manager import ConversationManager
from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager
from src.services.context_assembly_service.optimization.compression.compression_strategy_factory import CompressionStrategyFactory

logger = logging.getLogger(__name__)

class RequestType(Enum):
    """Types of requests that require different token allocation strategies."""
    CREATION = "creation_mode"
    REFINEMENT = "refinement_mode"
    ANALYSIS = "analysis_mode"
    CONVERSATION = "conversation_mode"

class ContextType(Enum):
    """Types of context that can be included in Warren's prompt."""
    SYSTEM_PROMPT = "system_prompt"
    CONVERSATION_HISTORY = "conversation_history"
    DOCUMENT_SUMMARIES = "document_summaries"
    COMPLIANCE_SOURCES = "compliance_sources"
    CURRENT_CONTENT = "current_content"
    VECTOR_SEARCH_RESULTS = "vector_search_results"
    YOUTUBE_CONTEXT = "youtube_context"
    USER_INPUT = "user_input"

class ContextAssembler:
    
    # Token allocation strategies based on request type
    CONTEXT_BUDGETS = {
        RequestType.CREATION: {
            ContextType.SYSTEM_PROMPT: 5000,
            ContextType.CONVERSATION_HISTORY: 40000,
            ContextType.DOCUMENT_SUMMARIES: 30000,
            ContextType.COMPLIANCE_SOURCES: 25000,
            ContextType.VECTOR_SEARCH_RESULTS: 20000,
            ContextType.YOUTUBE_CONTEXT: 30000,
            ContextType.USER_INPUT: 2000,
            "buffer": 48000  # Reserve for response generation
        },
        RequestType.REFINEMENT: {
            ContextType.SYSTEM_PROMPT: 5000,
            ContextType.CURRENT_CONTENT: 15000,
            ContextType.CONVERSATION_HISTORY: 25000,
            ContextType.DOCUMENT_SUMMARIES: 20000,  # NEW: Add document summaries to refinement mode
            ContextType.COMPLIANCE_SOURCES: 20000,
            ContextType.VECTOR_SEARCH_RESULTS: 15000,
            ContextType.USER_INPUT: 2000,
            "buffer": 98000  # Reduced buffer to accommodate document summaries
        },
        RequestType.ANALYSIS: {
            ContextType.SYSTEM_PROMPT: 5000,
            ContextType.DOCUMENT_SUMMARIES: 50000,
            ContextType.CONVERSATION_HISTORY: 30000,
            ContextType.COMPLIANCE_SOURCES: 30000,
            ContextType.VECTOR_SEARCH_RESULTS: 25000,
            ContextType.USER_INPUT: 2000,
            "buffer": 58000
        },
        RequestType.CONVERSATION: {
            ContextType.SYSTEM_PROMPT: 5000,
            ContextType.CONVERSATION_HISTORY: 60000,
            ContextType.COMPLIANCE_SOURCES: 15000,
            ContextType.VECTOR_SEARCH_RESULTS: 10000,
            ContextType.USER_INPUT: 2000,
            "buffer": 108000
        }
    }
    
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
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.token_manager = TextTokenManager()
        self.compression_factory = CompressionStrategyFactory(self.token_manager)
        self.conversation_manager = ConversationManager(db_session)
        
        # Claude's limits
        self.MAX_TOTAL_TOKENS = 200000
        self.TARGET_INPUT_TOKENS = 180000  # Leave 20K for output
    
    async def build_warren_context(
        self, 
        session_id: str, 
        user_input: str,
        context_data: Optional[Dict] = None,
        current_content: Optional[str] = None,
        youtube_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build optimized context for Warren based on intelligent token allocation.
        
        Args:
            session_id: Session identifier for conversation history
            user_input: Current user request
            context_data: Vector search results and compliance sources
            current_content: Existing content for refinement scenarios
            youtube_context: YouTube video transcript context
            
        Returns:
            Dict containing optimized context and metadata
        """
        try:
            # Determine request type and allocate token budget
            request_type = self._determine_request_type(user_input, current_content)
            token_budget = await self.allocate_token_budget(request_type, user_input)
            
            logger.info(f"Building context for {request_type.value} with budget: {token_budget}")
            
            # Gather all available context elements
            context_elements = await self._gather_context_elements(
                session_id, user_input, context_data, current_content, youtube_context
            )
            
            # Prioritize and optimize context within budget
            optimized_context = await self.prioritize_context_elements(
                context_elements, token_budget, request_type
            )
            
            # Build final context string
            final_context = self._build_final_context_string(optimized_context)
            
            # Validate total token count
            total_tokens = self.token_manager.count_tokens(final_context)
            
            logger.info(f"Context assembled: {total_tokens} tokens for {request_type.value}")
            
            return {
                "context": final_context,
                "request_type": request_type.value,
                "total_tokens": total_tokens,
                "token_budget": token_budget,
                "context_breakdown": {ctx_type.value: len(content) for ctx_type, content in optimized_context.items()},
                "optimization_applied": total_tokens > self.TARGET_INPUT_TOKENS
            }
            
        except Exception as e:
            logger.error(f"Error building Warren context: {e}")
            # Fallback to basic context
            return await self._build_fallback_context(user_input, context_data)
    
    async def allocate_token_budget(self, request_type: RequestType, user_input: str) -> Dict[ContextType, int]:
        base_budget = self.CONTEXT_BUDGETS.get(request_type, self.CONTEXT_BUDGETS[RequestType.CREATION]).copy()
        
        # Dynamic adjustments based on request characteristics
        user_input_tokens = self.token_manager.count_tokens(user_input)
        
        # Adjust for longer user input
        if user_input_tokens > base_budget.get(ContextType.USER_INPUT, 2000):
            excess_tokens = user_input_tokens - base_budget[ContextType.USER_INPUT]
            base_budget[ContextType.USER_INPUT] = user_input_tokens
            
            # Reduce other budgets proportionally
            adjustable_contexts = [
                ContextType.DOCUMENT_SUMMARIES,
                ContextType.VECTOR_SEARCH_RESULTS,
                ContextType.YOUTUBE_CONTEXT
            ]
            
            reduction_per_context = excess_tokens // len(adjustable_contexts)
            for context_type in adjustable_contexts:
                if context_type in base_budget:
                    base_budget[context_type] = max(1000, base_budget[context_type] - reduction_per_context)
        
        # Convert to ContextType keys and remove buffer
        budget = {}
        for key, value in base_budget.items():
            if isinstance(key, ContextType):
                budget[key] = value
            elif key != "buffer":  # Skip buffer allocation
                try:
                    budget[ContextType(key)] = value
                except ValueError:
                    continue
        
        return budget
    
    async def prioritize_context_elements(
        self, 
        context_elements: Dict[ContextType, str], 
        budget: Dict[ContextType, int],
        request_type: RequestType
    ) -> Dict[ContextType, str]:
        optimized_context = {}
        total_used_tokens = 0
        
        # Sort context types by priority
        sorted_contexts = sorted(
            context_elements.items(),
            key=lambda x: self.CONTEXT_PRIORITIES.get(x[0], 0),
            reverse=True
        )
        
        for context_type, content in sorted_contexts:
            if not content:
                continue
                
            allocated_budget = budget.get(context_type, 0)
            if allocated_budget <= 0:
                continue
                
            content_tokens = self.token_manager.count_tokens(content)
            
            if content_tokens <= allocated_budget:
                # Content fits within budget
                optimized_context[context_type] = content
                total_used_tokens += content_tokens
                logger.debug(f"{context_type.value}: {content_tokens} tokens (within budget)")
                
            else:
                # Need to compress content
                compressed_content = await self._compress_content(
                    content, allocated_budget, context_type
                )
                optimized_context[context_type] = compressed_content
                compressed_tokens = self.token_manager.count_tokens(compressed_content)
                total_used_tokens += compressed_tokens
                
                logger.debug(f"{context_type.value}: {content_tokens} → {compressed_tokens} tokens (compressed)")
        
        # Check total and apply emergency compression if needed
        if total_used_tokens > self.TARGET_INPUT_TOKENS:
            logger.warning(f"Total tokens ({total_used_tokens}) exceeds target, applying emergency compression")
            optimized_context = await self._apply_emergency_compression(
                optimized_context, self.TARGET_INPUT_TOKENS
            )
        
        logger.info(f"Context optimization complete: {total_used_tokens} total tokens")
        return optimized_context
    
    def _determine_request_type(self, user_input: str, current_content: Optional[str]) -> RequestType:
        user_input_lower = user_input.lower()
        
        # Check for refinement indicators
        if current_content or any(keyword in user_input_lower for keyword in [
            'edit', 'change', 'modify', 'update', 'revise', 'improve', 'make it', 'adjust'
        ]):
            return RequestType.REFINEMENT
        
        # Check for analysis requests
        if any(keyword in user_input_lower for keyword in [
            'analyze', 'review', 'compare', 'evaluate', 'assess', 'what do you think'
        ]):
            return RequestType.ANALYSIS
        
        # Check for creation requests
        if any(keyword in user_input_lower for keyword in [
            'create', 'write', 'generate', 'draft', 'compose', 'help me with'
        ]):
            return RequestType.CREATION
        
        # Default to conversation mode
        return RequestType.CONVERSATION
    
    async def _gather_context_elements(
        self,
        session_id: str,
        user_input: str,
        context_data: Optional[Dict],
        current_content: Optional[str],
        youtube_context: Optional[Dict]
    ) -> Dict[ContextType, str]:
        elements = {}
        
        # User input (always include)
        elements[ContextType.USER_INPUT] = user_input
        
        # Current content for refinement
        if current_content:
            elements[ContextType.CURRENT_CONTENT] = current_content
        
        # Conversation history
        try:
            conversation_context = await self.conversation_manager.get_conversation_context(session_id)
            if conversation_context:
                elements[ContextType.CONVERSATION_HISTORY] = conversation_context
        except Exception as e:
            logger.warning(f"Could not get conversation context: {e}")
        
        # Vector search results and compliance sources
        if context_data:
            # Compliance sources
            compliance_sources = self._extract_compliance_sources(context_data)
            if compliance_sources:
                elements[ContextType.COMPLIANCE_SOURCES] = compliance_sources
            
            # Vector search results
            vector_results = self._extract_vector_search_results(context_data)
            if vector_results:
                elements[ContextType.VECTOR_SEARCH_RESULTS] = vector_results
        
        # YouTube context
        if youtube_context:
            youtube_formatted = self._format_youtube_context(youtube_context)
            elements[ContextType.YOUTUBE_CONTEXT] = youtube_formatted
        
        return elements
    
    def _extract_compliance_sources(self, context_data: Dict) -> str:
        compliance_parts = []
        
        # Rules
        rules = context_data.get("rules", [])
        if rules:
            compliance_parts.append("## COMPLIANCE RULES:")
            for rule in rules[:3]:  # Limit to most relevant
                compliance_parts.append(f"**{rule.get('title', 'Rule')}**: {rule.get('content_text', '')[:200]}...")
        
        # Disclaimers
        disclaimers = context_data.get("disclaimers", [])
        if disclaimers:
            compliance_parts.append("\n## REQUIRED DISCLAIMERS:")
            for disclaimer in disclaimers[:2]:
                compliance_parts.append(f"**{disclaimer.get('title', 'Disclaimer')}**: {disclaimer.get('content_text', '')[:200]}...")
        
        return "\n".join(compliance_parts)
    
    def _extract_vector_search_results(self, context_data: Dict) -> str:
        results_parts = []
        
        examples = context_data.get("examples", [])
        if examples:
            results_parts.append("## APPROVED EXAMPLES:")
            for example in examples[:3]:  # Limit to most relevant
                results_parts.append(f"**{example.get('title', 'Example')}**")
                results_parts.append(f"Content: {example.get('content_text', '')[:300]}...")
                if example.get('tags'):
                    results_parts.append(f"Tags: {example['tags']}")
                results_parts.append("")
        
        return "\n".join(results_parts)
    
    def _format_youtube_context(self, youtube_context: Dict) -> str:
        context_parts = []
        context_parts.append("## VIDEO CONTEXT:")
        
        video_info = youtube_context.get("metadata", {})
        if video_info.get("url"):
            context_parts.append(f"Video URL: {video_info['url']}")
        
        transcript = youtube_context.get("transcript", "")
        if transcript:
            context_parts.append("**VIDEO TRANSCRIPT:**")
            context_parts.append(transcript)
        
        return "\n".join(context_parts)
    
    def _build_final_context_string(self, optimized_context: Dict[ContextType, str]) -> str:
        context_parts = []
        
        # Add context elements in logical order
        ordered_types = [
            ContextType.COMPLIANCE_SOURCES,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.CONVERSATION_HISTORY,
            ContextType.CURRENT_CONTENT,
            ContextType.YOUTUBE_CONTEXT,
            ContextType.USER_INPUT
        ]
        
        for context_type in ordered_types:
            if context_type in optimized_context and optimized_context[context_type]:
                context_parts.append(optimized_context[context_type])
        
        return "\n\n".join(context_parts)
    
    async def _apply_emergency_compression(
        self, 
        context: Dict[ContextType, str], 
        target_tokens: int
    ) -> Dict[ContextType, str]:
        """Apply emergency compression when context exceeds limits."""
        current_tokens = sum(self.token_manager.count_tokens(content) for content in context.values())
        reduction_needed = current_tokens - target_tokens
        
        if reduction_needed <= 0:
            return context
        
        # Priority order for compression (compress less important items first)
        compression_order = [
            ContextType.YOUTUBE_CONTEXT,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.CONVERSATION_HISTORY,
            ContextType.COMPLIANCE_SOURCES,
            ContextType.CURRENT_CONTENT
        ]
        
        compressed_context = context.copy()
        tokens_saved = 0
        
        for context_type in compression_order:
            if context_type not in compressed_context or tokens_saved >= reduction_needed:
                continue
            
            original_content = compressed_context[context_type]
            original_tokens = self.token_manager.count_tokens(original_content)
            
            # Reduce by 30% at a time
            target_reduction = min(original_tokens * 0.3, reduction_needed - tokens_saved)
            new_target = max(500, original_tokens - target_reduction)  # Minimum 500 tokens
            
            compressed_content = await self._compress_content(
                original_content, new_target, context_type
            )
            
            compressed_context[context_type] = compressed_content
            tokens_saved += original_tokens - self.token_manager.count_tokens(compressed_content)
        
        logger.warning(f"Emergency compression applied: {tokens_saved} tokens saved")
        return compressed_context
    
    async def _build_fallback_context(self, user_input: str, context_data: Optional[Dict]) -> Dict:
        basic_context = f"USER REQUEST: {user_input}"
        
        if context_data:
            examples = context_data.get("examples", [])
            if examples:
                basic_context += f"\n\nAPPROVED EXAMPLES:\n{examples[0].get('content_text', '')[:500]}..."
        
        return {
            "context": basic_context,
            "request_type": "fallback",
            "total_tokens": self.token_manager.count_tokens(basic_context),
            "token_budget": {},
            "context_breakdown": {},
            "optimization_applied": False
        }

    async def _compress_content(
        self, 
        content: str, 
        target_tokens: int, 
        context_type: ContextType
    ) -> str:

        if not content:
            return content
            
        current_tokens = self.token_manager.count_tokens(content)
        if current_tokens <= target_tokens:
            return content
        
        # Get appropriate compression strategy
        strategy = self.compression_factory.get_best_strategy_for_content(content, context_type)
        
        try:
            compressed_content = await strategy.compress_content(content, target_tokens, context_type)
            return compressed_content
        except Exception as e:
            logger.error(f"Compression failed for {context_type}: {e}")
            # Fallback to simple truncation
            return self._simple_truncate(content, target_tokens)
    
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
