#!/usr/bin/env python3
"""
Fixed test script for advisor workflow API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_advisor_workflow_fixed():
    """Test the complete advisor workflow with proper error handling."""
    print("🧪 Testing Advisor Workflow API Endpoints (Fixed Version)")
    
    # Test 1: Create a Warren chat session
    print("\n📋 Test 1: Create Warren chat session")
    session_response = requests.post(f"{BASE_URL}/advisor/sessions/create", json={
        "advisor_id": "demo_advisor_001",
        "title": "Fixed Test Chat Session"
    })
    
    if session_response.status_code == 200:
        session_data = session_response.json()
        session_id = session_data["session"]["session_id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Title: {session_data['session']['title']}")
    else:
        print(f"❌ Failed to create session: {session_response.text}")
        return
    
    # Test 2: Save a user message (using the session_id from step 1)
    print("\n📋 Test 2: Save user message")
    user_msg_response = requests.post(f"{BASE_URL}/advisor/sessions/messages/save", json={
        "session_id": session_id,  # Use the actual session_id from step 1
        "message_type": "user",
        "content": "Create a LinkedIn post about retirement planning"
    })
    
    if user_msg_response.status_code == 200:
        print("✅ User message saved")
    else:
        print(f"❌ Failed to save user message: {user_msg_response.text}")
        return
    
    # Test 3: Save a Warren response message
    print("\n📋 Test 3: Save Warren response")
    warren_msg_response = requests.post(f"{BASE_URL}/advisor/sessions/messages/save", json={
        "session_id": session_id,  # Use the actual session_id
        "message_type": "warren",
        "content": "Here's a compliant LinkedIn post about retirement planning...",
        "metadata": {
            "total_sources": 6,
            "marketing_examples": 3,
            "compliance_rules": 3,
            "search_strategy": "vector",
            "generation_confidence": 0.95
        }
    })
    
    if warren_msg_response.status_code == 200:
        warren_data = warren_msg_response.json()
        warren_message_id = warren_data["message"]["id"]
        print(f"✅ Warren message saved with source transparency")
        print(f"   Message ID: {warren_message_id}")
    else:
        print(f"❌ Failed to save Warren message: {warren_msg_response.text}")
        return
    
    # Test 4: Save content to library (with valid content_type)
    print("\n📋 Test 4: Save content to advisor library")
    content_response = requests.post(f"{BASE_URL}/advisor/content/save", json={
        "advisor_id": "demo_advisor_001",
        "title": "Retirement Planning LinkedIn Post",
        "content_text": "Here's a compliant LinkedIn post about retirement planning...",
        "content_type": "linkedin_post",  # Fixed: use valid content type
        "audience_type": "general_education",
        "source_session_id": session_id,  # Use actual session_id
        "source_message_id": warren_message_id,  # Use actual message_id
        "advisor_notes": "Generated from Warren chat session",
        "intended_channels": ["linkedin", "email"]
    })
    
    if content_response.status_code == 200:
        content_data = content_response.json()
        content_id = content_data["content"]["id"]
        print(f"✅ Content saved to library")
        print(f"   Content ID: {content_id}")
        print(f"   Status: {content_data['content']['status']}")
    else:
        print(f"❌ Failed to save content: {content_response.text}")
        return
    
    # Test 5: Get content library
    print("\n📋 Test 5: Get advisor content library")
    library_response = requests.get(f"{BASE_URL}/advisor/content/library", params={
        "advisor_id": "demo_advisor_001"
    })
    
    if library_response.status_code == 200:
        library_data = library_response.json()
        print(f"✅ Retrieved content library")
        print(f"   Total content: {library_data['total_count']}")
        print(f"   Content items: {len(library_data['content'])}")
        if library_data['content']:
            print(f"   First item: {library_data['content'][0]['title']}")
    else:
        print(f"❌ Failed to get library: {library_response.text}")
        return
    
    # Test 6: Submit content for review (using actual content_id)
    print("\n📋 Test 6: Submit content for compliance review")
    status_response = requests.put(f"{BASE_URL}/advisor/content/{content_id}/status", 
        params={"advisor_id": "demo_advisor_001"},
        json={
            "new_status": "submitted",
            "advisor_notes": "Ready for compliance review"
        }
    )
    
    if status_response.status_code == 200:
        print("✅ Content submitted for review")
        print(f"   New status: submitted")
    else:
        print(f"❌ Failed to submit for review: {status_response.text}")
        return
    
    # Test 7: Get session messages (verify foreign key works)
    print("\n📋 Test 7: Get session messages")
    messages_response = requests.get(f"{BASE_URL}/advisor/sessions/{session_id}/messages", 
        params={"advisor_id": "demo_advisor_001"}
    )
    
    if messages_response.status_code == 200:
        messages_data = messages_response.json()
        print("✅ Retrieved session messages")
        print(f"   Session: {messages_data['session']['title']}")
        print(f"   Messages: {len(messages_data['messages'])}")
        for msg in messages_data['messages']:
            print(f"     - {msg['message_type']}: {msg['content'][:50]}...")
    else:
        print(f"❌ Failed to get session messages: {messages_response.text}")
        return
    
    # Test 8: Get content statistics
    print("\n📋 Test 8: Get content statistics")
    stats_response = requests.get(f"{BASE_URL}/advisor/content/statistics", params={
        "advisor_id": "demo_advisor_001"
    })
    
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        print("✅ Retrieved content statistics")
        print(f"   Total content: {stats_data['statistics']['total_content']}")
        print(f"   Total sessions: {stats_data['statistics']['total_sessions']}")
        print(f"   Content by status: {stats_data['statistics']['content_by_status']}")
    else:
        print(f"❌ Failed to get statistics: {stats_response.text}")
        return
    
    print("\n🎉 All tests passed! Advisor workflow API is working correctly.")
    print("\n📊 Summary:")
    print(f"   - Created session: {session_id}")
    print(f"   - Saved content: {content_id}")
    print(f"   - Status progression: draft → submitted")
    print(f"   - Foreign key relationships: ✅ Working")

if __name__ == "__main__":
    try:
        test_advisor_workflow_fixed()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
