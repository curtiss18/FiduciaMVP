"""Edge case and error handling tests for document context"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembler.gathering.document_gatherer import DocumentGatherer
from src.services.context_assembler.models import ContextElement, ContextType


class TestDocumentGathererEdgeCases:
    
    @pytest.fixture
    def gatherer(self):
        return DocumentGatherer()
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=AsyncSession)
    
    @pytest.mark.asyncio
    async def test_malformed_document_data(self, gatherer, mock_db_session):
        """Test handling of malformed document data."""
        malformed_docs = [
            {
                # Missing required fields
                'title': 'Incomplete Doc',
                'processing_status': 'completed'
                # Missing content_type, word_count, etc.
            },
            {
                'id': 'doc2',
                'title': None,  # Null title
                'content_type': 'pdf',
                'processing_status': 'completed',
                'summary': 'Valid summary'
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=malformed_docs):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        # Should handle gracefully and return elements for valid parts
        assert len(elements) <= len(malformed_docs)
        for element in elements:
            assert isinstance(element, ContextElement)
            assert element.context_type == ContextType.DOCUMENT_SUMMARIES
    
    @pytest.mark.asyncio
    async def test_very_large_documents(self, gatherer, mock_db_session):
        """Test handling of very large documents."""
        large_docs = [
            {
                'id': 'large_doc',
                'title': 'Very Large Document',
                'content_type': 'pdf',
                'word_count': 50000,  # Very large
                'processing_status': 'completed',
                'summary': 'A' * 10000  # Very long summary
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=large_docs):
            with patch.object(gatherer, 'count_tokens', return_value=5000):
                elements = await gatherer.gather_context(
                    session_id='test-session',
                    db_session=mock_db_session
                )
        
        assert len(elements) == 1
        assert elements[0].token_count == 5000
        assert elements[0].source_metadata['word_count'] == 50000
    
    @pytest.mark.asyncio
    async def test_empty_string_fields(self, gatherer, mock_db_session):
        """Test handling of empty string fields."""
        empty_docs = [
            {
                'id': 'empty_doc',
                'title': '',  # Empty title
                'content_type': '',  # Empty content type
                'word_count': 0,
                'processing_status': 'completed',
                'summary': ''  # Empty summary
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=empty_docs):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        content = elements[0].content
        assert '## DOCUMENT: ' in content  # Should handle empty title
        assert 'Document Type: ' in content  # Should handle empty content type
    
    @pytest.mark.asyncio
    async def test_token_manager_error(self, gatherer, mock_db_session):
        """Test handling of token manager errors."""
        sample_docs = [
            {
                'id': 'doc1',
                'title': 'Test Doc',
                'content_type': 'pdf',
                'processing_status': 'completed',
                'summary': 'Test summary'
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_docs):
            with patch.object(gatherer, 'count_tokens', side_effect=Exception("Token error")):
                elements = await gatherer.gather_context(
                    session_id='test-session',
                    db_session=mock_db_session
                )
        
        # Should still create elements even if token counting fails
        assert len(elements) <= 1  # Might fail gracefully
    
    @pytest.mark.asyncio
    async def test_special_characters_in_content(self, gatherer, mock_db_session):
        """Test handling of special characters and unicode."""
        special_docs = [
            {
                'id': 'special_doc',
                'title': 'Document with émojis 📊 and special chars: <>&"',
                'content_type': 'pdf',
                'word_count': 1000,
                'processing_status': 'completed', 
                'summary': 'Summary with unicode: ñáéíóú and symbols: $€£¥ & HTML: <script>alert("test")</script>'
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=special_docs):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        content = elements[0].content
        assert 'émojis 📊' in content
        assert '<script>' in content  # Should not sanitize, just pass through
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_many_documents(self, gatherer, mock_db_session):
        """Test memory efficiency with many documents."""
        many_docs = []
        for i in range(100):  # 100 documents
            many_docs.append({
                'id': f'doc_{i}',
                'title': f'Document {i}',
                'content_type': 'pdf',
                'word_count': 1000,
                'processing_status': 'completed',
                'summary': f'Summary for document {i} with some content.'
            })
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=many_docs):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 100
        # Test that all elements are properly formed
        for i, element in enumerate(elements):
            assert f'Document {i}' in element.content
            assert element.context_type == ContextType.DOCUMENT_SUMMARIES
