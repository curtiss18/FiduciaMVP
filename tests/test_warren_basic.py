import requests
import json

# Test Warren content generation
def test_warren():
    url = "http://localhost:8000/api/v1/warren/generate"
    
    test_request = {
        "request": "Create a LinkedIn post about retirement planning for someone in their 40s",
        "content_type": "linkedin"
    }
    
    try:
        response = requests.post(url, json=test_request)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Warren Test SUCCESS!")
            print(f"Status: {result.get('status')}")
            print(f"Knowledge sources used: {result.get('knowledge_sources_used')}")
            print(f"Content type: {result.get('content_type')}")
            print("\n📝 Generated Content:")
            print("=" * 60)
            print(result.get('content', 'No content generated'))
            print("=" * 60)
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    test_warren()
