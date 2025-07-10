import asyncio
from anthropic import Anthropic
from config.settings import settings


class ClaudeService:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
    
    async def generate_content(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate content using Claude AI"""
        try:
            # Run the synchronous API call in a thread pool
            message = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    async def test_connection(self) -> dict:
        """Test Claude API connection"""
        try:
            response = await self.generate_content("Hello! Please respond with 'Connection successful'", max_tokens=50)
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global instance
claude_service = ClaudeService()
