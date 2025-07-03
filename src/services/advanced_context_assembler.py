"""
Advanced Context Assembly Enhancement for Phase 2

Implements sophisticated context prioritization, relevance scoring, and 
advanced compression algorithms for Warren's intelligent token management system.

Extends the existing ContextAssembler with Phase 2 capabilities:
- Enhanced context prioritization with relevance scoring
- Multi-source context optimization for complex scenarios
- Advanced compression algorithms for different content types
- Context quality metrics and performance monitoring

Based on SCRUM-34 Phase 2 requirements.
"""

import asyncio
import json
import logging
import tiktoken
import re
import math
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from src.services.context_assembler import ContextAssembler, TokenManager, ContextType, RequestType

logger = logging.getLogger(__name__)

@dataclass
class ContextElement:
    """Represents a single piece of context with metadata for prioritization."""
    content: str
    context_type: ContextType
    priority_score: float
    relevance_score: float
    token_count: int
    source_metadata: Dict[str, Any]
    compression_level: float = 0.0  # 0 = no compression, 1 = maximum compression
    
class CompressionStrategy(Enum):
    """Different compression strategies for various content types."""
    PRESERVE_STRUCTURE = "preserve_structure"  # Keep headings, bullet points
    EXTRACT_KEY_POINTS = "extract_key_points"  # Focus on main ideas
    SUMMARIZE_SEMANTIC = "summarize_semantic"  # Semantic summarization
    TRUNCATE_SMART = "truncate_smart"  # Intelligent truncation
    CONVERSATION_COMPRESS = "conversation_compress"  # Dialog-specific compression

class RelevanceAnalyzer:
    """Analyzes content relevance for intelligent context prioritization."""
    
    def __init__(self):
        self.financial_keywords = {
            'high': {'investment', 'portfolio', 'diversification', 'retirement', 'financial', 
                    'advisory', 'client', 'market', 'risk', 'return', 'assets', 'allocation'},
            'medium': {'money', 'savings', 'planning', 'strategy', 'growth', 'income', 
                      'wealth', 'advisor', 'fund', 'stocks', 'bonds', 'insurance'},
            'low': {'business', 'economy', 'tax', 'legal', 'regulatory', 'compliance', 
                   'communication', 'marketing', 'content', 'social', 'media'}
        }
        
        self.content_type_keywords = {
            'linkedin_post': {'linkedin', 'social', 'professional', 'network', 'post', 'share'},
            'email_template': {'email', 'message', 'communication', 'send', 'newsletter'},
            'website_content': {'website', 'web', 'page', 'site', 'online', 'digital'},
            'blog_post': {'blog', 'article', 'post', 'content', 'writing', 'publish'},
            'newsletter': {'newsletter', 'update', 'news', 'periodic', 'subscription'}
        }
    
    def calculate_relevance_score(
        self, 
        content: str, 
        user_request: str, 
        content_type: str,
        context_metadata: Dict[str, Any] = None
    ) -> float:
        """
        Calculate relevance score (0.0 to 1.0) based on multiple factors.
        
        Higher scores indicate more relevant content for the current request.
        """
        scores = []
        
        # 1. Keyword overlap analysis
        keyword_score = self._calculate_keyword_overlap(content, user_request)
        scores.append(('keyword_overlap', keyword_score, 0.3))
        
        # 2. Financial domain relevance
        financial_score = self._calculate_financial_relevance(content, user_request)
        scores.append(('financial_relevance', financial_score, 0.25))
        
        # 3. Content type alignment
        content_type_score = self._calculate_content_type_relevance(content, content_type)
        scores.append(('content_type_alignment', content_type_score, 0.2))
        
        # 4. Semantic similarity (simplified)
        semantic_score = self._calculate_semantic_similarity(content, user_request)
        scores.append(('semantic_similarity', semantic_score, 0.15))
        
        # 5. Content quality indicators
        quality_score = self._calculate_content_quality(content, context_metadata)
        scores.append(('content_quality', quality_score, 0.1))
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        logger.debug(f"Relevance scores: {[(name, f'{score:.3f}') for name, score, _ in scores]} -> {total_score:.3f}")
        
        return min(1.0, max(0.0, total_score))
    
    def _calculate_keyword_overlap(self, content: str, user_request: str) -> float:
        """Calculate keyword overlap between content and user request."""
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        request_words = set(re.findall(r'\b\w+\b', user_request.lower()))
        
        if not request_words:
            return 0.0
        
        overlap = len(content_words.intersection(request_words))
        return min(1.0, overlap / len(request_words))
    
    def _calculate_financial_relevance(self, content: str, user_request: str) -> float:
        """Calculate relevance to financial advisory domain."""
        content_lower = content.lower()
        request_lower = user_request.lower()
        
        total_score = 0.0
        total_possible = 0.0
        
        for level, keywords in self.financial_keywords.items():
            weight = {'high': 1.0, 'medium': 0.6, 'low': 0.3}[level]
            
            content_matches = sum(1 for keyword in keywords if keyword in content_lower)
            request_matches = sum(1 for keyword in keywords if keyword in request_lower)
            
            # Boost score if keywords appear in both content and request
            if content_matches > 0 and request_matches > 0:
                total_score += weight * min(1.0, (content_matches + request_matches) / len(keywords))
            elif content_matches > 0:
                total_score += weight * 0.5 * min(1.0, content_matches / len(keywords))
            
            total_possible += weight
        
        return total_score / total_possible if total_possible > 0 else 0.0
    
    def _calculate_content_type_relevance(self, content: str, content_type: str) -> float:
        """Calculate how well content matches the target content type."""
        content_lower = content.lower()
        
        if content_type not in self.content_type_keywords:
            return 0.5  # Neutral score for unknown content types
        
        keywords = self.content_type_keywords[content_type]
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        
        return min(1.0, matches / len(keywords))
    
    def _calculate_semantic_similarity(self, content: str, user_request: str) -> float:
        """Calculate semantic similarity (simplified implementation)."""
        # Simple implementation based on sentence structure and length similarity
        content_sentences = len(re.split(r'[.!?]+', content))
        request_sentences = len(re.split(r'[.!?]+', user_request))
        
        content_length = len(content.split())
        request_length = len(user_request.split())
        
        # Similarity based on structure and length ratios
        if content_length == 0 or request_length == 0:
            return 0.0
        
        length_ratio = min(content_length, request_length) / max(content_length, request_length)
        sentence_ratio = min(content_sentences, request_sentences) / max(content_sentences, request_sentences)
        
        return (length_ratio + sentence_ratio) / 2
    
    def _calculate_content_quality(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate content quality indicators."""
        quality_score = 0.5  # Base score
        
        # Length quality (not too short, not too long)
        word_count = len(content.split())
        if 50 <= word_count <= 500:
            quality_score += 0.2
        elif 20 <= word_count <= 1000:
            quality_score += 0.1
        
        # Structure quality (has paragraphs, sentences)
        if '\n' in content:
            quality_score += 0.1
        if re.search(r'[.!?]', content):
            quality_score += 0.1
        
        # Metadata quality
        if metadata:
            if metadata.get('compliance_score', 0) > 0.8:
                quality_score += 0.1
            if metadata.get('usage_count', 0) > 0:
                quality_score += 0.05
        
        return min(1.0, quality_score)

class AdvancedContextAssembler(ContextAssembler):
    """
    Enhanced Context Assembler with Phase 2 capabilities:
    - Advanced context prioritization with relevance scoring
    - Multi-source context optimization
    - Context quality metrics and monitoring
    """
    
    def __init__(self, db_session):
        super().__init__(db_session)
        self.relevance_analyzer = RelevanceAnalyzer()
        self.advanced_token_manager = AdvancedTokenManager()
        
        # Phase 2 enhancements
        self.context_quality_threshold = 0.7
        self.min_high_priority_sources = 3
        self.relevance_score_weight = 0.4
        self.priority_score_weight = 0.6
        
    async def build_warren_context(
        self, 
        session_id: str, 
        user_input: str,
        context_data: Optional[Dict] = None,
        current_content: Optional[str] = None,
        youtube_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Enhanced context building with Phase 2 advanced features.
        """
        try:
            # Phase 1: Basic token allocation and request type detection
            request_type = self._determine_request_type(user_input, current_content)
            token_budget = await self.allocate_token_budget(request_type, user_input)
            
            logger.info(f"Phase 2: Advanced context assembly for {request_type.value}")
            
            # Phase 2: Gather context elements with enhanced metadata
            context_elements = await self._gather_enhanced_context_elements(
                session_id, user_input, context_data, current_content, youtube_context, request_type
            )
            
            # Phase 2: Advanced prioritization with relevance scoring
            prioritized_elements = await self._prioritize_context_with_relevance(
                context_elements, user_input, request_type, token_budget
            )
            
            # Phase 2: Multi-source optimization
            optimized_context = await self._optimize_multi_source_context(
                prioritized_elements, token_budget, request_type
            )
            
            # Phase 2: Context quality assessment
            quality_metrics = self._assess_context_quality_advanced(optimized_context, user_input)
            
            # Build final context with enhanced assembly
            final_context = self._build_enhanced_context_string(optimized_context)
            total_tokens = self.token_manager.count_tokens(final_context)
            
            logger.info(f"Phase 2 Context Assembly Complete:")
            logger.info(f"   Request Type: {request_type.value}")
            logger.info(f"   Total Tokens: {total_tokens}")
            logger.info(f"   Quality Score: {quality_metrics['overall_quality']:.3f}")
            logger.info(f"   High Priority Sources: {quality_metrics['high_priority_count']}")
            logger.info(f"   Average Relevance: {quality_metrics['avg_relevance']:.3f}")
            
            return {
                "context": final_context,
                "request_type": request_type.value,
                "total_tokens": total_tokens,
                "token_budget": token_budget,
                "context_breakdown": {elem.context_type.value: elem.token_count for elem in optimized_context},
                "optimization_applied": total_tokens > self.TARGET_INPUT_TOKENS,
                "quality_metrics": quality_metrics,
                "relevance_scores": {elem.context_type.value: elem.relevance_score for elem in optimized_context},
                "priority_scores": {elem.context_type.value: elem.priority_score for elem in optimized_context},
                "phase": "Phase_2_Advanced"
            }
            
        except Exception as e:
            logger.error(f"Error in Phase 2 context assembly: {e}")
            # Fallback to Phase 1 implementation
            return await super().build_warren_context(
                session_id, user_input, context_data, current_content, youtube_context
            )
    
    async def _gather_enhanced_context_elements(
        self,
        session_id: str,
        user_input: str,
        context_data: Optional[Dict],
        current_content: Optional[str],
        youtube_context: Optional[Dict],
        request_type: RequestType
    ) -> List[ContextElement]:
        """
        Gather context elements with enhanced metadata and relevance scoring.
        """
        elements = []
        
        # User input (always highest priority)
        elements.append(ContextElement(
            content=user_input,
            context_type=ContextType.USER_INPUT,
            priority_score=1.0,
            relevance_score=1.0,
            token_count=self.token_manager.count_tokens(user_input),
            source_metadata={"type": "user_request", "timestamp": datetime.utcnow().isoformat()}
        ))
        
        # Current content for refinement
        if current_content:
            relevance_score = self.relevance_analyzer.calculate_relevance_score(
                current_content, user_input, "refinement_content"
            )
            elements.append(ContextElement(
                content=current_content,
                context_type=ContextType.CURRENT_CONTENT,
                priority_score=0.9,
                relevance_score=relevance_score,
                token_count=self.token_manager.count_tokens(current_content),
                source_metadata={"type": "current_content", "refinement_mode": True}
            ))
        
        # Conversation history with relevance analysis
        conversation_context = await self._get_enhanced_conversation_context(session_id, user_input)
        if conversation_context:
            elements.append(conversation_context)
        
        # Enhanced compliance sources
        if context_data:
            compliance_elements = self._extract_enhanced_compliance_sources(context_data, user_input)
            elements.extend(compliance_elements)
            
            # Enhanced vector search results
            vector_elements = self._extract_enhanced_vector_results(context_data, user_input)
            elements.extend(vector_elements)
        
        # Enhanced YouTube context
        if youtube_context:
            youtube_element = self._extract_enhanced_youtube_context(youtube_context, user_input)
            elements.append(youtube_element)
        
        logger.info(f"Gathered {len(elements)} enhanced context elements")
        return elements
    
    async def _get_enhanced_conversation_context(self, session_id: str, user_input: str) -> Optional[ContextElement]:
        """Get conversation context with relevance analysis."""
        try:
            conversation_text = await self.conversation_manager.get_conversation_context(session_id)
            if not conversation_text:
                return None
            
            relevance_score = self.relevance_analyzer.calculate_relevance_score(
                conversation_text, user_input, "conversation"
            )
            
            return ContextElement(
                content=conversation_text,
                context_type=ContextType.CONVERSATION_HISTORY,
                priority_score=0.7,
                relevance_score=relevance_score,
                token_count=self.token_manager.count_tokens(conversation_text),
                source_metadata={
                    "type": "conversation_history",
                    "session_id": session_id,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Could not enhance conversation context: {e}")
            return None
    
    def _extract_enhanced_compliance_sources(self, context_data: Dict, user_input: str) -> List[ContextElement]:
        """Extract compliance sources with relevance scoring."""
        elements = []
        
        # Process rules
        rules = context_data.get("rules", [])
        for i, rule in enumerate(rules[:5]):  # Limit to top 5 rules
            content = f"**{rule.get('regulation_name', 'Rule')}**: {rule.get('requirement_text', '')}"
            
            relevance_score = self.relevance_analyzer.calculate_relevance_score(
                content, user_input, "compliance_rule", rule
            )
            
            # Higher priority for highly relevant compliance rules
            priority_score = 0.8 + (0.2 * relevance_score)
            
            elements.append(ContextElement(
                content=content,
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=priority_score,
                relevance_score=relevance_score,
                token_count=self.token_manager.count_tokens(content),
                source_metadata={
                    "type": "compliance_rule",
                    "rule_id": rule.get('id'),
                    "regulation": rule.get('regulation_name'),
                    "index": i
                }
            ))
        
        # Process disclaimers
        disclaimers = context_data.get("disclaimers", [])
        for i, disclaimer in enumerate(disclaimers[:3]):  # Limit to top 3 disclaimers
            content = f"**{disclaimer.get('title', 'Disclaimer')}**: {disclaimer.get('content_text', '')}"
            
            relevance_score = self.relevance_analyzer.calculate_relevance_score(
                content, user_input, "disclaimer", disclaimer
            )
            
            priority_score = 0.75 + (0.15 * relevance_score)
            
            elements.append(ContextElement(
                content=content,
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=priority_score,
                relevance_score=relevance_score,
                token_count=self.token_manager.count_tokens(content),
                source_metadata={
                    "type": "disclaimer",
                    "disclaimer_id": disclaimer.get('id'),
                    "title": disclaimer.get('title'),
                    "index": i
                }
            ))
        
        return elements
    
    def _extract_enhanced_vector_results(self, context_data: Dict, user_input: str) -> List[ContextElement]:
        """Extract vector search results with enhanced relevance analysis."""
        elements = []
        
        examples = context_data.get("examples", [])
        for i, example in enumerate(examples[:4]):  # Limit to top 4 examples
            content = f"**{example.get('title', 'Example')}**\n{example.get('content_text', '')}"
            if example.get('tags'):
                content += f"\nTags: {example['tags']}"
            
            # Use existing similarity score if available, otherwise calculate relevance
            similarity_score = example.get('similarity_score', 0.0)
            relevance_score = self.relevance_analyzer.calculate_relevance_score(
                content, user_input, "marketing_example", example
            )
            
            # Combine similarity and relevance scores
            combined_relevance = (similarity_score + relevance_score) / 2
            priority_score = 0.6 + (0.3 * combined_relevance)
            
            elements.append(ContextElement(
                content=content,
                context_type=ContextType.VECTOR_SEARCH_RESULTS,
                priority_score=priority_score,
                relevance_score=combined_relevance,
                token_count=self.token_manager.count_tokens(content),
                source_metadata={
                    "type": "marketing_example",
                    "example_id": example.get('id'),
                    "similarity_score": similarity_score,
                    "usage_count": example.get('usage_count', 0),
                    "index": i
                }
            ))
        
        return elements
    
    def _extract_enhanced_youtube_context(self, youtube_context: Dict, user_input: str) -> ContextElement:
        """Extract YouTube context with relevance analysis."""
        content_parts = ["## VIDEO CONTEXT:"]
        
        video_info = youtube_context.get("metadata", {})
        if video_info.get("url"):
            content_parts.append(f"Video URL: {video_info['url']}")
        
        transcript = youtube_context.get("transcript", "")
        if transcript:
            content_parts.append("**VIDEO TRANSCRIPT:**")
            content_parts.append(transcript)
        
        content = "\n".join(content_parts)
        
        relevance_score = self.relevance_analyzer.calculate_relevance_score(
            content, user_input, "youtube_video", video_info
        )
        
        priority_score = 0.5 + (0.4 * relevance_score)  # YouTube context can be very relevant or not
        
        return ContextElement(
            content=content,
            context_type=ContextType.YOUTUBE_CONTEXT,
            priority_score=priority_score,
            relevance_score=relevance_score,
            token_count=self.token_manager.count_tokens(content),
            source_metadata={
                "type": "youtube_video",
                "video_url": video_info.get("url"),
                "video_title": video_info.get("title"),
                "transcript_length": len(transcript)
            }
        )
    
    async def _prioritize_context_with_relevance(
        self,
        context_elements: List[ContextElement],
        user_input: str,
        request_type: RequestType,
        token_budget: Dict[ContextType, int]
    ) -> List[ContextElement]:
        """
        Advanced prioritization combining priority scores and relevance scores.
        """
        # Calculate combined scores for each element
        for element in context_elements:
            # Combine priority and relevance with configurable weights
            element.combined_score = (
                element.priority_score * self.priority_score_weight + 
                element.relevance_score * self.relevance_score_weight
            )
        
        # Group by context type for balanced selection
        grouped_elements = defaultdict(list)
        for element in context_elements:
            grouped_elements[element.context_type].append(element)
        
        # Sort each group by combined score
        for context_type in grouped_elements:
            grouped_elements[context_type].sort(key=lambda x: x.combined_score, reverse=True)
        
        # Select top elements from each group based on budget
        prioritized_elements = []
        
        for context_type, elements in grouped_elements.items():
            budget = token_budget.get(context_type, 0)
            if budget <= 0:
                continue
            
            selected_elements = []
            current_tokens = 0
            
            for element in elements:
                if current_tokens + element.token_count <= budget:
                    selected_elements.append(element)
                    current_tokens += element.token_count
                elif len(selected_elements) == 0:
                    # Always include at least one element, compress if needed
                    element.compression_level = 1 - (budget / element.token_count)
                    selected_elements.append(element)
                    break
            
            prioritized_elements.extend(selected_elements)
        
        # Final sort by combined score
        prioritized_elements.sort(key=lambda x: x.combined_score, reverse=True)
        
        logger.info(f"Prioritized {len(prioritized_elements)} context elements with relevance scoring")
        return prioritized_elements
    
    async def _optimize_multi_source_context(
        self,
        prioritized_elements: List[ContextElement],
        token_budget: Dict[ContextType, int],
        request_type: RequestType
    ) -> List[ContextElement]:
        """
        Multi-source optimization with advanced compression strategies.
        """
        optimized_elements = []
        total_tokens_used = 0
        
        for element in prioritized_elements:
            # Apply compression if needed
            if element.compression_level > 0:
                compressed_content = await self.advanced_token_manager.compress_content_advanced(
                    element.content,
                    int(element.token_count * (1 - element.compression_level)),
                    element.context_type,
                    CompressionStrategy.EXTRACT_KEY_POINTS
                )
                element.content = compressed_content
                element.token_count = self.token_manager.count_tokens(compressed_content)
            
            optimized_elements.append(element)
            total_tokens_used += element.token_count
            
            # Check if we're approaching token limits
            if total_tokens_used > self.TARGET_INPUT_TOKENS * 0.9:
                logger.warning(f"Approaching token limit with {total_tokens_used} tokens used")
                break
        
        logger.info(f"Multi-source optimization complete: {len(optimized_elements)} elements, {total_tokens_used} tokens")
        return optimized_elements
    
    def _assess_context_quality_advanced(self, context_elements: List[ContextElement], user_input: str) -> Dict[str, Any]:
        """
        Advanced context quality assessment with detailed metrics.
        """
        if not context_elements:
            return {"overall_quality": 0.0, "metrics": {}}
        
        # Calculate various quality metrics
        total_relevance = sum(elem.relevance_score for elem in context_elements)
        avg_relevance = total_relevance / len(context_elements)
        
        high_priority_count = sum(1 for elem in context_elements if elem.priority_score > 0.8)
        high_relevance_count = sum(1 for elem in context_elements if elem.relevance_score > 0.7)
        
        # Context type diversity
        context_types = set(elem.context_type for elem in context_elements)
        diversity_score = len(context_types) / len(ContextType)
        
        # Token efficiency
        total_tokens = sum(elem.token_count for elem in context_elements)
        avg_tokens_per_element = total_tokens / len(context_elements)
        token_efficiency = min(1.0, 1000 / avg_tokens_per_element) if avg_tokens_per_element > 0 else 0.0
        
        # Overall quality score
        overall_quality = (
            avg_relevance * 0.4 +
            (high_priority_count / len(context_elements)) * 0.3 +
            diversity_score * 0.2 +
            token_efficiency * 0.1
        )
        
        return {
            "overall_quality": overall_quality,
            "avg_relevance": avg_relevance,
            "high_priority_count": high_priority_count,
            "high_relevance_count": high_relevance_count,
            "context_diversity": diversity_score,
            "token_efficiency": token_efficiency,
            "total_elements": len(context_elements),
            "total_tokens": total_tokens,
            "quality_threshold_met": overall_quality >= self.context_quality_threshold
        }
    
    def _build_enhanced_context_string(self, context_elements: List[ContextElement]) -> str:
        """
        Build final context string with enhanced formatting and structure.
        """
        context_parts = []
        
        # Group elements by type for organized presentation
        grouped = defaultdict(list)
        for element in context_elements:
            grouped[element.context_type].append(element)
        
        # Add elements in logical order with enhanced formatting
        for context_type in [
            ContextType.COMPLIANCE_SOURCES,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.CONVERSATION_HISTORY,
            ContextType.CURRENT_CONTENT,
            ContextType.YOUTUBE_CONTEXT,
            ContextType.USER_INPUT
        ]:
            if context_type in grouped:
                # Add section header
                section_name = context_type.value.replace('_', ' ').title()
                context_parts.append(f"\n## {section_name}")
                
                # Add elements with relevance indicators
                for element in grouped[context_type]:
                    relevance_indicator = "⭐" if element.relevance_score > 0.8 else "▶"
                    context_parts.append(f"\n{relevance_indicator} {element.content}")
        
        return "\n".join(context_parts)


class AdvancedTokenManager(TokenManager):
    """
    Enhanced Token Manager with advanced compression strategies for Phase 2.
    """
    
    async def compress_content_advanced(
        self,
        content: str,
        target_tokens: int,
        context_type: ContextType,
        strategy: CompressionStrategy = CompressionStrategy.EXTRACT_KEY_POINTS
    ) -> str:
        """
        Advanced content compression using different strategies.
        """
        if not content:
            return content
            
        current_tokens = self.count_tokens(content)
        if current_tokens <= target_tokens:
            return content
        
        logger.debug(f"Applying {strategy.value} compression: {current_tokens} -> {target_tokens} tokens")
        
        if strategy == CompressionStrategy.PRESERVE_STRUCTURE:
            return self._compress_preserve_structure(content, target_tokens)
        elif strategy == CompressionStrategy.EXTRACT_KEY_POINTS:
            return self._compress_extract_key_points(content, target_tokens)
        elif strategy == CompressionStrategy.SUMMARIZE_SEMANTIC:
            return self._compress_summarize_semantic(content, target_tokens)
        elif strategy == CompressionStrategy.CONVERSATION_COMPRESS:
            return self._compress_conversation(content, target_tokens)
        else:
            return self._compress_generic(content, target_tokens)
    
    def _compress_preserve_structure(self, content: str, target_tokens: int) -> str:
        """Compress while preserving headings, bullet points, and structure."""
        lines = content.split('\n')
        important_lines = []
        regular_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify important structural elements
            if (line.startswith('#') or line.startswith('**') or 
                line.startswith('- ') or line.startswith('* ') or
                line.endswith(':') or len(line) < 50):
                important_lines.append(line)
            else:
                regular_lines.append(line)
        
        # Always include important lines
        result_lines = important_lines[:]
        current_tokens = self.count_tokens('\n'.join(result_lines))
        
        # Add regular lines until we hit the token limit
        for line in regular_lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens <= target_tokens:
                result_lines.append(line)
                current_tokens += line_tokens
            else:
                # Truncate the line if it's the only one that fits
                if len(result_lines) == len(important_lines):
                    remaining_tokens = target_tokens - current_tokens
                    truncated = self._truncate_to_token_limit(line, remaining_tokens)
                    if truncated:
                        result_lines.append(truncated)
                break
        
        return '\n'.join(result_lines)
    
    def _compress_extract_key_points(self, content: str, target_tokens: int) -> str:
        """Extract key points and important sentences."""
        sentences = re.split(r'[.!?]+', content)
        sentence_scores = []
        
        # Score sentences based on importance indicators
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            score = 0.0
            
            # Length-based scoring (prefer medium-length sentences)
            word_count = len(sentence.split())
            if 8 <= word_count <= 25:
                score += 1.0
            elif 5 <= word_count <= 35:
                score += 0.5
            
            # Keyword-based scoring
            important_words = ['important', 'key', 'critical', 'must', 'should', 
                             'compliance', 'required', 'regulation', 'risk', 'investment']
            score += sum(0.2 for word in important_words if word.lower() in sentence.lower())
            
            # Position-based scoring (first and last sentences often important)
            if sentence == sentences[0] or sentence == sentences[-1]:
                score += 0.5
            
            sentence_scores.append((sentence, score, self.count_tokens(sentence)))
        
        # Sort by score and select top sentences that fit within token limit
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected_sentences = []
        current_tokens = 0
        
        for sentence, score, tokens in sentence_scores:
            if current_tokens + tokens <= target_tokens:
                selected_sentences.append(sentence)
                current_tokens += tokens
            elif not selected_sentences:
                # If no sentences fit, truncate the highest-scored one
                truncated = self._truncate_to_token_limit(sentence, target_tokens)
                selected_sentences.append(truncated)
                break
        
        return '. '.join(selected_sentences) + '.' if selected_sentences else content[:100]
    
    def _compress_summarize_semantic(self, content: str, target_tokens: int) -> str:
        """Create semantic summary focusing on main concepts."""
        # Simple semantic summarization
        paragraphs = content.split('\n\n')
        paragraph_scores = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # Score based on information density
            sentences = len(re.split(r'[.!?]+', paragraph))
            words = len(paragraph.split())
            
            if words == 0:
                continue
            
            # Information density score
            density_score = sentences / words if words > 0 else 0
            
            # Content richness score
            unique_words = len(set(word.lower() for word in paragraph.split()))
            richness_score = unique_words / words if words > 0 else 0
            
            combined_score = density_score + richness_score
            token_count = self.count_tokens(paragraph)
            
            paragraph_scores.append((paragraph, combined_score, token_count))
        
        # Select paragraphs with highest information content
        paragraph_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected_paragraphs = []
        current_tokens = 0
        
        for paragraph, score, tokens in paragraph_scores:
            if current_tokens + tokens <= target_tokens:
                selected_paragraphs.append(paragraph)
                current_tokens += tokens
            elif not selected_paragraphs:
                # Truncate the most information-dense paragraph
                truncated = self._truncate_to_token_limit(paragraph, target_tokens)
                selected_paragraphs.append(truncated)
                break
        
        return '\n\n'.join(selected_paragraphs)
