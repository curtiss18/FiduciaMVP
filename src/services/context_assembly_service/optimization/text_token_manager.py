"""Text token counting and caching for AI text processing."""

import hashlib
import logging
import tiktoken
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TextTokenManager:
    """Precise token counting with hash-based caching for performance."""
    
    def __init__(self, cache_size_limit: int = 1000):
        # Use Claude's tokenizer (approximating with GPT-4 tokenizer)
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
            logger.info("TextTokenManager initialized with tiktoken GPT-4 encoding")
        except Exception as e:
            # Fallback to rough estimation
            self.tokenizer = None
            logger.warning(f"Could not load tiktoken, using approximation: {e}")
        
        # Hash-based cache for performance optimization
        self._token_cache: Dict[str, int] = {}
        self._cache_size_limit = cache_size_limit
        
        # Performance metrics
        self._cache_hits = 0
        self._cache_misses = 0
    
    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        
        # Generate content hash for caching
        content_hash = self._generate_content_hash(text)
        
        # Check cache first
        if content_hash in self._token_cache:
            self._cache_hits += 1
            return self._token_cache[content_hash]
        
        # Cache miss - calculate tokens
        self._cache_misses += 1
        token_count = self._calculate_tokens(text)
        
        # Store in cache with size management
        self._store_in_cache(content_hash, token_count)
        
        return token_count
    
    def _generate_content_hash(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _calculate_tokens(self, text: str) -> int:
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Tiktoken encoding failed, using fallback: {e}")
        
        # Fallback: rough approximation (1 token ≈ 4 characters)
        return len(text) // 4
    
    def _store_in_cache(self, content_hash: str, token_count: int) -> None:
        # Remove oldest entries if cache is full
        if len(self._token_cache) >= self._cache_size_limit:
            # Simple FIFO eviction - remove first entry
            oldest_key = next(iter(self._token_cache))
            del self._token_cache[oldest_key]
        
        self._token_cache[content_hash] = token_count
    
    def get_cache_stats(self) -> Dict[str, any]:
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._token_cache),
            "cache_limit": self._cache_size_limit
        }
    
    def clear_cache(self) -> None:
        self._token_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("TextTokenManager cache cleared")
    
    def estimate_tokens_from_chars(self, char_count: int) -> int:
        return char_count // 4
    
    def estimate_chars_from_tokens(self, token_count: int) -> int:
        return token_count * 4
