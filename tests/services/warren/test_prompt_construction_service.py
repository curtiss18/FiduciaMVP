"""
Tests for PromptConstructionService

Test Coverage:
- build_generation_prompt (advanced, standard, legacy types)
- build_refinement_prompt
- optimize_context_tokens 
- assemble_context_sections
- add_document_instructions
- add_youtube_context
- _extract_platform_from_content_type
- _build_advanced_generation_prompt
- _build_standard_generation_prompt
- _build_legacy_generation_prompt
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.prompt_construction_service import PromptConstructionService, PromptType


class TestPromptConstructionService:
    """Test suite for PromptConstructionService."""
    
    @pytest.fixture
    def service(self):
        """Create PromptConstructionService instance for testing."""
        return PromptConstructionService()
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "session_id": "test-session-123",
            "conversation_context": "Previous conversation about retirement planning...",
            "marketing_examples": [
                {
                    "id": "example_1",
                    "title": "Retirement Planning Post",
                    "content_text": "Planning for retirement requires careful consideration of various factors including risk tolerance, time horizon, and financial goals...",
                    "tags": "retirement, planning",
                    "similarity_score": 0.85
                },
                {
                    "id": "example_2",
                    "title": "Investment Strategy Newsletter", 
                    "content_text": "Diversification is a key component of any sound investment strategy, helping to manage risk while pursuing returns...",
                    "tags": "investment, strategy",
                    "similarity_score": 0.75
                }
            ],
            "disclaimers": [
                {
                    "id": "disclaimer_1",
                    "title": "Investment Risk Disclaimer",
                    "content_text": "Past performance does not guarantee future results. All investments carry risk of loss...",
                    "tags": "disclaimer, risk"
                },
                {
                    "id": "disclaimer_2",
                    "title": "General Financial Advice Disclaimer",
                    "content_text": "This content is for educational purposes only and should not be considered personalized investment advice...",
                    "tags": "disclaimer, educational"
                }
            ],
            "session_documents": [
                {"title": "Investment Philosophy", "summary": "Our investment approach..."},
                {"title": "Service Overview", "summary": "Services we provide..."}
            ],
            "youtube_context": {
                "metadata": {"url": "https://youtube.com/watch?v=test123"},
                "stats": {"word_count": 500},
                "transcript": "Welcome to today's video about retirement planning. In this video, we'll discuss the importance of starting early..."
            }
        }
    
    @pytest.fixture
    def mock_prompt_service(self):
        """Mock prompt service."""
        with patch('src.services.warren.prompt_construction_service.prompt_service') as mock:
            mock.get_warren_system_prompt.return_value = "System prompt for Warren..."
            mock.get_warren_refinement_prompt.return_value = "Refinement prompt for Warren..."
            yield mock
    
    @pytest.fixture
    def mock_advanced_context_assembler(self):
        """Mock AdvancedContextAssembler."""
        mock_assembler = AsyncMock()
        mock_assembler.build_warren_context.return_value = {
            "context": "Advanced assembled context with high-quality content...",
            "total_tokens": 1500,
            "request_type": "creation_mode",
            "optimization_applied": True,
            "context_breakdown": {"conversation": 200, "documents": 300, "examples": 500},
            "quality_metrics": {"overall_quality": 0.95, "avg_relevance": 0.88},
            "relevance_scores": {"high": 3, "medium": 2},
            "priority_scores": {"critical": 1, "important": 4}
        }
        return mock_assembler
    
    @pytest.fixture
    def mock_context_assembler(self):
        """Mock ContextAssembler."""
        mock_assembler = AsyncMock()
        mock_assembler.build_warren_context.return_value = {
            "context": "Standard assembled context with good content...",
            "total_tokens": 1200,
            "request_type": "creation_mode",
            "optimization_applied": False,
            "context_breakdown": {"conversation": 150, "documents": 250, "examples": 400}
        }
        return mock_assembler

    # Test build_generation_prompt method
    @pytest.mark.asyncio
    async def test_build_generation_prompt_advanced(self, service, sample_context_data, mock_prompt_service):
        """Test advanced generation prompt building."""
        with patch('src.services.warren.prompt_construction_service.AdvancedContextAssembler') as mock_class:
            with patch('src.services.warren.prompt_construction_service.AsyncSessionLocal') as mock_session:
                # Setup mocks
                mock_instance = AsyncMock()
                mock_class.return_value = mock_instance
                mock_instance.build_warren_context.return_value = {
                    "context": "Advanced context...",
                    "total_tokens": 1500,
                    "request_type": "creation_mode",
                    "optimization_applied": True,
                    "context_breakdown": {},
                    "quality_metrics": {},
                    "relevance_scores": {},
                    "priority_scores": {}
                }
                
                # Execute
                result = await service.build_generation_prompt(
                    context_data=sample_context_data,
                    user_request="Create a LinkedIn post about retirement planning",
                    content_type="linkedin_post",
                    audience_type="retail_investors",
                    prompt_type=PromptType.ADVANCED_GENERATION
                )
                
                # Verify
                assert isinstance(result, str)
                assert "Advanced context..." in result
                assert "retirement planning" not in result  # User request should not be in prompt
                assert "##MARKETINGCONTENT##" in result
                assert "uploaded documents" in result  # Should mention documents
                mock_prompt_service.get_warren_system_prompt.assert_called_once()
                mock_instance.build_warren_context.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_build_generation_prompt_standard(self, service, sample_context_data, mock_prompt_service):
        """Test standard generation prompt building."""
        with patch('src.services.warren.prompt_construction_service.ContextAssembler') as mock_class:
            with patch('src.services.warren.prompt_construction_service.AsyncSessionLocal') as mock_session:
                # Setup mocks
                mock_instance = AsyncMock()
                mock_class.return_value = mock_instance
                mock_instance.build_warren_context.return_value = {
                    "context": "Standard context...",
                    "total_tokens": 1200,
                    "optimization_applied": False
                }
                
                # Execute
                result = await service.build_generation_prompt(
                    context_data=sample_context_data,
                    user_request="Create email newsletter",
                    content_type="newsletter",
                    prompt_type=PromptType.STANDARD_GENERATION
                )
                
                # Verify
                assert isinstance(result, str)
                assert "Standard context..." in result
                assert "##MARKETINGCONTENT##" in result
                mock_prompt_service.get_warren_system_prompt.assert_called_once()
                mock_instance.build_warren_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_generation_prompt_legacy(self, service, sample_context_data, mock_prompt_service):
        """Test legacy generation prompt building."""
        # Execute
        result = await service.build_generation_prompt(
            context_data=sample_context_data,
            user_request="Create social media post",
            content_type="social_media",
            prompt_type=PromptType.LEGACY_GENERATION
        )
        
        # Verify
        assert isinstance(result, str)
        assert "CONVERSATION HISTORY:" in result
        assert "APPROVED SOCIAL_MEDIA EXAMPLES:" in result
        assert "REQUIRED DISCLAIMERS:" in result
        assert "VIDEO CONTEXT:" in result
        assert "##MARKETINGCONTENT##" in result
        mock_prompt_service.get_warren_system_prompt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_generation_prompt_invalid_type(self, service, sample_context_data):
        """Test generation prompt with invalid prompt type."""
        with pytest.raises(ValueError, match="Unknown prompt type"):
            await service.build_generation_prompt(
                context_data=sample_context_data,
                user_request="Test request",
                content_type="linkedin_post",
                prompt_type="invalid_type"
            )

    # Test build_refinement_prompt method
    @pytest.mark.asyncio
    async def test_build_refinement_prompt_with_conversation(self, service, sample_context_data, mock_prompt_service):
        """Test refinement prompt building with conversation context."""
        # Execute
        result = await service.build_refinement_prompt(
            current_content="Original content about investments...",
            refinement_request="Make it more engaging and add risk disclosures",
            context_data=sample_context_data,
            content_type="linkedin_post",
            audience_type="retail_investors"
        )
        
        # Verify
        assert isinstance(result, str)
        assert "CONVERSATION HISTORY:" in result
        assert "CURRENT CONTENT TO REFINE:" in result
        assert "Original content about investments..." in result
        assert "Make it more engaging and add risk disclosures" in result
        assert "##MARKETINGCONTENT##" in result
        mock_prompt_service.get_warren_refinement_prompt.assert_called_once()
        
        # Check refinement context structure
        call_args = mock_prompt_service.get_warren_refinement_prompt.call_args[0][0]
        assert call_args['current_content'] == "Original content about investments..."
        assert call_args['refinement_request'] == "Make it more engaging and add risk disclosures"
        assert call_args['platform'] == 'linkedin'
        assert call_args['content_type'] == 'linkedin_post'
        assert call_args['audience_type'] == 'retail_investors'
    
    @pytest.mark.asyncio
    async def test_build_refinement_prompt_no_conversation(self, service, mock_prompt_service):
        """Test refinement prompt building without conversation context."""
        context_data = {"session_id": "test-123"}  # No conversation_context
        
        # Execute
        result = await service.build_refinement_prompt(
            current_content="Some content",
            refinement_request="Improve this",
            context_data=context_data,
            content_type="email_template"
        )
        
        # Verify
        assert isinstance(result, str)
        assert "CONVERSATION HISTORY:" not in result
        assert "CURRENT CONTENT TO REFINE:" in result
        assert "Some content" in result
        assert "Improve this" in result

    # Test optimize_context_tokens method
    def test_optimize_context_tokens(self, service):
        """Test context token optimization."""
        context_parts = [
            "Section 1: Important compliance information...",
            "Section 2: Marketing examples and best practices...",
            "Section 3: Required disclaimers and risk disclosures..."
        ]
        max_tokens = 1000
        
        # Execute
        result = service.optimize_context_tokens(context_parts, max_tokens)
        
        # Verify (current implementation just returns as-is)
        assert result == context_parts
        assert len(result) == 3

    # Test assemble_context_sections method
    def test_assemble_context_sections_full_context(self, service, sample_context_data):
        """Test context section assembly with all types present."""
        # Execute
        result = service.assemble_context_sections(sample_context_data)
        
        # Verify
        assert isinstance(result, dict)
        assert "conversation_history" in result
        assert "marketing_examples" in result
        assert "disclaimers" in result
        
        # Check conversation section
        assert "## CONVERSATION HISTORY:" in result["conversation_history"]
        assert "Previous conversation about retirement planning..." in result["conversation_history"]
        
        # Check marketing examples section
        assert "## APPROVED" in result["marketing_examples"]
        assert "Retirement Planning Post" in result["marketing_examples"]
        assert "(relevance: 0.85)" in result["marketing_examples"]
        assert "Investment Strategy Newsletter" in result["marketing_examples"]
        assert "(relevance: 0.75)" in result["marketing_examples"]
        
        # Check disclaimers section
        assert "## REQUIRED DISCLAIMERS:" in result["disclaimers"]
        assert "Investment Risk Disclaimer" in result["disclaimers"]
        assert "Past performance does not guarantee" in result["disclaimers"]
    
    def test_assemble_context_sections_minimal_context(self, service):
        """Test context section assembly with minimal data."""
        context_data = {"session_id": "test-123"}
        
        # Execute
        result = service.assemble_context_sections(context_data)
        
        # Verify
        assert isinstance(result, dict)
        assert len(result) == 0  # No sections should be created

    # Test add_document_instructions method
    def test_add_document_instructions_with_documents(self, service, sample_context_data):
        """Test document instruction generation with documents present."""
        # Execute
        result = service.add_document_instructions(sample_context_data)
        
        # Verify
        assert isinstance(result, str)
        assert "IMPORTANT: You have access to the following uploaded documents" in result
        assert "Investment Philosophy" in result
        assert "Service Overview" in result
        assert "Please reference and incorporate information" in result
    
    def test_add_document_instructions_no_documents(self, service):
        """Test document instruction generation with no documents."""
        context_data = {"session_id": "test-123"}
        
        # Execute
        result = service.add_document_instructions(context_data)
        
        # Verify
        assert result == ""

    # Test add_youtube_context method
    def test_add_youtube_context_full_transcript(self, service):
        """Test YouTube context addition with full transcript."""
        context_parts = ["Existing context..."]
        original_length = len(context_parts)
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test123"},
            "stats": {"word_count": 300},
            "transcript": "Short transcript content about financial planning."
        }
        
        # Execute
        result = service.add_youtube_context(context_parts, youtube_context)
        
        # Verify - the method modifies the list in place and returns it
        assert result is context_parts  # Same object reference
        assert len(result) > original_length  # More items than we started with
        joined_result = "\n".join(result)
        assert "## VIDEO CONTEXT:" in joined_result
        assert "https://youtube.com/watch?v=test123" in joined_result
        assert "~300 words" in joined_result
        assert "Short transcript content about financial planning." in joined_result
        assert "**IMPORTANT**: You have been provided with the actual video transcript" in joined_result
    
    def test_add_youtube_context_long_transcript(self, service):
        """Test YouTube context addition with long transcript that gets truncated."""
        context_parts = ["Existing context..."]
        original_length = len(context_parts)
        long_transcript = "Very long transcript content. " * 200  # Make it longer than max_transcript_length
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test456"},
            "stats": {"word_count": 2000},
            "transcript": long_transcript
        }
        
        # Execute
        result = service.add_youtube_context(context_parts, youtube_context)
        
        # Verify
        assert result is context_parts  # Same object reference
        assert len(result) > original_length  # More items added
        joined_result = "\n".join(result)
        assert "## VIDEO CONTEXT:" in joined_result
        assert "preview of the full" in joined_result
        assert len(joined_result) < len(long_transcript) + 1000  # Should be truncated
    
    def test_add_youtube_context_no_transcript(self, service):
        """Test YouTube context addition with no transcript."""
        context_parts = ["Existing context..."]
        original_length = len(context_parts)
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test789"},
            "stats": {"word_count": 0},
            "transcript": ""
        }
        
        # Execute
        result = service.add_youtube_context(context_parts, youtube_context)
        
        # Verify
        assert result is context_parts  # Same object reference
        assert len(result) > original_length  # Items should still be added even without transcript
        joined_result = "\n".join(result)
        assert "## VIDEO CONTEXT:" in joined_result
        assert "No transcript found" not in joined_result  # Warning is logged, not added to context
        assert "**IMPORTANT**: You have been provided" in joined_result  # Still adds the instruction
    
    def test_add_youtube_context_none(self, service):
        """Test YouTube context addition with None context."""
        context_parts = ["Existing context..."]
        
        # Execute
        result = service.add_youtube_context(context_parts, None)
        
        # Verify
        assert result == context_parts  # Should return unchanged

    # Test _extract_platform_from_content_type method
    def test_extract_platform_from_content_type_known_platforms(self, service):
        """Test platform extraction for known content types."""
        test_cases = [
            ('linkedin_post', 'linkedin'),
            ('email_template', 'email'),
            ('website_content', 'website'),
            ('newsletter', 'newsletter'),
            ('social_media', 'twitter'),
            ('blog_post', 'website'),
            ('LINKEDIN_POST', 'linkedin'),  # Test case insensitive
        ]
        
        for content_type, expected_platform in test_cases:
            result = service._extract_platform_from_content_type(content_type)
            assert result == expected_platform
    
    def test_extract_platform_from_content_type_unknown(self, service):
        """Test platform extraction for unknown content types."""
        result = service._extract_platform_from_content_type("unknown_type")
        assert result == "general"

    # Test integration scenarios
    @pytest.mark.asyncio
    async def test_end_to_end_generation_workflow(self, service, sample_context_data, mock_prompt_service):
        """Test complete generation workflow from context to final prompt."""
        # Test legacy generation (doesn't require mocking assemblers)
        result = await service.build_generation_prompt(
            context_data=sample_context_data,
            user_request="Create comprehensive retirement planning guide",
            content_type="website_content",
            audience_type="high_net_worth",
            prompt_type=PromptType.LEGACY_GENERATION
        )
        
        # Verify complete prompt structure
        assert isinstance(result, str)
        assert len(result) > 1000  # Should be substantial
        assert "CONVERSATION HISTORY:" in result
        assert "APPROVED WEBSITE_CONTENT EXAMPLES:" in result
        assert "REQUIRED DISCLAIMERS:" in result
        assert "VIDEO CONTEXT:" in result
        assert "USER REQUEST: Create comprehensive retirement planning guide" in result
        assert "CONTENT TYPE: website_content" in result
        assert "TARGET AUDIENCE: high_net_worth" in result
        assert "##MARKETINGCONTENT##" in result
        
        # Verify compliance requirements are included
        assert "SEC Marketing Rule" in result
        assert "FINRA 2210" in result
        assert "educational tone" in result
        assert "performance predictions" in result

    @pytest.mark.asyncio
    async def test_refinement_workflow_comprehensive(self, service, sample_context_data, mock_prompt_service):
        """Test complete refinement workflow."""
        current_content = """
        Retirement planning is important for everyone. Start saving early and invest wisely.
        Consider working with a financial advisor to create a personalized strategy.
        """
        
        refinement_request = "Add more specific examples and include required risk disclosures"
        
        # Execute
        result = await service.build_refinement_prompt(
            current_content=current_content,
            refinement_request=refinement_request,
            context_data=sample_context_data,
            content_type="linkedin_post",
            audience_type="millennials"
        )
        
        # Verify complete refinement structure
        assert isinstance(result, str)
        assert current_content.strip() in result
        assert refinement_request in result
        assert "CONVERSATION HISTORY:" in result
        assert "REFINEMENT CONTEXT:" in result
        assert "##MARKETINGCONTENT##" in result
        assert "SEC/FINRA compliance" in result

    # Test error handling
    @pytest.mark.asyncio
    async def test_advanced_generation_assembler_failure(self, service, sample_context_data, mock_prompt_service):
        """Test handling of AdvancedContextAssembler failure."""
        with patch('src.services.warren.prompt_construction_service.AdvancedContextAssembler') as mock_class:
            with patch('src.services.warren.prompt_construction_service.AsyncSessionLocal') as mock_session:
                # Setup mock to raise exception
                mock_instance = AsyncMock()
                mock_class.return_value = mock_instance
                mock_instance.build_warren_context.side_effect = Exception("Assembler failed")
                
                # Execute and verify exception is raised
                with pytest.raises(Exception, match="Assembler failed"):
                    await service.build_generation_prompt(
                        context_data=sample_context_data,
                        user_request="Test request",
                        content_type="linkedin_post",
                        prompt_type=PromptType.ADVANCED_GENERATION
                    )

    @pytest.mark.asyncio
    async def test_standard_generation_assembler_failure(self, service, sample_context_data, mock_prompt_service):
        """Test handling of ContextAssembler failure."""
        with patch('src.services.warren.prompt_construction_service.ContextAssembler') as mock_class:
            with patch('src.services.warren.prompt_construction_service.AsyncSessionLocal') as mock_session:
                # Setup mock to raise exception
                mock_instance = AsyncMock()
                mock_class.return_value = mock_instance  
                mock_instance.build_warren_context.side_effect = Exception("Standard assembler failed")
                
                # Execute and verify exception is raised
                with pytest.raises(Exception, match="Standard assembler failed"):
                    await service.build_generation_prompt(
                        context_data=sample_context_data,
                        user_request="Test request",
                        content_type="email_template",
                        prompt_type=PromptType.STANDARD_GENERATION
                    )
