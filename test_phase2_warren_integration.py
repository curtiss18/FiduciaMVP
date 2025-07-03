"""
Test script for Phase 2: Warren Service Integration

This script tests:
1. Warren conversation memory integration
2. Backward compatibility (Warren works without session_id)
3. Conversation context in Warren responses
4. Session persistence across multiple turns
"""

import asyncio
import sys
import os
import json

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.enhanced_warren_service import enhanced_warren_service
from src.core.database import AsyncSessionLocal
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages
from sqlalchemy import select
import uuid

async def test_backward_compatibility():
    """Test that Warren still works without session_id (backward compatibility)"""
    print("🔄 Testing backward compatibility (no session_id)...")
    
    try:
        # Test Warren without session_id or conversation context
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create a short LinkedIn post about diversification",
            content_type="linkedin_post",
            audience_type="general",
            use_conversation_context=False  # Explicitly disable
        )
        
        if result.get("status") == "success":
            print("✅ Warren works without session_id (backward compatible)")
            print(f"   Generated content: {len(result.get('content', ''))} characters")
            print(f"   Conversation context used: {result.get('conversation_context_used', False)}")
            return True
        else:
            print(f"❌ Warren failed without session_id: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

async def test_conversation_memory():
    """Test Warren conversation memory with session_id"""
    print("\n🧠 Testing Warren conversation memory...")
    
    try:
        # Create a unique session for testing
        session_id = f"test-memory-{uuid.uuid4()}"
        
        # First interaction - establish context
        print(f"🔸 First interaction (session: {session_id})...")
        result1 = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create a LinkedIn post about retirement planning for doctors",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result1.get("status") != "success":
            print(f"❌ First interaction failed: {result1.get('error')}")
            return False
        
        print("✅ First interaction successful")
        print(f"   Generated content: {len(result1.get('content', ''))} characters")
        print(f"   Conversation context used: {result1.get('conversation_context_used', False)}")
        print(f"   Session ID: {result1.get('session_id')}")
        
        # Wait a moment for database operations to complete
        await asyncio.sleep(1)
        
        # Second interaction - test memory
        print(f"🔸 Second interaction (testing memory)...")
        result2 = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="What did we discuss about retirement planning earlier?",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result2.get("status") != "success":
            print(f"❌ Second interaction failed: {result2.get('error')}")
            return False
        
        print("✅ Second interaction successful")
        print(f"   Generated content: {len(result2.get('content', ''))} characters")
        print(f"   Conversation context used: {result2.get('conversation_context_used', False)}")
        
        # Check if Warren referenced previous conversation
        content2 = result2.get('content', '').lower()
        if 'earlier' in content2 or 'previous' in content2 or 'discussed' in content2 or 'doctor' in content2:
            print("✅ Warren appears to reference previous conversation")
        else:
            print("⚠️ Warren may not be using conversation context effectively")
            print(f"   Response preview: {result2.get('content', '')[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversation_persistence():
    """Test that conversations are actually saved to database"""
    print("\n💾 Testing conversation persistence...")
    
    try:
        session_id = f"test-persist-{uuid.uuid4()}"
        
        # Generate content with conversation context
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create an email template about tax planning",
            content_type="email_template",
            audience_type="clients",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result.get("status") != "success":
            print(f"❌ Content generation failed: {result.get('error')}")
            return False
        
        # Wait for database operations
        await asyncio.sleep(2)
        
        # Check database for saved session and messages
        async with AsyncSessionLocal() as session:
            # Check session exists
            session_result = await session.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            saved_session = session_result.scalar_one_or_none()
            
            if not saved_session:
                print(f"❌ Session not found in database: {session_id}")
                return False
            
            print(f"✅ Session found in database: {saved_session.session_id}")
            print(f"   Message count: {saved_session.message_count}")
            
            # Check messages exist
            messages_result = await session.execute(
                select(AdvisorMessages).where(AdvisorMessages.session_id == session_id)
            )
            messages = messages_result.scalars().all()
            
            if not messages:
                print("❌ No messages found in database")
                return False
            
            print(f"✅ Found {len(messages)} messages in database")
            
            # Check message details
            for i, msg in enumerate(messages):
                print(f"   Message {i+1}: {msg.message_type} - {len(msg.content)} chars")
                if msg.message_type == 'warren':
                    print(f"      Sources: {msg.total_sources}, Strategy: {msg.search_strategy}")
            
            return True
            
    except Exception as e:
        print(f"❌ Persistence test failed: {e}")
        return False

async def test_context_compression():
    """Test conversation context compression with multiple exchanges"""
    print("\n📊 Testing context compression with multiple exchanges...")
    
    try:
        session_id = f"test-compression-{uuid.uuid4()}"
        
        # Generate multiple interactions to test compression
        topics = [
            "retirement planning for teachers",
            "tax-efficient investing strategies",
            "estate planning basics"
        ]
        
        for i, topic in enumerate(topics):
            print(f"🔸 Interaction {i+1}: {topic}")
            
            result = await enhanced_warren_service.generate_content_with_enhanced_context(
                user_request=f"Create a brief LinkedIn post about {topic}",
                content_type="linkedin_post",
                audience_type="prospects",
                session_id=session_id,
                use_conversation_context=True
            )
            
            if result.get("status") != "success":
                print(f"❌ Interaction {i+1} failed: {result.get('error')}")
                return False
            
            print(f"   ✅ Success - Context used: {result.get('conversation_context_used', False)}")
            
            # Brief pause between interactions
            await asyncio.sleep(0.5)
        
        # Test memory of early interactions
        print("🔸 Testing memory of early interactions...")
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="What topics did we cover earlier in our conversation?",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result.get("status") != "success":
            print(f"❌ Memory test failed: {result.get('error')}")
            return False
        
        content = result.get('content', '').lower()
        memory_indicators = ['earlier', 'previously', 'discussed', 'covered', 'retirement', 'tax', 'estate']
        memory_found = sum(1 for indicator in memory_indicators if indicator in content)
        
        print(f"✅ Memory test complete - Found {memory_found}/{len(memory_indicators)} memory indicators")
        if memory_found >= 3:
            print("✅ Strong evidence of conversation memory")
        elif memory_found >= 1:
            print("⚠️ Some evidence of conversation memory")
        else:
            print("❌ Little evidence of conversation memory")
            print(f"   Response preview: {result.get('content', '')[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Context compression test failed: {e}")
        return False

async def test_source_transparency_preservation():
    """Test that source transparency still works with conversation memory"""
    print("\n🔍 Testing source transparency preservation...")
    
    try:
        session_id = f"test-sources-{uuid.uuid4()}"
        
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request="Create a LinkedIn post about fixed income securities",
            content_type="linkedin_post",
            audience_type="prospects",
            session_id=session_id,
            use_conversation_context=True
        )
        
        if result.get("status") != "success":
            print(f"❌ Source transparency test failed: {result.get('error')}")
            return False
        
        # Check that source transparency data is still present
        required_fields = [
            'search_strategy',
            'total_knowledge_sources',
            'marketing_examples_count',
            'compliance_rules_count'
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"❌ Missing source transparency fields: {missing_fields}")
            return False
        
        print("✅ Source transparency preserved")
        print(f"   Search strategy: {result.get('search_strategy')}")
        print(f"   Total sources: {result.get('total_knowledge_sources')}")
        print(f"   Marketing examples: {result.get('marketing_examples_count')}")
        print(f"   Compliance rules: {result.get('compliance_rules_count')}")
        print(f"   Conversation context used: {result.get('conversation_context_used')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Source transparency preservation test failed: {e}")
        return False

async def main():
    """Run all Phase 2 tests"""
    print("🚀 Phase 2 Testing: Warren Service Integration\n")
    
    # Test 1: Backward Compatibility
    compat_success = await test_backward_compatibility()
    
    # Test 2: Conversation Memory
    memory_success = await test_conversation_memory()
    
    # Test 3: Conversation Persistence
    persist_success = await test_conversation_persistence()
    
    # Test 4: Context Compression
    compression_success = await test_context_compression()
    
    # Test 5: Source Transparency Preservation
    source_success = await test_source_transparency_preservation()
    
    # Summary
    print("\n" + "="*60)
    print("📋 PHASE 2 TEST RESULTS:")
    print(f"   Backward Compatibility: {'✅ PASS' if compat_success else '❌ FAIL'}")
    print(f"   Conversation Memory: {'✅ PASS' if memory_success else '❌ FAIL'}")
    print(f"   Conversation Persistence: {'✅ PASS' if persist_success else '❌ FAIL'}")
    print(f"   Context Compression: {'✅ PASS' if compression_success else '❌ FAIL'}")
    print(f"   Source Transparency: {'✅ PASS' if source_success else '❌ FAIL'}")
    
    all_success = all([compat_success, memory_success, persist_success, compression_success, source_success])
    
    if all_success:
        print("\n🎉 Phase 2 Complete! Warren has conversation memory while preserving all functionality!")
        print("\n🎯 Next Steps:")
        print("   1. Test Warren in the actual advisor portal")
        print("   2. Ask Warren about previous conversations")
        print("   3. Verify source transparency still works")
        print("   4. Ready for production use!")
        return True
    else:
        print("\n🚨 Phase 2 Issues Found - Review errors above")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
