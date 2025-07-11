"""Additional tests for DocumentGatherer to achieve 90%+ coverage"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.gathering.document_gatherer import DocumentGatherer


class TestDocumentGathererCoverage:
    
    @pytest.mark.asyncio 
    async def test_tiktoken_initialization_failure(self):
        """Test DocumentGatherer initialization when tiktoken fails."""
        with patch('src.services.context_assembly_service.gathering.document_gatherer.tiktoken.encoding_for_model', side_effect=Exception("tiktoken error")):
            gatherer = DocumentGatherer()
            assert gatherer.tokenizer is None
    
    @pytest.mark.asyncio
    async def test_token_counting_with_no_tokenizer(self):
        """Test token counting fallback when no tokenizer available."""
        with patch('src.services.context_assembly_service.gathering.document_gatherer.tiktoken.encoding_for_model', side_effect=Exception("tiktoken error")):
            gatherer = DocumentGatherer()
            
            # Test with text
            tokens = gatherer.count_tokens("test text")
            assert tokens == len("test text") // 4
            
            # Test with empty text
            tokens = gatherer.count_tokens("")
            assert tokens == 0
    
    @pytest.mark.asyncio
    async def test_token_counting_encoding_failure(self):
        """Test token counting when tokenizer.encode fails."""
        gatherer = DocumentGatherer()
        
        # Mock tokenizer to exist but encoding to fail
        mock_tokenizer = Mock()
        mock_tokenizer.encode.side_effect = Exception("encoding error")
        gatherer.tokenizer = mock_tokenizer
        
        tokens = gatherer.count_tokens("test text")
        assert tokens == len("test text") // 4  # Falls back to approximation
    
    @pytest.mark.asyncio
    async def test_empty_text_token_counting(self):
        """Test token counting with empty text."""
        gatherer = DocumentGatherer()
        
        tokens = gatherer.count_tokens("")
        assert tokens == 0
        
        tokens = gatherer.count_tokens(None)
        assert tokens == 0
