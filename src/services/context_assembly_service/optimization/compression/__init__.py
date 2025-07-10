"""
Compression Package

Compression strategies for context optimization.
Extracted from ContextAssembler for improved separation of concerns.
"""

from .compression_strategy import BaseCompressionStrategy
from .structure_preserving_compressor import StructurePreservingCompressor
from .conversation_compressor import ConversationCompressor
from .generic_compressor import GenericCompressor
from .compression_strategy_factory import CompressionStrategyFactory

__all__ = [
    'BaseCompressionStrategy',
    'StructurePreservingCompressor',
    'ConversationCompressor',
    'GenericCompressor',
    'CompressionStrategyFactory'
]
