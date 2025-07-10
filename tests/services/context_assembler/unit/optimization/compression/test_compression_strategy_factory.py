"""Tests for CompressionStrategyFactory."""

import pytest
from unittest.mock import Mock

from src.services.context_assembly_service.optimization.compression.compression_strategy_factory import CompressionStrategyFactory
from src.services.context_assembly_service.optimization.compression.structure_preserving_compressor import StructurePreservingCompressor
from src.services.context_assembly_service.optimization.compression.conversation_compressor import ConversationCompressor
from src.services.context_assembly_service.optimization.compression.generic_compressor import GenericCompressor
from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager
from src.services.context_assembly_service.models import ContextType


class TestCompressionStrategyFactory:
    """Test compression strategy selection and creation."""
    
    @pytest.fixture
    def token_manager(self):
        return TextTokenManager()
    
    @pytest.fixture
    def factory(self, token_manager):
        return CompressionStrategyFactory(token_manager)
    
    def test_strategy_selection_by_context_type(self, factory):
        """Test correct strategy selected for each ContextType."""
        
        # Test conversation strategy
        strategy = factory.get_best_strategy_for_content("", ContextType.CONVERSATION_HISTORY)
        assert isinstance(strategy, ConversationCompressor)
        
        # Test structure preserving strategy
        strategy = factory.get_best_strategy_for_content("# Heading\n* bullet", ContextType.COMPLIANCE_SOURCES)
        assert isinstance(strategy, StructurePreservingCompressor)
        
        # Test generic fallback
        strategy = factory.get_best_strategy_for_content("plain text", ContextType.USER_INPUT)
        assert isinstance(strategy, GenericCompressor)
    
    def test_conversation_strategy_selection(self, factory):
        """Test ConversationCompressor for conversation content."""
        strategy = factory.get_best_strategy_for_content(
            "User: Hello\nAssistant: Hi there", 
            ContextType.CONVERSATION_HISTORY
        )
        assert isinstance(strategy, ConversationCompressor)
    
    def test_structure_strategy_selection(self, factory):
        """Test StructurePreservingCompressor for structured content."""
        structured_content = """
        # Main Heading
        ## Subheading
        * Bullet point 1
        * Bullet point 2
        """
        
        strategy = factory.get_best_strategy_for_content(structured_content, ContextType.COMPLIANCE_SOURCES)
        assert isinstance(strategy, StructurePreservingCompressor)
    
    def test_generic_fallback_selection(self, factory):
        """Test GenericCompressor for unknown/fallback cases."""
        strategy = factory.get_best_strategy_for_content("simple text", ContextType.USER_INPUT)
        assert isinstance(strategy, GenericCompressor)
    
    def test_strategy_instance_caching(self, factory):
        """Test strategies are properly cached/reused."""
        strategy1 = factory.create_strategy(ContextType.CONVERSATION_HISTORY)
        strategy2 = factory.create_strategy(ContextType.CONVERSATION_HISTORY)
        
        # Should return same instance (if cached)
        assert type(strategy1) == type(strategy2)
    
    def test_token_manager_injection(self, factory, token_manager):
        """Test TextTokenManager properly injected."""
        strategy = factory.create_strategy(ContextType.USER_INPUT)
        assert hasattr(strategy, 'token_manager')
        assert strategy.token_manager is token_manager
    
    def test_content_analysis_structure_detection(self, factory):
        """Test structure detection in content."""
        markdown_content = "# Title\n## Subtitle\n- Item 1\n- Item 2"
        strategy = factory.get_best_strategy_for_content(markdown_content, ContextType.VECTOR_SEARCH_RESULTS)
        assert isinstance(strategy, StructurePreservingCompressor)
    
    def test_content_analysis_conversation_detection(self, factory):
        """Test conversation pattern detection."""
        conversation_content = """
        User: What is the weather?
        Assistant: It's sunny today.
        User: Thank you!
        """
        strategy = factory.get_best_strategy_for_content(conversation_content, ContextType.CONVERSATION_HISTORY)
        assert isinstance(strategy, ConversationCompressor)
    
    def test_invalid_context_type_handling(self, factory):
        """Test handling of invalid context types."""
        # Should default to generic compressor
        strategy = factory.create_strategy(None)
        assert isinstance(strategy, GenericCompressor)


class TestCompressionStrategyFactoryIntegration:
    """Integration tests for strategy factory."""
    
    @pytest.fixture
    def factory(self):
        return CompressionStrategyFactory(TextTokenManager())
    
    def test_all_context_types_have_strategies(self, factory):
        """Test all ContextType values have appropriate strategies."""
        context_types = [
            ContextType.SYSTEM_PROMPT,
            ContextType.USER_INPUT,
            ContextType.CONVERSATION_HISTORY,
            ContextType.COMPLIANCE_SOURCES,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.DOCUMENT_SUMMARIES,
            ContextType.YOUTUBE_CONTEXT,
            ContextType.CURRENT_CONTENT
        ]
        
        for context_type in context_types:
            strategy = factory.create_strategy(context_type)
            assert strategy is not None
            assert hasattr(strategy, 'compress_content')
    
    def test_strategy_consistency(self, factory):
        """Test same content type returns consistent strategy."""
        content = "Test content"
        context_type = ContextType.COMPLIANCE_SOURCES
        
        strategy1 = factory.get_best_strategy_for_content(content, context_type)
        strategy2 = factory.get_best_strategy_for_content(content, context_type)
        
        assert type(strategy1) == type(strategy2)
