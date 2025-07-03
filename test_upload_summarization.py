#!/usr/bin/env python3
"""
Test script for SCRUM-41 Phase 1.3: Upload Workflow with AI Summarization

Tests the enhanced /documents/upload-file endpoint with automatic AI summarization.
This verifies that all new document uploads automatically get AI summaries.
"""

import asyncio
import requests
import json
import os

def test_upload_with_summarization():
    """Test document upload with automatic AI summarization."""
    
    print("🧪 SCRUM-41 Phase 1.3 Testing: Upload Workflow with AI Summarization")
    print("=" * 70)
    
    # Test with a sample text file
    test_content = """
    Investment Portfolio Review - Q4 2024
    
    Executive Summary:
    Our portfolio has shown strong performance this quarter with a 8.5% total return.
    The equity allocation performed particularly well, driven by technology and healthcare sectors.
    
    Asset Allocation:
    - Equities: 65% (Target: 60%)
    - Fixed Income: 25% (Target: 30%) 
    - Alternatives: 10% (Target: 10%)
    
    Key Performance Metrics:
    - Total Return: 8.5%
    - Benchmark (S&P 500): 7.2%
    - Alpha Generation: +1.3%
    - Sharpe Ratio: 1.42
    - Maximum Drawdown: -2.1%
    
    Sector Performance:
    Technology: +12.3%
    Healthcare: +9.8%
    Financial Services: +6.4%
    Energy: +3.2%
    Consumer Discretionary: +5.1%
    
    Risk Analysis:
    The portfolio currently has a beta of 0.95, indicating slightly lower volatility than the market.
    Correlation analysis shows good diversification across sectors.
    Value at Risk (95% confidence): -3.2%
    
    Recommendations:
    1. Rebalance to target allocations
    2. Consider increasing fixed income exposure
    3. Monitor technology sector concentration
    4. Evaluate ESG integration opportunities
    
    Market Outlook:
    Economic indicators suggest continued growth with moderate inflation.
    Federal Reserve policy remains accommodative.
    Recommend maintaining current strategic allocation with tactical adjustments.
    """
    
    # Save test content to a temporary file
    test_filename = "test_portfolio_review.txt"
    file_handle = None
    
    try:
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        print(f"📁 Created test file: {test_filename}")
        print(f"   Content length: {len(test_content)} characters")
        print(f"   Word count: ~{len(test_content.split())} words")
        
        # Step 1: Create a valid advisor session first
        session_api_url = "http://localhost:8000/api/v1/advisor/sessions/create"
        print(f"\n🔧 Creating advisor session first...")
        
        session_response = requests.post(session_api_url, json={
            "advisor_id": "test-advisor-scrum41",  # Required field
            "title": "SCRUM-41 Testing Session"
        })
        
        if session_response.status_code != 200:
            print(f"❌ Failed to create session!")
            print(f"   Status: {session_response.status_code}")
            print(f"   Response: {session_response.text}")
            return
        
        session_data = session_response.json()
        session_id = session_data.get('session', {}).get('session_id')
        print(f"✅ Session created: {session_id}")
        
        if not session_id:
            print(f"❌ No session_id in response!")
            print(f"   Full response: {session_data}")
            return
        
        # Step 2: Test API endpoint with valid session
        api_url = "http://localhost:8000/api/v1/advisor/documents/upload-file"
        
        print(f"\n🚀 Testing Enhanced Upload Endpoint: {api_url}")
        print("   This should now include automatic AI summarization...")
        
        # Prepare the request with proper file handling
        with open(test_filename, 'rb') as file_handle:
            files = {
                'file': (test_filename, file_handle, 'text/plain')
            }
            data = {
                'session_id': session_id,  # Use valid session ID
                'title': 'Q4 2024 Portfolio Review - AI Summarization Test'
            }
            
            print(f"\n📤 Uploading document with auto-summarization...")
            response = requests.post(api_url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"\n📊 Response Details:")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Message: {result.get('message')}")
            
            processing_results = result.get('processing_results', {})
            print(f"\n📋 Processing Results:")
            print(f"   Word count: {processing_results.get('word_count')}")
            print(f"   Processing time: {processing_results.get('processing_time_ms')}ms")
            
            # Check AI summarization results (new in Phase 1.3)
            if processing_results.get('summary_generated'):
                print(f"\n🎉 AI SUMMARIZATION SUCCESS!")
                print(f"   Summary tokens: {processing_results.get('summary_tokens')}")
                print(f"   Summary preview: {processing_results.get('summary_preview')}")
                
                # Calculate compression ratio
                original_chars = len(test_content)
                summary_preview = processing_results.get('summary_preview', '')
                if summary_preview:
                    compression_ratio = len(summary_preview) / original_chars
                    print(f"   Compression ratio: {compression_ratio:.1%} (preview only)")
                
                print(f"\n✅ Phase 1.3 SUCCESS: Upload workflow now includes automatic AI summarization!")
                
            else:
                print(f"\n❌ AI Summarization Issues:")
                if processing_results.get('summary_error'):
                    print(f"   Error: {processing_results.get('summary_error')}")
                else:
                    print(f"   No summary information in response")
                    
            # Pretty print full response for debugging
            print(f"\n🔍 Full API Response:")
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ Upload failed!")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   Make sure the backend is running:")
        print("   uvicorn src.main:app --reload")
        
    except Exception as e:
        print(f"❌ Test Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up test file (with proper error handling)
        try:
            if os.path.exists(test_filename):
                os.remove(test_filename)
                print(f"\n🧹 Cleaned up test file: {test_filename}")
        except Exception as e:
            print(f"\n⚠️  Could not remove test file: {str(e)}")
    
    print(f"\n🎯 Phase 1.3 Test Complete!")

if __name__ == "__main__":
    test_upload_with_summarization()
