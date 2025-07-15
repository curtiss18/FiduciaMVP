"""
YouTube Context Service

Shared service for handling YouTube context across all Warren strategies.
Extracted from LegacyGenerationStrategy to eliminate code duplication.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class YouTubeContextService:
    """
    Shared service for YouTube context handling across all strategies.
    
    This service provides consistent YouTube transcript processing and context
    integration for both Advanced and Legacy generation strategies.
    """
    
    def __init__(self, max_transcript_length: int = 4000):
        """
        Initialize YouTube context service.
        
        Args:
            max_transcript_length: Maximum length of transcript to include in context
        """
        self.max_transcript_length = max_transcript_length
    
    def add_youtube_context(
        self, 
        context_parts: List[str], 
        youtube_context: Dict[str, Any]
    ) -> List[str]:
        """
        Add YouTube context to context parts list.
        
        This method processes YouTube metadata, stats, and transcript data
        to create properly formatted context for content generation.
        
        Args:
            context_parts: List of context strings to append YouTube data to
            youtube_context: Dictionary containing YouTube video data
            
        Returns:
            List[str]: Updated context parts with YouTube information
        """
        if not youtube_context:
            logger.debug("No YouTube context provided")
            return context_parts
        
        try:
            context_parts.append("\n## VIDEO CONTEXT:")
            video_info = youtube_context.get("metadata", {})
            stats = youtube_context.get("stats", {})
            
            context_parts.append("\nYou are creating content based on a YouTube video:")
            
            # Add video metadata if available
            if video_info.get("url"):
                context_parts.append(f"Video URL: {video_info['url']}")
            if video_info.get("title"):
                context_parts.append(f"Video Title: {video_info['title']}")
            if stats.get("word_count"):
                context_parts.append(f"Transcript length: ~{stats['word_count']} words")
            
            # Add transcript with length management
            transcript = youtube_context.get("transcript", "")
            if transcript:
                context_parts.append("\n**VIDEO TRANSCRIPT PROVIDED BELOW:**")
                
                if len(transcript) > self.max_transcript_length:
                    transcript_preview = transcript[:self.max_transcript_length] + "..."
                    context_parts.append(f"\n{transcript_preview}")
                    context_parts.append(
                        f"\n[Note: This is a preview of the full {len(transcript)}-character transcript]"
                    )
                    logger.debug(f"YouTube transcript truncated from {len(transcript)} to {self.max_transcript_length} characters")
                else:
                    context_parts.append(f"\n{transcript}")
                    logger.debug(f"YouTube transcript included: {len(transcript)} characters")
            
            # Add usage instructions
            context_parts.append(
                "\n**IMPORTANT**: You have been provided with the actual video transcript above. "
                "Please create content that references, summarizes, or analyzes the key points "
                "from this video transcript while maintaining SEC/FINRA compliance."
            )
            
            logger.info("✅ YouTube context successfully added to context parts")
            
        except Exception as e:
            logger.error(f"❌ Failed to add YouTube context: {e}")
            # Don't raise exception - just log error and continue without YouTube context
            context_parts.append("\n[Note: YouTube context could not be processed]")
        
        return context_parts
    
    def format_youtube_context_for_prompt(self, youtube_context: Dict[str, Any]) -> str:
        """
        Format YouTube context as a standalone string for prompt integration.
        
        Useful for strategies that build prompts differently than context_parts lists.
        
        Args:
            youtube_context: Dictionary containing YouTube video data
            
        Returns:
            str: Formatted YouTube context string
        """
        if not youtube_context:
            return ""
        
        context_parts = []
        context_parts = self.add_youtube_context(context_parts, youtube_context)
        return "\n".join(context_parts)
    
    def validate_youtube_context(self, youtube_context: Dict[str, Any]) -> bool:
        """
        Validate that YouTube context has required structure.
        
        Args:
            youtube_context: YouTube context data to validate
            
        Returns:
            bool: True if context is valid, False otherwise
        """
        if not isinstance(youtube_context, dict):
            return False
        
        # Check for either transcript or metadata
        has_transcript = bool(youtube_context.get("transcript"))
        has_metadata = bool(youtube_context.get("metadata"))
        
        return has_transcript or has_metadata
    
    def get_transcript_summary(self, youtube_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary information about the YouTube transcript.
        
        Args:
            youtube_context: YouTube context data
            
        Returns:
            Dict containing transcript statistics
        """
        transcript = youtube_context.get("transcript", "")
        stats = youtube_context.get("stats", {})
        
        return {
            "has_transcript": bool(transcript),
            "transcript_length": len(transcript),
            "word_count": stats.get("word_count", 0),
            "will_be_truncated": len(transcript) > self.max_transcript_length,
            "truncated_length": min(len(transcript), self.max_transcript_length)
        }


# Create default instance for easy import
youtube_context_service = YouTubeContextService()
