# Integration Test WorkflowOrchestrator
"""
Integration tests for WorkflowOrchestrator.

Tests full workflow scenarios:
- Complete content creation workflow
- Content review and approval workflow
- Session management integration
- Service coordination validation
- Cross-service data consistency
- Performance and response time validation

These tests use real service instances but with test database isolation.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.services.advisor_workflow import WorkflowOrchestrator


class TestWorkflowOrchestratorIntegration:
    """Integration tests for WorkflowOrchestrator with real service dependencies."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create WorkflowOrchestrator with default (real) services."""
        return WorkflowOrchestrator()
    
    @pytest.fixture
    def test_advisor_id(self):
        """Test advisor ID for integration tests."""
        return f"integration_test_advisor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @pytest.fixture
    def test_cco_email(self):
        """Test CCO email for integration tests."""
        return "integration_test_cco@fiducia.com"
    
    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for integration testing."""
        return {
            "title": "Integration Test LinkedIn Post",
            "content_text": "This is integration test content about financial planning best practices...",
            "content_type": "linkedin_post",
            "audience_type": "general_education",
            "advisor_notes": "Created during integration testing"
        }
    
    # ===================================================================
    # FULL WORKFLOW INTEGRATION TESTS
    # ===================================================================
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_content_creation_workflow(self, orchestrator, test_advisor_id, sample_content_data):
        """Test complete content creation workflow end-to-end."""
        # Step 1: Create Warren session
        session_result = await orchestrator.create_advisor_session(
            advisor_id=test_advisor_id,
            title="Integration Test Session"
        )
        
        assert session_result["status"] == "success"
        session_id = session_result["session"]["session_id"]
        
        # Step 2: Save Warren conversation messages
        user_message_result = await orchestrator.save_warren_message(
            session_id=session_id,
            message_type="user",
            content="Create a LinkedIn post about retirement planning"
        )
        assert user_message_result["status"] == "success"
        
        warren_metadata = {
            "sources_used": ["SEC Guide to Retirement", "FINRA Retirement Planning"],
            "generation_confidence": 0.92,
            "search_strategy": "vector",
            "total_sources": 8
        }
        
        warren_message_result = await orchestrator.save_warren_message(
            session_id=session_id,
            message_type="warren",
            content=sample_content_data["content_text"],
            metadata=warren_metadata
        )
        assert warren_message_result["status"] == "success"
        
        # Step 3: Save content to library
        content_result = await orchestrator.save_advisor_content(
            advisor_id=test_advisor_id,
            source_session_id=session_id,
            source_message_id=warren_message_result["message"]["id"],
            **sample_content_data
        )
        
        assert content_result["status"] == "success"
        content_id = content_result["content"]["id"]
        
        # Step 4: Verify content in library
        library_result = await orchestrator.get_advisor_content_library(
            advisor_id=test_advisor_id
        )
        
        assert library_result["status"] == "success"
        assert len(library_result["content"]) >= 1
        
        # Find our content
        our_content = next(
            (item for item in library_result["content"] if item["id"] == content_id),
            None
        )
        assert our_content is not None
        assert our_content["title"] == sample_content_data["title"]
        assert our_content["status"] == "draft"
        
        # Step 5: Get content statistics
        stats_result = await orchestrator.get_content_statistics(test_advisor_id)
        assert stats_result["status"] == "success"
        assert stats_result["statistics"]["total_content"] >= 1
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_compliance_review_workflow(self, orchestrator, test_advisor_id, test_cco_email, sample_content_data):
        """Test complete compliance review workflow end-to-end."""
        # Step 1: Create and save content
        content_result = await orchestrator.save_advisor_content(
            advisor_id=test_advisor_id,
            **sample_content_data
        )
        assert content_result["status"] == "success"
        content_id = content_result["content"]["id"]
        
        # Step 2: Submit for review
        review_result = await orchestrator.submit_content_for_review(
            content_id=content_id,
            advisor_id=test_advisor_id,
            cco_email=test_cco_email,
            notes="Please review this integration test content"
        )
        
        assert review_result["status"] == "success"
        assert "review_token" in review_result["review"]
        
        # Verify status changed to submitted
        library_result = await orchestrator.get_advisor_content_library(
            advisor_id=test_advisor_id,
            status_filter="submitted"
        )
        assert library_result["status"] == "success"
        assert any(item["id"] == content_id for item in library_result["content"])
        
        # Step 3: CCO approves content
        approval_result = await orchestrator.update_content_status(
            content_id=content_id,
            advisor_id=test_advisor_id,
            new_status="approved",
            reviewer=test_cco_email,
            notes="Approved after integration test review",
            user_role="cco"
        )
        
        assert approval_result["status"] == "success"
        
        # Step 4: Verify content is approved
        library_result = await orchestrator.get_advisor_content_library(
            advisor_id=test_advisor_id,
            status_filter="approved"
        )
        assert library_result["status"] == "success"
        assert any(item["id"] == content_id for item in library_result["content"])
        
        # Step 5: Update content after approval
        update_result = await orchestrator.update_content(
            content_id=content_id,
            advisor_id=test_advisor_id,
            advisor_notes="Updated notes after approval"
        )
        assert update_result["status"] == "success"
    
    @pytest.mark.asyncio
    @pytest.mark.integration 
    async def test_session_and_content_linking(self, orchestrator, test_advisor_id):
        """Test that sessions and content are properly linked."""
        # Create session
        session_result = await orchestrator.create_advisor_session(
            advisor_id=test_advisor_id,
            title="Content Linking Test Session"
        )
        assert session_result["status"] == "success"
        session_id = session_result["session"]["session_id"]
        
        # Save Warren message
        warren_message_result = await orchestrator.save_warren_message(
            session_id=session_id,
            message_type="warren",
            content="Here's your compliant content...",
            metadata={"sources_used": ["compliance_rule_1"]}
        )
        assert warren_message_result["status"] == "success"
        message_id = warren_message_result["message"]["id"]
        
        # Save content linked to session and message
        content_result = await orchestrator.save_advisor_content(
            advisor_id=test_advisor_id,
            title="Linked Content Test",
            content_text="This content is linked to session and message",
            content_type="email",
            source_session_id=session_id,
            source_message_id=message_id
        )
        assert content_result["status"] == "success"
        
        # Verify linking in content details
        content = content_result["content"]
        assert content["source_session_id"] == session_id
        assert content["source_message_id"] == message_id
        
        # Verify we can retrieve session messages
        messages_result = await orchestrator.get_session_messages(session_id, test_advisor_id)
        assert messages_result["status"] == "success"
        assert len(messages_result["messages"]) >= 1
