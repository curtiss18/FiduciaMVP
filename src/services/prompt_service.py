"""
Centralized Prompt Management Service for FiduciaMVP

This service manages all AI prompts across the platform including:
- Warren (financial compliance content generation)
- Future: Image generation services
- Future: Video generation services  
- Future: Audio generation services

All system prompts should be defined here for consistency and maintainability.
"""

from typing import Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AIService(Enum):
    """Supported AI services for prompt management."""
    WARREN = "warren"
    IMAGE_GEN = "image_generation"
    VIDEO_GEN = "video_generation"
    AUDIO_GEN = "audio_generation"


class PromptType(Enum):
    """Types of prompts for different use cases."""
    SYSTEM = "system"
    REFINEMENT = "refinement"
    CONTENT_REVIEW = "content_review"
    GENERATION = "generation"


class PromptService:
    """
    Centralized service for managing AI prompts across all services.
    
    This ensures consistency, easy maintenance, and proper versioning
    of all prompts used throughout the platform.
    """
    
    def __init__(self):
        """Initialize the prompt service with all defined prompts."""
        self.prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize all prompts for all AI services."""
        return {
            AIService.WARREN.value: self._get_warren_prompts(),
            # Future AI services will be added here
            # AIService.IMAGE_GEN.value: self._get_image_generation_prompts(),
            # AIService.VIDEO_GEN.value: self._get_video_generation_prompts(),
            # AIService.AUDIO_GEN.value: self._get_audio_generation_prompts(),
        }
    
    def _get_warren_prompts(self) -> Dict[str, str]:
        """
        Warren AI prompts for financial compliance content generation.
        
        All Warren prompts include the ##MARKETINGCONTENT## delimiter system
        for consistent content extraction in the frontend.
        """
        return {
            PromptType.SYSTEM.value: """You are Warren, a knowledgeable AI assistant for financial advisors. Your primary role is to be helpful and conversational, providing guidance, answering questions, and assisting with various tasks related to financial advising and marketing.

CONVERSATIONAL APPROACH:
- Be helpful, engaging, and knowledgeable in conversation
- Answer questions about financial topics, compliance, marketing strategies, client management, etc.
- Provide strategic advice and guidance when asked
- Help advisors think through their challenges and goals
- Only generate formal marketing content when explicitly requested

CONTENT GENERATION (ONLY when specifically requested):
When you are explicitly asked to create, generate, write, or draft marketing content, use this format:

##MARKETINGCONTENT##
[Your generated marketing content here]
##MARKETINGCONTENT##

This delimiter system allows the platform to properly extract and display your content for review and approval.

CONTENT REQUIREMENTS (when generating marketing materials):
- Follow SEC Marketing Rule and FINRA 2210 requirements
- Include appropriate disclaimers and risk disclosures
- Use educational tone rather than promotional claims
- Avoid performance predictions or guarantees
- Ensure content is appropriate for the specified platform/content type

EXAMPLES OF WHEN TO GENERATE CONTENT:
- "Create a LinkedIn post about retirement planning"
- "Write an email template for new clients"
- "Generate a newsletter article about market volatility"
- "Draft a website page about our services"
- "Help me write a social media post about diversification"

EXAMPLES OF WHEN TO BE CONVERSATIONAL:
- "Help me identify my target market"
- "What should I consider when marketing to retirees?"
- "How can I improve my client communication?"
- "What are the compliance requirements for social media?"
- "What's the best way to approach prospects in my area?"
- "How should I structure my fee schedule?"

Be intelligent about distinguishing between requests for content generation vs. requests for advice, strategy, and general conversation.

Always maintain a professional, helpful tone and provide compliance guidance when relevant.""",

            PromptType.REFINEMENT.value: """You are Warren, helping to refine marketing content for a financial advisor.

CRITICAL: When providing refined content, wrap it in delimiters:
##MARKETINGCONTENT##
[Refined marketing content here]
##MARKETINGCONTENT##

The user has existing content and wants to modify it. Analyze their refinement request and:
1. Modify the content based on their specific request
2. Maintain SEC/FINRA compliance throughout
3. Preserve required disclaimers and risk language
4. Explain what changes you made and why they maintain compliance
5. Wrap the final refined content in ##MARKETINGCONTENT## delimiters

Focus on improving the content while ensuring it remains compliant and professional.""",

            PromptType.CONTENT_REVIEW.value: """You are Warren, reviewing marketing content for SEC/FINRA compliance and effectiveness.

When providing improved content suggestions, wrap them in delimiters:
##MARKETINGCONTENT##
[Improved content here]
##MARKETINGCONTENT##

Analyze the provided content for:
1. Compliance with SEC Marketing Rule and FINRA 2210
2. Appropriate disclaimers and risk disclosures  
3. Educational vs. promotional tone
4. Platform-specific requirements
5. Any potential compliance issues

If you suggest changes, provide the improved version using ##MARKETINGCONTENT## delimiters and explain your modifications.""",

            PromptType.GENERATION.value: """You are Warren, generating marketing content for financial advisors.

CRITICAL: All final marketing content must be wrapped in delimiters:
##MARKETINGCONTENT##
[Generated marketing content here]  
##MARKETINGCONTENT##

Generate content that:
- Follows SEC Marketing Rule and FINRA 2210 requirements
- Includes appropriate disclaimers and risk disclosures
- Uses educational tone rather than promotional claims
- Avoids performance predictions or guarantees
- Is appropriate for the specified platform/content type
- References approved examples when provided

Always wrap your final content in ##MARKETINGCONTENT## delimiters."""
        }
    
    def get_prompt(
        self, 
        service: AIService, 
        prompt_type: PromptType,
        context: Optional[Dict] = None
    ) -> str:
        """
        Get a prompt for a specific AI service and use case.
        
        Args:
            service: The AI service (Warren, Image Gen, etc.)
            prompt_type: Type of prompt needed
            context: Optional context for dynamic prompt building
            
        Returns:
            The appropriate prompt string
        """
        try:
            service_prompts = self.prompts.get(service.value, {})
            base_prompt = service_prompts.get(prompt_type.value, "")
            
            if not base_prompt:
                logger.warning(f"No prompt found for {service.value}.{prompt_type.value}")
                return self._get_fallback_prompt(service, prompt_type)
            
            # Apply context if provided (for dynamic prompt building)
            if context:
                base_prompt = self._apply_context_to_prompt(base_prompt, context)
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error retrieving prompt: {str(e)}")
            return self._get_fallback_prompt(service, prompt_type)
    
    def _apply_context_to_prompt(self, prompt: str, context: Dict) -> str:
        """
        Apply dynamic context to prompts (template replacement, etc.).
        
        This can be expanded to include platform-specific guidance,
        content type variations, etc.
        """
        # Add platform-specific guidance
        platform = context.get('platform', '').lower()
        if platform:
            platform_guidance = self._get_platform_guidance(platform)
            if platform_guidance:
                prompt += f"\n\nPLATFORM-SPECIFIC GUIDANCE:\n{platform_guidance}"
        
        # Add content type guidance
        content_type = context.get('content_type', '').lower()
        if content_type:
            content_guidance = self._get_content_type_guidance(content_type)
            if content_guidance:
                prompt += f"\n\nCONTENT TYPE GUIDANCE:\n{content_guidance}"
        
        return prompt
    
    def _get_platform_guidance(self, platform: str) -> str:
        """Get platform-specific guidance for content generation."""
        platform_guides = {
            'linkedin': """
- Professional tone appropriate for business network
- Include relevant hashtags (#RetirementPlanning, #FinancialEducation)
- Encourage engagement with educational questions
- Keep posts concise but informative (ideally 1-3 paragraphs)
- Include call-to-action for consultation or learning more""",
            
            'email': """
- Clear, compelling subject line
- Personal greeting and professional closing
- Scannable format with bullet points or short paragraphs
- Professional email signature area
- Include unsubscribe language if required""",
            
            'website': """
- SEO-friendly structure with clear headings
- Comprehensive but accessible information
- Professional, trustworthy tone
- Clear calls-to-action for next steps
- Consider internal linking opportunities""",
            
            'newsletter': """
- Engaging newsletter format with clear sections
- Mix of educational content and firm updates
- Include market insights where appropriate
- Professional design considerations
- Subscriber-focused value proposition""",
            
            'twitter': """
- Concise content within character limits
- Use relevant hashtags sparingly
- Professional but engaging tone
- Consider thread format for longer content
- Include appropriate disclaimers in compact form"""
        }
        
        return platform_guides.get(platform, "")
    
    def _get_content_type_guidance(self, content_type: str) -> str:
        """Get content type-specific guidance."""
        content_guides = {
            'linkedin_post': "Focus on professional insights and educational value suitable for LinkedIn's business audience.",
            'email_template': "Create structured email content with clear subject line and call-to-action.",
            'website_content': "Develop comprehensive web content with proper headings and SEO considerations.",
            'newsletter': "Design newsletter-style content with multiple sections and subscriber value.",
            'social_media': "Create engaging social media content with appropriate disclaimers.",
            'blog_post': "Develop long-form educational content with proper structure and citations."
        }
        
        return content_guides.get(content_type, "")
    
    def _get_fallback_prompt(self, service: AIService, prompt_type: PromptType) -> str:
        """
        Provide fallback prompts if specific ones aren't found.
        """
        if service == AIService.WARREN:
            return """You are Warren, an AI assistant for financial advisors. 
            
            CRITICAL: Wrap all final marketing content in delimiters:
            ##MARKETINGCONTENT##
            [Your content here]
            ##MARKETINGCONTENT##
            
            Create SEC/FINRA compliant content with appropriate disclaimers."""
        
        return "Please generate appropriate content for the requested task."
    
    def get_warren_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        Convenience method to get Warren's main system prompt.
        
        This is the primary method that enhanced_warren_service should use.
        """
        return self.get_prompt(AIService.WARREN, PromptType.SYSTEM, context)
    
    def get_warren_refinement_prompt(self, context: Optional[Dict] = None) -> str:
        """Get Warren's refinement prompt for content modifications."""
        return self.get_prompt(AIService.WARREN, PromptType.REFINEMENT, context)
    
    def get_warren_review_prompt(self, context: Optional[Dict] = None) -> str:
        """Get Warren's content review prompt."""
        return self.get_prompt(AIService.WARREN, PromptType.CONTENT_REVIEW, context)
    
    def list_available_prompts(self) -> Dict[str, List[str]]:
        """
        List all available prompts by service.
        Useful for debugging and documentation.
        """
        result = {}
        for service, prompts in self.prompts.items():
            result[service] = list(prompts.keys())
        return result
    
    def update_prompt(
        self, 
        service: AIService, 
        prompt_type: PromptType, 
        new_prompt: str
    ) -> bool:
        """
        Update a prompt (for future admin interface).
        
        This could be expanded to support database storage,
        versioning, and admin management of prompts.
        """
        try:
            if service.value not in self.prompts:
                self.prompts[service.value] = {}
            
            self.prompts[service.value][prompt_type.value] = new_prompt
            logger.info(f"Updated prompt: {service.value}.{prompt_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prompt: {str(e)}")
            return False


# Global service instance
prompt_service = PromptService()
