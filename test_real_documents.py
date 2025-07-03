#!/usr/bin/env python3
"""
List existing documents and test AI summarization with a real document
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.services.document_manager import DocumentManager
from src.core.database import AsyncSessionLocal
from src.models.advisor_workflow_models import SessionDocuments
from sqlalchemy import select

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_documents_and_test():
    """List documents and test AI summarization."""
    
    print("🧪 SCRUM-41 Phase 1.1: Testing with Real Documents")
    print("=" * 60)
    
    document_manager = DocumentManager()
    
    # List all documents
    print("\n📋 Available Documents:")
    print("-" * 40)
    
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(SessionDocuments).limit(10)
            result = await db.execute(stmt)
            documents = result.scalars().all()
            
            if not documents:
                print("❌ No documents found in system")
                return
            
            for i, doc in enumerate(documents, 1):
                print(f"{i}. ID: {doc.id}")
                print(f"   Title: {doc.title}")
                print(f"   Type: {doc.content_type}")
                print(f"   Words: {doc.word_count}")
                print(f"   Status: {doc.processing_status}")
                print(f"   Has Summary: {'Yes' if doc.summary else 'No'}")
                print(f"   Content Preview: {doc.full_content[:100]}...")
                print()
            
            # Test with the first document that has content
            test_doc = None
            for doc in documents:
                if doc.full_content and len(doc.full_content.strip()) > 100:
                    test_doc = doc
                    break
            
            if not test_doc:
                print("❌ No documents with sufficient content found for testing")
                return
            
            print(f"🧪 Testing AI Summarization with Document: {test_doc.id}")
            print(f"   Title: {test_doc.title}")
            print(f"   Type: {test_doc.content_type}")
            print(f"   Words: {test_doc.word_count}")
            print("-" * 60)
            
            # Test AI summarization
            success = await document_manager.update_document_with_summary(test_doc.id)
            
            if success:
                print("✅ AI Summary Generated Successfully!")
                
                # Retrieve the updated document
                updated_doc = await document_manager.retrieve_full_document(test_doc.id)
                
                if updated_doc and updated_doc.get('summary'):
                    from src.services.context_assembler import TokenManager
                    token_manager = TokenManager()
                    summary_tokens = token_manager.count_tokens(updated_doc['summary'])
                    
                    print(f"\n📊 Summary Statistics:")
                    print(f"   Original content: {updated_doc.get('word_count', 0)} words")
                    print(f"   Summary length: {summary_tokens} tokens")
                    print(f"   Target: 800 tokens")
                    print(f"   Efficiency: {summary_tokens <= 960}")  # Within 20% buffer
                    
                    print(f"\n📝 Generated AI Summary:")
                    print("-" * 50)
                    print(updated_doc['summary'])
                    print("-" * 50)
                    
                    # Check metadata
                    if updated_doc.get('metadata'):
                        metadata = updated_doc['metadata']
                        if isinstance(metadata, dict) and metadata.get('ai_summary_generated'):
                            print(f"\n🔍 Summarization Metadata:")
                            print(f"   Generated at: {metadata.get('summary_generated_at')}")
                            print(f"   Token count: {metadata.get('summary_token_count')}")
                            print(f"   Version: {metadata.get('summarization_version')}")
                else:
                    print("⚠️  Summary was generated but couldn't retrieve it")
            else:
                print("❌ Failed to generate AI summary")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_documents_and_test())
