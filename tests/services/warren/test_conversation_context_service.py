"""
Tests for ConversationContextService

Test Coverage:
- get_conversation_context (direct port of _get_conversation_context)
- get_session_documents (direct port of session document retrieval logic)
- get_session_context (combination logic from enhanced_warren_service)
- save_conversation_turn (direct port of _save_conversation_turn)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.conversation_context_service import ConversationContextService


class TestConversationContextService:
    """Test suite for ConversationContextService."""
    
    @pytest.fixture
    def mock_conversation_manager_class(self):
        """Mock ConversationManager class."""
        mock_class = MagicMock()
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance
        mock_instance.get_conversation_context.return_value = ""
        mock_instance.save_conversation_turn.return_value = None
        return mock_class
    
    @pytest.fixture
    def mock_document_manager(self):
        """Mock DocumentManager."""
        mock_manager = AsyncMock()
        mock_manager.get_session_documents.return_value = []
        return mock_manager
    
    @pytest.fixture
    def service(self, mock_conversation_manager_class, mock_document_manager):
        """Create ConversationContextService instance for testing."""
        return ConversationContextService(
            conversation_manager=mock_conversation_manager_class,
            document_manager=mock_document_manager
        )
    
    @pytest.fixture
    def sample_conversation_context(self):
        """Sample conversation context for testing."""
        return "User asked about retirement planning. Warren suggested diversification strategies."
    
    @pytest.fixture
    def sample_documents(self):
        """Sample session documents for testing."""
        return [
            {
                'id': 'doc_1',
                'title': 'Investment Strategy Guide',
                'processing_status': 'processed',
                'summary': 'Comprehensive guide to investment strategies for retirement planning.',
                'content_type': 'pdf',
                'word_count': 1500
            },
            {
                'id': 'doc_2', 
                'title': 'Market Analysis Report',
                'processing_status': 'processed',
                'summary': 'Current market trends and analysis for Q4 2024.',
                'content_type': 'docx',
                'word_count': 800
            },
            {
                'id': 'doc_3',
                'title': 'Unprocessed Document',
                'processing_status': 'processing',
                'summary': None,
                'content_type': 'pdf',
                'word_count': 0
            }
        ]
    
    @pytest.fixture
    def sample_processed_documents(self):
        """Expected processed documents with summaries."""
        return [
            {
                'title': 'Investment Strategy Guide',
                'summary': 'Comprehensive guide to investment strategies for retirement planning.',
                'content_type': 'pdf',
                'word_count': 1500,
                'document_id': 'doc_1'
            },
            {
                'title': 'Market Analysis Report',
                'summary': 'Current market trends and analysis for Q4 2024.',
                'content_type': 'docx',
                'word_count': 800,
                'document_id': 'doc_2'
            }
        ]
    
    # Test get_conversation_context method
    @pytest.mark.asyncio
    async def test_get_conversation_context_success(self, service, mock_conversation_manager_class, sample_conversation_context):
        """Test successful conversation context retrieval."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.get_conversation_context.return_value = sample_conversation_context
        
        # Execute
        result = await service.get_conversation_context("test-session-123")
        
        # Verify
        assert result == sample_conversation_context
        mock_conversation_manager_class.assert_called_once()
        mock_instance.get_conversation_context.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio 
    async def test_get_conversation_context_empty(self, service, mock_conversation_manager_class):
        """Test conversation context retrieval when no context exists."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.get_conversation_context.return_value = ""
        
        # Execute
        result = await service.get_conversation_context("test-session-123")
        
        # Verify
        assert result == ""
        mock_instance.get_conversation_context.assert_called_once_with("test-session-123")
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_exception(self, service, mock_conversation_manager_class):
        """Test conversation context retrieval when exception occurs."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.get_conversation_context.side_effect = Exception("Database error")
        
        # Execute
        result = await service.get_conversation_context("test-session-123")
        
        # Verify - should return empty string on error
        assert result == ""
    
    # Test get_session_documents method
    @pytest.mark.asyncio
    async def test_get_session_documents_success(self, service, mock_document_manager, sample_documents, sample_processed_documents):
        """Test successful session documents retrieval."""
        # Setup
        mock_document_manager.get_session_documents.return_value = sample_documents
        
        # Execute
        result = await service.get_session_documents("test-session-123")
        
        # Verify
        assert result == sample_processed_documents
        mock_document_manager.get_session_documents.assert_called_once_with(
            session_id="test-session-123",
            include_content=True
        )
    
    @pytest.mark.asyncio
    async def test_get_session_documents_no_processed(self, service, mock_document_manager):
        """Test session documents retrieval when no processed documents exist."""
        # Setup - all documents are still processing
        unprocessed_documents = [
            {
                'id': 'doc_1',
                'title': 'Processing Document',
                'processing_status': 'processing',
                'summary': None,
                'content_type': 'pdf'
            }
        ]
        mock_document_manager.get_session_documents.return_value = unprocessed_documents
        
        # Execute
        result = await service.get_session_documents("test-session-123")
        
        # Verify
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_session_documents_no_session_id(self, service, mock_document_manager):
        """Test session documents retrieval when no session_id provided."""
        # Execute
        result = await service.get_session_documents(None)
        
        # Verify
        assert result == []
        mock_document_manager.get_session_documents.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_session_documents_exception(self, service, mock_document_manager):
        """Test session documents retrieval when exception occurs."""
        # Setup
        mock_document_manager.get_session_documents.side_effect = Exception("Document retrieval failed")
        
        # Execute
        result = await service.get_session_documents("test-session-123")
        
        # Verify - should return empty list on error
        assert result == []
    
    # Test get_session_context method (combination method)
    @pytest.mark.asyncio
    async def test_get_session_context_full(self, service, mock_conversation_manager_class, mock_document_manager, 
                                           sample_conversation_context, sample_documents, sample_processed_documents):
        """Test complete session context retrieval with conversation and documents."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.get_conversation_context.return_value = sample_conversation_context
        mock_document_manager.get_session_documents.return_value = sample_documents
        
        # Execute
        result = await service.get_session_context("test-session-123", use_conversation_context=True)
        
        # Verify
        expected = {
            "conversation_context": sample_conversation_context,
            "session_documents": sample_processed_documents,
            "session_id": "test-session-123",
            "conversation_context_available": True,
            "session_documents_available": True,
            "session_documents_count": 2
        }
        assert result == expected
        # Verify we only used one database session (efficiency improvement)
        mock_conversation_manager_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_context_no_conversation(self, service, mock_document_manager, sample_documents, sample_processed_documents):
        """Test session context retrieval with conversation disabled."""
        # Setup
        mock_document_manager.get_session_documents.return_value = sample_documents
        
        # Execute
        result = await service.get_session_context("test-session-123", use_conversation_context=False)
        
        # Verify
        expected = {
            "conversation_context": "",
            "session_documents": sample_processed_documents,
            "session_id": "test-session-123", 
            "conversation_context_available": False,
            "session_documents_available": True,
            "session_documents_count": 2
        }
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_get_session_context_no_session_id(self, service):
        """Test session context retrieval when no session_id provided."""
        # Execute
        result = await service.get_session_context(None, use_conversation_context=True)
        
        # Verify
        expected = {
            "conversation_context": "",
            "session_documents": [],
            "session_id": None,
            "conversation_context_available": False,
            "session_documents_available": False,
            "session_documents_count": 0
        }
        assert result == expected
    
    # Test save_conversation_turn method
    @pytest.mark.asyncio
    async def test_save_conversation_turn_success(self, service, mock_conversation_manager_class):
        """Test successful conversation turn saving."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        context_data = {
            'marketing_examples': [{'id': 'ex1'}],
            'disclaimers': [{'id': 'disc1'}],
            'context_quality_score': 0.8,
            'search_strategy': 'vector',
            'total_sources': 2,
            'marketing_examples_count': 1,
            'compliance_rules_count': 1
        }
        
        # Execute
        await service.save_conversation_turn(
            session_id="test-session-123",
            user_input="Create a retirement planning post",
            warren_response="Here's your retirement planning content...",
            context_data=context_data
        )
        
        # Verify
        expected_metadata = {
            'sources_used': [{'id': 'ex1'}, {'id': 'disc1'}],
            'generation_confidence': 0.8,
            'search_strategy': 'vector',
            'total_sources': 2,
            'marketing_examples': 1,
            'compliance_rules': 1
        }
        
        mock_instance.save_conversation_turn.assert_called_once_with(
            session_id="test-session-123",
            user_input="Create a retirement planning post",
            warren_response="Here's your retirement planning content...",
            warren_metadata=expected_metadata
        )
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_missing_context_data(self, service, mock_conversation_manager_class):
        """Test conversation turn saving with minimal context data."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        context_data = {}  # Empty context data
        
        # Execute
        await service.save_conversation_turn(
            session_id="test-session-123",
            user_input="Test input",
            warren_response="Test response",
            context_data=context_data
        )
        
        # Verify - should handle missing fields gracefully
        expected_metadata = {
            'sources_used': [],  # [] + [] = []
            'generation_confidence': 0.5,  # default
            'search_strategy': 'unknown',  # default
            'total_sources': 0,  # default
            'marketing_examples': 0,  # default
            'compliance_rules': 0  # default
        }
        
        mock_instance.save_conversation_turn.assert_called_once_with(
            session_id="test-session-123",
            user_input="Test input",
            warren_response="Test response",
            warren_metadata=expected_metadata
        )
    
    @pytest.mark.asyncio
    async def test_save_conversation_turn_exception(self, service, mock_conversation_manager_class):
        """Test conversation turn saving when exception occurs."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.save_conversation_turn.side_effect = Exception("Database save failed")
        context_data = {}
        
        # Execute - should not raise exception
        await service.save_conversation_turn(
            session_id="test-session-123",
            user_input="Test input",
            warren_response="Test response",
            context_data=context_data
        )
        
        # Verify - exception should be caught and logged, not raised
        mock_instance.save_conversation_turn.assert_called_once()
    
    # Integration test
    @pytest.mark.asyncio
    async def test_full_workflow(self, service, mock_conversation_manager_class, mock_document_manager,
                                sample_conversation_context, sample_documents, sample_processed_documents):
        """Test complete workflow matching original enhanced_warren_service behavior."""
        # Setup
        mock_instance = mock_conversation_manager_class.return_value
        mock_instance.get_conversation_context.return_value = sample_conversation_context
        mock_document_manager.get_session_documents.return_value = sample_documents
        
        # Execute - Get session context
        session_context = await service.get_session_context("test-session-123", use_conversation_context=True)
        
        # Execute - Save conversation turn
        context_data = {
            'marketing_examples': [{'id': 'ex1'}],
            'disclaimers': [{'id': 'disc1'}],
            'context_quality_score': 0.9,
            'search_strategy': 'hybrid'
        }
        
        await service.save_conversation_turn(
            session_id="test-session-123",
            user_input="Create LinkedIn post",
            warren_response="Generated content here...",
            context_data=context_data
        )
        
        # Verify session context
        assert session_context["conversation_context"] == sample_conversation_context
        assert session_context["session_documents"] == sample_processed_documents
        assert session_context["conversation_context_available"] == True
        assert session_context["session_documents_available"] == True
        assert session_context["session_documents_count"] == 2
        
        # Verify conversation turn was saved
        mock_instance.save_conversation_turn.assert_called_once()
        call_args = mock_instance.save_conversation_turn.call_args
        assert call_args[1]['session_id'] == "test-session-123"
        assert call_args[1]['user_input'] == "Create LinkedIn post"
        assert call_args[1]['warren_response'] == "Generated content here..."
        assert call_args[1]['warren_metadata']['search_strategy'] == 'hybrid'
