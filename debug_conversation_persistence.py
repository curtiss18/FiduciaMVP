"""
Focused test for conversation persistence debugging

This script will test step-by-step:
1. Warren content generation with session_id
2. Database session creation
3. Message saving
4. Context retrieval
5. Context integration in Warren prompts
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.enhanced_warren_service import enhanced_warren_service
from src.services.conversation_manager import ConversationManager
from src.core.database import AsyncSessionLocal
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages, ConversationContext
from sqlalchemy import select
import uuid
import json

async def debug_conversation_persistence():
    """Debug conversation persistence step by step"""
    print("🔍 Debugging Conversation Persistence\n")
    
    session_id = f"debug-{uuid.uuid4()}"
    print(f"Test session ID: {session_id}")
    
    # Step 1: Test Warren content generation
    print("\n1. 🧠 Testing Warren content generation with session_id...")
    try:
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create a LinkedIn post about cryptocurrency investing",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result.get("status") == "success":
            print("✅ Warren generation successful")
            print(f"   Content length: {len(result.get('content', ''))} chars")
            print(f"   Session ID in response: {result.get('session_id')}")
            print(f"   Conversation context used: {result.get('conversation_context_used')}")
        else:
            print(f"❌ Warren generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Warren generation exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Wait for database operations
    print("\n2. ⏳ Waiting for database operations...")
    await asyncio.sleep(3)
    
    # Step 2: Check if session was created
    print("\n3. 🗄️ Checking database for session...")
    try:
        async with AsyncSessionLocal() as db_session:
            session_result = await db_session.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            saved_session = session_result.scalar_one_or_none()
            
            if saved_session:
                print("✅ Session found in database")
                print(f"   Session ID: {saved_session.session_id}")
                print(f"   Advisor ID: {saved_session.advisor_id}")
                print(f"   Message count: {saved_session.message_count}")
                print(f"   Title: {saved_session.title}")
            else:
                print("❌ Session NOT found in database")
                print("   This suggests session creation is failing")
                return False
                
    except Exception as e:
        print(f"❌ Database session check failed: {e}")
        return False
    
    # Step 3: Check if messages were saved
    print("\n4. 💬 Checking database for messages...")
    try:
        async with AsyncSessionLocal() as db_session:
            messages_result = await db_session.execute(
                select(AdvisorMessages).where(AdvisorMessages.session_id == session_id)
            )
            messages = messages_result.scalars().all()
            
            print(f"Found {len(messages)} messages:")
            for i, msg in enumerate(messages):
                print(f"   Message {i+1}:")
                print(f"      Type: {msg.message_type}")
                print(f"      Content length: {len(msg.content)} chars")
                print(f"      Content preview: {msg.content[:100]}...")
                if msg.message_type == 'warren':
                    print(f"      Total sources: {msg.total_sources}")
                    print(f"      Search strategy: {msg.search_strategy}")
                    
            if len(messages) >= 2:
                print("✅ Messages saved correctly")
            else:
                print("❌ Expected at least 2 messages (user + warren)")
                return False
                
    except Exception as e:
        print(f"❌ Database message check failed: {e}")
        return False
    
    # Step 4: Test ConversationManager directly
    print("\n5. 🔧 Testing ConversationManager directly...")
    try:
        async with AsyncSessionLocal() as db_session:
            manager = ConversationManager(db_session)
            context = await manager.get_conversation_context(session_id)
            
            print(f"Retrieved context length: {len(context)} characters")
            if context:
                print("✅ ConversationManager retrieving context")
                print(f"   Context preview: {context[:200]}...")
            else:
                print("❌ ConversationManager returned empty context")
                return False
                
    except Exception as e:
        print(f"❌ ConversationManager test failed: {e}")
        return False
    
    # Step 5: Check conversation_context table
    print("\n6. 📊 Checking conversation_context table...")
    try:
        async with AsyncSessionLocal() as db_session:
            context_result = await db_session.execute(
                select(ConversationContext).where(ConversationContext.session_id == session_id)
            )
            context_records = context_result.scalars().all()
            
            print(f"Found {len(context_records)} context records:")
            for i, record in enumerate(context_records):
                print(f"   Record {i+1}:")
                print(f"      Type: {record.context_type}")
                print(f"      Token count: {record.token_count}")
                print(f"      Content length: {len(record.content)} chars")
                print(f"      Created: {record.created_at}")
                
    except Exception as e:
        print(f"❌ Context table check failed: {e}")
        return False
    
    # Step 6: Test second interaction with memory
    print("\n7. 🔄 Testing second interaction with memory...")
    try:
        result2 = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="What did we discuss about cryptocurrency earlier?",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result2.get("status") == "success":
            print("✅ Second interaction successful")
            print(f"   Conversation context used: {result2.get('conversation_context_used')}")
            
            content = result2.get('content', '').lower()
            memory_indicators = ['earlier', 'previous', 'discussed', 'cryptocurrency', 'crypto']
            found_indicators = [ind for ind in memory_indicators if ind in content]
            
            print(f"   Memory indicators found: {found_indicators}")
            
            if found_indicators:
                print("✅ Warren appears to use conversation memory")
            else:
                print("❌ Warren doesn't seem to use conversation memory")
                print(f"   Response preview: {result2.get('content', '')[:300]}...")
        else:
            print(f"❌ Second interaction failed: {result2.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Second interaction exception: {e}")
        return False
    
    print("\n✅ All persistence checks completed!")
    return True

async def main():
    """Run focused persistence debugging"""
    success = await debug_conversation_persistence()
    
    if success:
        print("\n🎉 Conversation persistence appears to be working!")
    else:
        print("\n🚨 Found issues with conversation persistence")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
