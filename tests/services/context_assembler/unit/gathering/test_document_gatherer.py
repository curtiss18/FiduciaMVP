"""Unit tests for DocumentGatherer"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembler.gathering.document_gatherer import DocumentGatherer
from src.services.context_assembler.models import ContextElement, ContextType


class TestDocumentGatherer:
    
    @pytest.fixture
    def gatherer(self):
        return DocumentGatherer()
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_documents(self):
        return [
            {
                'id': 'doc1',
                'title': 'Investment Strategy Guide',
                'content_type': 'pdf',
                'word_count': 1500,
                'processing_status': 'completed',
                'summary': 'Document discusses various investment strategies including risk assessment and portfolio diversification.'
            },
            {
                'id': 'doc2', 
                'title': 'Compliance Manual',
                'content_type': 'docx',
                'word_count': 3000,
                'processing_status': 'completed',
                'summary': 'Comprehensive compliance guidelines for financial advisors including SEC and FINRA requirements.'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_gather_context_success(self, gatherer, mock_db_session, sample_documents):
        """Test successful document context gathering."""
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_documents):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 2
        
        # Test first document element
        first_element = elements[0]
        assert isinstance(first_element, ContextElement)
        assert first_element.context_type == ContextType.DOCUMENT_SUMMARIES
        assert first_element.priority_score == 0.6
        assert first_element.relevance_score == 0.5
        assert 'Investment Strategy Guide' in first_element.content
        assert 'PDF' in first_element.content
        assert 'Word Count: 1500' in first_element.content
        assert 'investment strategies' in first_element.content
        
        # Test metadata
        assert first_element.source_metadata['document_id'] == 'doc1'
        assert first_element.source_metadata['document_title'] == 'Investment Strategy Guide'
        assert first_element.source_metadata['document_type'] == 'pdf'
        assert first_element.source_metadata['word_count'] == 1500
    
    @pytest.mark.asyncio
    async def test_gather_context_no_documents(self, gatherer, mock_db_session):
        """Test gathering when no documents exist."""
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=[]):
            elements = await gatherer.gather_context(
                session_id='empty-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 0
    
    @pytest.mark.asyncio
    async def test_gather_context_incomplete_processing(self, gatherer, mock_db_session):
        """Test filtering out documents that haven't completed processing."""
        incomplete_docs = [
            {
                'id': 'doc1',
                'title': 'Processing Doc',
                'content_type': 'pdf',
                'processing_status': 'processing',
                'summary': 'This should be filtered out'
            },
            {
                'id': 'doc2',
                'title': 'Failed Doc', 
                'content_type': 'pdf',
                'processing_status': 'failed',
                'summary': 'This should also be filtered out'
            },
            {
                'id': 'doc3',
                'title': 'Completed Doc',
                'content_type': 'pdf', 
                'processing_status': 'completed',
                'summary': 'This should be included'
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=incomplete_docs):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        assert 'Completed Doc' in elements[0].content
    
    @pytest.mark.asyncio
    async def test_gather_context_missing_summary(self, gatherer, mock_db_session):
        """Test handling documents without summaries."""
        docs_no_summary = [
            {
                'id': 'doc1',
                'title': 'No Summary Doc',
                'content_type': 'txt',
                'word_count': 500,
                'processing_status': 'completed'
                # No summary field
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=docs_no_summary):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        assert 'No Summary Doc' in elements[0].content
        assert 'TXT' in elements[0].content
        assert 'DOCUMENT SUMMARY' not in elements[0].content
    
    @pytest.mark.asyncio
    async def test_gather_context_missing_word_count(self, gatherer, mock_db_session):
        """Test handling documents without word count."""
        docs_no_count = [
            {
                'id': 'doc1',
                'title': 'No Count Doc',
                'content_type': 'pdf',
                'processing_status': 'completed',
                'summary': 'Test summary'
                # No word_count field
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=docs_no_count):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        assert 'Word Count: Unknown' in elements[0].content
        assert elements[0].source_metadata['word_count'] == 0
    
    @pytest.mark.asyncio
    async def test_gather_context_document_manager_error(self, gatherer, mock_db_session):
        """Test handling DocumentManager errors gracefully."""
        with patch.object(gatherer.document_manager, 'get_session_documents', side_effect=Exception("DB Error")):
            elements = await gatherer.gather_context(
                session_id='error-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 0
    
    @pytest.mark.asyncio
    async def test_content_formatting(self, gatherer, mock_db_session):
        """Test proper content formatting."""
        sample_doc = [
            {
                'id': 'doc1',
                'title': 'Test Document',
                'content_type': 'pdf',
                'word_count': 1000,
                'processing_status': 'completed',
                'summary': 'This is a test summary with multiple lines.\nIt contains important information.'
            }
        ]
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_doc):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        content = elements[0].content
        lines = content.split('\n')
        
        assert lines[0] == '## DOCUMENT: Test Document'
        assert lines[1] == 'Document Type: PDF'
        assert lines[2] == 'Word Count: 1000'
        assert lines[3] == '**DOCUMENT SUMMARY:**'
        assert 'test summary' in content
    
    @pytest.mark.asyncio
    async def test_token_counting(self, gatherer, mock_db_session, sample_documents):
        """Test token counting for document content."""
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_documents):
            with patch.object(gatherer, 'count_tokens', return_value=250) as mock_count:
                elements = await gatherer.gather_context(
                    session_id='test-session',
                    db_session=mock_db_session
                )
        
        assert len(elements) == 2
        assert all(element.token_count == 250 for element in elements)
        assert mock_count.call_count == 2
    
    @pytest.mark.asyncio 
    async def test_context_data_parameter(self, gatherer, mock_db_session, sample_documents):
        """Test that context_data parameter is accepted but not used."""
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_documents):
            elements = await gatherer.gather_context(
                session_id='test-session',
                db_session=mock_db_session,
                context_data={'some': 'data'}
            )
        
        assert len(elements) == 2
