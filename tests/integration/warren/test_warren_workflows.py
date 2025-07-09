"""
Comprehensive Integration Tests for Warren Service End-to-End Workflows

Epic: [SCRUM-86] Warren Service Tech Debt Remediation  
Task: [SCRUM-90] Create comprehensive integration test suite

Purpose: Test complete Warren content generation workflows with real dependencies
including database, vector search, conversation management, and content generation.

These tests ensure the entire Warren pipeline works correctly in realistic scenarios.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import patch, AsyncMock

from tests.fixtures import (
    db_session_with_test_data, 
    get_test_data,
    TEST_USER_REQUESTS,
    PERFORMANCE_TEST_SCENARIOS,
    ERROR_TEST_SCENARIOS
)
from src.services.warren import ContentGenerationOrchestrator
from src.models.refactored_database import ContentType


class TestWarrenEndToEndWorkflows:
    """
    Comprehensive integration tests for Warren service end-to-end workflows.
    Tests complete user request → content generation → response pipeline.
    """
    
    @pytest.fixture
    def warren_orchestrator(self):
        """Warren orchestrator with real dependencies for integration testing."""
        return ContentGenerationOrchestrator()
    
    @pytest.fixture
    def mock_external_services(self):
        """Mock external services (vector search, Claude) with realistic responses."""
        vector_data = get_test_data("vector_results")
        compliance_data = get_test_data("compliance_results")
        text_data = get_test_data("text_results")
        
        with patch('src.services.vector_search_service.vector_search_service') as mock_vector, \
             patch('src.services.claude_service.ClaudeService.generate_content') as mock_claude:
            
            # Setup vector search service responses
            mock_vector.check_readiness.return_value = {"ready": True}
            mock_vector.search_marketing_content.return_value = vector_data
            mock_vector.search_compliance_rules.return_value = compliance_data
            
            # Setup Claude service response
            mock_claude.return_value = "Here's your compliant financial content with proper disclaimers..."
            
            yield {
                'vector_search': mock_vector,
                'claude': mock_claude
            }
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_simple_content_generation_workflow(
        self, 
        warren_orchestrator: ContentGenerationOrchestrator,
        db_session_with_test_data,
        mock_external_services
    ):
        """
        Test complete workflow for simple content generation request.
        
        Workflow: User Request → Context Retrieval → Content Generation → Response
        """
        # Arrange
        test_request = {
            "user_request": "Create a LinkedIn post about retirement planning for young professionals",
            "content_type": "linkedin_post",
            "audience_type": "retail_investors"
        }
        
        # Act
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request=test_request["user_request"],
            content_type=test_request["content_type"], 
            audience_type=test_request["audience_type"]
        )
        
        # Assert - Verify complete workflow execution
        assert result is not None
        assert "content" in result
        assert "status" in result
        assert result["status"] == "success"
        
        # Verify content structure
        assert result["content"] is not None
        assert len(result["content"]) > 0
        
        # Verify context was properly retrieved
        assert "search_strategy" in result
        assert "marketing_examples_count" in result
        assert "compliance_rules_count" in result
        
        # Verify metadata tracking
        assert "content_type" in result
        assert result["content_type"] == "linkedin_post"
        assert "context_quality_score" in result
        
        # Verify external service calls were made
        mock_external_services['vector_search'].search_marketing_content.assert_called()
        mock_external_services['claude'].assert_called()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_context_workflow(
        self,
        warren_orchestrator: ContentGenerationOrchestrator, 
        db_session_with_test_data,
        mock_external_services
    ):
        """
        Test workflow with conversation context and session documents.
        
        Workflow: User Request + Context + Session Docs → Enhanced Context → Content
        """
        # Arrange
        conversation_history = get_test_data("conversation_history")
        session_documents = get_test_data("session_documents")
        
        test_request = {
            "user_request": "Based on our discussion and the uploaded demographics, create a newsletter about 401k planning",
            "content_type": "newsletter",
            "audience_type": "existing_clients",
            "conversation_history": conversation_history,
            "session_documents": session_documents
        }
        
        # Act
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request=test_request["user_request"],
            content_type=test_request["content_type"],
            audience_type=test_request["audience_type"],
            conversation_history=test_request["conversation_history"],
            session_documents=test_request["session_documents"]
        )
        
        # Assert - Verify conversation context integration
        assert result is not None
        assert "generated_content" in result
        assert "context_used" in result
        
        # Verify conversation context was included
        context = result["context_used"]
        assert "conversation_context" in context
        assert "session_documents" in context
        
        # Verify session documents were processed
        session_context = context["session_documents"]
        assert len(session_context) > 0
        assert any("client_demographics" in doc.get("content_summary", "") for doc in session_context)
        
        # Verify conversation history influenced the context
        conversation_context = context["conversation_context"]
        assert len(conversation_context) > 0
        assert any("retirement planning" in msg.get("content", "") for msg in conversation_context)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_vector_search_fallback_workflow(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        db_session_with_test_data,
        mock_external_services
    ):
        """
        Test fallback behavior when vector search fails.
        
        Workflow: User Request → Vector Search Failure → Text Search Fallback → Content
        """
        # Arrange - Setup vector search failure
        text_data = get_test_data("text_results")
        compliance_data = get_test_data("compliance_results")
        
        mock_external_services['vector_search'].check_readiness.return_value = {"ready": False}
        mock_external_services['vector_search'].search_marketing_content.side_effect = Exception("Vector search unavailable")
        
        with patch('src.services.warren_database_service.warren_db_service') as mock_warren_db:
            mock_warren_db.search_marketing_content.return_value = text_data
            mock_warren_db.get_disclaimers_for_content_type.return_value = compliance_data
            
            # Act
            result = await warren_orchestrator.generate_content_with_enhanced_context(
                user_request="Create investment guidance content",
                content_type="blog_post",
                audience_type="prospective_clients"
            )
        
        # Assert - Verify fallback behavior
        assert result is not None
        assert "generated_content" in result
        assert "context_used" in result
        
        # Verify fallback to text search occurred
        context = result["context_used"]
        assert context["search_strategy"] == "text_fallback"
        assert "marketing_examples" in context
        assert len(context["marketing_examples"]) > 0
        
        # Verify content was still generated despite vector search failure
        assert result["generated_content"] is not None
        assert len(result["generated_content"]) > 0
        
        # Verify fallback was logged in metadata
        metadata = result["metadata"]
        assert "fallback_used" in metadata
        assert metadata["fallback_used"] == True
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_content_quality_assessment_workflow(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        db_session_with_test_data,
        mock_external_services
    ):
        """
        Test content quality assessment throughout the workflow.
        
        Workflow: Request → Context Retrieval → Quality Assessment → Content Generation
        """
        # Test scenarios with different quality levels
        test_scenarios = [
            {
                "name": "high_quality_context",
                "vector_results": get_test_data("vector_results"),
                "expected_quality": "high"
            },
            {
                "name": "low_quality_context", 
                "vector_results": [],  # No results
                "expected_quality": "low"
            }
        ]
        
        for scenario in test_scenarios:
            # Arrange
            mock_external_services['vector_search'].search_marketing_content.return_value = scenario["vector_results"]
            
            # Act
            result = await warren_orchestrator.generate_content_with_enhanced_context(
                user_request="Create financial planning content",
                content_type="linkedin_post",
                audience_type="retail_investors"
            )
            
            # Assert
            assert result is not None
            assert "context_quality" in result["metadata"]
            
            quality_assessment = result["metadata"]["context_quality"]
            assert "score" in quality_assessment
            assert "sufficient" in quality_assessment
            assert "reason" in quality_assessment
            
            # Verify quality assessment aligns with expectations
            if scenario["expected_quality"] == "high":
                assert quality_assessment["sufficient"] == True
                assert quality_assessment["score"] > 0.5
            else:
                assert quality_assessment["sufficient"] == False
                assert quality_assessment["score"] <= 0.5
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_workflow_data_integrity(
        self,
        warren_orchestrator: ContentGenerationOrchestrator,
        db_session_with_test_data,
        mock_external_services
    ):
        """
        Test data integrity throughout the complete workflow.
        
        Verifies that data is properly passed between services and no corruption occurs.
        """
        # Act
        result = await warren_orchestrator.generate_content_with_enhanced_context(
            user_request="Create comprehensive retirement planning guide",
            content_type="blog_post",
            audience_type="retail_investors"
        )
        
        # Assert - Data integrity checks
        assert result is not None
        
        # Verify all expected data structures are present
        required_fields = ["generated_content", "context_used", "metadata"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify context data integrity
        context = result["context_used"]
        context_fields = ["marketing_examples", "disclaimers", "search_strategy"]
        for field in context_fields:
            assert field in context, f"Missing context field: {field}"
            
        # Verify metadata completeness
        metadata = result["metadata"]
        metadata_fields = ["generation_time", "content_type", "context_quality"]
        for field in metadata_fields:
            assert field in metadata, f"Missing metadata field: {field}"
            
        # Verify data types are correct
        assert isinstance(result["generated_content"], str)
        assert isinstance(context["marketing_examples"], list)
        assert isinstance(context["disclaimers"], list)
        assert isinstance(metadata["generation_time"], (int, float))
        
        # Verify no empty or null critical data
        assert len(result["generated_content"]) > 0
        assert result["generated_content"] is not None
        assert context["search_strategy"] is not None
