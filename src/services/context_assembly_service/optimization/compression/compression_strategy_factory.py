"""
Compression Strategy Factory

Factory for creating appropriate compression strategies based on content type.
Follows Warren strategy pattern for consistent interface and selection.
"""

import logging
from typing import Optional

from ...models import ContextType
from ..text_token_manager import TextTokenManager
from .compression_strategy import BaseCompressionStrategy
from .structure_preserving_compressor import StructurePreservingCompressor
from .conversation_compressor import ConversationCompressor
from .generic_compressor import GenericCompressor

logger = logging.getLogger(__name__)


class CompressionStrategyFactory:
    
    def __init__(self, token_manager: Optional[TextTokenManager] = None):
        self.token_manager = token_manager or TextTokenManager()
    
    def create_strategy(self, context_type: ContextType) -> BaseCompressionStrategy:
        strategy_map = {
            ContextType.CONVERSATION_HISTORY: ConversationCompressor,
            ContextType.COMPLIANCE_SOURCES: StructurePreservingCompressor,
            ContextType.VECTOR_SEARCH_RESULTS: StructurePreservingCompressor,
            ContextType.DOCUMENT_SUMMARIES: StructurePreservingCompressor,
            ContextType.YOUTUBE_CONTEXT: GenericCompressor,
            ContextType.CURRENT_CONTENT: GenericCompressor,
            ContextType.SYSTEM_PROMPT: GenericCompressor,
            ContextType.USER_INPUT: GenericCompressor
        }
        
        strategy_class = strategy_map.get(context_type, GenericCompressor)
        
        context_name = context_type.value if context_type else "None"
        logger.debug(f"Creating {strategy_class.__name__} for {context_name}")
        
        return strategy_class(self.token_manager)
    
    def get_best_strategy_for_content(self, content: str, context_type: ContextType) -> BaseCompressionStrategy:
        # Start with type-based strategy
        primary_strategy = self.create_strategy(context_type)
        
        # Analyze content characteristics for potential overrides
        content_analysis = self._analyze_content_characteristics(content)
        
        # Override strategy based on content analysis
        if content_analysis['has_conversation_markers'] and context_type != ContextType.CONVERSATION_HISTORY:
            logger.debug(f"Overriding to ConversationCompressor due to conversation markers")
            return ConversationCompressor(self.token_manager)
        
        if content_analysis['high_structure'] and context_type not in [
            ContextType.COMPLIANCE_SOURCES, 
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.DOCUMENT_SUMMARIES
        ]:
            logger.debug(f"Overriding to StructurePreservingCompressor due to high structure")
            return StructurePreservingCompressor(self.token_manager)
        
        return primary_strategy
    
    def _analyze_content_characteristics(self, content: str) -> dict:
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Check for conversation markers
        conversation_markers = ['user:', 'advisor:', 'warren:', 'assistant:', 'human:']
        has_conversation = any(
            any(marker in line.lower() for marker in conversation_markers)
            for line in non_empty_lines[:10]  # Check first 10 lines
        )
        
        # Check for structural elements
        structural_lines = 0
        for line in non_empty_lines:
            line = line.strip()
            if (line.startswith('#') or  # Markdown headers
                line.startswith(('*', '-', '•')) or  # Bullet points
                line.startswith(('**', '__')) or  # Bold headers
                (len(line) < 50 and line.isupper() and ':' in line)):  # Section headers
                structural_lines += 1
        
        structure_ratio = structural_lines / len(non_empty_lines) if non_empty_lines else 0
        
        return {
            'has_conversation_markers': has_conversation,
            'high_structure': structure_ratio > 0.2,
            'structure_ratio': structure_ratio,
            'line_count': len(non_empty_lines),
            'avg_line_length': sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0
        }
    
    def get_strategy_recommendations(self, content: str, context_type: ContextType) -> list:
        characteristics = self._analyze_content_characteristics(content)
        
        recommendations = []
        
        # Score each strategy based on content characteristics
        strategies = [
            (ConversationCompressor, self._score_conversation_strategy(characteristics)),
            (StructurePreservingCompressor, self._score_structure_strategy(characteristics)),
            (GenericCompressor, self._score_generic_strategy(characteristics))
        ]
        
        # Sort by score (highest first)
        strategies.sort(key=lambda x: x[1], reverse=True)
        
        return strategies
    
    def _score_conversation_strategy(self, characteristics: dict) -> float:
        score = 0.0
        
        if characteristics['has_conversation_markers']:
            score += 10.0
        
        # Conversation content tends to have shorter lines
        if characteristics['avg_line_length'] < 100:
            score += 2.0
        
        return score
    
    def _score_structure_strategy(self, characteristics: dict) -> float:
        score = 5.0  # Base score since it's generally good
        
        score += characteristics['structure_ratio'] * 10.0
        
        if characteristics['line_count'] > 20:
            score += 2.0  # Works better with more content
        
        return score
    
    def _score_generic_strategy(self, characteristics: dict) -> float:
        score = 3.0  # Base fallback score
        
        # Generic works well for unstructured content
        if characteristics['structure_ratio'] < 0.1:
            score += 3.0
        
        return score
