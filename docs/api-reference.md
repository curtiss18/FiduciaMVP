# FiduciaMVP API Documentation

## 🚀 **Base URL**
```
http://localhost:8000/api/v1
```

**Interactive Documentation**: `http://localhost:8000/docs`

## 🤖 **Warren AI Endpoints**

### **Generate Content (Enhanced)**
Generate compliant marketing content using vector search + fallbacks.

```http
POST /warren/generate-v3
```

**Request Body:**
```json
{
    "request": "Create a LinkedIn post about retirement planning for someone in their 40s",
    "content_type": "linkedin_post",
    "audience_type": "general_education",
    "user_id": "optional_user_id",
    "session_id": "optional_session_id"
}
```

**Response:**
```json
{
    "status": "success",
    "content": "Generated compliant marketing content...",
    "content_type": "linkedin_post",
    "search_strategy": "vector",
    "vector_results_found": 3,
    "text_results_found": 0,
    "total_knowledge_sources": 5,
    "fallback_used": false,
    "context_quality_score": 0.85,
    "user_request": "Original request..."
}
```

**Content Types:**
- `linkedin_post` - LinkedIn social media posts
- `email_template` - Email marketing templates
- `newsletter` - Newsletter content
- `website_copy` - Website marketing copy

**Audience Types:**
- `general_education` - Educational content for general audience
- `client_communication` - Existing client communications
- `prospect_advertising` - New prospect marketing

---

### **Generate Content (Database)**
Fallback generation using database search only.

```http
POST /warren/generate-v2
```

**Request Body:**
```json
{
    "request": "Content request",
    "content_type": "linkedin_post",
    "audience_type": "general_education"
}
```

## 🔍 **Vector Search Endpoints**

### **Test Vector Search**
Test semantic search functionality with custom queries.

```http
POST /vector-search/test
```

**Request Body:**
```json
{
    "query": "retirement planning",
    "content_type": "linkedin_post",
    "limit": 3
}
```

**Response:**
```json
{
    "status": "success",
    "query": "retirement planning",
    "content_type": "linkedin_post",
    "results_found": 3,
    "results": [
        {
            "id": 1,
            "title": "LinkedIn Example 1: Economic Education/Analysis",
            "content_text": "Content preview...",
            "similarity_score": 0.3792,
            "content_type": "linkedin_post",
            "tags": "retirement, planning, education"
        }
    ]
}
```

---

### **Vector Search Statistics**
Get statistics about vector search system readiness.

```http
GET /vector-search/stats
```

**Response:**
```json
{
    "status": "success",
    "vector_search_stats": {
        "marketing_content": {
            "total": 29,
            "with_embeddings": 29,
            "embedding_percentage": 100.0
        },
        "vector_search_ready": true
    }
}
```

---

### **System Readiness Check**
Comprehensive check of vector search system components.

```http
GET /vector-search/readiness
```

**Response:**
```json
{
    "status": "success",
    "ready_for_production": true,
    "components": {
        "embedding_service": {
            "status": "success",
            "model": "text-embedding-3-large",
            "dimensions": 1536
        },
        "vectorization_status": {
            "vector_search_available": true
        }
    },
    "next_steps": [
        "Vector search ready",
        "Test /warren/generate-v3 endpoint",
        "Monitor performance"
    ]
}
```

## 🎯 **Embedding Management**

### **Test Embedding Service**
Test OpenAI embedding service connectivity.

```http
POST /embeddings/test
```

**Response:**
```json
{
    "status": "success",
    "embedding_test": {
        "status": "success",
        "model": "text-embedding-3-large",
        "dimensions": 1536,
        "response_time_ms": 245.3,
        "token_count": 4,
        "estimated_cost": 0.000001
    }
}
```

---

### **Vectorize Content**
Generate embeddings for existing marketing content.

```http
POST /embeddings/vectorize-content?force_update=false
```

**Response:**
```json
{
    "status": "success",
    "message": "Vectorization completed",
    "processed": 29,
    "errors": 0,
    "total_items": 29,
    "estimated_cost": 0.0004,
    "batch_count": 3
}
```

---

### **Vectorization Status**
Check current status of content vectorization.

```http
GET /embeddings/status
```

**Response:**
```json
{
    "status": "success",
    "vectorization_status": {
        "marketing_content": {
            "total_approved": 29,
            "vectorized": 29,
            "pending": 0,
            "completion_percentage": 100.0
        },
        "overall_status": "ready",
        "vector_search_available": true
    }
}
```

---

### **Cost Estimation**
Estimate the cost of vectorizing unprocessed content.

```http
GET /embeddings/cost-estimate
```

**Response:**
```json
{
    "status": "success",
    "cost_estimate": {
        "marketing_content": {
            "items": 0,
            "estimated_tokens": 0,
            "estimated_cost": 0.0000
        },
        "total": {
            "items": 0,
            "estimated_tokens": 0,
            "estimated_cost": 0.0000
        },
        "note": "Estimated cost is approximately $0.0000 for 0 tokens"
    }
}
```

## 📚 **Knowledge Base Endpoints**

### **Database Summary**
Get overview of content in the database.

```http
GET /knowledge-base/database/summary
```

**Response:**
```json
{
    "status": "success",
    "summary": {
        "database_type": "refactored_granular",
        "marketing_content_total": 29,
        "content_by_type": {
            "linkedin_post": 3,
            "email_template": 26
        },
        "compliance_rules_total": 12,
        "warren_interactions_total": 15,
        "last_updated": "2025-06-11T14:00:00Z"
    }
}
```

---

### **Search Database Content**
Search knowledge base content using text search.

```http
GET /knowledge-base/database/search?query=retirement&limit=5
```

**Response:**
```json
{
    "status": "success",
    "results": [
        {
            "id": 1,
            "title": "LinkedIn Example 1",
            "document_type": "linkedin_post",
            "content_preview": "Content preview...",
            "compliance_score": 1.0
        }
    ],
    "query": "retirement"
}
```

## 🔧 **System Endpoints**

### **Health Check**
Basic system health verification.

```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "service": "FiduciaMVP"
}
```

---

### **Test Database**
Test database connectivity.

```http
GET /test-database
```

**Response:**
```json
{
    "status": "success",
    "message": "Database connection successful"
}
```

---

### **Test Claude AI**
Test Claude AI service connectivity.

```http
GET /test-claude
```

**Response:**
```json
{
    "status": "success",
    "message": "Claude API connection successful"
}
```

## 📊 **Response Codes**

| Code | Status | Description |
|------|--------|-------------|
| `200` | Success | Request completed successfully |
| `400` | Bad Request | Invalid request parameters |
| `404` | Not Found | Endpoint or resource not found |
| `500` | Server Error | Internal server error |

## 🔐 **Authentication**

Currently, the API operates without authentication for development. Production deployment will include:

- **API Key Authentication** for external integrations
- **JWT Tokens** for user sessions
- **Role-based Access Control** for multi-tenant usage

## 📈 **Rate Limiting**

Development environment has no rate limits. Production will implement:

- **100 requests/minute** per API key
- **10 Warren generations/minute** per user
- **5 vectorization requests/hour** per account

## 💡 **Usage Examples**

### **Basic Warren Usage**

```bash
# Generate LinkedIn content
curl -X POST "http://localhost:8000/api/v1/warren/generate-v3" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Create a LinkedIn post about retirement planning",
    "content_type": "linkedin_post"
  }'
```

### **Vector Search Testing**

```bash
# Test semantic search
curl -X POST "http://localhost:8000/api/v1/vector-search/test" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "financial planning advice",
    "content_type": "linkedin_post",
    "limit": 3
  }'
```

### **System Health Check**

```bash
# Check overall system health
curl "http://localhost:8000/api/v1/health"

# Check vector search readiness
curl "http://localhost:8000/api/v1/vector-search/readiness"

# Check embedding service
curl -X POST "http://localhost:8000/api/v1/embeddings/test"
```

### **Content Management**

```bash
# Get database overview
curl "http://localhost:8000/api/v1/knowledge-base/database/summary"

# Check vectorization status
curl "http://localhost:8000/api/v1/embeddings/status"

# Estimate vectorization costs
curl "http://localhost:8000/api/v1/embeddings/cost-estimate"
```

## 🚀 **Python SDK Examples**

### **Using Requests Library**

```python
import requests
import json

# Initialize API client
BASE_URL = "http://localhost:8000/api/v1"

class FiduciaClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def generate_content(self, request, content_type, audience_type=None):
        """Generate content using Warren V3"""
        response = requests.post(
            f"{self.base_url}/warren/generate-v3",
            json={
                "request": request,
                "content_type": content_type,
                "audience_type": audience_type
            }
        )
        return response.json()
    
    def search_content(self, query, content_type=None, limit=5):
        """Search content using vector search"""
        response = requests.post(
            f"{self.base_url}/vector-search/test",
            json={
                "query": query,
                "content_type": content_type,
                "limit": limit
            }
        )
        return response.json()
    
    def get_system_status(self):
        """Get comprehensive system status"""
        health = requests.get(f"{self.base_url}/health").json()
        readiness = requests.get(f"{self.base_url}/vector-search/readiness").json()
        return {"health": health, "readiness": readiness}

# Usage examples
client = FiduciaClient()

# Generate LinkedIn content
result = client.generate_content(
    request="Create a post about tax planning",
    content_type="linkedin_post",
    audience_type="general_education"
)
print(f"Generated content: {result['content']}")

# Search for similar content
search_results = client.search_content(
    query="retirement advice",
    content_type="linkedin_post"
)
print(f"Found {search_results['results_found']} similar posts")

# Check system status
status = client.get_system_status()
print(f"System healthy: {status['health']['status'] == 'healthy'}")
```

---

**This API provides comprehensive access to FiduciaMVP's AI-powered content generation and semantic search capabilities.**
5. **Start API Server**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Test System**
   ```bash
   python tests/test_warren_basic.py
   ```

### **Development Workflow**

```bash
# Daily development routine
docker-compose up -d                    # Start infrastructure
source venv/bin/activate               # Activate environment
uvicorn src.main:app --reload           # Start API server
python tests/test_warren_basic.py       # Verify functionality
```

## 🏗️ **Architecture Overview**

### **Project Structure**
```
FiduciaMVP/
├── src/
│   ├── api/
│   │   └── endpoints.py               # FastAPI routes
│   ├── services/
│   │   ├── enhanced_warren_service.py # Vector-enhanced Warren
│   │   ├── vector_search_service.py   # Semantic search engine
│   │   ├── embedding_service.py       # OpenAI embeddings
│   │   ├── content_vectorization_service.py
│   │   ├── warren_database_service.py # Original Warren V2
│   │   └── claude_service.py          # Claude AI integration
│   ├── models/
│   │   ├── refactored_database.py     # Production database schema
│   │   └── database.py                # Legacy schema
│   ├── core/
│   │   └── database.py                # Database configuration
│   └── main.py                        # FastAPI application
├── config/
│   └── settings.py                    # Environment configuration
├── docs/                              # Documentation
├── tests/                             # Test files
├── data/knowledge_base/               # Compliance content
└── docker-compose.yml                # Infrastructure
```

### **Key Services**

1. **Enhanced Warren Service** - Main AI assistant with vector search
2. **Vector Search Service** - PostgreSQL + pgvector semantic search
3. **Embedding Service** - OpenAI text-embedding-3-large integration
4. **Content Vectorization Service** - Batch and real-time processing
5. **Claude Service** - Content generation backend

## 🔧 **Development Tasks**

### **Adding New Content Types**

1. **Update Database Enum**
   ```python
   # In src/models/refactored_database.py
   class ContentType(enum.Enum):
       LINKEDIN_POST = "linkedin_post"
       EMAIL_TEMPLATE = "email_template"
       NEW_TYPE = "new_type"  # Add new type
   ```

2. **Create Content Examples**
   ```python
   # Add to data/knowledge_base/ or database directly
   new_content = MarketingContent(
       title="Example New Content",
       content_text="...",
       content_type=ContentType.NEW_TYPE,
       audience_type=AudienceType.GENERAL_EDUCATION
   )
   ```

3. **Test Warren Generation**
   ```python
   result = await enhanced_warren_service.generate_content_with_enhanced_context(
       user_request="Create new content type",
       content_type="new_type"
   )
   ```

### **Improving Vector Search**

1. **Adjust Similarity Thresholds**
   ```python
   # In src/services/enhanced_warren_service.py
   self.vector_similarity_threshold = 0.4  # Adjust as needed
   ```

2. **Add Content Preprocessing**
   ```python
   # In src/services/embedding_service.py
   def prepare_text_for_embedding(self, title, content, **metadata):
       # Add custom preprocessing logic
       enhanced_text = f"{title}\n{content}\nMetadata: {metadata}"
       return enhanced_text
   ```

3. **Optimize Search Queries**
   ```sql
   -- In src/services/vector_search_service.py
   CREATE INDEX CONCURRENTLY idx_content_embedding 
   ON marketing_content USING ivfflat (embedding vector_cosine_ops);
   ```

### **Adding API Endpoints**

1. **Define New Endpoint**
   ```python
   # In src/api/endpoints.py
   @router.post("/new-feature")
   async def new_feature_endpoint(request: dict):
       # Implementation
       return {"status": "success", "data": result}
   ```

2. **Add Service Logic**
   ```python
   # In appropriate service file
   async def new_feature_logic(self, params):
       # Business logic implementation
       return processed_result
   ```

3. **Test Endpoint**
   ```python
   response = requests.post(
       "http://localhost:8000/api/v1/new-feature",
       json={"param": "value"}
   )
   ```

## 🧪 **Testing Guidelines**

### **Unit Testing**
```python
# Test individual services
import pytest
from src.services.embedding_service import embedding_service

@pytest.mark.asyncio
async def test_embedding_generation():
    result = await embedding_service.generate_embedding("test text")
    assert result is not None
    assert len(result) == 1536  # text-embedding-3-large dimensions
```

### **Integration Testing**
```python
# Test Warren end-to-end
async def test_warren_content_generation():
    result = await enhanced_warren_service.generate_content_with_enhanced_context(
        user_request="Test content generation",
        content_type="linkedin_post"
    )
    assert result["status"] == "success"
    assert len(result["content"]) > 100
```

### **API Testing**
```python
# Test API endpoints
def test_warren_api():
    response = requests.post(
        "http://localhost:8000/api/v1/warren/generate-v3",
        json={
            "request": "Test API request",
            "content_type": "linkedin_post"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## 🔍 **Debugging Guidelines**

### **Common Issues**

1. **Vector Search Returns 0 Results**
   ```python
   # Check similarity threshold
   results = await vector_search_service.search_marketing_content(
       query_text="test",
       similarity_threshold=0.1  # Lower threshold for debugging
   )
   
   # Check if embeddings exist
   stats = await vector_search_service.get_vector_search_stats()
   print(f"Vectorized content: {stats['marketing_content']['with_embeddings']}")
   ```

2. **Warren Fallback Always Used**
   ```python
   # Check context quality assessment
   context_data = await enhanced_warren_service._get_vector_search_context(...)
   quality = enhanced_warren_service._assess_context_quality(context_data)
   print(f"Context quality: {quality}")
   ```

3. **OpenAI API Errors**
   ```python
   # Test embedding service directly
   test_result = await embedding_service.test_connection()
   print(f"OpenAI status: {test_result}")
   ```

### **Logging Configuration**
```python
# In config/settings.py
LOG_LEVEL = "DEBUG"  # For detailed logging

# In main.py
logging.basicConfig(level=settings.LOG_LEVEL)
```

### **Database Debugging**
```python
# Check database content directly
from src.core.database import AsyncSessionLocal
from src.models.refactored_database import MarketingContent

async with AsyncSessionLocal() as db:
    result = await db.execute(select(MarketingContent).limit(5))
    content = result.scalars().all()
    print(f"Sample content: {[c.title for c in content]}")
```

## 🚀 **Performance Optimization**

### **Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX idx_marketing_content_type ON marketing_content(content_type);
CREATE INDEX idx_marketing_content_approval ON marketing_content(approval_status);
CREATE INDEX idx_warren_interactions_user ON warren_interactions(user_id);
```

### **Caching Strategy**
```python
# Add Redis caching for frequent queries
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache expensive operations
cache_key = f"embedding:{hash(text)}"
cached_result = redis_client.get(cache_key)
if cached_result:
    return json.loads(cached_result)
```

### **Async Optimization**
```python
# Use asyncio.gather for concurrent operations
results = await asyncio.gather(
    vector_search_service.search_marketing_content(...),
    vector_search_service.search_compliance_rules(...),
    enhanced_warren_service.get_disclaimers_for_content_type(...)
)
```

## 📦 **Deployment Guidelines**

### **Environment Configuration**
```bash
# Production environment variables
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/fiducia
REDIS_URL=redis://prod-redis:6379
DEBUG=False
LOG_LEVEL=INFO
```

### **Docker Production Build**
```dockerfile
# Dockerfile for production
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Health Checks**
```python
# Kubernetes health check endpoints
@router.get("/health/live")
async def liveness_check():
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_check():
    # Check database, Redis, OpenAI connectivity
    return {"status": "ready", "checks": {...}}
```

## 🔐 **Security Guidelines**

### **API Security**
```python
# Add authentication middleware
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/warren/generate-v3")
async def generate_content(request: dict, token: str = Depends(security)):
    # Validate token
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
```

### **Environment Security**
```python
# Never commit API keys
# Use environment variables only
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Validate configuration
if not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable required")
```

### **Input Validation**
```python
from pydantic import BaseModel, validator

class ContentRequest(BaseModel):
    request: str
    content_type: str
    
    @validator('request')
    def validate_request(cls, v):
        if len(v) < 10:
            raise ValueError('Request too short')
        return v
```

## 📊 **Monitoring & Analytics**

### **Metrics Collection**
```python
# Track usage metrics
from prometheus_client import Counter, Histogram

CONTENT_GENERATED = Counter('warren_content_generated_total', 'Total content generated')
GENERATION_TIME = Histogram('warren_generation_seconds', 'Time to generate content')

@GENERATION_TIME.time()
async def generate_content(...):
    result = await enhanced_warren_service.generate_content_with_enhanced_context(...)
    CONTENT_GENERATED.inc()
    return result
```

### **Error Tracking**
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)

# Automatic error reporting
try:
    result = await risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

## 🎯 **Contributing Guidelines**

### **Code Style**
```python
# Use Black for formatting
black src/ tests/

# Use isort for imports
isort src/ tests/

# Use flake8 for linting
flake8 src/ tests/
```

### **Commit Messages**
```bash
# Use conventional commits
feat: add new vector search endpoint
fix: resolve embedding generation timeout
docs: update API documentation
test: add vector search integration tests
```

### **Pull Request Process**
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Run test suite
5. Submit PR with clear description

---

**This development guide provides everything needed to contribute to FiduciaMVP's continued evolution as a leading AI compliance platform.**
