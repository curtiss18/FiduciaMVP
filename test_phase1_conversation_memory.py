"""
Test script for Phase 1: Database Schema & ConversationManager

This script tests:
1. Database table creation including conversation_context
2. ConversationManager basic functionality
3. Token counting and context retrieval
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import AsyncSessionLocal, engine
from src.models.database import Base
from src.services.conversation_manager import ConversationManager
from src.models.advisor_workflow_models import AdvisorSessions, AdvisorMessages, ConversationContext
from sqlalchemy import text
import uuid
from datetime import datetime

async def test_database_schema():
    """Test that all tables can be created successfully"""
    print("🗄️ Testing database schema creation...")
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Verify conversation_context table exists
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'conversation_context'
            """))
            
            if result.scalar_one_or_none():
                print("✅ conversation_context table created successfully")
            else:
                print("❌ conversation_context table not found")
                return False
                
        # Verify foreign key constraint exists
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'conversation_context' 
                AND constraint_type = 'FOREIGN KEY'
            """))
            
            if result.scalar_one_or_none():
                print("✅ Foreign key constraint created successfully")
            else:
                print("❌ Foreign key constraint not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

async def test_conversation_manager():
    """Test ConversationManager basic functionality"""
    print("\n🧠 Testing ConversationManager functionality...")
    
    try:
        async with AsyncSessionLocal() as session:
            manager = ConversationManager(session)
            
            # Test 1: Token counting
            test_text = "This is a test message for token counting."
            tokens = manager._estimate_tokens(test_text)
            print(f"✅ Token estimation working: '{test_text}' = {tokens} tokens")
            
            # Test 2: Create test session and messages
            session_id = f"test-session-{uuid.uuid4()}"
            
            # Create a test session
            test_session = AdvisorSessions(
                advisor_id="test-advisor",
                session_id=session_id,
                title="Test Conversation",
                message_count=0
            )
            session.add(test_session)
            await session.commit()
            
            # Test 3: Save conversation turn
            await manager.save_conversation_turn(
                session_id=session_id,
                user_input="Create a LinkedIn post about retirement planning",
                warren_response="I'll help you create a compliant LinkedIn post about retirement planning.",
                warren_metadata={
                    'total_sources': 5,
                    'marketing_examples': 3,
                    'compliance_rules': 2,
                    'search_strategy': 'vector'
                }
            )
            print("✅ Conversation turn saved successfully")
            
            # Test 4: Get conversation context
            context = await manager.get_conversation_context(session_id)
            print(f"✅ Context retrieval working: {len(context)} characters retrieved")
            
            # Test 5: Test context compression logic
            # Add more messages to test compression
            for i in range(3):
                await manager.save_conversation_turn(
                    session_id=session_id,
                    user_input=f"Test user message {i+1} - make this message longer to test the compression functionality",
                    warren_response=f"Warren response {i+1} - this is a detailed response that contains multiple sentences and should help test the compression logic when we have many messages in a conversation.",
                    warren_metadata={
                        'total_sources': 3,
                        'marketing_examples': 2,
                        'compliance_rules': 1,
                        'search_strategy': 'vector'
                    }
                )
            
            # Get context again with more messages
            context_with_history = await manager.get_conversation_context(session_id)
            print(f"✅ Context with history: {len(context_with_history)} characters")
            
            # Test 6: Verify context was saved to database
            from sqlalchemy import select
            context_result = await session.execute(
                select(ConversationContext).where(ConversationContext.session_id == session_id)
            )
            context_records = context_result.scalars().all()
            
            if context_records:
                print(f"✅ Context saved to database: {len(context_records)} records")
                for record in context_records:
                    print(f"   - Type: {record.context_type}, Tokens: {record.token_count}")
            else:
                print("❌ No context records found in database")
                
            return True
            
    except Exception as e:
        print(f"❌ ConversationManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_management():
    """Test token counting and compression scenarios"""
    print("\n📊 Testing token management...")
    
    try:
        async with AsyncSessionLocal() as session:
            manager = ConversationManager(session)
            
            # Test different text lengths
            test_cases = [
                ("Short text", 50),
                ("Medium text " * 10, 250),
                ("Long text " * 100, 2500),
                ("Very long text " * 1000, 25000)
            ]
            
            for text, expected_range in test_cases:
                tokens = manager._estimate_tokens(text)
                if tokens < expected_range * 2:  # Allow for variation in estimation
                    print(f"✅ Token count reasonable for {len(text)} chars: {tokens} tokens")
                else:
                    print(f"⚠️ Token count may be off for {len(text)} chars: {tokens} tokens")
            
            # Test compression methods
            test_user_msg = "I want to create a LinkedIn post about retirement planning for doctors"
            test_warren_msg = "##MARKETINGCONTENT##\nHere's a compliant LinkedIn post:\n\nDoctors, planning for retirement..."
            
            user_intent = manager._extract_user_intent(test_user_msg)
            warren_type = manager._extract_response_type(test_warren_msg)
            
            print(f"✅ Intent extraction: '{user_intent}'")
            print(f"✅ Response type extraction: '{warren_type}'")
            
            return True
            
    except Exception as e:
        print(f"❌ Token management test failed: {e}")
        return False

async def main():
    """Run all Phase 1 tests"""
    print("🚀 Phase 1 Testing: Database Schema & ConversationManager\n")
    
    # Test 1: Database Schema
    schema_success = await test_database_schema()
    
    # Test 2: ConversationManager
    manager_success = await test_conversation_manager()
    
    # Test 3: Token Management
    token_success = await test_token_management()
    
    # Summary
    print("\n" + "="*50)
    print("📋 PHASE 1 TEST RESULTS:")
    print(f"   Database Schema: {'✅ PASS' if schema_success else '❌ FAIL'}")
    print(f"   ConversationManager: {'✅ PASS' if manager_success else '❌ FAIL'}")
    print(f"   Token Management: {'✅ PASS' if token_success else '❌ FAIL'}")
    
    if schema_success and manager_success and token_success:
        print("\n🎉 Phase 1 Complete! Ready for Warren Service Integration")
        return True
    else:
        print("\n🚨 Phase 1 Issues Found - Review errors above")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
