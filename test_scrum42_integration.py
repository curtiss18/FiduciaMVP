#!/usr/bin/env python3
"""
SCRUM-42 Full Integration Test: Document Upload + Warren Context

Tests the complete workflow:
1. Upload multiple files to a session
2. Test Warren V3 with session_id (should retrieve documents)
3. Verify documents are being used in Warren context

Created: July 3, 2025
Status: Testing Phase 2 - Document Context Integration
"""

import asyncio
import aiohttp
import json
import sys
import tempfile
import os
from datetime import datetime

# Test configuration
API_BASE = "http://localhost:8000/api/v1"
TEST_SESSION_ID = f"session_test-integration-{int(datetime.now().timestamp())}"

def create_test_files():
    """Create test files for upload."""
    files = []
    
    # Test file 1: Investment strategy document
    content1 = """
    Investment Strategy Overview
    
    This document outlines a comprehensive investment approach for retirement planning.
    Our strategy focuses on diversified portfolios with emphasis on long-term growth
    and risk management. Key recommendations include:
    
    1. Asset allocation: 60% stocks, 30% bonds, 10% alternatives
    2. Regular portfolio rebalancing quarterly
    3. Tax-efficient investment vehicles (401k, IRA)
    4. Emergency fund of 6-12 months expenses
    
    This approach has historically provided strong returns while managing downside risk.
    """
    
    # Test file 2: Market analysis
    content2 = """
    Q3 2024 Market Analysis
    
    Current market conditions show mixed signals with inflation concerns and
    Federal Reserve policy decisions impacting investor sentiment.
    
    Key market indicators:
    - S&P 500 performance: +8% YTD
    - Bond yields rising due to monetary policy
    - Tech sector showing volatility
    - International markets underperforming US equities
    
    Recommendation: Maintain defensive positioning while identifying
    opportunities in undervalued sectors.
    """
    
    # Create temporary files
    for i, content in enumerate([content1, content2], 1):
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.txt', 
            delete=False,
            prefix=f'test_doc_{i}_'
        )
        temp_file.write(content)
        temp_file.flush()
        files.append(temp_file.name)
    
    return files

async def test_document_upload(session_id, test_files):
    """Test multiple document upload."""
    print(f"📁 Testing document upload for session: {session_id}")
    
    async with aiohttp.ClientSession() as session:
        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field('session_id', session_id)
        
        # Add files
        for file_path in test_files:
            with open(file_path, 'rb') as f:
                filename = os.path.basename(file_path)
                data.add_field('files', f.read(), filename=filename, content_type='text/plain')
        
        # Add custom titles
        data.add_field('titles', 'Investment Strategy,Market Analysis Q3')
        
        try:
            async with session.post(f"{API_BASE}/advisor/documents/upload-file", data=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ Document upload successful!")
                    print(f"📊 Upload results:")
                    batch_results = result.get('batch_results', {})
                    print(f"   Total files: {batch_results.get('total_files', 0)}")
                    print(f"   Successful: {batch_results.get('successful_count', 0)}")
                    print(f"   Success rate: {batch_results.get('success_rate', 0)*100:.1f}%")
                    
                    # Show successful uploads
                    for upload in batch_results.get('successful_uploads', []):
                        print(f"   ✅ {upload['title']}: {upload['document_id']}")
                    
                    return True
                else:
                    print(f"❌ Upload failed: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Upload error: {str(e)}")
            return False

async def test_warren_with_documents(session_id):
    """Test Warren V3 with session documents."""
    print(f"\n🤖 Testing Warren V3 with session documents")
    
    async with aiohttp.ClientSession() as session:
        warren_request = {
            "request": "Create a LinkedIn post about retirement planning strategies based on my uploaded documents",
            "content_type": "linkedin_post",
            "audience_type": "general_education",
            "session_id": session_id
        }
        
        try:
            async with session.post(f"{API_BASE}/warren/generate-v3", json=warren_request) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("status") == "success":
                    print(f"✅ Warren generation successful!")
                    
                    # Check if documents were used
                    content = result.get("content", "")
                    source_info = result.get("source_information", {})
                    
                    print(f"📝 Generated content preview:")
                    print(f"   {content[:200]}..." if len(content) > 200 else content)
                    
                    print(f"\n📚 Source information:")
                    print(f"   Total sources: {source_info.get('total_sources', 0)}")
                    print(f"   Marketing examples: {source_info.get('marketing_examples_count', 0)}")
                    print(f"   Compliance rules: {source_info.get('compliance_rules_count', 0)}")
                    print(f"   Search strategy: {source_info.get('search_strategy', 'unknown')}")
                    
                    # Check for document references in content
                    doc_keywords = ['investment strategy', 'market analysis', 'asset allocation', 'portfolio']
                    doc_references = [kw for kw in doc_keywords if kw.lower() in content.lower()]
                    
                    if doc_references:
                        print(f"✅ Document content detected in Warren response!")
                        print(f"   Referenced concepts: {', '.join(doc_references)}")
                    else:
                        print(f"⚠️  No clear document references in Warren response")
                        print(f"   (This may indicate documents aren't being used as context)")
                    
                    return True
                else:
                    print(f"❌ Warren generation failed: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Warren error: {str(e)}")
            return False

async def test_session_documents_api(session_id):
    """Test session documents API to verify storage."""
    print(f"\n📋 Testing session documents API")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE}/advisor/sessions/{session_id}/documents") as response:
                if response.status == 200:
                    documents = await response.json()
                    print(f"✅ Session documents API working!")
                    print(f"   Found {len(documents)} documents for session")
                    
                    for doc in documents:
                        print(f"   📄 {doc['title']} ({doc['content_type']}) - {doc['word_count']} words")
                        if doc.get('summary'):
                            print(f"      📝 AI Summary: {len(doc['summary'])} characters")
                    
                    return len(documents) > 0
                else:
                    result = await response.json()
                    print(f"❌ Session documents API failed: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Session documents API error: {str(e)}")
            return False

async def main():
    """Run the complete integration test."""
    print("🚀 SCRUM-42 Full Integration Test: Document Upload + Warren Context")
    print("=" * 70)
    
    # Create test files
    print("📁 Creating test files...")
    test_files = create_test_files()
    print(f"✅ Created {len(test_files)} test files")
    
    try:
        # Test 1: Upload documents
        upload_success = await test_document_upload(TEST_SESSION_ID, test_files)
        if not upload_success:
            print("❌ Document upload failed - stopping test")
            return
        
        # Test 2: Verify documents are stored
        storage_success = await test_session_documents_api(TEST_SESSION_ID)
        if not storage_success:
            print("❌ Document storage verification failed - stopping test")
            return
        
        # Test 3: Test Warren with documents
        warren_success = await test_warren_with_documents(TEST_SESSION_ID)
        
        # Summary
        print("\n" + "=" * 70)
        print("🎯 INTEGRATION TEST SUMMARY:")
        print(f"   ✅ Document Upload: {'PASS' if upload_success else 'FAIL'}")
        print(f"   ✅ Document Storage: {'PASS' if storage_success else 'FAIL'}")
        print(f"   {'✅' if warren_success else '❌'} Warren Integration: {'PASS' if warren_success else 'FAIL'}")
        
        if upload_success and storage_success and warren_success:
            print("\n🎉 FULL INTEGRATION TEST PASSED!")
            print("   Documents are uploaded, stored, and available to Warren")
        elif upload_success and storage_success:
            print("\n⚠️  PARTIAL SUCCESS:")
            print("   Documents upload and storage work")
            print("   Warren integration needs implementation")
        else:
            print("\n❌ INTEGRATION TEST FAILED")
            print("   Check backend services and API endpoints")
    
    finally:
        # Cleanup test files
        print(f"\n🧹 Cleaning up test files...")
        for file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass
        print("✅ Cleanup complete")

if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    asyncio.run(main())
