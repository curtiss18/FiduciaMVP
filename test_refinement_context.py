"""
Test script specifically for Warren refinement with conversation context
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.enhanced_warren_service import enhanced_warren_service
from src.core.database import AsyncSessionLocal
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages
from sqlalchemy import select, text

async def test_refinement_with_context():
    """Test Warren refinement functionality with conversation context"""
    print("🔍 Testing Warren Refinement with Conversation Context\n")
    
    session_id = "refinement-test-session"
    
    # Step 1: Create conversation history
    print("1. 📝 Setting up conversation history...")
    
    async with AsyncSessionLocal() as db:
        # Clean up any existing test data
        await db.execute(text("DELETE FROM advisor_messages WHERE session_id = :session_id"), {"session_id": session_id})
        await db.execute(text("DELETE FROM advisor_sessions WHERE session_id = :session_id"), {"session_id": session_id})
        await db.commit()
        
        # Create session
        test_session = AdvisorSessions(
            advisor_id="demo-advisor",
            session_id=session_id,
            title="Refinement Test - Retirement Planning",
            message_count=4
        )
        db.add(test_session)
        await db.flush()
        
        # Add conversation history
        messages = [
            ("user", "Create a LinkedIn post about retirement planning for doctors"),
            ("warren", "I created a LinkedIn post about retirement planning for doctors, focusing on their unique challenges like later career starts, high debt loads, and complex compensation structures."),
            ("user", "Can you make it more specific about tax considerations?"),
            ("warren", "I refined the post to focus specifically on tax considerations for physicians, including retirement account options, strategic tax planning, and practice structure considerations.")
        ]
        
        for msg_type, content in messages:
            message = AdvisorMessages(
                session_id=session_id,
                message_type=msg_type,
                content=content
            )
            db.add(message)
        
        await db.commit()
        print(f"✅ Created session with {len(messages)} messages")
    
    # Step 2: Test initial content generation (should use context)
    print("\n2. 🧠 Testing initial content generation with context...")
    
    initial_result = await enhanced_warren_service.generate_content_with_enhanced_context(
        user_request="Create a LinkedIn post about estate planning for physicians",
        content_type="linkedin_post",
        audience_type="general_education",
        session_id=session_id,
        use_conversation_context=True
    )
    
    print(f"📤 Initial generation result:")
    print(f"   Context used: {initial_result.get('conversation_context_used')}")
    print(f"   Content length: {len(initial_result.get('content', ''))}")
    print(f"   Content preview: {initial_result.get('content', '')[:200]}...")
    
    initial_content = initial_result.get('content', '')
    
    # Step 3: Test refinement (this should also use context)
    print("\n3. 🔧 Testing refinement with conversation context...")
    
    refinement_result = await enhanced_warren_service.generate_content_with_enhanced_context(
        user_request="Make this more specific about trust structures and how they relate to the tax planning we discussed earlier",
        content_type="linkedin_post",
        audience_type="general_education",
        session_id=session_id,
        current_content=initial_content,
        is_refinement=True,
        use_conversation_context=True
    )
    
    print(f"📤 Refinement result:")
    print(f"   Context used: {refinement_result.get('conversation_context_used')}")
    print(f"   Content length: {len(refinement_result.get('content', ''))}")
    print(f"   Content preview: {refinement_result.get('content', '')[:200]}...")
    
    # Step 4: Test refinement WITHOUT context for comparison
    print("\n4. 🆚 Testing refinement WITHOUT conversation context...")
    
    no_context_result = await enhanced_warren_service.generate_content_with_enhanced_context(
        user_request="Make this more specific about trust structures and how they relate to the tax planning we discussed earlier",
        content_type="linkedin_post",
        audience_type="general_education",
        session_id=session_id,
        current_content=initial_content,
        is_refinement=True,
        use_conversation_context=False  # Disabled context
    )
    
    print(f"📤 No-context refinement result:")
    print(f"   Context used: {no_context_result.get('conversation_context_used')}")
    print(f"   Content length: {len(no_context_result.get('content', ''))}")
    print(f"   Content preview: {no_context_result.get('content', '')[:200]}...")
    
    # Step 5: Analysis
    print("\n" + "="*70)
    print("🔍 ANALYSIS:")
    print(f"   Initial generation uses context: {'✅' if initial_result.get('conversation_context_used') else '❌'}")
    print(f"   Refinement with context: {'✅' if refinement_result.get('conversation_context_used') else '❌'}")
    print(f"   Refinement without context: {'❌' if not no_context_result.get('conversation_context_used') else '✅'}")
    
    # Check if refinement content references conversation history
    refinement_content = refinement_result.get('content', '').lower()
    context_references = [
        'discussed earlier',
        'previous',
        'we talked about',
        'as mentioned',
        'our conversation',
        'retirement planning',
        'tax consideration'
    ]
    
    references_found = [ref for ref in context_references if ref in refinement_content]
    
    print(f"\n📊 Context Integration Analysis:")
    print(f"   References to conversation found: {len(references_found)}")
    if references_found:
        print(f"   References: {', '.join(references_found)}")
    
    if initial_result.get('conversation_context_used') and refinement_result.get('conversation_context_used'):
        print("\n🎉 SUCCESS: Both initial generation AND refinements use conversation context!")
    elif initial_result.get('conversation_context_used') and not refinement_result.get('conversation_context_used'):
        print("\n🚨 ISSUE: Initial generation uses context but refinements do NOT!")
    else:
        print("\n❌ PROBLEM: Conversation context not working properly")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM advisor_messages WHERE session_id = :session_id"), {"session_id": session_id})
        await db.execute(text("DELETE FROM advisor_sessions WHERE session_id = :session_id"), {"session_id": session_id})
        await db.commit()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_refinement_with_context())
