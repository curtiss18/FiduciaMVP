"""
Tests for Individual Content Generation Strategies

Test Coverage:
- AdvancedGenerationStrategy implementation
- StandardGenerationStrategy implementation  
- LegacyGenerationStrategy implementation
- Strategy-specific behavior and error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.warren.strategies import (
    AdvancedGenerationStrategy,
    StandardGenerationStrategy,
    LegacyGenerationStrategy,
    GenerationResult
)


class TestAdvancedGenerationStrategy:
    """Test AdvancedGenerationStrategy implementation."""
    
    @pytest.fixture
    def strategy(self):
        """Create AdvancedGenerationStrategy instance for testing."""
        return AdvancedGenerationStrategy()
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "session_id": "test-session-123",
            "marketing_examples": [
                {"title": "Example 1", "content_text": "Sample content..."}
            ],
            "disclaimers": [
                {"title": "Risk Disclaimer", "content_text": "Past performance..."}
            ],
            "conversation_context": "Previous conversation...",
            "session_documents": [
                {"title": "Investment Philosophy", "summary": "Our approach..."}
            ]
        }
    
    def test_strategy_properties(self, strategy):
        """Test strategy basic properties."""
        assert strategy.get_strategy_name() == "advanced"
        assert strategy.get_strategy_priority() == 10
        assert strategy.requires_advanced_context() is True
    
    def test_can_handle_rich_context(self, strategy, sample_context_data):
        """Test can_handle with rich context data."""
        assert strategy.can_handle(sample_context_data) is True
    
    def test_can_handle_minimal_context(self, strategy):
        """Test can_handle with minimal context."""
        minimal_context = {"session_id": "test-123"}
        assert strategy.can_handle(minimal_context) is False
    
    def test_can_handle_exception(self, strategy):
        """Test can_handle with invalid context causing exception."""
        invalid_context = {"marketing_examples": "not_a_list"}
        
        # Should handle exceptions gracefully
        result = strategy.can_handle(invalid_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, strategy, sample_context_data):
        """Test successful content generation."""
        with patch('src.services.warren.strategies.advanced_generation_strategy.BasicContextAssemblyOrchestrator') as mock_assembler_class:
            with patch('src.services.warren.strategies.advanced_generation_strategy.AsyncSessionLocal'):
                with patch('src.services.warren.strategies.advanced_generation_strategy.prompt_service') as mock_prompt:
                    with patch('src.services.warren.strategies.advanced_generation_strategy.claude_service') as mock_claude:
                        
                        # Setup mocks
                        mock_assembler = AsyncMock()
                        mock_assembler_class.return_value = mock_assembler
                        mock_assembler.build_warren_context.return_value = {
                            "context": "Advanced assembled context...",
                            "total_tokens": 1500,
                            "request_type": "creation_mode",
                            "optimization_applied": True,
                            "context_breakdown": {"documents": 300, "examples": 500},
                            "quality_metrics": {"overall_quality": 0.95},
                            "relevance_scores": {"high": 3},
                            "priority_scores": {"critical": 1}
                        }
                        
                        mock_prompt.get_warren_system_prompt.return_value = "System prompt..."
                        mock_claude.generate_content = AsyncMock(return_value="Generated compliant content...")
                        
                        # Execute
                        result = await strategy.generate_content(
                            context_data=sample_context_data,
                            user_request="Create LinkedIn post about retirement planning",
                            content_type="linkedin_post",
                            audience_type="retail_investors"
                        )
                        
                        # Verify
                        assert isinstance(result, GenerationResult)
                        assert result.success is True
                        assert result.content == "Generated compliant content..."
                        assert result.strategy_used == "advanced"
                        assert result.error_message is None
                        assert "assembly_result" in result.metadata
                        assert "token_management" in result.metadata
                        assert result.metadata["phase"] == "Phase_2_Advanced"
                        assert result.generation_time > 0
                        
                        # Verify mock calls
                        mock_assembler.build_warren_context.assert_called_once()
                        mock_prompt.get_warren_system_prompt.assert_called_once()
                        mock_claude.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_content_refinement(self, strategy, sample_context_data):
        """Test content generation for refinement scenario."""
        with patch('src.services.warren.strategies.advanced_generation_strategy.BasicContextAssemblyOrchestrator') as mock_assembler_class:
            with patch('src.services.warren.strategies.advanced_generation_strategy.AsyncSessionLocal'):
                with patch('src.services.warren.strategies.advanced_generation_strategy.prompt_service') as mock_prompt:
                    with patch('src.services.warren.strategies.advanced_generation_strategy.claude_service') as mock_claude:
                        
                        # Setup mocks for refinement
                        mock_assembler = AsyncMock()
                        mock_assembler_class.return_value = mock_assembler
                        mock_assembler.build_warren_context.return_value = {
                            "context": "Context for refinement...",
                            "total_tokens": 1200,
                            "request_type": "refinement_mode",
                            "optimization_applied": True,
                            "context_breakdown": {},
                            "quality_metrics": {},
                            "relevance_scores": {},
                            "priority_scores": {}
                        }
                        
                        mock_prompt.get_warren_refinement_prompt.return_value = "Refinement prompt..."
                        mock_claude.generate_content = AsyncMock(return_value="Refined content...")
                        
                        # Execute
                        result = await strategy.generate_content(
                            context_data=sample_context_data,
                            user_request="Make it more engaging",
                            content_type="email_template",
                            current_content="Original content...",
                            is_refinement=True
                        )
                        
                        # Verify
                        assert result.success is True
                        assert result.content == "Refined content..."
                        
                        # Verify refinement prompt was used
                        mock_prompt.get_warren_refinement_prompt.assert_called_once()
                        mock_prompt.get_warren_system_prompt.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_content_failure(self, strategy, sample_context_data):
        """Test content generation failure handling."""
        with patch('src.services.warren.strategies.advanced_generation_strategy.BasicContextAssemblyOrchestrator') as mock_assembler_class:
            with patch('src.services.warren.strategies.advanced_generation_strategy.AsyncSessionLocal'):
                
                # Setup mock to raise exception
                mock_assembler_class.side_effect = Exception("Context assembler failed")
                
                # Execute
                result = await strategy.generate_content(
                    context_data=sample_context_data,
                    user_request="Test request",
                    content_type="linkedin_post"
                )
                
                # Verify
                assert isinstance(result, GenerationResult)
                assert result.success is False
                assert result.content is None
                assert result.strategy_used == "advanced"
                assert "Context assembler failed" in result.error_message
                assert result.metadata["error_type"] == "advanced_generation_failure"
                assert result.generation_time > 0


class TestStandardGenerationStrategy:
    """Test StandardGenerationStrategy implementation."""
    
    @pytest.fixture
    def strategy(self):
        """Create StandardGenerationStrategy instance for testing."""
        return StandardGenerationStrategy()
    
    @pytest.fixture  
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "session_id": "test-session-456",
            "marketing_examples": [
                {"title": "Example", "content_text": "Content..."}
            ]
        }
    
    def test_strategy_properties(self, strategy):
        """Test strategy basic properties."""
        assert strategy.get_strategy_name() == "standard"
        assert strategy.get_strategy_priority() == 50
        assert strategy.requires_advanced_context() is False
    
    def test_can_handle_any_context(self, strategy):
        """Test can_handle - standard strategy handles any context."""
        contexts = [
            {"rich": "context"},
            {"minimal": True},
            {},
            {"session_id": "test"}
        ]
        
        for context in contexts:
            assert strategy.can_handle(context) is True
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, strategy, sample_context_data):
        """Test successful content generation."""
        with patch('src.services.warren.strategies.standard_generation_strategy.BasicContextAssemblyOrchestrator') as mock_assembler_class:
            with patch('src.services.warren.strategies.standard_generation_strategy.AsyncSessionLocal'):
                with patch('src.services.warren.strategies.standard_generation_strategy.prompt_service') as mock_prompt:
                    with patch('src.services.warren.strategies.standard_generation_strategy.claude_service') as mock_claude:
                        
                        # Setup mocks
                        mock_assembler = AsyncMock()
                        mock_assembler_class.return_value = mock_assembler
                        mock_assembler.build_warren_context.return_value = {
                            "context": "Standard assembled context...",
                            "total_tokens": 1000,
                            "optimization_applied": False
                        }
                        
                        mock_prompt.get_warren_system_prompt.return_value = "System prompt..."
                        mock_claude.generate_content = AsyncMock(return_value="Generated content...")
                        
                        # Execute
                        result = await strategy.generate_content(
                            context_data=sample_context_data,
                            user_request="Create newsletter",
                            content_type="newsletter"
                        )
                        
                        # Verify
                        assert result.success is True
                        assert result.content == "Generated content..."
                        assert result.strategy_used == "standard"
                        assert result.metadata["phase"] == "Phase_1_Standard"


class TestLegacyGenerationStrategy:
    """Test LegacyGenerationStrategy implementation."""
    
    @pytest.fixture
    def strategy(self):
        """Create LegacyGenerationStrategy instance for testing."""
        return LegacyGenerationStrategy()
    
    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "conversation_context": "Previous conversation...",
            "marketing_examples": [
                {
                    "title": "Retirement Post",
                    "content_text": "Planning for retirement is important...",
                    "tags": "retirement",
                    "similarity_score": 0.85
                }
            ],
            "disclaimers": [
                {
                    "title": "Risk Disclaimer", 
                    "content_text": "Past performance does not guarantee future results..."
                }
            ]
        }
    
    def test_strategy_properties(self, strategy):
        """Test strategy basic properties."""
        assert strategy.get_strategy_name() == "legacy"
        assert strategy.get_strategy_priority() == 100
        assert strategy.requires_advanced_context() is False
        assert strategy.max_transcript_length == 4000
    
    def test_can_handle_always_true(self, strategy):
        """Test can_handle - legacy strategy always handles any context."""
        contexts = [
            {"complex": "context"},
            {},
            {"error": "scenario"},
            {"session_id": "test"}
        ]
        
        for context in contexts:
            assert strategy.can_handle(context) is True
    
    @pytest.mark.asyncio
    async def test_generate_content_new_content(self, strategy, sample_context_data):
        """Test new content generation (not refinement)."""
        with patch('src.services.warren.strategies.legacy_generation_strategy.prompt_service') as mock_prompt:
            with patch('src.services.warren.strategies.legacy_generation_strategy.claude_service') as mock_claude:
                
                mock_prompt.get_warren_system_prompt.return_value = "System prompt..."
                mock_claude.generate_content = AsyncMock(return_value="Legacy generated content...")
                
                # Execute
                result = await strategy.generate_content(
                    context_data=sample_context_data,
                    user_request="Create social media post",
                    content_type="social_media"
                )
                
                # Verify
                assert result.success is True
                assert result.content == "Legacy generated content..."
                assert result.strategy_used == "legacy"
                assert result.metadata["phase"] == "Legacy_Fallback"
                assert result.metadata["context_building"] == "manual"
                assert result.metadata["refinement"] is False
    
    @pytest.mark.asyncio
    async def test_generate_content_refinement(self, strategy, sample_context_data):
        """Test refinement content generation."""
        with patch('src.services.warren.strategies.legacy_generation_strategy.prompt_service') as mock_prompt:
            with patch('src.services.warren.strategies.legacy_generation_strategy.claude_service') as mock_claude:
                
                mock_prompt.get_warren_refinement_prompt.return_value = "Refinement prompt..."
                mock_claude.generate_content = AsyncMock(return_value="Refined legacy content...")
                
                # Execute
                result = await strategy.generate_content(
                    context_data=sample_context_data,
                    user_request="Make it more engaging",
                    content_type="website_content",
                    current_content="Original website content...",
                    is_refinement=True
                )
                
                # Verify
                assert result.success is True
                assert result.content == "Refined legacy content..."
                assert result.strategy_used == "legacy"
                assert result.metadata["refinement"] is True
                
                # Verify refinement prompt was used
                mock_prompt.get_warren_refinement_prompt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_content_with_youtube(self, strategy, sample_context_data):
        """Test content generation with YouTube context."""
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test123"},
            "stats": {"word_count": 300},
            "transcript": "YouTube transcript about financial planning..."
        }
        
        sample_context_data["youtube_context"] = youtube_context
        
        with patch('src.services.warren.strategies.legacy_generation_strategy.prompt_service') as mock_prompt:
            with patch('src.services.warren.strategies.legacy_generation_strategy.claude_service') as mock_claude:
                
                mock_prompt.get_warren_system_prompt.return_value = "System prompt..."
                mock_claude.generate_content = AsyncMock(return_value="Content with YouTube context...")
                
                # Execute
                result = await strategy.generate_content(
                    context_data=sample_context_data,
                    user_request="Create blog post based on video",
                    content_type="blog_post",
                    youtube_context=youtube_context
                )
                
                # Verify
                assert result.success is True
                assert result.content == "Content with YouTube context..."
                
                # Verify YouTube context was included in prompt
                generated_prompt = mock_claude.generate_content.call_args[0][0]
                assert "VIDEO CONTEXT:" in generated_prompt
                assert "youtube.com/watch?v=test123" in generated_prompt
                assert "financial planning" in generated_prompt
    
    @pytest.mark.asyncio
    async def test_generate_content_failure(self, strategy, sample_context_data):
        """Test content generation failure handling."""
        with patch('src.services.warren.strategies.legacy_generation_strategy.prompt_service') as mock_prompt:
            with patch('src.services.warren.strategies.legacy_generation_strategy.claude_service') as mock_claude:
                
                # Setup mock to raise exception
                mock_claude.generate_content.side_effect = Exception("Claude service failed")
                mock_prompt.get_warren_system_prompt.return_value = "System prompt..."
                
                # Execute
                result = await strategy.generate_content(
                    context_data=sample_context_data,
                    user_request="Test request",
                    content_type="linkedin_post"
                )
                
                # Verify
                assert result.success is False
                assert result.content is None
                assert result.strategy_used == "legacy"
                assert "Claude service failed" in result.error_message
                assert result.metadata["error_type"] == "legacy_generation_failure"
                assert result.generation_time > 0
    
    def test_add_youtube_context_full_transcript(self, strategy):
        """Test YouTube context addition with full transcript."""
        context_parts = ["Existing context..."]
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test456"},
            "stats": {"word_count": 250},
            "transcript": "Short transcript about investments and financial planning strategies."
        }
        
        result = strategy._add_youtube_context(context_parts, youtube_context)
        
        joined_result = "\n".join(result)
        assert "## VIDEO CONTEXT:" in joined_result
        assert "youtube.com/watch?v=test456" in joined_result
        assert "~250 words" in joined_result
        assert "financial planning strategies" in joined_result
        assert "**IMPORTANT**: You have been provided" in joined_result
    
    def test_add_youtube_context_long_transcript(self, strategy):
        """Test YouTube context with transcript that gets truncated."""
        context_parts = ["Existing context..."]
        long_transcript = "Very long transcript content. " * 200  # Make it longer than max_transcript_length
        youtube_context = {
            "metadata": {"url": "https://youtube.com/watch?v=test789"},
            "stats": {"word_count": 2000},
            "transcript": long_transcript
        }
        
        result = strategy._add_youtube_context(context_parts, youtube_context)
        
        joined_result = "\n".join(result)
        assert "## VIDEO CONTEXT:" in joined_result
        assert "preview of the full" in joined_result
        assert len(joined_result) < len(long_transcript) + 1000  # Should be truncated


class TestStrategiesComparison:
    """Test comparative behavior between strategies."""
    
    @pytest.fixture
    def all_strategies(self):
        """Create instances of all strategies."""
        return {
            "advanced": AdvancedGenerationStrategy(),
            "standard": StandardGenerationStrategy(), 
            "legacy": LegacyGenerationStrategy()
        }
    
    def test_priority_ordering(self, all_strategies):
        """Test that strategy priorities are properly ordered."""
        priorities = {name: strategy.get_strategy_priority() for name, strategy in all_strategies.items()}
        
        assert priorities["advanced"] < priorities["standard"] < priorities["legacy"]
        assert priorities["advanced"] == 10
        assert priorities["standard"] == 50
        assert priorities["legacy"] == 100
    
    def test_platform_extraction_consistency(self, all_strategies):
        """Test that all strategies extract platforms consistently."""
        test_content_types = ["linkedin_post", "email_template", "website_content", "unknown_type"]
        
        # Get platform mappings from each strategy
        for content_type in test_content_types:
            platforms = {}
            for name, strategy in all_strategies.items():
                platforms[name] = strategy._extract_platform_from_content_type(content_type)
            
            # All strategies should return the same platform for the same content type
            unique_platforms = set(platforms.values())
            assert len(unique_platforms) == 1, f"Inconsistent platforms for {content_type}: {platforms}"
    
    def test_strategy_names_unique(self, all_strategies):
        """Test that all strategy names are unique."""
        names = [strategy.get_strategy_name() for strategy in all_strategies.values()]
        assert len(names) == len(set(names))
        assert set(names) == {"advanced", "standard", "legacy"}
    
    def test_advanced_context_requirements(self, all_strategies):
        """Test advanced context requirements are set correctly."""
        assert all_strategies["advanced"].requires_advanced_context() is True
        assert all_strategies["standard"].requires_advanced_context() is False
        assert all_strategies["legacy"].requires_advanced_context() is False

