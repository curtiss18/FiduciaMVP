"""Tests for StructurePreservingCompressor."""

import pytest
from unittest.mock import Mock

from src.services.context_assembly_service.optimization.compression.structure_preserving_compressor import StructurePreservingCompressor
from src.services.context_assembly_service.optimization.text_token_manager import TextTokenManager
from src.services.context_assembly_service.models import ContextType


class TestStructurePreservingCompressor:
    """Test structure preservation during compression."""
    
    @pytest.fixture
    def token_manager(self):
        return TextTokenManager()
    
    @pytest.fixture
    def compressor(self, token_manager):
        return StructurePreservingCompressor(token_manager)
    
    @pytest.mark.asyncio
    async def test_heading_preservation(self, compressor):
        """Test markdown headings are preserved."""
        content = """
        # Main Title
        ## Subtitle
        ### Sub-subtitle
        
        Regular content here that can be compressed more aggressively.
        This paragraph has lots of text that should be compressed first.
        """
        
        target_tokens = 50
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        assert "# Main Title" in result
        assert "## Subtitle" in result or "### Sub-subtitle" in result
    
    @pytest.mark.asyncio
    async def test_bullet_point_preservation(self, compressor):
        """Test bullet points and lists are preserved."""
        content = """
        Important requirements:
        * First requirement item
        * Second requirement item  
        * Third requirement item
        - Alternative bullet style
        - Another alternative bullet
        
        Additional text that can be compressed away safely.
        More content that is less important than the list structure.
        """
        
        target_tokens = 30
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should preserve list structure
        assert "*" in result or "-" in result
        assert any(item in result for item in ["First requirement", "Second requirement", "Third requirement"])
    
    @pytest.mark.asyncio
    async def test_formatting_preservation(self, compressor):
        """Test bold, italic, code formatting preserved."""
        content = """
        **Important bold text** should be preserved.
        *Italic emphasis* is also important.
        `code snippets` need to stay intact.
        
        Regular text that can be compressed away without losing meaning.
        Additional filler content that is not as critical as formatted text.
        More padding content for compression testing purposes.
        """
        
        target_tokens = 25
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should preserve formatting markers
        formatted_preserved = any(marker in result for marker in ["**", "*", "`"])
        assert formatted_preserved
    
    @pytest.mark.asyncio
    async def test_target_token_compliance(self, compressor):
        """Test compression meets target token limits."""
        content = "This is test content. " * 100  # Large content
        target_tokens = 50
        
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        actual_tokens = compressor.token_manager.count_tokens(result)
        
        # Should be at or under target
        assert actual_tokens <= target_tokens * 1.1  # Allow 10% tolerance
    
    @pytest.mark.asyncio
    async def test_content_quality_maintenance(self, compressor):
        """Test compressed content maintains meaning."""
        content = """
        # Compliance Guidelines
        
        ## Key Requirements
        * Must include disclaimer
        * Risk warnings required
        * Performance data needs context
        
        Additional explanatory text that provides context but can be compressed.
        This section explains the reasoning behind the requirements listed above.
        """
        
        target_tokens = 40
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should maintain key structural elements
        assert "Compliance" in result or "Guidelines" in result
        assert "Requirements" in result or "Key" in result
        assert "disclaimer" in result or "warnings" in result
    
    @pytest.mark.asyncio
    async def test_short_content_handling(self, compressor):
        """Test behavior with content already under limit."""
        content = "Short content that fits."
        target_tokens = 100
        
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should return unchanged if under limit
        assert result == content
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, compressor):
        """Test handling of empty/whitespace content."""
        assert await compressor.compress_content("", 50, ContextType.COMPLIANCE_SOURCES) == ""
        assert await compressor.compress_content("   ", 50, ContextType.COMPLIANCE_SOURCES) == "   "
        assert await compressor.compress_content(None, 50, ContextType.COMPLIANCE_SOURCES) is None
    
    @pytest.mark.asyncio
    async def test_structure_hierarchy_preservation(self, compressor):
        """Test nested structure preservation."""
        content = """
        # Level 1 Heading
        ## Level 2 Heading
        ### Level 3 Heading
        
        * Top level bullet
          * Nested bullet
            * Deeply nested bullet
        
        1. Numbered item
           a. Sub-item
           b. Another sub-item
        
        Long explanatory text that can be compressed away while preserving
        the hierarchical structure shown above. This text is meant to test
        the compression algorithm's ability to maintain document structure.
        """
        
        target_tokens = 60
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should preserve heading hierarchy
        heading_levels = ["#", "##", "###"]
        preserved_headings = sum(1 for level in heading_levels if level in result)
        assert preserved_headings >= 1
        
        # Should preserve some list structure  
        list_markers = ["*", "1.", "a.", "b."]
        preserved_lists = sum(1 for marker in list_markers if marker in result)
        assert preserved_lists >= 1


class TestStructurePreservingCompressorEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def compressor(self):
        return StructurePreservingCompressor(TextTokenManager())
    
    @pytest.mark.asyncio
    async def test_very_small_target_tokens(self, compressor):
        """Test behavior with extremely small token limits."""
        content = "# Title\nSome content here"
        target_tokens = 5
        
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should still return something meaningful
        assert len(result) > 0
        actual_tokens = compressor.token_manager.count_tokens(result)
        assert actual_tokens <= target_tokens * 1.5  # Allow some tolerance for very small limits
    
    @pytest.mark.asyncio
    async def test_malformed_markdown_handling(self, compressor):
        """Test handling of malformed markdown."""
        content = """
        # Incomplete heading
        ## Another heading##wrong
        * Bullet without space
        *Missing space bullet
        **Unclosed bold
        `Unclosed code
        """
        
        target_tokens = 30
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should handle gracefully without errors
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_mixed_formatting_styles(self, compressor):
        """Test content with mixed formatting styles."""
        content = """
        # Markdown heading
        <h2>HTML heading</h2>
        * Markdown bullet
        <li>HTML list item</li>
        **Markdown bold**
        <strong>HTML bold</strong>
        """
        
        target_tokens = 40
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should preserve some formatting from both styles
        assert isinstance(result, str)
        assert len(result) > 0


class TestStructurePreservingCompressorIntegration:
    """Integration tests with different content types."""
    
    @pytest.fixture
    def compressor(self):
        return StructurePreservingCompressor(TextTokenManager())
    
    @pytest.mark.asyncio
    async def test_compliance_content_compression(self, compressor):
        """Test compression of typical compliance content."""
        content = """
        ## SEC Marketing Rule Requirements
        
        ### Key Provisions
        * All marketing materials must be fair and balanced
        * Performance data requires appropriate context
        * Risk disclosures must be prominent
        
        ### Required Disclaimers
        * Past performance does not guarantee future results
        * All investments carry risk of loss
        * Consult with qualified advisor before investing
        
        Additional explanatory text about compliance requirements that
        provides context but can be compressed if needed for space.
        """
        
        target_tokens = 70
        result = await compressor.compress_content(content, target_tokens, ContextType.COMPLIANCE_SOURCES)
        
        # Should preserve regulatory structure
        assert "SEC" in result or "Marketing" in result
        assert "Requirements" in result or "Provisions" in result
        assert "risk" in result or "Risk" in result
    
    @pytest.mark.asyncio
    async def test_vector_search_results_compression(self, compressor):
        """Test compression of vector search results."""
        content = """
        ## APPROVED EXAMPLES:
        
        **Example 1: Social Media Post**
        Content: "Building wealth takes time and patience..."
        Tags: social_media, wealth_building, patience
        
        **Example 2: Newsletter Content** 
        Content: "Market volatility is normal and expected..."
        Tags: newsletter, volatility, education
        
        Detailed explanations of why these examples were approved
        and how they demonstrate proper compliance with regulations.
        """
        
        target_tokens = 60
        result = await compressor.compress_content(content, target_tokens, ContextType.VECTOR_SEARCH_RESULTS)
        
        # Should preserve example structure
        assert "EXAMPLES" in result or "Example" in result
        assert "Content:" in result or "Tags:" in result
