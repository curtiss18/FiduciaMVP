"""
Compression Strategy Implementation

"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ...interfaces import CompressionStrategy as ICompressionStrategy
from ...models import ContextType
from ..text_token_manager import TextTokenManager

logger = logging.getLogger(__name__)


class BaseCompressionStrategy(ICompressionStrategy):
    def __init__(self, token_manager: Optional[TextTokenManager] = None):
        self.token_manager = token_manager or TextTokenManager()
    
    async def compress_content(self, content: str, target_tokens: int, context_type: ContextType) -> str:
        if not content:
            return content
        
        current_tokens = self.token_manager.count_tokens(content)
        if current_tokens <= target_tokens:
            return content
        
        logger.debug(f"Compressing {context_type.value}: {current_tokens} → {target_tokens} tokens")
        
        # Use specific compression algorithm
        compressed = await self._compress_implementation(content, target_tokens, context_type)
        
        # Verify compression was successful
        final_tokens = self.token_manager.count_tokens(compressed)
        if final_tokens > target_tokens:
            logger.warning(f"Compression exceeded target: {final_tokens} > {target_tokens}")
        
        return compressed
    
    @abstractmethod
    async def _compress_implementation(self, content: str, target_tokens: int, context_type: ContextType) -> str:
        pass
    
    def estimate_compression_ratio(self, content: str, context_type: ContextType) -> float:
        # Base implementation - can be overridden by specific strategies
        if len(content) < 500:
            return 0.1  # Very little compression possible
        elif len(content) < 2000:
            return 0.3  # Moderate compression
        else:
            return 0.5  # Good compression potential
    
    def _truncate_to_token_limit(self, text: str, token_limit: int) -> str:
        if self.token_manager.count_tokens(text) <= token_limit:
            return text
        
        # Binary search for optimal truncation point
        left, right = 0, len(text)
        best_length = 0
        
        while left <= right:
            mid = (left + right) // 2
            truncated = text[:mid]
            
            if self.token_manager.count_tokens(truncated) <= token_limit:
                best_length = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return text[:best_length].rstrip() + "..."
