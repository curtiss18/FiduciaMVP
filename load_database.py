import requests
import json

def load_to_database():
    """Load knowledge base files into PostgreSQL database"""
    url = "http://localhost:8000/api/v1/knowledge-base/load-to-database"
    
    try:
        print("Loading knowledge base files into database...")
        response = requests.post(url)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status').upper()}")
            
            if result.get('status') == 'success':
                print(f"Loaded {result.get('loaded_documents', 0)} documents")
                print("\nDocuments loaded:")
                for doc in result.get('documents', []):
                    print(f"  - {doc.get('title')} (ID: {doc.get('id')}, Type: {doc.get('document_type')})")
            else:
                print(f"Message: {result.get('message', '')}")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Connection Error: {str(e)}")

def check_database_summary():
    """Check what's in the database after loading"""
    url = "http://localhost:8000/api/v1/knowledge-base/database/summary"
    
    try:
        print("\nChecking database summary...")
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('summary', {})
            
            print("Database Summary:")
            print(f"  Total documents: {summary.get('total_documents', 0)}")
            print(f"  By type: {summary.get('by_type', {})}")
            print(f"  By platform: {summary.get('by_platform', {})}")
            
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Connection Error: {str(e)}")

if __name__ == "__main__":
    load_to_database()
    check_database_summary()
