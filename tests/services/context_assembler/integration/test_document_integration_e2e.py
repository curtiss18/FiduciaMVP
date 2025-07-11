"""End-to-end integration test for document context"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context_assembly_service import ContextGatherer, DocumentGatherer, ContextType


class TestDocumentContextIntegration:
    
    @pytest.mark.asyncio
    async def test_full_document_context_workflow(self):
        """Test complete document context workflow from gatherer to element."""
        
        # Mock document data
        sample_documents = [
            {
                'id': 'test_doc_1',
                'title': 'Financial Planning Guide',
                'content_type': 'pdf',
                'word_count': 2500,
                'processing_status': 'completed',
                'summary': 'Comprehensive guide covering retirement planning, investment strategies, and risk management for financial advisors.'
            }
        ]
        
        mock_db_session = Mock(spec=AsyncSession)
        
        # Create gatherer and test
        gatherer = ContextGatherer()
        
        with patch.object(gatherer.document_gatherer.document_manager, 'get_session_documents', return_value=sample_documents):
            with patch.object(gatherer.conversation_gatherer, 'gather_context', return_value=[]):
                with patch.object(gatherer.compliance_gatherer, 'gather_context', return_value=[]):
                    
                    elements = await gatherer.gather_all_context(
                        session_id='integration_test_session',
                        db_session=mock_db_session,
                        context_data={}
                    )
        
        # Verify we got document elements
        document_elements = [e for e in elements if e.context_type == ContextType.DOCUMENT_SUMMARIES]
        assert len(document_elements) == 1
        
        doc_element = document_elements[0]
        
        # Verify content structure
        assert '## DOCUMENT: Financial Planning Guide' in doc_element.content
        assert 'Document Type: PDF' in doc_element.content
        assert 'Word Count: 2500' in doc_element.content
        assert 'DOCUMENT SUMMARY:' in doc_element.content
        assert 'retirement planning' in doc_element.content
        
        # Verify metadata
        assert doc_element.source_metadata['document_id'] == 'test_doc_1'
        assert doc_element.source_metadata['document_title'] == 'Financial Planning Guide'
        assert doc_element.source_metadata['document_type'] == 'pdf'
        assert doc_element.source_metadata['word_count'] == 2500
        
        # Verify scoring
        assert doc_element.priority_score == 0.6
        assert doc_element.relevance_score == 0.5
        assert doc_element.token_count > 0
    
    @pytest.mark.asyncio
    async def test_document_context_with_budget_allocation(self):
        """Test that document context integrates with budget allocation."""
        
        from src.services.context_assembly_service import BudgetAllocator, RequestType
        
        budget_allocator = BudgetAllocator()
        budget = await budget_allocator.allocate_budget(
            request_type=RequestType.CREATION,
            user_input="Create a retirement planning post"
        )
        
        # Verify DOCUMENT_SUMMARIES is included in budget
        assert ContextType.DOCUMENT_SUMMARIES in budget
        assert budget[ContextType.DOCUMENT_SUMMARIES].allocated_tokens > 0
    
    @pytest.mark.asyncio
    async def test_document_gatherer_standalone(self):
        """Test DocumentGatherer can be used standalone."""
        
        sample_docs = [
            {
                'id': 'standalone_doc',
                'title': 'Standalone Test Document',
                'content_type': 'txt',
                'word_count': 1000,
                'processing_status': 'completed',
                'summary': 'Test document for standalone gatherer testing.'
            }
        ]
        
        gatherer = DocumentGatherer()
        mock_db_session = Mock(spec=AsyncSession)
        
        with patch.object(gatherer.document_manager, 'get_session_documents', return_value=sample_docs):
            elements = await gatherer.gather_context(
                session_id='standalone_session',
                db_session=mock_db_session
            )
        
        assert len(elements) == 1
        assert elements[0].context_type == ContextType.DOCUMENT_SUMMARIES
        assert 'Standalone Test Document' in elements[0].content
