"""Integration tests for ContextGatherer with document support"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service.gathering.context_gatherer import ContextGatherer
from src.services.context_assembly_service.models import ContextElement, ContextType


class TestContextGathererDocumentIntegration:
    
    @pytest.fixture
    def gatherer(self):
        return ContextGatherer()
    
    @pytest.fixture
    def mock_db_session(self):
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_documents(self):
        return [
            {
                'id': 'doc1',
                'title': 'Investment Guide',
                'content_type': 'pdf',
                'word_count': 1500,
                'processing_status': 'completed',
                'summary': 'Investment strategies and risk management.'
            }
        ]
    
    @pytest.fixture
    def sample_context_data(self):
        return {
            'rules': [
                {
                    'id': 'rule1',
                    'regulation_name': 'SEC Rule 1',
                    'requirement_text': 'Investment advisors must disclose conflicts of interest.'
                }
            ],
            'disclaimers': [
                {
                    'id': 'disc1',
                    'title': 'Investment Disclaimer',
                    'content_text': 'Past performance does not guarantee future results.'
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_gather_all_context_with_documents(self, gatherer, mock_db_session, sample_documents, sample_context_data):
        """Test gathering all context types including documents."""
        
        # Mock all gatherers
        with patch.object(gatherer.conversation_gatherer, 'gather_context', return_value=[]):
            with patch.object(gatherer.compliance_gatherer, 'gather_context', return_value=[]):
                with patch.object(gatherer.document_gatherer, 'gather_context', return_value=[
                    ContextElement(
                        content="## DOCUMENT: Investment Guide\nDocument Type: PDF\nWord Count: 1500\n**DOCUMENT SUMMARY:**\nInvestment strategies and risk management.",
                        context_type=ContextType.DOCUMENT_SUMMARIES,
                        priority_score=0.6,
                        relevance_score=0.5,
                        token_count=50,
                        source_metadata={'document_id': 'doc1'}
                    )
                ]):
                    elements = await gatherer.gather_all_context(
                        session_id='test-session',
                        db_session=mock_db_session,
                        context_data=sample_context_data
                    )
        
        # Should have document elements
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.DOCUMENT_SUMMARIES
        assert 'Investment Guide' in elements[0].content
    
    @pytest.mark.asyncio
    async def test_gather_documents_only(self, gatherer, mock_db_session, sample_documents):
        """Test gathering only document context."""
        
        with patch.object(gatherer.document_gatherer, 'gather_context', return_value=[
            ContextElement(
                content="Test document content",
                context_type=ContextType.DOCUMENT_SUMMARIES,
                priority_score=0.6,
                relevance_score=0.5,
                token_count=25,
                source_metadata={'document_id': 'doc1'}
            )
        ]) as mock_gather:
            elements = await gatherer.gather_documents_only(
                session_id='test-session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.DOCUMENT_SUMMARIES
        mock_gather.assert_called_once_with(
            session_id='test-session',
            db_session=mock_db_session
        )
    
    @pytest.mark.asyncio
    async def test_document_gatherer_error_handling(self, gatherer, mock_db_session, sample_context_data):
        """Test graceful handling of document gatherer errors."""
        
        with patch.object(gatherer.conversation_gatherer, 'gather_context', return_value=[]):
            with patch.object(gatherer.compliance_gatherer, 'gather_context', return_value=[]):
                with patch.object(gatherer.document_gatherer, 'gather_context', side_effect=Exception("Document error")):
                    elements = await gatherer.gather_all_context(
                        session_id='test-session', 
                        db_session=mock_db_session,
                        context_data=sample_context_data
                    )
        
        # Should return elements from other gatherers, not fail completely
        assert isinstance(elements, list)
    
    @pytest.mark.asyncio
    async def test_all_gatherers_called_with_correct_params(self, gatherer, mock_db_session, sample_context_data):
        """Test that all gatherers are called with correct parameters."""
        
        with patch.object(gatherer.conversation_gatherer, 'gather_context', return_value=[]) as mock_conv:
            with patch.object(gatherer.compliance_gatherer, 'gather_context', return_value=[]) as mock_comp:
                with patch.object(gatherer.document_gatherer, 'gather_context', return_value=[]) as mock_doc:
                    await gatherer.gather_all_context(
                        session_id='test-session',
                        db_session=mock_db_session,
                        context_data=sample_context_data
                    )
        
        # Verify conversation gatherer called correctly
        mock_conv.assert_called_once_with(
            session_id='test-session',
            db_session=mock_db_session
        )
        
        # Verify compliance gatherer called correctly
        mock_comp.assert_called_once_with(
            context_data=sample_context_data
        )
        
        # Verify document gatherer called correctly
        mock_doc.assert_called_once_with(
            session_id='test-session',
            db_session=mock_db_session,
            context_data=sample_context_data
        )
