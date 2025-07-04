"""
Context Assembler for Intelligent Token Management

Implements sophisticated token allocation strategies and dynamic context assembly
for Warren's conversation system. Handles Claude's 200K token limits with
intelligent context prioritization and optimization.

Based on SCRUM-34 requirements for enhanced token management and context assembly.
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
    """
    Intelligent context assembly with dynamic token allocation strategies.
    
    Features:
    - Request-type-aware token budgeting
    - Priority-based context selection
    - Intelligent context compression
    - Graceful degradation strategies
    """
    
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
        self.token_manager = TokenManager()
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
        """
        Allocate token budget based on request type and characteristics.
        
        Returns optimized budget allocation for different context types.
        """
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
        """
        Prioritize and optimize context elements within token budget.
        
        Uses intelligent compression and selection based on priority and available budget.
        """
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
                compressed_content = await self.token_manager.compress_content(
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
        """
        Analyze user input to determine the type of request for optimal token allocation.
        """
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
        """
        Gather all available context elements for optimization.
        """
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
        """Extract and format compliance sources from context data."""
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
        """Extract and format vector search results from context data."""
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
        """Format YouTube context for inclusion in prompt."""
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
        """Build the final context string from optimized context elements."""
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
            
            compressed_content = await self.token_manager.compress_content(
                original_content, new_target, context_type
            )
            
            compressed_context[context_type] = compressed_content
            tokens_saved += original_tokens - self.token_manager.count_tokens(compressed_content)
        
        logger.warning(f"Emergency compression applied: {tokens_saved} tokens saved")
        return compressed_context
    
    async def _build_fallback_context(self, user_input: str, context_data: Optional[Dict]) -> Dict:
        """Build basic fallback context when optimization fails."""
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


class TokenManager:
    """
    Precise token counting and content compression for Claude AI.
    
    Uses tiktoken for accurate token counting and intelligent compression strategies.
    """
    
    def __init__(self):
        # Use Claude's tokenizer (approximating with GPT-4 tokenizer)
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            # Fallback to rough estimation
            self.tokenizer = None
            logger.warning("Could not load tiktoken, using approximation")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens accurately using tiktoken.
        """
        if not text:
            return 0
            
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4
    
    async def compress_content(
        self, 
        content: str, 
        target_tokens: int, 
        context_type: ContextType
    ) -> str:
        """
        Compress content to fit within target token count while preserving key information.
        """
        if not content:
            return content
            
        current_tokens = self.count_tokens(content)
        if current_tokens <= target_tokens:
            return content
        
        # Choose compression strategy based on context type
        if context_type == ContextType.CONVERSATION_HISTORY:
            return self._compress_conversation(content, target_tokens)
        elif context_type == ContextType.YOUTUBE_CONTEXT:
            return self._compress_youtube_context(content, target_tokens)
        elif context_type == ContextType.VECTOR_SEARCH_RESULTS:
            return self._compress_search_results(content, target_tokens)
        else:
            return self._compress_generic(content, target_tokens)
    
    def _compress_conversation(self, content: str, target_tokens: int) -> str:
        """Compress conversation history by keeping recent exchanges."""
        lines = content.split('\n')
        
        # Keep most recent exchanges
        compressed_lines = []
        current_tokens = 0
        
        for line in reversed(lines):
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens <= target_tokens:
                compressed_lines.insert(0, line)
                current_tokens += line_tokens
            else:
                break
        
        if len(compressed_lines) < len(lines):
            compressed_lines.insert(0, "[Earlier conversation truncated]")
        
        return '\n'.join(compressed_lines)
    
    def _compress_youtube_context(self, content: str, target_tokens: int) -> str:
        """Compress YouTube context by truncating transcript."""
        lines = content.split('\n')
        header_lines = []
        transcript_lines = []
        
        in_transcript = False
        for line in lines:
            if "**VIDEO TRANSCRIPT:**" in line:
                in_transcript = True
                header_lines.append(line)
            elif not in_transcript:
                header_lines.append(line)
            else:
                transcript_lines.append(line)
        
        # Calculate available tokens for transcript
        header_tokens = self.count_tokens('\n'.join(header_lines))
        available_transcript_tokens = target_tokens - header_tokens - 50  # Buffer
        
        if available_transcript_tokens <= 0:
            return '\n'.join(header_lines) + "\n[Transcript too long to include]"
        
        # Truncate transcript to fit
        transcript_text = '\n'.join(transcript_lines)
        if self.count_tokens(transcript_text) <= available_transcript_tokens:
            return content
        
        # Keep beginning of transcript
        compressed_transcript = self._truncate_to_token_limit(transcript_text, available_transcript_tokens)
        
        return '\n'.join(header_lines) + '\n' + compressed_transcript + "\n[Transcript truncated for length]"
    
    def _compress_search_results(self, content: str, target_tokens: int) -> str:
        """Compress search results by limiting examples."""
        lines = content.split('\n')
        compressed_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens <= target_tokens:
                compressed_lines.append(line)
                current_tokens += line_tokens
            else:
                if not compressed_lines or "Examples truncated" not in compressed_lines[-1]:
                    compressed_lines.append("[Additional examples truncated for space]")
                break
        
        return '\n'.join(compressed_lines)
    
    def _compress_generic(self, content: str, target_tokens: int) -> str:
        """Generic compression by truncating while preserving structure."""
        return self._truncate_to_token_limit(content, target_tokens)
    
    def _truncate_to_token_limit(self, text: str, token_limit: int) -> str:
        """Truncate text to approximate token limit."""
        if self.count_tokens(text) <= token_limit:
            return text
        
        # Binary search for optimal truncation point
        left, right = 0, len(text)
        best_length = 0
        
        while left <= right:
            mid = (left + right) // 2
            truncated = text[:mid]
            
            if self.count_tokens(truncated) <= token_limit:
                best_length = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return text[:best_length] + "..."
    
    async def optimize_context_for_budget(self, context: Dict, budget: int) -> Dict:
        """
        Optimize entire context dictionary to fit within token budget.
        """
        optimized = {}
        total_tokens = 0
        
        # Sort by priority and allocate tokens
        for key, content in context.items():
            content_tokens = self.count_tokens(content)
            
            if total_tokens + content_tokens <= budget:
                optimized[key] = content
                total_tokens += content_tokens
            else:
                # Try to compress to fit remaining budget
                remaining_budget = budget - total_tokens
                if remaining_budget > 100:  # Minimum viable content
                    compressed = await self.compress_content(content, remaining_budget, key)
                    optimized[key] = compressed
                    total_tokens += self.count_tokens(compressed)
                break
        
        return optimized
