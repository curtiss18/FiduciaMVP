#!/usr/bin/env python3
"""
Test script for DocumentManager CRUD operations
SCRUM-39: Validate DocumentManager class functionality

Run this script to test:
1. Document storage
2. Document retrieval
3. Context summary generation
4. Relevant section extraction
5. Document updates and deletion
6. Session document listing
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.document_manager import DocumentManager
from src.services.advisor_workflow_service import AdvisorWorkflowService
from src.core.database import create_tables


async def test_document_manager():
    """Test all DocumentManager CRUD operations."""
    print("🧪 Testing DocumentManager CRUD Operations")
    print("=" * 50)
    
    # Initialize database (ensure tables exist)
    await create_tables()
    
    # Initialize services
    doc_manager = DocumentManager()
    advisor_service = AdvisorWorkflowService()
    
    # Create a valid advisor session first
    print("🔧 Setting up test session...")
    session_result = await advisor_service.create_advisor_session(
        advisor_id="demo_advisor_001",
        title="Test Session for Document Management"
    )
    
    if session_result["status"] != "success":
        raise Exception(f"Failed to create session: {session_result.get('error', 'Unknown error')}")
    
    test_session_id = session_result["session"]["session_id"]
    print(f"✅ Created test session: {test_session_id}")
    
    try:
        # Test 1: Store a document
        print("\n📝 Test 1: Store Document")
        test_doc_data = {
            "title": "Test Retirement Planning Guide",
            "content_type": "txt",
            "full_content": "This is a comprehensive guide to retirement planning. "
                          "It covers 401k contributions, IRA rollovers, and investment strategies. "
                          "Key points include diversification, risk tolerance assessment, and "
                          "the importance of starting early. Tax-advantaged accounts are crucial "
                          "for building long-term wealth. Consider both traditional and Roth options.",
            "original_filename": "retirement_guide.txt",
            "file_size_bytes": 1024,
            "metadata": {
                "source": "test_script",
                "topics": ["retirement", "401k", "IRA", "investments"],
                "difficulty": "intermediate"
            }
        }
        
        document_id = await doc_manager.store_document(test_doc_data, test_session_id)
        print(f"✅ Document stored with ID: {document_id}")
        
        # Test 2: Retrieve full document
        print("\n📖 Test 2: Retrieve Full Document")
        full_doc = await doc_manager.retrieve_full_document(document_id)
        print(f"✅ Retrieved document: {full_doc['title']}")
        print(f"   Word count: {full_doc['word_count']}")
        print(f"   Content type: {full_doc['content_type']}")
        print(f"   Status: {full_doc['processing_status']}")
        
        # Test 3: Get context summary
        print("\n📄 Test 3: Get Context Summary")
        summary = await doc_manager.get_context_summary(document_id)
        print(f"✅ Summary retrieved (length: {len(summary)} chars)")
        print(f"   Preview: {summary[:100]}...")
        
        # Test 4: Extract relevant sections
        print("\n🔍 Test 4: Extract Relevant Sections")
        relevant_sections = await doc_manager.extract_relevant_sections(
            document_id, 
            "401k retirement investment", 
            max_length=500
        )
        print(f"✅ Relevant sections extracted (length: {len(relevant_sections)} chars)")
        print(f"   Preview: {relevant_sections[:150]}...")
        
        # Test 5: Get session documents
        print("\n📚 Test 5: Get Session Documents")
        session_docs = await doc_manager.get_session_documents(test_session_id)
        print(f"✅ Found {len(session_docs)} documents in session")
        for doc in session_docs:
            print(f"   - {doc['title']} ({doc['content_type']}, {doc['word_count']} words)")
        
        # Test 6: Update document
        print("\n✏️ Test 6: Update Document")
        update_success = await doc_manager.update_document(document_id, {
            "summary": "AI-generated summary: This document covers essential retirement planning strategies including 401k, IRA, and investment diversification.",
            "processing_status": "processed",
            "document_metadata": {
                "source": "test_script",
                "topics": ["retirement", "401k", "IRA", "investments"],
                "difficulty": "intermediate",
                "processed": True,
                "summary_generated": True
            }
        })
        print(f"✅ Document update successful: {update_success}")
        
        # Test 7: Verify update
        print("\n🔄 Test 7: Verify Update")
        updated_doc = await doc_manager.retrieve_full_document(document_id)
        print(f"✅ Summary updated: {updated_doc['summary'][:100]}...")
        print(f"   Status now: {updated_doc['processing_status']}")
        
        # Test 8: Get document statistics
        print("\n📊 Test 8: Get Document Statistics")
        stats = await doc_manager.get_document_statistics(test_session_id)
        print(f"✅ Statistics retrieved:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total words: {stats['total_word_count']}")
        print(f"   Content types: {stats['content_types']}")
        print(f"   Processing statuses: {stats['processing_statuses']}")
        
        # Test 9: Test error handling (try to get non-existent document)
        print("\n❌ Test 9: Error Handling")
        try:
            await doc_manager.retrieve_full_document("non_existent_doc_id")
            print("❌ Should have raised an error!")
        except Exception as e:
            print(f"✅ Error handling works: {str(e)[:100]}...")
        
        # Test 10: Delete document (optional - comment out to keep test data)
        print("\n🗑️ Test 10: Delete Document")
        delete_choice = input("Delete test document? (y/N): ").lower().strip()
        if delete_choice == 'y':
            delete_success = await doc_manager.delete_document(document_id)
            print(f"✅ Document deletion successful: {delete_success}")
            
            # Verify deletion
            try:
                await doc_manager.retrieve_full_document(document_id)
                print("❌ Document should have been deleted!")
            except Exception:
                print("✅ Document successfully deleted and cannot be retrieved")
        else:
            print("📋 Test document kept for further testing")
            print(f"   Document ID: {document_id}")
            print(f"   Session ID: {test_session_id}")
        
        print("\n🎉 All DocumentManager tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_multiple_documents():
    """Test handling of multiple documents in a session."""
    print("\n\n🔄 Testing Multiple Documents")
    print("=" * 40)
    
    doc_manager = DocumentManager()
    advisor_service = AdvisorWorkflowService()
    
    # Create a valid session for multi-document test
    session_result = await advisor_service.create_advisor_session(
        advisor_id="demo_advisor_001",
        title="Multi-Document Test Session"
    )
    
    if session_result["status"] != "success":
        raise Exception(f"Failed to create multi-doc session: {session_result.get('error', 'Unknown error')}")
    
    test_session_id = session_result["session"]["session_id"]
    print(f"🔧 Created multi-doc test session: {test_session_id}")
    
    # Create multiple test documents
    documents = [
        {
            "title": "Social Security Benefits Guide",
            "content_type": "pdf",
            "full_content": "Social Security benefits calculation depends on your earnings history. "
                          "Full retirement age varies by birth year. Early retirement reduces benefits. "
                          "Delayed retirement credits increase monthly payments.",
            "metadata": {"topic": "social_security"}
        },
        {
            "title": "Tax Planning Strategies",
            "content_type": "docx",
            "full_content": "Tax-loss harvesting can reduce your tax burden. Asset location matters "
                          "for tax efficiency. Consider Roth conversions in low-income years. "
                          "Municipal bonds may be beneficial for high earners.",
            "metadata": {"topic": "taxes"}
        },
        {
            "title": "Estate Planning Basics",
            "content_type": "txt",
            "full_content": "Wills and trusts are fundamental estate planning tools. Power of attorney "
                          "documents are essential. Beneficiary designations should be reviewed regularly. "
                          "Life insurance can provide liquidity for estate taxes.",
            "metadata": {"topic": "estate_planning"}
        }
    ]
    
    try:
        stored_docs = []
        for i, doc_data in enumerate(documents):
            doc_id = await doc_manager.store_document(doc_data, test_session_id)
            stored_docs.append(doc_id)
            print(f"✅ Stored document {i+1}: {doc_data['title']}")
        
        # Test session document retrieval
        session_docs = await doc_manager.get_session_documents(test_session_id, include_content=True)
        print(f"\n📚 Retrieved {len(session_docs)} documents from session")
        
        # Test relevant section extraction with different queries
        queries = ["social security retirement", "tax planning", "estate planning wills"]
        
        for query in queries:
            print(f"\n🔍 Testing query: '{query}'")
            for doc_id in stored_docs:
                try:
                    sections = await doc_manager.extract_relevant_sections(doc_id, query, max_length=300)
                    if "Relevant sections" in sections and len(sections) > 50:
                        doc_info = await doc_manager.retrieve_full_document(doc_id)
                        print(f"   ✅ Found relevant content in: {doc_info['title']}")
                except Exception as e:
                    print(f"   ⚠️ No relevant content found: {str(e)[:50]}...")
        
        # Get final statistics
        final_stats = await doc_manager.get_document_statistics(test_session_id)
        print(f"\n📊 Final Statistics:")
        print(f"   Total documents: {final_stats['total_documents']}")
        print(f"   Content types: {final_stats['content_types']}")
        
        print(f"\n✨ Multi-document test completed!")
        print(f"📋 Test session ID: {test_session_id}")
        print(f"📋 Document IDs: {stored_docs}")
        
    except Exception as e:
        print(f"❌ Multi-document test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting DocumentManager Test Suite")
    print("SCRUM-39: DocumentManager Class with CRUD Operations")
    print("=" * 60)
    
    # Run basic CRUD tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_document_manager())
        if success:
            # Run multi-document tests
            loop.run_until_complete(test_multiple_documents())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
    finally:
        loop.close()
    
    print("\n📋 Test completed. Check results above.")
    print("📖 Next: Test the API endpoints in FastAPI docs at /docs")
