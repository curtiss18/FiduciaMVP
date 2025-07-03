"""
API Request/Response Debugging Tool

This script will help us trace what's happening in the Warren API calls
to debug why conversation memory isn't working.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.endpoints import router
from src.services.enhanced_warren_service import enhanced_warren_service
from src.core.database import AsyncSessionLocal
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages
from sqlalchemy import select

async def debug_api_request():
    """Debug what happens when we make a Warren API request"""
    print("🔍 Debugging Warren API Request/Response Flow\n")
    
    # Simulate the exact request the frontend would make
    session_id = "debug-api-test-12345"
    
    print("📤 SIMULATED FRONTEND REQUEST:")
    frontend_request = {
        "request": "What did we discuss earlier about retirement planning?",
        "content_type": "linkedin_post",
        "audience_type": "general_education", 
        "session_id": session_id
    }
    print(json.dumps(frontend_request, indent=2))
    
    # First, let's create some conversation history
    print("\n1. 🗄️ Creating test conversation history...")
    
    async with AsyncSessionLocal() as db:
        # Create session
        test_session = AdvisorSessions(
            advisor_id="demo-advisor",
            session_id=session_id,
            title="Test Conversation",
            message_count=0
        )
        db.add(test_session)
        
        # Add previous messages
        user_msg = AdvisorMessages(
            session_id=session_id,
            message_type='user',
            content="Create a LinkedIn post about retirement planning for doctors"
        )
        db.add(user_msg)
        
        warren_msg = AdvisorMessages(
            session_id=session_id,
            message_type='warren',
            content="I created a LinkedIn post about retirement planning for doctors focusing on their unique needs.",
            total_sources=5,
            search_strategy='vector'
        )
        db.add(warren_msg)
        
        await db.commit()
        print("✅ Created test session and messages")
    
    # Now test the Warren service directly
    print("\n2. 🧠 Testing Enhanced Warren Service...")
    
    try:
        print(f"📥 Calling enhanced_warren_service.generate_content_with_enhanced_context:")
        print(f"   user_request: {frontend_request['request']}")
        print(f"   content_type: {frontend_request['content_type']}")
        print(f"   audience_type: {frontend_request['audience_type']}")
        print(f"   session_id: {frontend_request['session_id']}")
        print(f"   use_conversation_context: True")
        
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request=frontend_request['request'],
            content_type=frontend_request['content_type'],
            audience_type=frontend_request['audience_type'],
            session_id=frontend_request['session_id'],
            use_conversation_context=True
        )
        
        print(f"\n📤 WARREN SERVICE RESPONSE:")
        response_summary = {
            "status": result.get("status"),
            "conversation_context_used": result.get("conversation_context_used"),
            "session_id": result.get("session_id"),
            "search_strategy": result.get("search_strategy"),
            "total_knowledge_sources": result.get("total_knowledge_sources"),
            "content_length": len(result.get("content", "")),
            "content_preview": result.get("content", "")[:200] + "..." if result.get("content") else None
        }
        print(json.dumps(response_summary, indent=2))
        
        if result.get("conversation_context_used"):
            print("✅ Conversation context was used!")
        else:
            print("❌ Conversation context was NOT used")
            
        return result
        
    except Exception as e:
        print(f"❌ Warren service error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def debug_conversation_manager():
    """Debug the ConversationManager directly"""
    print("\n3. 🔧 Testing ConversationManager directly...")
    
    session_id = "debug-api-test-12345"
    
    try:
        from src.services.conversation_manager import ConversationManager
        
        async with AsyncSessionLocal() as db:
            manager = ConversationManager(db)
            
            print(f"📥 Getting conversation context for session: {session_id}")
            context = await manager.get_conversation_context(session_id)
            
            print(f"📤 Context retrieved:")
            print(f"   Length: {len(context)} characters")
            if context:
                print(f"   Content preview: {context[:300]}...")
                print("✅ ConversationManager retrieved context successfully")
            else:
                print("❌ ConversationManager returned empty context")
                
            return context
            
    except Exception as e:
        print(f"❌ ConversationManager error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def debug_database_state():
    """Check what's actually in the database"""
    print("\n4. 🗄️ Checking database state...")
    
    session_id = "debug-api-test-12345"
    
    try:
        async with AsyncSessionLocal() as db:
            # Check sessions
            session_result = await db.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if session:
                print(f"✅ Session found: {session.session_id}")
                print(f"   Title: {session.title}")
                print(f"   Message count: {session.message_count}")
            else:
                print(f"❌ Session NOT found: {session_id}")
                return False
            
            # Check messages
            messages_result = await db.execute(
                select(AdvisorMessages).where(AdvisorMessages.session_id == session_id)
            )
            messages = messages_result.scalars().all()
            
            print(f"📬 Found {len(messages)} messages:")
            for i, msg in enumerate(messages):
                print(f"   Message {i+1}: {msg.message_type} - '{msg.content[:50]}...'")
                
            return len(messages) > 0
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

async def debug_warren_prompt():
    """Debug what prompt Warren actually receives"""
    print("\n5. 📝 Debugging Warren's prompt construction...")
    
    session_id = "debug-api-test-12345"
    
    # We'll need to modify the enhanced_warren_service temporarily to log the prompt
    # For now, let's just check if conversation context is being retrieved
    
    try:
        async with AsyncSessionLocal() as db:
            from src.services.conversation_manager import ConversationManager
            manager = ConversationManager(db)
            
            context = await manager.get_conversation_context(session_id)
            
            if context:
                print("📝 Conversation context that would be added to prompt:")
                print("="*60)
                print(context)
                print("="*60)
                print(f"✅ Context length: {len(context)} characters")
            else:
                print("❌ No conversation context to add to prompt")
                
            return context
            
    except Exception as e:
        print(f"❌ Prompt debug error: {e}")
        return None

async def main():
    """Run complete API debugging"""
    print("🚀 Warren API Debugging Session\n")
    
    # Step 1: Test the database state
    db_ok = await debug_database_state()
    
    # Step 2: Test ConversationManager
    context = await debug_conversation_manager()
    
    # Step 3: Test Warren prompt
    prompt_context = await debug_warren_prompt()
    
    # Step 4: Test Warren service
    warren_result = await debug_api_request()
    
    # Summary
    print("\n" + "="*60)
    print("🔍 DEBUGGING SUMMARY:")
    print(f"   Database has session/messages: {'✅' if db_ok else '❌'}")
    print(f"   ConversationManager works: {'✅' if context else '❌'}")
    print(f"   Warren receives context: {'✅' if warren_result and warren_result.get('conversation_context_used') else '❌'}")
    
    if warren_result and warren_result.get('conversation_context_used'):
        print("\n🎉 Conversation memory is working!")
    else:
        print("\n🚨 Conversation memory is NOT working")
        
        if not db_ok:
            print("   Issue: Database session/messages not found")
        elif not context:
            print("   Issue: ConversationManager not retrieving context")
        else:
            print("   Issue: Warren service not using context properly")

if __name__ == "__main__":
    asyncio.run(main())
