"""Tests for ContextBuilder service."""

import pytest
from unittest.mock import Mock, patch
from src.services.context_assembly_service.assembly import ContextBuilder
from src.services.context_assembly_service.models import (
    ContextElement, 
    ContextType, 
    FormattingOptions
)


class TestContextBuilder:
    
    def setup_method(self):
        self.builder = ContextBuilder()
    
    def test_empty_context_elements(self):
        """Test handling of empty context elements list."""
        result = self.builder.build_context_string([])
        assert result == ""
    
    def test_single_context_element(self):
        """Test building context with single element."""
        element = ContextElement(
            content="Test content for user input",
            context_type=ContextType.USER_INPUT,
            priority_score=8.0,
            relevance_score=0.9,
            token_count=50,
            source_metadata={"source_type": "user_request"}
        )
        
        result = self.builder.build_context_string([element])
        
        assert "=== USER REQUEST ===" in result
        assert "Test content for user input" in result
        assert "[Source: user_request]" in result
    
    def test_multiple_context_elements_ordering(self):
        """Test that context elements are ordered correctly."""
        elements = [
            ContextElement(
                content="User wants to create a post",
                context_type=ContextType.USER_INPUT,
                priority_score=9.0,
                relevance_score=1.0,
                token_count=30,
                source_metadata={}
            ),
            ContextElement(
                content="System instructions for Warren",
                context_type=ContextType.SYSTEM_PROMPT,
                priority_score=10.0,
                relevance_score=1.0,
                token_count=100,
                source_metadata={}
            ),
            ContextElement(
                content="Previous conversation context",
                context_type=ContextType.CONVERSATION_HISTORY,
                priority_score=7.0,
                relevance_score=0.8,
                token_count=200,
                source_metadata={}
            )
        ]
        
        result = self.builder.build_context_string(elements)
        
        # Verify order: SYSTEM_PROMPT should come before CONVERSATION_HISTORY before USER_INPUT
        system_pos = result.find("=== SYSTEM INSTRUCTIONS ===")
        conversation_pos = result.find("=== CONVERSATION HISTORY ===")
        user_pos = result.find("=== USER REQUEST ===")
        
        assert system_pos < conversation_pos < user_pos
    
    def test_group_elements_by_type(self):
        """Test grouping of elements by context type."""
        elements = [
            ContextElement(
                content="First compliance guideline",
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=8.0,
                relevance_score=0.9,
                token_count=50,
                source_metadata={}
            ),
            ContextElement(
                content="Second compliance guideline",
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=9.0,  # Higher priority
                relevance_score=0.8,
                token_count=60,
                source_metadata={}
            ),
            ContextElement(
                content="Vector search result",
                context_type=ContextType.VECTOR_SEARCH_RESULTS,
                priority_score=7.0,
                relevance_score=0.7,
                token_count=40,
                source_metadata={}
            )
        ]
        
        grouped = self.builder._group_elements_by_type(elements)
        
        assert len(grouped) == 2
        assert ContextType.COMPLIANCE_SOURCES in grouped
        assert ContextType.VECTOR_SEARCH_RESULTS in grouped
        assert len(grouped[ContextType.COMPLIANCE_SOURCES]) == 2
        assert len(grouped[ContextType.VECTOR_SEARCH_RESULTS]) == 1
        
        # Verify sorting by priority (higher priority first)
        compliance_elements = grouped[ContextType.COMPLIANCE_SOURCES]
        assert compliance_elements[0].priority_score == 9.0
        assert compliance_elements[1].priority_score == 8.0
    
    def test_section_headers(self):
        """Test correct section headers for different context types."""
        test_cases = [
            (ContextType.SYSTEM_PROMPT, "=== SYSTEM INSTRUCTIONS ==="),
            (ContextType.CURRENT_CONTENT, "=== CURRENT CONTENT FOR EDITING ==="),
            (ContextType.DOCUMENT_SUMMARIES, "=== UPLOADED DOCUMENTS ==="),
            (ContextType.COMPLIANCE_SOURCES, "=== COMPLIANCE GUIDELINES ==="),
            (ContextType.VECTOR_SEARCH_RESULTS, "=== RELEVANT EXAMPLES ==="),
            (ContextType.YOUTUBE_CONTEXT, "=== VIDEO TRANSCRIPT CONTEXT ==="),
            (ContextType.CONVERSATION_HISTORY, "=== CONVERSATION HISTORY ==="),
            (ContextType.USER_INPUT, "=== USER REQUEST ===")
        ]
        
        for context_type, expected_header in test_cases:
            header = self.builder._get_section_header(context_type)
            assert header == expected_header
    
    def test_context_summary(self):
        """Test context summary generation."""
        elements = [
            ContextElement(
                content="Test content 1",
                context_type=ContextType.USER_INPUT,
                priority_score=8.0,
                relevance_score=0.9,
                token_count=50,
                source_metadata={}
            ),
            ContextElement(
                content="Test content 2",
                context_type=ContextType.USER_INPUT,
                priority_score=7.0,
                relevance_score=0.8,
                token_count=30,
                source_metadata={}
            ),
            ContextElement(
                content="Compliance content",
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=9.0,
                relevance_score=1.0,
                token_count=100,
                source_metadata={}
            )
        ]
        
        summary = self.builder.get_context_summary(elements)
        
        assert summary['user_input'] == 80  # 50 + 30
        assert summary['compliance_sources'] == 100
        assert summary['total_tokens'] == 180  # 50 + 30 + 100
        assert summary['total_elements'] == 3
    
    def test_vector_search_section_formatting(self):
        """Test special formatting for vector search results."""
        elements = [
            ContextElement(
                content="First example content",
                context_type=ContextType.VECTOR_SEARCH_RESULTS,
                priority_score=8.0,
                relevance_score=0.9,
                token_count=50,
                source_metadata={"source_type": "approved_example"}
            ),
            ContextElement(
                content="Second example content",
                context_type=ContextType.VECTOR_SEARCH_RESULTS,
                priority_score=7.0,
                relevance_score=0.8,
                token_count=40,
                source_metadata={"source_type": "compliance_template"}
            )
        ]
        
        result = self.builder.build_context_string(elements)
        
        # Should contain separator between multiple vector search results
        assert "---" in result
        assert "First example content" in result
        assert "Second example content" in result
        assert "[Source: approved_example]" in result
        assert "[Source: compliance_template]" in result
    
    def test_conversation_history_formatting(self):
        """Test conversation history maintains proper structure."""
        element = ContextElement(
            content="User: Hello\nAssistant: Hi there!\nUser: Help me create content",
            context_type=ContextType.CONVERSATION_HISTORY,
            priority_score=7.0,
            relevance_score=0.8,
            token_count=100,
            source_metadata={"source_type": "conversation"}
        )
        
        result = self.builder.build_context_string([element])
        
        assert "=== CONVERSATION HISTORY ===" in result
        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result
        assert "User: Help me create content" in result
    
    @patch('src.services.context_assembly_service.assembly.context_builder.logger')
    def test_error_handling_fallback(self, mock_logger):
        """Test fallback context when main assembly fails."""
        # Create element that might cause issues
        element = ContextElement(
            content="Test content",
            context_type=ContextType.USER_INPUT,
            priority_score=8.0,
            relevance_score=0.9,
            token_count=50,
            source_metadata={}
        )
        
        # Mock the main build process to fail
        with patch.object(self.builder, '_group_elements_by_type', side_effect=Exception("Test error")):
            result = self.builder.build_context_string([element])
            
            # Should get fallback context
            assert "user_input" in result
            assert "Test content" in result
            mock_logger.error.assert_called()
    
    def test_empty_content_filtering(self):
        """Test that whitespace-only content elements are filtered out."""
        elements = [
            ContextElement(
                content="   ",  # Whitespace only
                context_type=ContextType.COMPLIANCE_SOURCES,
                priority_score=7.0,
                relevance_score=0.8,
                token_count=5,
                source_metadata={}
            ),
            ContextElement(
                content="Valid content",
                context_type=ContextType.DOCUMENT_SUMMARIES,
                priority_score=9.0,
                relevance_score=1.0,
                token_count=50,
                source_metadata={}
            )
        ]
        
        result = self.builder.build_context_string(elements)
        
        # Should only contain the valid content
        assert "Valid content" in result
        assert "=== UPLOADED DOCUMENTS ===" in result
        # Should not contain empty sections (whitespace-only content should be filtered)
        assert "=== COMPLIANCE GUIDELINES ===" not in result
    
    @patch('src.services.context_assembly_service.assembly.context_builder.TextTokenManager')
    def test_token_manager_integration(self, mock_token_manager_class):
        """Test integration with TextTokenManager."""
        mock_token_manager = Mock()
        mock_token_manager.count_tokens.return_value = 150
        mock_token_manager_class.return_value = mock_token_manager
        
        builder = ContextBuilder(token_manager=mock_token_manager)
        
        element = ContextElement(
            content="Test content",
            context_type=ContextType.USER_INPUT,
            priority_score=8.0,
            relevance_score=0.9,
            token_count=50,
            source_metadata={}
        )
        
        result = builder.build_context_string([element])
        
        # Verify token manager was called
        mock_token_manager.count_tokens.assert_called()
        assert result  # Should have content
