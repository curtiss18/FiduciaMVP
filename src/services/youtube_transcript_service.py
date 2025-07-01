# YouTube Transcript Service
"""
Service for fetching and processing YouTube video transcripts using SearchAPI.io
Supports extracting transcripts from YouTube URLs for Warren AI content generation.
"""

import logging
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import aiohttp
import json

from config.settings import settings

logger = logging.getLogger(__name__)


class YouTubeTranscriptService:
    """Service for fetching YouTube transcripts via SearchAPI.io."""
    
    def __init__(self):
        """Initialize the YouTube transcript service."""
        self.api_key = settings.searchapi_key
        self.base_url = "https://www.searchapi.io/api/v1/search"
        self.timeout = 30  # 30 second timeout for API calls
        
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            youtube_url: YouTube URL in various formats
            
        Returns:
            Video ID string or None if not found
        """
        # Common YouTube URL patterns
        patterns = [
            r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]+)',
            r'(?:youtu\.be/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/v/)([a-zA-Z0-9_-]+)',
            r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                video_id = match.group(1)
                logger.info(f"Extracted video ID: {video_id} from URL: {youtube_url}")
                return video_id
        
        logger.warning(f"Could not extract video ID from URL: {youtube_url}")
        return None
    
    async def fetch_transcript_data(self, video_id: str) -> Dict[str, Any]:
        """
        Fetch raw transcript data from SearchAPI.io.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with success status and data/error
        """
        params = {
            "engine": "youtube_transcripts",
            "video_id": video_id,
            "api_key": self.api_key
        }
        
        try:
            logger.info(f"Fetching transcript for video ID: {video_id}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.base_url, params=params) as response:
                    logger.info(f"SearchAPI response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched transcript data")
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        logger.error(f"SearchAPI error {response.status}: {error_text}")
                        return {
                            "success": False, 
                            "error": f"HTTP {response.status}: {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching transcript for video {video_id}")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"Exception fetching transcript: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_transcript_entries(self, transcript_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Process raw transcript data into structured entries.
        
        Args:
            transcript_data: Raw data from SearchAPI.io
            
        Returns:
            List of transcript entries or None if not found
        """
        if "transcripts" not in transcript_data:
            logger.warning("No 'transcripts' field found in response data")
            return None
        
        transcripts = transcript_data["transcripts"]
        logger.info(f"Found {len(transcripts)} transcript entries")
        
        # Validate entries have required fields
        valid_entries = []
        for entry in transcripts:
            if "text" in entry:
                valid_entries.append(entry)
        
        logger.info(f"Processed {len(valid_entries)} valid transcript entries")
        return valid_entries
    
    def combine_transcript_text(self, transcript_entries: List[Dict[str, Any]]) -> str:
        """
        Combine transcript entries into a single text string.
        
        Args:
            transcript_entries: List of transcript entry dictionaries
            
        Returns:
            Combined transcript text
        """
        text_parts = []
        
        for entry in transcript_entries:
            if "text" in entry and entry["text"].strip():
                text_parts.append(entry["text"].strip())
        
        combined_text = " ".join(text_parts)
        
        logger.info(f"Combined transcript: {len(combined_text)} characters, {len(combined_text.split())} words")
        
        return combined_text
    
    def get_video_metadata(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract video metadata from transcript response.
        
        Args:
            transcript_data: Raw data from SearchAPI.io
            
        Returns:
            Dictionary with video metadata
        """
        metadata = {
            "video_id": None,
            "title": None,
            "channel": None,
            "duration": None,
            "url": None
        }
        
        # Check search metadata
        if "search_metadata" in transcript_data:
            search_meta = transcript_data["search_metadata"]
            if "request_url" in search_meta:
                metadata["url"] = search_meta["request_url"]
                # Extract video ID from URL
                video_id = self.extract_video_id(search_meta["request_url"])
                if video_id:
                    metadata["video_id"] = video_id
        
        # Check for video details if available
        if "video_details" in transcript_data:
            details = transcript_data["video_details"]
            metadata.update({k: v for k, v in details.items() if k in metadata})
        
        logger.info(f"Extracted video metadata: {metadata}")
        return metadata
    
    async def get_transcript_from_url(self, youtube_url: str) -> Dict[str, Any]:
        """
        Main method to get transcript from YouTube URL.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dictionary with transcript text, metadata, and status
        """
        logger.info(f"Processing YouTube URL: {youtube_url}")
        
        # Extract video ID
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            return {
                "success": False,
                "error": "Could not extract video ID from URL",
                "url": youtube_url
            }
        
        # Fetch transcript data
        result = await self.fetch_transcript_data(video_id)
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "url": youtube_url,
                "video_id": video_id
            }
        
        transcript_data = result["data"]
        
        # Process transcript entries
        transcript_entries = self.process_transcript_entries(transcript_data)
        if not transcript_entries:
            return {
                "success": False,
                "error": "No transcript entries found",
                "url": youtube_url,
                "video_id": video_id
            }
        
        # Combine transcript text
        transcript_text = self.combine_transcript_text(transcript_entries)
        if not transcript_text.strip():
            return {
                "success": False,
                "error": "Empty transcript text",
                "url": youtube_url,
                "video_id": video_id
            }
        
        # Get metadata
        metadata = self.get_video_metadata(transcript_data)
        
        # Success response
        return {
            "success": True,
            "transcript": transcript_text,
            "metadata": metadata,
            "stats": {
                "character_count": len(transcript_text),
                "word_count": len(transcript_text.split()),
                "entry_count": len(transcript_entries)
            },
            "url": youtube_url,
            "video_id": video_id
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test SearchAPI.io connection and API key.
        
        Returns:
            Dictionary with connection test results
        """
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short test video
        
        try:
            result = await self.get_transcript_from_url(test_video_url)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "SearchAPI.io connection successful",
                    "test_stats": result.get("stats", {})
                }
            else:
                return {
                    "success": False,
                    "message": f"SearchAPI.io test failed: {result['error']}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"SearchAPI.io connection test failed: {str(e)}"
            }


# Global service instance
youtube_transcript_service = YouTubeTranscriptService()
