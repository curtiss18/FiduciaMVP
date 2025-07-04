#!/usr/bin/env python3
"""
SCRUM-42 Integration Test - Simple Version

Tests the complete workflow without emoji characters.
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

async def test_backend_status():
    """Test if backend is running."""
    print("Testing backend connection...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE}/../health") as response:
                if response.status == 200:
                    print("Backend is running!")
                    return True
                else:
                    print("Backend not responding correctly")
                    return False
        except Exception as e:
            print(f"Backend connection failed: {str(e)}")
            return False

async def test_warren_without_documents():
    """Test Warren V3 without documents."""
    print("\nTesting Warren V3 without documents...")
    
    async with aiohttp.ClientSession() as session:
        warren_request = {
            "request": "Create a LinkedIn post about retirement planning",
            "content_type": "linkedin_post",
            "session_id": TEST_SESSION_ID
        }
        
        try:
            async with session.post(f"{API_BASE}/warren/generate-v3", json=warren_request) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("status") == "success":
                    print("Warren V3 working!")
                    print(f"Generated {len(result.get('content', ''))} characters")
                    return True
                else:
                    print(f"Warren failed: {result}")
                    return False
        except Exception as e:
            print(f"Warren error: {str(e)}")
            return False

async def test_document_upload():
    """Test document upload API."""
    print("\nTesting document upload...")
    
    # Create a simple test file
    test_content = """Investment Strategy Document
    
This document contains information about retirement planning strategies.
Key points include diversification, risk management, and long-term growth.
Asset allocation should be based on investor age and risk tolerance.
"""
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(test_content)
    temp_file.flush()
    temp_file.close()
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('session_id', TEST_SESSION_ID)
            
            with open(temp_file.name, 'rb') as f:
                data.add_field('files', f.read(), filename='test_doc.txt', content_type='text/plain')
            
            async with session.post(f"{API_BASE}/advisor/documents/upload-file", data=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("Document upload successful!")
                    batch_results = result.get('batch_results', {})
                    print(f"Success rate: {batch_results.get('success_rate', 0)*100:.1f}%")
                    return True
                else:
                    print(f"Upload failed: {result}")
                    return False
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return False
    finally:
        os.unlink(temp_file.name)

async def test_session_documents_retrieval():
    """Test if we can retrieve session documents."""
    print("\nTesting session documents retrieval...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE}/advisor/sessions/{TEST_SESSION_ID}/documents") as response:
                if response.status == 200:
                    documents = await response.json()
                    print(f"Found {len(documents)} documents for session")
                    return len(documents) > 0
                else:
                    result = await response.json()
                    print(f"Document retrieval failed: {result}")
                    return False
        except Exception as e:
            print(f"Document retrieval error: {str(e)}")
            return False

async def main():
    """Run integration test."""
    print("SCRUM-42 Integration Test")
    print("=" * 50)
    
    # Test backend connection
    if not await test_backend_status():
        print("Backend not available - please start the server")
        return
    
    # Test Warren without documents
    warren_basic = await test_warren_without_documents()
    
    # Test document upload
    upload_success = await test_document_upload()
    
    # Test document retrieval
    retrieval_success = False
    if upload_success:
        retrieval_success = await test_session_documents_retrieval()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Warren Basic: {'PASS' if warren_basic else 'FAIL'}")
    print(f"Document Upload: {'PASS' if upload_success else 'FAIL'}")
    print(f"Document Retrieval: {'PASS' if retrieval_success else 'FAIL'}")
    
    if warren_basic and upload_success and retrieval_success:
        print("\nAll tests passed! Ready for Warren document integration.")
    else:
        print("\nSome tests failed - check the issues above.")

if __name__ == "__main__":
    print("Make sure FastAPI server is running on localhost:8000")
    asyncio.run(main())
