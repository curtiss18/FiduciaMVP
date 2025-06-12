# Vector Search Implementation Guide

## 🎯 **Overview**

This document details the vector search implementation in FiduciaMVP, including architecture, usage, and performance optimization.

## 🏗️ **Architecture**

### **Components**

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Enhanced Warren    │───▶│  Vector Search      │───▶│  PostgreSQL +       │
│  Service            │    │  Service            │    │  pgvector           │
│  (Hybrid Strategy)  │    │  (Semantic Search)  │    │  (Vector Storage)   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  Content           │    │  Embedding          │    │  OpenAI Embeddings  │
│  Vectorization     │    │  Service            │    │  text-embedding-3   │
│  Service           │    │  (Cost Tracking)    │    │  -large             │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### **Data Flow**

1. **Content Ingestion**: Marketing content → Content Vectorization Service
2. **Embedding Generation**: Text → OpenAI API → 1536-dimensional vectors
3. **Storage**: Vectors → PostgreSQL with pgvector extension
4. **Query Processing**: User request → Embedding → Semantic search
5. **Context Assembly**: Similar content → Enhanced Warren → Claude AI
6. **Content Generation**: Contextual prompt → Compliant marketing content

## 🔍 **Vector Search Process**

### **1. Embedding Generation**

```python
# Text preprocessing for optimal embeddings
def prepare_text_for_embedding(title, content, content_type, audience_type, tags):
    combined_parts = [
        f"Title: {title}",
        f"Content: {content}",
        f"Type: {content_type}",
        f"Audience: {audience_type}",
        f"Tags: {tags}"
    ]
    return "\n\n".join(combined_parts)

# Generate embedding using OpenAI
embedding = await openai_client.embeddings.create(
    model="text-embedding-3-large",
    input=prepared_text,
    dimensions=1536
)
```

### **2. Similarity Search**

```sql
-- PostgreSQL + pgvector cosine similarity query
SELECT id, title, content_text, 
       1 - (embedding <=> query_embedding) as similarity_score
FROM marketing_content 
WHERE embedding IS NOT NULL
  AND approval_status = 'APPROVED'
  AND (1 - (embedding <=> query_embedding)) > threshold
ORDER BY similarity_score DESC 
LIMIT 5;
```

### **3. Hybrid Strategy**

Warren uses a sophisticated fallback system:

```python
async def generate_content_with_enhanced_context():
    # 1. Try vector search first
    vector_results = await vector_search(query, threshold=0.1)
    
    # 2. Assess quality
    if assess_context_quality(vector_results)["sufficient"]:
        return generate_with_vector_context(vector_results)
    
    # 3. Fallback to text search
    text_results = await text_search(query)
    combined_results = combine_contexts(vector_results, text_results)
    
    # 4. Emergency fallback to original Warren V2
    if not combined_results:
        return warren_v2_fallback(query)
```

## 📊 **Performance Metrics**

### **Current Performance**

| Metric | Value | Notes |
|--------|-------|-------|
| **Content Pieces** | 29 | 100% vectorized |
| **Embedding Dimensions** | 1536 | OpenAI text-embedding-3-large |
| **Search Latency** | <500ms | Sub-second semantic search |
| **Similarity Scores** | 0.32-0.38 | For "retirement planning" queries |
| **Cost per Query** | ~$0.0001 | Including embedding generation |
| **Vector Storage** | ~45KB | Per content piece (1536 × 4 bytes) |

### **Similarity Score Interpretation**

| Score Range | Meaning | Use Case |
|-------------|---------|----------|
| **0.8+** | Nearly identical | Exact duplicates |
| **0.6-0.8** | Very similar | Strong semantic match |
| **0.4-0.6** | Moderately similar | Good contextual relevance |
| **0.2-0.4** | Loosely related | Broad topic relevance |
| **<0.2** | Unrelated | Filter out |

### **Current Thresholds**

- **Enhanced Warren Service**: 0.1 (discovery mode)
- **Vector Search Service**: 0.4 (default)
- **API Test Endpoint**: 0.1 (testing)

## 🎯 **Usage Examples**

### **Basic Vector Search**

```python
# Direct vector search
results = await vector_search_service.search_marketing_content(
    query_text="retirement planning",
    content_type=ContentType.LINKEDIN_POST,
    similarity_threshold=0.4,
    limit=5
)

# Results format
[
    {
        "id": 1,
        "title": "LinkedIn Example 1: Economic Education/Analysis",
        "content_text": "...",
        "similarity_score": 0.3792,
        "content_type": "linkedin_post",
        "tags": "retirement, planning, education"
    }
]
```

### **Warren V3 Enhanced Generation**

```python
# Generate content with vector search
result = await enhanced_warren_service.generate_content_with_enhanced_context(
    user_request="Create a LinkedIn post about retirement planning for someone in their 40s",
    content_type="linkedin_post",
    audience_type="general_education"
)

# Response includes search metadata
{
    "status": "success",
    "content": "...",
    "search_strategy": "vector",  # or "hybrid" or "text"
    "vector_results_found": 3,
    "total_knowledge_sources": 5,
    "fallback_used": False,
    "context_quality_score": 0.85
}
```

## 🛠️ **Configuration**

### **Similarity Thresholds**

Adjust thresholds based on use case:

```python
# Conservative (high precision)
similarity_threshold = 0.7

# Balanced (recommended)
similarity_threshold = 0.4

# Discovery (high recall)  
similarity_threshold = 0.1
```

### **Content Filtering**

```python
# Filter by content type
results = await search_marketing_content(
    query_text="planning",
    content_type=ContentType.LINKEDIN_POST
)

# Filter by approval status (automatic)
WHERE approval_status = 'APPROVED'

# Filter by audience type
WHERE audience_type = 'GENERAL_EDUCATION'
```

## 🔧 **Optimization**

### **Embedding Optimization**

1. **Text Preprocessing**: Include metadata (type, audience, tags) in embedding text
2. **Chunking Strategy**: Keep content pieces focused and atomic
3. **Update Frequency**: Re-embed only when content substantially changes

### **Search Optimization**

1. **Index Configuration**: 
   ```sql
   CREATE INDEX CONCURRENTLY idx_marketing_content_embedding 
   ON marketing_content USING ivfflat (embedding vector_cosine_ops) 
   WITH (lists = 100);
   ```

2. **Query Optimization**:
   - Use appropriate similarity thresholds
   - Limit result sets to avoid over-retrieval
   - Cache frequent queries

3. **Batch Processing**:
   ```python
   # Process multiple queries efficiently
   embeddings = await generate_batch_embeddings(texts)
   ```

### **Cost Optimization**

1. **Embedding Caching**: Cache embeddings for identical content
2. **Batch Generation**: Process multiple items together
3. **Incremental Updates**: Only re-embed changed content
4. **Query Deduplication**: Cache frequent query embeddings

## 📈 **Monitoring**

### **Key Metrics to Track**

```python
# Performance metrics
{
    "vector_search_latency": "avg_ms_per_query",
    "embedding_generation_cost": "monthly_spend",
    "similarity_score_distribution": "histogram",
    "fallback_usage_rate": "percentage",
    "content_discovery_rate": "items_found_per_query"
}
```

### **Health Checks**

```python
# Vector search readiness
GET /api/v1/vector-search/readiness

# Embedding service status
POST /api/v1/embeddings/test

# Database vectorization status
GET /api/v1/embeddings/status
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **No Results Found**
   - Check similarity threshold (try 0.1)
   - Verify embeddings exist in database
   - Test with broader queries

2. **Poor Result Quality**
   - Increase similarity threshold
   - Improve content preprocessing
   - Add more diverse training content

3. **High Latency**
   - Check database indexes
   - Optimize query complexity
   - Consider result caching

4. **High Costs**
   - Implement embedding caching
   - Use batch processing
   - Monitor token usage

### **Debug Commands**

```python
# Check vector search stats
GET /api/v1/vector-search/stats

# Test direct embedding
POST /api/v1/embeddings/test

# Query database directly
python check_database_direct.py
```

## 🔮 **Future Enhancements**

### **Planned Improvements**

1. **Advanced Filtering**: Combine semantic + metadata filtering
2. **Content Clustering**: Group similar content automatically  
3. **Recommendation Engine**: "Related content" suggestions
4. **A/B Testing**: Compare search strategies
5. **Real-time Analytics**: Live performance dashboards

### **Scaling Considerations**

1. **Vector Database**: Consider specialized vector databases (Pinecone, Weaviate)
2. **Distributed Search**: Shard large content collections
3. **Edge Caching**: Cache embeddings globally
4. **GPU Acceleration**: For large-scale similarity computation

---

**This vector search system provides FiduciaMVP with enterprise-grade semantic search capabilities while maintaining cost efficiency and reliability.**
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

### **Async Usage with aiohttp**

```python
import aiohttp
import asyncio

class AsyncFiduciaClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    async def generate_content(self, session, request, content_type):
        async with session.post(
            f"{self.base_url}/warren/generate-v3",
            json={"request": request, "content_type": content_type}
        ) as response:
            return await response.json()
    
    async def batch_generate(self, requests_list):
        """Generate multiple content pieces concurrently"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.generate_content(session, req["request"], req["content_type"])
                for req in requests_list
            ]
            return await asyncio.gather(*tasks)

# Usage
async def main():
    client = AsyncFiduciaClient()
    
    requests_batch = [
        {"request": "LinkedIn post about investing", "content_type": "linkedin_post"},
        {"request": "Email about retirement", "content_type": "email_template"},
    ]
    
    results = await client.batch_generate(requests_batch)
    for i, result in enumerate(results):
        print(f"Content {i+1}: {result['status']}")

# Run async example
asyncio.run(main())
```

## 🔧 **Error Handling**

### **Common Error Responses**

```json
// Bad Request (400)
{
    "error": "Content request is required"
}

// Server Error (500)
{
    "status": "error",
    "error": "OpenAI API rate limit exceeded"
}

// Not Found (404)
{
    "detail": "Not Found"
}
```

### **Error Handling Best Practices**

```python
import requests
from requests.exceptions import RequestException

def safe_generate_content(request, content_type):
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/warren/generate-v3",
            json={"request": request, "content_type": content_type},
            timeout=30  # 30 second timeout
        )
        response.raise_for_status()  # Raise exception for 4xx/5xx
        
        result = response.json()
        
        if result.get("status") == "error":
            print(f"API Error: {result.get('error')}")
            return None
        
        return result
        
    except RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        print(f"Invalid JSON response: {e}")
        return None

# Usage with error handling
result = safe_generate_content(
    "Create a LinkedIn post about retirement",
    "linkedin_post"
)

if result:
    print(f"Success: {result['content']}")
else:
    print("Content generation failed")
```

## 📋 **Best Practices**

### **Performance Optimization**

1. **Batch Requests**: Use concurrent requests for multiple content generation
2. **Appropriate Timeouts**: Set reasonable timeouts (30s for Warren, 10s for search)
3. **Result Caching**: Cache generated content to avoid duplicate API calls
4. **Error Recovery**: Implement retry logic with exponential backoff

### **Content Quality**

1. **Specific Requests**: Provide detailed, specific content requests
2. **Appropriate Types**: Match content type to intended platform
3. **Audience Targeting**: Specify audience type for better context
4. **Iterative Refinement**: Use search results to refine content requests

### **Cost Management**

1. **Monitor Usage**: Track API calls and embedding generation costs
2. **Efficient Queries**: Use specific search terms to reduce irrelevant results
3. **Batch Operations**: Combine multiple operations when possible
4. **Cache Results**: Store frequently accessed content locally

---

**This API provides comprehensive access to FiduciaMVP's AI-powered content generation and semantic search capabilities.**
