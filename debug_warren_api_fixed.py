"""
API Request/Response Debugging Tool - FIXED VERSION

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
from sqlalchemy import select, text

async def create_test_data():
    """Create test session and conversation history FIRST"""
    print("1. 🗄️ Creating test conversation history...")
    
    session_id = "debug-api-test-12345"
    
    async with AsyncSessionLocal() as db:
        # Clean up any existing test data first
        await db.execute(
            text("DELETE FROM advisor_messages WHERE session_id = :session_id"),
            {"session_id": session_id}
        )
        await db.execute(
            text("DELETE FROM advisor_sessions WHERE session_id = :session_id"), 
            {"session_id": session_id}
        )
        await db.commit()
        
        # Create fresh session
        test_session = AdvisorSessions(
            advisor_id="demo-advisor",
            session_id=session_id,
            title="Test Conversation About Retirement Planning",
            message_count=2
        )
        db.add(test_session)
        await db.flush()  # Ensure session is created before messages
        
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
            content="I created a LinkedIn post about retirement planning for doctors focusing on their unique needs: high-stress careers, irregular income patterns, and specific tax considerations. The post emphasized the importance of starting early despite busy schedules and seeking specialized financial advice.",
            total_sources=5,
            search_strategy='vector',
            generation_confidence=0.85
        )
        db.add(warren_msg)
        
        await db.commit()
        print(f"✅ Created test session '{session_id}' with 2 messages")
        return session_id

async def debug_database_state(session_id):
    """Check what's actually in the database"""
    print("\n2. 🗄️ Checking database state...")
    
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
                select(AdvisorMessages).where(AdvisorMessages.session_id == session_id).order_by(AdvisorMessages.created_at)
            )
            messages = messages_result.scalars().all()
            
            print(f"📬 Found {len(messages)} messages:")
            for i, msg in enumerate(messages):
                print(f"   Message {i+1}: {msg.message_type} - '{msg.content[:50]}...'")
                
            return len(messages) > 0
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

async def debug_conversation_manager(session_id):
    """Debug the ConversationManager directly"""
    print("\n3. 🔧 Testing ConversationManager directly...")
    
    try:
        from src.services.conversation_manager import ConversationManager
        
        async with AsyncSessionLocal() as db:
            manager = ConversationManager(db)
            
            print(f"📥 Getting conversation context for session: {session_id}")
            context = await manager.get_conversation_context(session_id)
            
            print(f"📤 Context retrieved:")
            print(f"   Length: {len(context)} characters")
            if context:
                print(f"   Content preview:")
                print(f"   {'-'*50}")
                print(f"   {context[:400]}...")
                print(f"   {'-'*50}")
                print("✅ ConversationManager retrieved context successfully")
            else:
                print("❌ ConversationManager returned empty context")
                
            return context
            
    except Exception as e:
        print(f"❌ ConversationManager error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def debug_warren_service(session_id):
    """Test the Enhanced Warren Service with the conversation context"""
    print("\n4. 🧠 Testing Enhanced Warren Service...")
    
    # Simulate the exact request the frontend would make
    frontend_request = {
        "request": "What did we discuss earlier about retirement planning? Can you expand on the tax considerations?",
        "content_type": "linkedin_post",
        "audience_type": "general_education", 
        "session_id": session_id
    }
    
    print("📤 SIMULATED FRONTEND REQUEST:")
    print(json.dumps(frontend_request, indent=2))
    
    try:
        print(f"\n📥 Calling enhanced_warren_service.generate_content_with_enhanced_context:")
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
            "content_preview": result.get("content", "")[:300] + "..." if result.get("content") else None
        }
        print(json.dumps(response_summary, indent=2))
        
        if result.get("conversation_context_used"):
            print("✅ Conversation context was used!")
            
            # Show the generated content
            if result.get("content"):
                print(f"\n📝 GENERATED CONTENT:")
                print("="*60)
                print(result.get("content"))
                print("="*60)
        else:
            print("❌ Conversation context was NOT used")
            
        return result
        
    except Exception as e:
        print(f"❌ Warren service error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_warren_without_context(session_id):
    """Test Warren without conversation context for comparison"""
    print("\n5. 🆚 Testing Warren WITHOUT conversation context (for comparison)...")
    
    try:
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create a LinkedIn post about tax considerations for doctors",
            content_type="linkedin_post",
            audience_type="general_education",
            session_id=session_id,
            use_conversation_context=False  # Key difference
        )
        
        print(f"📤 Warren WITHOUT context:")
        print(f"   Content length: {len(result.get('content', ''))}")
        print(f"   Context used: {result.get('conversation_context_used', False)}")
        print(f"   Content preview: {result.get('content', '')[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Warren without context error: {e}")
        return None

async def main():
    """Run complete API debugging with proper order"""
    print("🚀 Warren API Debugging Session\n")
    
    # Step 1: Create test data FIRST
    session_id = await create_test_data()
    
    # Step 2: Verify database state
    db_ok = await debug_database_state(session_id)
    
    # Step 3: Test ConversationManager
    context = await debug_conversation_manager(session_id)
    
    # Step 4: Test Warren service WITH context
    warren_result_with_context = await debug_warren_service(session_id)
    
    # Step 5: Test Warren service WITHOUT context for comparison
    warren_result_without_context = await test_warren_without_context(session_id)
    
    # Summary
    print("\n" + "="*70)
    print("🔍 DEBUGGING SUMMARY:")
    print(f"   Database has session/messages: {'✅' if db_ok else '❌'}")
    print(f"   ConversationManager works: {'✅' if context else '❌'}")
    print(f"   Warren uses context: {'✅' if warren_result_with_context and warren_result_with_context.get('conversation_context_used') else '❌'}")
    
    if warren_result_with_context and warren_result_with_context.get('conversation_context_used'):
        print("\n🎉 Conversation memory is working!")
        
        # Compare with/without context
        if warren_result_without_context:
            with_context_len = len(warren_result_with_context.get('content', ''))
            without_context_len = len(warren_result_without_context.get('content', ''))
            print(f"\n📊 Context Impact:")
            print(f"   Content with context: {with_context_len} characters")
            print(f"   Content without context: {without_context_len} characters")
            print(f"   Difference: {with_context_len - without_context_len} characters")
    else:
        print("\n🚨 Conversation memory is NOT working")
        
        if not db_ok:
            print("   Issue: Database session/messages not found")
        elif not context:
            print("   Issue: ConversationManager not retrieving context")
        else:
            print("   Issue: Warren service not using context properly")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM advisor_messages WHERE session_id = :session_id"),
            {"session_id": session_id}
        )
        await db.execute(
            text("DELETE FROM advisor_sessions WHERE session_id = :session_id"), 
            {"session_id": session_id}
        )
        await db.commit()
        print("✅ Test data cleaned up")

if __name__ == "__main__":
    asyncio.run(main())
