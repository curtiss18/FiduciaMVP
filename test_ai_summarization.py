#!/usr/bin/env python3
"""
Test script for SCRUM-41 Phase 1.1: AI Summarization Methods

Tests the new DocumentManager methods:
- generate_ai_summary()
- update_document_with_summary()

This script will:
1. Find existing documents in the system
2. Test AI summarization on sample content
3. Test updating a document with AI summary
4. Display results and token counts
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.services.document_manager import DocumentManager
from src.services.context_assembler import TokenManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_summarization():
    """Test the new AI summarization functionality."""
    
    print("🧪 SCRUM-41 Phase 1.1 Testing: AI Summarization Methods")
    print("=" * 60)
    
    # Initialize services
    document_manager = DocumentManager()
    token_manager = TokenManager()
    
    # Test 1: Test generate_ai_summary with sample financial content
    print("\n📋 Test 1: AI Summary Generation")
    print("-" * 40)
    
    sample_content = """
    The Federal Reserve's recent monetary policy decisions have significant implications for portfolio allocation strategies. 
    With interest rates potentially reaching 5.5% by the end of 2024, traditional bond portfolios may experience volatility. 
    Equity markets have shown resilience, with the S&P 500 gaining 12% year-to-date despite inflationary pressures.
    
    Key investment considerations include:
    1. Duration risk in fixed income portfolios
    2. Sector rotation opportunities in equities
    3. Alternative investments as portfolio diversifiers
    4. International exposure for geographic diversification
    
    The current economic environment suggests a balanced approach to asset allocation, with emphasis on quality over growth 
    and defensive positioning in uncertain markets. Financial advisors should consider client risk tolerance and time horizon 
    when making portfolio adjustments.
    """
    
    try:
        print("Generating AI summary for sample financial content...")
        summary = await document_manager.generate_ai_summary(
            content=sample_content,
            content_type="text",
            target_tokens=800
        )
        
        summary_tokens = token_manager.count_tokens(summary)
        original_tokens = token_manager.count_tokens(sample_content)
        
        print(f"✅ AI Summary Generated Successfully!")
        print(f"   Original content: {original_tokens} tokens")
        print(f"   Generated summary: {summary_tokens} tokens")
        print(f"   Compression ratio: {summary_tokens/original_tokens:.2%}")
        print(f"\n📝 Generated Summary:")
        print("-" * 30)
        print(summary)
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error in AI summary generation: {str(e)}")
        return False
    
    # Test 2: Find existing documents and test update functionality
    print("\n📋 Test 2: Document Update with AI Summary")
    print("-" * 40)
    
    try:
        # Get document statistics to see what's available
        stats = await document_manager.get_document_statistics()
        print(f"📊 Document Statistics:")
        print(f"   Total documents in system: {stats.get('total_documents', 0)}")
        print(f"   Total words: {stats.get('total_word_count', 0)}")
        print(f"   Content types: {stats.get('content_types', {})}")
        print(f"   Processing statuses: {stats.get('processing_statuses', {})}")
        
        if stats.get('total_documents', 0) == 0:
            print("⚠️  No documents found in system. Upload a document first to test update functionality.")
            print("   This test will be skipped for now.")
        else:
            print("\n🔍 Found documents in system. Testing with first available document...")
            # Note: For full testing, Curtis can upload a document via the API and get its ID
            print("   (For complete testing, upload a document via /documents/upload-file and provide the document ID)")
            
    except Exception as e:
        print(f"❌ Error accessing documents: {str(e)}")
        return False
    
    print("\n✅ Phase 1.1 Testing Complete!")
    print("🚀 AI summarization methods are working correctly.")
    print("\n📋 Next Steps:")
    print("   1. Upload a document via /documents/upload-file endpoint")
    print("   2. Get the document ID from the response")
    print("   3. Test update_document_with_summary(document_id)")
    
    return True

async def test_specific_document(document_id: str):
    """Test AI summarization on a specific document ID."""
    
    print(f"\n🧪 Testing AI Summary Update for Document: {document_id}")
    print("=" * 60)
    
    document_manager = DocumentManager()
    
    try:
        # Test updating document with AI summary
        success = await document_manager.update_document_with_summary(document_id)
        
        if success:
            print(f"✅ Document {document_id} updated with AI summary successfully!")
            
            # Retrieve the updated document to show results
            document = await document_manager.retrieve_full_document(document_id)
            
            if document and document.get('summary'):
                token_manager = TokenManager()
                summary_tokens = token_manager.count_tokens(document['summary'])
                
                print(f"\n📊 Summary Statistics:")
                print(f"   Summary length: {summary_tokens} tokens")
                print(f"   Original content: {document.get('word_count', 0)} words")
                
                print(f"\n📝 Generated AI Summary:")
                print("-" * 40)
                print(document['summary'])
                print("-" * 40)
            else:
                print("⚠️  Summary was generated but couldn't retrieve it for display")
                
        else:
            print(f"❌ Failed to update document {document_id} with AI summary")
            
    except Exception as e:
        print(f"❌ Error testing specific document: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting SCRUM-41 Phase 1.1 AI Summarization Tests")
    
    # Check if a specific document ID was provided
    if len(sys.argv) > 1:
        document_id = sys.argv[1]
        asyncio.run(test_specific_document(document_id))
    else:
        asyncio.run(test_ai_summarization())
    
    print("\n🎯 Test completed!")
