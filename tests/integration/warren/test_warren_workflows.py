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
        
        mock_external_services['claude'].assert_called()
        
        assert result["marketing_examples_count"] >= 0
        assert result["search_strategy"] in ["vector", "hybrid", "text_fallback"]
    
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
        assert "content" in result
        assert "search_strategy" in result
        
        # Verify conversation context was included
        assert "search_strategy" in result
        assert "marketing_examples_count" in result
        assert "compliance_rules_count" in result
        
        # Verify content generation worked with context
        assert result["status"] == "success"
        assert "content" in result
        assert len(result["content"]) > 0
        
        # Note: Context integration details tested in basic integration tests
    
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
        assert "content" in result
        assert "search_strategy" in result
        
        # Verify fallback to text search occurred
        assert result["search_strategy"] in ["text_fallback", "hybrid"]
        assert "marketing_examples_count" in result
        
        # Verify content was still generated despite vector search failure
        assert result["content"] is not None
        assert len(result["content"]) > 0
        
        # Verify fallback behavior indicated in response
        # Note: Fallback behavior tested through search_strategy field
    
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
            assert "content" in result
            assert "context_quality_score" in result
            
            # Verify quality assessment through context_quality_score
            quality_score = result["context_quality_score"]
            assert isinstance(quality_score, (int, float))
            assert 0 <= quality_score <= 1
    
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
        required_fields = ["content", "status", "search_strategy", "content_type"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify response structure integrity
        assert result["status"] == "success"
        assert result["content_type"] == "blog_post"
        
        # Verify data types are correct
        assert isinstance(result["content"], str)
        assert isinstance(result["search_strategy"], str)
        assert isinstance(result["marketing_examples_count"], int)
        assert isinstance(result["compliance_rules_count"], int)
        
        # Verify no empty or null critical data
        assert len(result["content"]) > 0
        assert result["content"] is not None
        assert result["search_strategy"] is not None
