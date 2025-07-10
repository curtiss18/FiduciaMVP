"""Tests for RequestTypeAnalyzer service."""

import pytest
from src.services.context_assembler.budget import RequestTypeAnalyzer
from src.services.context_assembler.models import RequestType


class TestRequestTypeAnalyzer:
    
    def setup_method(self):
        self.analyzer = RequestTypeAnalyzer()
    
    # Creation request tests
    def test_creation_keywords(self):
        creation_inputs = [
            "Create a LinkedIn post",
            "Write an email to clients",
            "Generate content for social media",
            "Draft a newsletter",
            "Compose a blog post",
            "Help me with a marketing message"
        ]
        
        for input_text in creation_inputs:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.CREATION, f"Failed for: {input_text}"
    
    def test_creation_case_insensitive(self):
        test_cases = [
            "CREATE A POST",
            "Write A Newsletter",
            "GENERATE content",
            "help me WITH this"
        ]
        
        for input_text in test_cases:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.CREATION
    
    # Refinement request tests
    def test_refinement_keywords(self):
        refinement_inputs = [
            "Edit this content",
            "Change the tone",
            "Modify the message",
            "Update this post",
            "Revise the draft",
            "Improve this text",
            "Make it more professional",
            "Adjust the language"
        ]
        
        for input_text in refinement_inputs:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.REFINEMENT, f"Failed for: {input_text}"
    
    def test_refinement_with_current_content(self):
        current_content = "Existing content to be refined"
        
        # Should return REFINEMENT even without keywords when current_content exists
        result = self.analyzer.analyze_request_type("Please help with this", current_content)
        assert result == RequestType.REFINEMENT
        
        # Should return REFINEMENT with keywords and current_content
        result = self.analyzer.analyze_request_type("Edit this content", current_content)
        assert result == RequestType.REFINEMENT
    
    def test_refinement_case_insensitive(self):
        test_cases = [
            "EDIT this content",
            "Change THE TONE",
            "make it BETTER",
            "ADJUST the style"
        ]
        
        for input_text in test_cases:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.REFINEMENT
    
    # Analysis request tests
    def test_analysis_keywords(self):
        analysis_inputs = [
            "Analyze this document",
            "Review the content",
            "Compare these options",
            "Evaluate the performance",
            "Assess the situation",
            "What do you think about this"
        ]
        
        for input_text in analysis_inputs:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.ANALYSIS, f"Failed for: {input_text}"
    
    def test_analysis_case_insensitive(self):
        test_cases = [
            "ANALYZE this document",
            "Review THE CONTENT",
            "WHAT DO YOU THINK",
            "evaluate THIS"
        ]
        
        for input_text in test_cases:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.ANALYSIS
    
    # Conversation request tests
    def test_conversation_fallback(self):
        conversation_inputs = [
            "Hello there",
            "How are you doing?",
            "Tell me about retirement planning",
            "What's the weather like?",
            "Random question without keywords"
        ]
        
        for input_text in conversation_inputs:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == RequestType.CONVERSATION, f"Failed for: {input_text}"
    
    # Priority order tests (refinement > analysis > creation > conversation)
    def test_keyword_priority_refinement_over_creation(self):
        # Refinement keywords should take priority over creation keywords
        result = self.analyzer.analyze_request_type("Edit and create a new post")
        assert result == RequestType.REFINEMENT
    
    def test_keyword_priority_refinement_over_analysis(self):
        # Refinement keywords should take priority over analysis keywords
        result = self.analyzer.analyze_request_type("Review and modify this content")
        assert result == RequestType.REFINEMENT
    
    def test_keyword_priority_analysis_over_creation(self):
        # Analysis keywords should take priority over creation keywords
        result = self.analyzer.analyze_request_type("Analyze and create a report")
        assert result == RequestType.ANALYSIS
    
    # Edge case tests
    def test_empty_input(self):
        result = self.analyzer.analyze_request_type("")
        assert result == RequestType.CONVERSATION
    
    def test_none_input(self):
        result = self.analyzer.analyze_request_type(None)
        assert result == RequestType.CONVERSATION
    
    def test_whitespace_only_input(self):
        result = self.analyzer.analyze_request_type("   \n\t   ")
        assert result == RequestType.CONVERSATION
    
    def test_very_long_input(self):
        long_input = "Please create a comprehensive marketing strategy " * 100
        result = self.analyzer.analyze_request_type(long_input)
        assert result == RequestType.CREATION
    
    def test_substring_keyword_matches(self):
        # Should match keywords as substrings (this is intended behavior)
        substring_matches = [
            ("I need to create something", RequestType.CREATION),  # contains "create"
            ("Please analyze this", RequestType.ANALYSIS),  # contains "analyze"  
            ("I will edit this", RequestType.REFINEMENT),  # contains "edit"
        ]
        
        for input_text, expected_type in substring_matches:
            result = self.analyzer.analyze_request_type(input_text)
            assert result == expected_type, f"Should match substring in: {input_text}"
    
    def test_keyword_at_word_boundaries(self):
        # Should match keywords at word boundaries
        matches = [
            "I need to edit this",
            "Please create something new",
            "Can you analyze the data",
        ]
        
        expected = [RequestType.REFINEMENT, RequestType.CREATION, RequestType.ANALYSIS]
        
        for input_text, expected_type in zip(matches, expected):
            result = self.analyzer.analyze_request_type(input_text)
            assert result == expected_type, f"Failed for: {input_text}"
    
    # Extract requirements tests
    def test_extract_requirements_basic(self):
        requirements = self.analyzer.extract_requirements("Create a LinkedIn post")
        
        assert requirements['request_type'] == RequestType.CREATION
        assert requirements['input_length'] == len("Create a LinkedIn post")
        assert requirements['has_keywords']['creation'] == True
        assert requirements['has_keywords']['refinement'] == False
        assert requirements['has_keywords']['analysis'] == False
    
    def test_extract_requirements_multiple_keywords(self):
        requirements = self.analyzer.extract_requirements("Create and analyze this content")
        
        assert requirements['request_type'] == RequestType.ANALYSIS  # Analysis has priority
        assert requirements['has_keywords']['creation'] == True
        assert requirements['has_keywords']['analysis'] == True
        assert requirements['has_keywords']['refinement'] == False
    
    def test_extract_requirements_empty_input(self):
        requirements = self.analyzer.extract_requirements("")
        
        assert requirements == {}
    
    def test_extract_requirements_none_input(self):
        requirements = self.analyzer.extract_requirements(None)
        
        assert requirements == {}
    
    # Real-world example tests
    def test_real_world_creation_examples(self):
        real_examples = [
            "Create a LinkedIn post about retirement planning for high-net-worth individuals",
            "Write an email newsletter highlighting our new ESG investment options",
            "Generate social media content about the benefits of working with a financial advisor",
            "Draft a blog post explaining the differences between traditional and Roth IRAs",
            "Help me with a client presentation about tax-loss harvesting strategies"
        ]
        
        for example in real_examples:
            result = self.analyzer.analyze_request_type(example)
            assert result == RequestType.CREATION, f"Failed for: {example}"
    
    def test_real_world_refinement_examples(self):
        real_examples = [
            "Edit this email to make it more professional and compliant",
            "Modify the tone of this newsletter to be more engaging",
            "Update this social media post to include the required disclaimers",
            "Revise this content to better target millennial investors",
            "Make it shorter and more impactful for Twitter"
        ]
        
        for example in real_examples:
            result = self.analyzer.analyze_request_type(example)
            assert result == RequestType.REFINEMENT, f"Failed for: {example}"
    
    def test_real_world_analysis_examples(self):
        real_examples = [
            "Analyze this market research document for key insights",
            "Review this compliance memo and summarize the main points",
            "Compare our investment performance against industry benchmarks",
            "Evaluate the effectiveness of this marketing campaign",
            "What do you think about the new SEC regulations on marketing?"
        ]
        
        for example in real_examples:
            result = self.analyzer.analyze_request_type(example)
            assert result == RequestType.ANALYSIS, f"Failed for: {example}"
