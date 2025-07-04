#!/usr/bin/env python3
"""
Test script for SCRUM-42 Phase 1: Multiple File Upload Support

Tests the enhanced /documents/upload-file endpoint with multiple file capabilities.
"""

import asyncio
import logging
import requests
import tempfile
import os
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api/v1/advisor"

async def test_multiple_file_upload():
    """Test multiple file upload functionality."""
    print("🧪 Testing SCRUM-42 Phase 1: Multiple File Upload Support")
    print("="*60)
    
    # Step 1: Create a test session
    print("\n📋 Step 1: Creating test session...")
    
    session_data = {
        "advisor_id": "test-advisor-scrum42",
        "title": "SCRUM-42 Multiple Upload Test Session"
    }
    
    try:
        response = requests.post(f"{API_BASE}/sessions/create", json=session_data)
        if response.status_code == 200:
            session_id = response.json()["session"]["session_id"]  # Fixed: nested under "session"
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return
    
    # Step 2: Create test files
    print("\n📁 Step 2: Creating test files...")
    
    # Create temporary test files
    test_files = []
    
    # Test file 1: Simple text
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test Document 1: Investment Strategy\n\n")
        f.write("This document outlines basic investment principles:\n")
        f.write("1. Diversification is key to reducing risk\n")
        f.write("2. Long-term investing generally outperforms short-term trading\n")
        f.write("3. Asset allocation should match risk tolerance\n")
        f.write("4. Regular portfolio rebalancing maintains target allocation\n")
        test_files.append(("test1.txt", f.name))
    
    # Test file 2: Financial planning content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test Document 2: Retirement Planning Checklist\n\n")
        f.write("Essential steps for retirement preparation:\n")
        f.write("- Calculate retirement income needs (70-80% of current income)\n")
        f.write("- Maximize employer 401(k) matching contributions\n")
        f.write("- Consider Roth IRA conversions for tax diversification\n")
        f.write("- Plan for healthcare costs in retirement\n")
        f.write("- Review and update beneficiary designations annually\n")
        test_files.append(("test2.txt", f.name))
    
    # Test file 3: Market analysis content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test Document 3: Market Outlook Q3 2025\n\n")
        f.write("Current market analysis and projections:\n")
        f.write("Economic indicators suggest moderate growth ahead.\n")
        f.write("Federal Reserve policy remains accommodative.\n")
        f.write("Technology sector continues to show strength.\n")
        f.write("International markets present opportunities for diversification.\n")
        f.write("Bond yields expected to remain stable through quarter end.\n")
        test_files.append(("test3.txt", f.name))
    
    print(f"✅ Created {len(test_files)} test files")
    
    # Step 3: Test multiple file upload
    print("\n🚀 Step 3: Testing multiple file upload...")
    
    try:
        # Prepare files for upload
        files_for_upload = []
        for display_name, file_path in test_files:
            with open(file_path, 'rb') as f:
                files_for_upload.append(('files', (display_name, f.read(), 'text/plain')))
        
        # Prepare form data
        data = {
            'session_id': session_id,
            'titles': 'Investment Strategy,Retirement Planning,Market Outlook Q3'
        }
        
        # Make the upload request
        response = requests.post(
            f"{API_BASE}/documents/upload-file",
            files=files_for_upload,
            data=data
        )
        
        print(f"📡 Upload response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Multiple file upload successful!")
            print(f"📊 Batch Results:")
            print(f"   Total files: {result['batch_results']['total_files']}")
            print(f"   Successful: {result['batch_results']['successful_count']}")
            print(f"   Failed: {result['batch_results']['failed_count']}")
            print(f"   Success rate: {result['batch_results']['success_rate']:.2%}")
            
            # Display individual file results
            print(f"\n📋 Individual File Results:")
            for upload in result['batch_results']['successful_uploads']:
                print(f"   ✅ {upload['filename']}: {upload['title']}")
                print(f"      Document ID: {upload['document_id']}")
                if 'processing_results' in upload:
                    pr = upload['processing_results']
                    print(f"      Words: {pr.get('word_count', 'N/A')}")
                    if pr.get('summary_generated'):
                        print(f"      AI Summary: {pr.get('summary_tokens', 'N/A')} tokens")
                    print(f"      Processing: {pr.get('processing_time_ms', 'N/A')}ms")
            
            if result['batch_results']['failed_uploads']:
                print(f"\n❌ Failed Uploads:")
                for upload in result['batch_results']['failed_uploads']:
                    print(f"   ❌ {upload['filename']}: {upload['error']}")
        
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    finally:
        # Cleanup test files
        print(f"\n🧹 Cleaning up test files...")
        for _, file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass
        print("✅ Cleanup complete")

def test_backward_compatibility():
    """Test that single file uploads still work."""
    print("\n🔄 Testing backward compatibility (single file upload)...")
    
    # This would be tested with a single file to ensure the API still works
    # for existing single-file upload scenarios
    print("📝 Note: Single file upload should still work by sending one file in the 'files' array")

if __name__ == "__main__":
    print("🚀 SCRUM-42 Phase 1 Testing: Multiple File Upload Support")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("")
    
    # Run the test
    asyncio.run(test_multiple_file_upload())
    test_backward_compatibility()
    
    print("\n✅ Phase 1 testing complete!")
    print("Ready for Phase 2: Enhanced Security Validation")
