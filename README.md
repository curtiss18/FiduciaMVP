# 🏛️ FiduciaMVP

> **AI-Powered Financial Compliance Content Generation Platform**

An enterprise-grade SaaS platform that generates SEC/FINRA-compliant marketing content for financial advisors using advanced semantic search, AI technology, and comprehensive content management.

## 🎯 **What is FiduciaMVP?**

FiduciaMVP solves a critical problem in financial services: creating compliant marketing content is expensive and time-consuming. Financial advisors typically pay $8K-$15K/month for compliance experts, while our platform provides automated compliance at $99-$599/month - saving customers $120K-$250K annually.

**Built for**: Investment Advisor Representatives (IARs), Registered Investment Advisors (RIAs), and financial services firms requiring SEC/FINRA-compliant marketing content.

## 🚀 **Core Features**

### **Warren AI Assistant**
- **Intelligent Content Generation**: Creates compliant marketing content for LinkedIn, email, websites
- **Hybrid Search Strategy**: Vector search + text fallback + emergency backup ensures 100% reliability
- **Compliance-First**: Built-in SEC/FINRA expertise with automatic disclaimers

### **Advanced Content Management**
- **Complete CRUD API**: Create, read, update, delete content with automatic vectorization
- **Dynamic Knowledge Base**: 29+ compliance content pieces with real-time management
- **Smart Search**: Semantic similarity search using OpenAI embeddings
- **Rich Metadata**: Content type, audience, approval status, source tracking

### **Professional Admin Portal**
- **Real-time Monitoring**: Live system health and performance metrics
- **Cost Transparency**: OpenAI API usage tracking (<$0.001/month operational costs)
- **Enterprise UI**: Next.js 14 + TypeScript + Tailwind CSS professional interface

## 🏗️ **Technical Architecture**

### **Backend**
- **FastAPI**: 20+ async endpoints including full CRUD operations
- **PostgreSQL + pgvector**: Vector database with 1536-dimensional embeddings
- **Redis**: Caching and session management
- **Docker**: Containerized infrastructure

### **Frontend**  
- **Next.js 14**: Modern React framework with App Router
- **Professional UI**: Tailwind CSS + Shadcn/ui component library
- **Real-time Integration**: Live API monitoring with auto-refresh

### **AI & Search**
- **Claude AI**: Primary content generation with compliance focus
- **OpenAI**: GPT-4o + text-embedding-3-large for semantic search
- **Vector Search**: Sub-second similarity matching with pgvector

## 🎯 **Business Impact**

### **Market Opportunity**
- **117,500+ potential customers** across SEC advisors, FINRA reps, insurance agents
- **$421M Total Addressable Market** with strong unit economics
- **$120K-$250K annual savings** per customer vs. traditional solutions

### **Competitive Advantages**
- **Complete Content Management**: Dynamic knowledge base vs. static competitors
- **Professional Admin Portal**: Real-time monitoring vs. basic dashboards  
- **Advanced Vector Search**: Semantic similarity vs. keyword-only systems
- **Enterprise Presentation**: Ready for investor/customer demos

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+, Node.js 18+, Docker & Docker Compose
- OpenAI API key (for embeddings and content generation)

### **Setup**
```bash
# 1. Clone and setup
git clone https://github.com/curtiss18/FiduciaMVP.git
cd FiduciaMVP
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 3. Start services
docker-compose up -d
uvicorn src.main:app --reload

# 4. Start admin portal (new terminal)
cd frontend-admin && npm install && npm run dev
```

### **Access Points**
- **Admin Portal**: http://localhost:3001 (real-time monitoring)
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (see all CRUD endpoints)

## 📊 **API Overview**

### **Content Management (CRUD)**
```
GET    /api/v1/content              # List with filtering/pagination
POST   /api/v1/content              # Create + auto-vectorize
GET    /api/v1/content/{id}         # Get specific item
PUT    /api/v1/content/{id}         # Update + re-vectorize
DELETE /api/v1/content/{id}         # Delete + remove embeddings
GET    /api/v1/content/statistics   # Database metrics
```

### **AI Content Generation**
```
POST   /api/v1/warren/generate-v3   # Warren AI with vector search
GET    /api/v1/vector-search/stats  # Search performance metrics
```

## 📁 **Project Structure**

```
FiduciaMVP/
├── src/                          # FastAPI Backend
│   ├── api/endpoints.py         # 20+ API endpoints
│   ├── services/                # Warren AI, Vector Search, Content Management
│   └── models/                  # Database models with vector support
├── frontend-admin/              # Next.js 14 Admin Portal
├── docs/                        # Documentation
│   ├── CURRENT_STATE.md        # Development status
│   ├── CONVERSATION_STARTER.md # Claude development guide
│   └── [technical guides]
├── data/knowledge_base/         # Compliance content
└── docker-compose.yml          # Infrastructure
```

## 📈 **Current Status**

**Production-Ready Core System** with:
- ✅ Complete CRUD API for content management
- ✅ Professional admin portal with real-time monitoring  
- ✅ Advanced vector search with 29 vectorized content pieces
- ✅ Warren V3 AI with hybrid search strategy
- ✅ Enterprise architecture ready for scaling

**Next Development Phase**: Frontend content management interface or advisor portal

> 📋 **For detailed development status and priorities**, see [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)

## 🔧 **Development**

### **Testing the System**
```bash
# Verify all services
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/content/statistics

# Test Warren AI
curl -X POST http://localhost:8000/api/v1/warren/generate-v3 \
  -H "Content-Type: application/json" \
  -d '{"request": "LinkedIn post about retirement planning", "content_type": "linkedin_post"}'
```

### **For Developers**
- **Architecture Details**: See technical guides in `/docs` directory
- **Development Workflow**: See [`docs/CONVERSATION_STARTER.md`](docs/CONVERSATION_STARTER.md)
- **API Reference**: Available at http://localhost:8000/docs when running

## 📞 **Documentation**

**Key Resources**:
- **[Current Development Status](docs/CURRENT_STATE.md)** - Latest features and priorities
- **[Developer Guide](docs/CONVERSATION_STARTER.md)** - How to continue development  
- **[Admin Portal Guide](docs/admin-portal-reference.md)** - Using the admin interface
- **[Technical Implementation](docs/vector-search.md)** - Vector search details

---

**Built for the financial services industry** 🏛️  
*Transforming compliance from a cost center to a competitive advantage*