"""Core Context Models"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


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


class CompressionStrategy(Enum):
    """Different compression strategies for various content types."""
    PRESERVE_STRUCTURE = "preserve_structure"
    EXTRACT_KEY_POINTS = "extract_key_points"
    SUMMARIZE_SEMANTIC = "summarize_semantic"
    TRUNCATE_SMART = "truncate_smart"
    CONVERSATION_COMPRESS = "conversation_compress"


@dataclass
class ContextElement:
    """Context piece with metadata for prioritization."""
    content: str
    context_type: ContextType
    priority_score: float
    relevance_score: float
    token_count: int
    source_metadata: Dict[str, Any]
    compression_level: float = 0.0
    
    def __post_init__(self):
        """Validate ContextElement data."""
        if not self.content:
            raise ValueError("ContextElement content cannot be empty")
        if not isinstance(self.context_type, ContextType):
            raise TypeError("context_type must be a ContextType enum")
        if not 0.0 <= self.priority_score <= 10.0:
            raise ValueError("priority_score must be between 0.0 and 10.0")
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("relevance_score must be between 0.0 and 1.0")
        if self.token_count < 0:
            raise ValueError("token_count cannot be negative")
        if not 0.0 <= self.compression_level <= 1.0:
            raise ValueError("compression_level must be between 0.0 and 1.0")
    
    @property
    def effective_priority(self) -> float:
        """Calculate effective priority combining base priority and relevance."""
        return self.priority_score * (1.0 + self.relevance_score)
    
    @property
    def compression_ratio(self) -> float:
        """Calculate how much the content has been compressed."""
        return 1.0 if self.compression_level == 0.0 else 1.0 - self.compression_level
    
    def is_high_priority(self) -> bool:
        """Check if this context element is high priority."""
        return self.effective_priority >= 8.0
    
    def is_compressible(self) -> bool:
        """Check if this context element can be compressed further."""
        return self.compression_level < 0.8 and self.token_count > 500
