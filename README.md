# FiduciaMVP - Warren RAG System

**AI-powered financial compliance content generation with advanced vector search**

[![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings-orange.svg)](https://openai.com)

## 🎯 **Overview**

FiduciaMVP is a production-ready AI system that generates SEC and FINRA compliant marketing content for financial advisors. It combines Claude AI with advanced semantic search using PostgreSQL + pgvector for intelligent content generation, now featuring a professional admin portal with real-time monitoring.

### **Key Features**

- **🤖 Warren AI Assistant**: Generates compliant financial marketing content
- **🔍 Vector Search**: Semantic similarity search using OpenAI embeddings
- **📊 Admin Portal**: Professional real-time monitoring dashboard
- **📊 Content Management**: Granular database with 29 vectorized content pieces
- **🛡️ Compliance-First**: Built-in SEC/FINRA rule enforcement
- **🔄 Hybrid Fallbacks**: Never fails - automatic text search fallback
- **📈 Live Monitoring**: Real-time system health and performance tracking
- **💰 Cost Efficient**: <$0.01 operational costs for typical usage

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Admin Portal  │───▶│   FastAPI API    │───▶│  PostgreSQL +   │
│   (Next.js)     │    │   + Warren AI    │    │   pgvector      │
│   Real-time     │    │   Live Endpoints │    │   Vector DB     │
│   Monitoring    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────┐         ┌─────────────────┐
                       │  Claude AI   │         │ OpenAI Embeddings│
                       │  Content Gen │         │ Vector Search    │
                       └──────────────┘         └─────────────────┘
```

### **Tech Stack**

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **AI**: Claude AI (Anthropic), OpenAI Embeddings  
- **Database**: PostgreSQL 15+ with pgvector extension
- **Cache**: Redis
- **Infrastructure**: Docker, Docker Compose

## 🚀 **Quick Start**

### **Prerequisites**

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Anthropic API key

### **Installation**

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd FiduciaMVP
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start infrastructure:**
   ```bash
   docker-compose up -d
   ```

4. **Run database setup:**
   ```bash
   python refactor_database.py
   python load_database.py
   ```

5. **Start the API server:**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Launch the Admin Portal:**
   ```bash
   cd frontend-admin
   npm install
   npm run dev
   ```

7. **Test Warren:**
   ```bash
   python tests/test_warren_basic.py
   ```

### **API Documentation**

### **Access Points**

- **Admin Portal**: http://localhost:3001 (Professional monitoring dashboard)
- **API Documentation**: http://localhost:8000/docs (Interactive API docs)
- **FastAPI Backend**: http://localhost:8000 (Main API server)

## 🎯 **Core Functionality**

### **Warren AI Assistant**

Warren generates compliant marketing content using:

- **Semantic Search**: Finds relevant examples using vector similarity
- **Compliance Engine**: Applies SEC/FINRA rules automatically  
- **Content Types**: LinkedIn posts, emails, newsletters, etc.
- **Hybrid Strategy**: Vector search + text fallback for reliability

**Example Usage:**
```python
POST /api/v1/warren/generate-v3
{
    "request": "Create a LinkedIn post about retirement planning",
    "content_type": "linkedin_post",
    "audience_type": "general_education"
}
```

### **Vector Search System**

Advanced semantic search powered by:

- **OpenAI Embeddings**: text-embedding-3-large (1536 dimensions)
- **PostgreSQL pgvector**: Efficient cosine similarity search
- **29 Vectorized Content Pieces**: Pre-approved marketing examples
- **Real-time Vectorization**: New content automatically indexed

**Search Performance:**
- Sub-second semantic search
- 0.38+ similarity scores for relevant content
- Automatic threshold optimization

## 📊 **Content Management**

### **Database Schema**

- **`marketing_content`**: 29 granular content pieces with embeddings
- **`compliance_rules`**: SEC/FINRA regulatory requirements  
- **`warren_interactions`**: Usage analytics and performance tracking
- **`user_content_queue`**: CCO-approved content workflow

### **Content Types Supported**

| Type | Count | Status |
|------|--------|--------|
| LinkedIn Posts | 3 | ✅ Vectorized |
| Email Templates | 26 | ✅ Vectorized |
| Compliance Rules | 12 | ✅ Active |
| Total Vectorized | 29 | 100% Coverage |

## 🔧 **API Endpoints**

### **Warren AI**
- `POST /warren/generate-v3` - Enhanced content generation with vector search
- `POST /warren/generate-v2` - Database-driven generation (fallback)

### **Vector Search**
- `POST /vector-search/test` - Test semantic search
- `GET /vector-search/stats` - Vector search statistics
- `GET /vector-search/readiness` - System readiness check

### **Content Management**
- `POST /embeddings/vectorize-content` - Generate embeddings
- `GET /embeddings/status` - Vectorization status
- `GET /embeddings/cost-estimate` - Cost estimation

### **Knowledge Base**
- `GET /knowledge-base/database/summary` - Content overview
- `GET /knowledge-base/database/search` - Search content

## 💰 **Cost Analysis**

### **Implementation Costs**
- **Initial Vectorization**: $0.0004 (29 content pieces)
- **Monthly Operational**: ~$0.001 (typical usage)
- **Query Cost**: ~$0.0001 per Warren request

### **Business Value**
- **Customer Savings**: $120,000-$250,000/year vs self-managed
- **Time to Market**: Instant content generation
- **Compliance Assurance**: Built-in regulatory compliance

## 🧪 **Testing**

### **Run Tests**
```bash
# Basic Warren functionality
python tests/test_warren_basic.py

# Vector search system  
python -c "
import requests
response = requests.post('http://localhost:8000/api/v1/vector-search/test', 
                        json={'query': 'retirement planning', 'limit': 3})
print(response.json())
"
```

### **Health Checks**
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/vector-search/readiness
```

## 🔮 **Roadmap**

### **Phase 5: Frontend Development**
- [ ] Next.js professional interface
- [ ] Content management dashboard  
- [ ] User authentication system
- [ ] Multi-tenant architecture

### **Phase 6: Advanced Features**
- [ ] Content recommendation engine
- [ ] Performance analytics dashboard
- [ ] User contribution workflow
- [ ] Advanced semantic filtering

### **Phase 7: Production Deployment**
- [ ] Cloud infrastructure (AWS/GCP)
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] Production optimization

## 📁 **Project Structure**

```
FiduciaMVP/
├── src/
│   ├── api/endpoints.py           # FastAPI routes
│   ├── services/
│   │   ├── enhanced_warren_service.py    # Vector-enhanced Warren
│   │   ├── vector_search_service.py      # Semantic search
│   │   ├── embedding_service.py          # OpenAI embeddings
│   │   └── content_vectorization_service.py
│   ├── models/refactored_database.py     # Database schema
│   └── core/database.py          # Database configuration
├── config/settings.py            # Environment configuration
├── tests/test_warren_basic.py    # Basic functionality tests
├── docs/                         # Documentation
├── data/knowledge_base/          # Compliance content
└── docker-compose.yml           # Infrastructure setup
```

## 📚 **Documentation**

### **Complete Documentation**
- **[Current State](./docs/CURRENT_STATE.md)** - Production readiness status and system capabilities
- **[Vector Search Guide](./docs/vector-search.md)** - Technical implementation details
- **[API Reference](./docs/api-reference.md)** - Complete endpoint documentation
- **[Development Guide](./docs/development-guide.md)** - Setup and contribution instructions
- **[Conversation Starter](./docs/CONVERSATION_STARTER.md)** - Template for continuing development

### **Quick Links**
- **API Documentation**: http://localhost:8000/docs (when server running)
- **Vector Search Endpoints**: `/api/v1/vector-search/*`
- **Warren V3 Enhanced**: `/api/v1/warren/generate-v3`
- **System Health**: `/api/v1/health`

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 **License**

This project is proprietary software. All rights reserved.

## 🆘 **Support**

For support and questions:
- Check the [documentation](./docs/)
- Review [API examples](./docs/api-examples.md)
- Test with the provided test scripts

---

**Built with ❤️ for financial advisors who need compliant, AI-generated marketing content.**
