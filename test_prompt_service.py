"""
Test script to verify the centralized prompt service is working correctly.
Run this to ensure Warren will now use delimiters.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.prompt_service import prompt_service, AIService, PromptType


async def test_prompt_service():
    """Test the centralized prompt service."""
    print("🧪 Testing Centralized Prompt Service")
    print("=" * 50)
    
    # Test basic Warren system prompt
    print("\n1️⃣ Testing Warren System Prompt:")
    warren_prompt = prompt_service.get_warren_system_prompt()
    
    # Check if delimiter instructions are present
    if "##MARKETINGCONTENT##" in warren_prompt:
        print("✅ Delimiter instructions found in system prompt")
    else:
        print("❌ Delimiter instructions NOT found in system prompt")
    
    # Print first few lines of the prompt
    prompt_lines = warren_prompt.split('\n')[:5]
    print(f"📝 First few lines of prompt:")
    for line in prompt_lines:
        print(f"   {line}")
    
    # Test platform-specific context
    print("\n2️⃣ Testing Platform-Specific Context:")
    linkedin_context = {
        'platform': 'linkedin',
        'content_type': 'linkedin_post'
    }
    
    linkedin_prompt = prompt_service.get_warren_system_prompt(linkedin_context)
    
    if "linkedin" in linkedin_prompt.lower():
        print("✅ LinkedIn-specific guidance added")
    else:
        print("❌ LinkedIn-specific guidance NOT found")
    
    # Test available prompts
    print("\n3️⃣ Available Prompts:")
    available = prompt_service.list_available_prompts()
    for service, prompt_types in available.items():
        print(f"   {service}: {', '.join(prompt_types)}")
    
    print("\n✅ Prompt Service Test Complete!")
    print("Warren should now use ##MARKETINGCONTENT## delimiters")


if __name__ == "__main__":
    asyncio.run(test_prompt_service())
