# FiduciaMVP Development Guide

## 🚀 **Quick Start for Developers**

### **Prerequisites**
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key (for embeddings)
- Anthropic API key (for Claude AI)

### **Setup Development Environment**

1. **Clone and Environment Setup**
   ```bash
   git clone <repository-url>
   cd FiduciaMVP
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=sk-your-openai-key
   # ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
   ```

3. **Start Infrastructure**
   ```bash
   docker-compose up -d  # PostgreSQL + Redis
   ```

4. **Initialize Database**
   ```bash
   python refactor_database.py  # Create tables
   python load_database.py     # Load content
   ```

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

## 🏗️ **Component Architecture Guidelines**

### **📦 MANDATORY: Component Decomposition Practice**

**For ANY frontend development session, ALWAYS follow these component architecture principles:**

#### **🎯 Component Size Rule**
- **Maximum 200 lines** per component file
- **If a file exceeds 200 lines**, decompose it into smaller components
- **Prefer 100-150 lines** for optimal maintainability

#### **🏗️ Component Organization Structure**
```
components/[feature]/
├── index.ts                    # Clean exports
├── types.ts                    # Shared interfaces
├── [Feature]Main.tsx          # Main orchestrating component
├── [Feature]Table.tsx         # Data display components
├── [Feature]Modal.tsx         # Modal/dialog components
├── [Feature]Form.tsx          # Form components
├── [Feature]Stats.tsx         # Statistics/dashboard components
└── [Feature]Controls.tsx      # Interactive controls
```

#### **🎨 Single Responsibility Principle**
Each component should have ONE clear purpose:
- **Data Display**: Tables, lists, cards
- **User Input**: Forms, modals, search bars
- **Navigation**: Menus, pagination, filters
- **Feedback**: Loading states, error messages, success notifications
- **Layout**: Headers, containers, wrappers

#### **🔄 Component Composition Pattern**
```typescript
// ❌ WRONG: Everything in one file
export default function MassiveComponent() {
  // 500+ lines of mixed concerns
}

// ✅ CORRECT: Composed from focused components
export default function FeatureMain() {
  return (
    <div>
      <FeatureHeader />
      <FeatureStats />
      <FeatureSearch />
      <FeatureTable />
      <FeaturePagination />
      <FeatureModals />
    </div>
  )
}
```

### **📋 Refactoring Triggers**

**IMMEDIATELY decompose when ANY of these occur:**

1. **File Length**: >200 lines
2. **Multiple Concerns**: Component handles >1 primary responsibility
3. **Repeated Code**: Similar patterns across different parts
4. **Testing Difficulty**: Hard to write focused unit tests
5. **Code Reviews**: Difficulty understanding component purpose
6. **State Complexity**: >5 useState hooks in one component

### **🛠️ Decomposition Process**

#### **Step 1: Identify Concerns**
- List all responsibilities in the current component
- Group related functionality together
- Identify shared state vs. local state

#### **Step 2: Extract Components**
```typescript
// Extract reusable UI components first
const DataTable = ({ data, onAction }) => { /* ... */ }
const SearchBar = ({ onSearch, filters }) => { /* ... */ }
const ActionModal = ({ isOpen, onClose }) => { /* ... */ }

// Then extract feature-specific components
const UserManagement = () => {
  return (
    <>
      <SearchBar onSearch={handleSearch} />
      <DataTable data={users} onAction={handleAction} />
      <ActionModal isOpen={showModal} onClose={closeModal} />
    </>
  )
}
```

#### **Step 3: Create Shared Types**
```typescript
// types.ts
export interface User {
  id: number
  name: string
  // ... other fields
}

export interface UserTableProps {
  users: User[]
  onEdit: (user: User) => void
  onDelete: (id: number) => void
}
```

#### **Step 4: Clean Exports**
```typescript
// index.ts - Make imports clean
export { default as UserTable } from './UserTable'
export { default as UserModal } from './UserModal'
export { default as UserStats } from './UserStats'
export * from './types'
```

### **🎯 Proven Benefits**

#### **✅ Maintainability**
- **Easier debugging**: Issues isolated to specific components
- **Simpler testing**: Each component tests one concern
- **Better git history**: Changes don't affect unrelated code
- **Code reviews**: Smaller, focused diffs

#### **✅ Reusability**
- **Cross-feature use**: Components work in multiple contexts
- **Consistent UI**: Shared components ensure design consistency
- **Development speed**: Don't rebuild common patterns
- **Documentation**: Each component is self-documenting

#### **✅ Team Collaboration**
- **Parallel development**: Multiple developers work on different components
- **Skill specialization**: Team members can focus on their strengths
- **Knowledge sharing**: Components serve as living documentation
- **Onboarding**: New developers understand focused components faster

### **🚨 Component Architecture Requirements**

#### **For EVERY development session:**

1. **Before writing ANY component >100 lines**:
   - Plan the component decomposition
   - Identify the sub-components needed
   - Create the folder structure

2. **During development**:
   - Keep components focused on single responsibilities
   - Extract shared interfaces to types.ts
   - Create clean export files

3. **After implementation**:
   - Review component sizes (max 200 lines)
   - Check for repeated patterns that could be extracted
   - Ensure each component has clear, single responsibility

4. **Component Review Checklist**:
   - [ ] Single, clear responsibility
   - [ ] <200 lines of code
   - [ ] Reusable with clear props interface
   - [ ] No repeated code across components
   - [ ] Clean imports/exports
   - [ ] TypeScript interfaces defined

### **📁 Example: Content Management Architecture**

**Perfect example of component decomposition:**
```
components/content/
├── index.ts                   # Clean exports (12 lines)
├── types.ts                   # Shared interfaces (32 lines)
├── AddContentModal.tsx        # Create operations (628 lines - LARGE BUT FUNCTIONAL)
├── EditContentModal.tsx       # Update operations with change tracking (580 lines)
├── DeleteContentModal.tsx     # Delete operations (191 lines - PERFECT)
├── ContentTable.tsx           # Data display (231 lines - GOOD SIZE)
├── ContentStatsCards.tsx      # Statistics (91 lines - PERFECT)
├── SearchFilterBar.tsx        # Search UI (47 lines - PERFECT)
└── Pagination.tsx             # Navigation (106 lines - PERFECT)
```

**Content management reduced from 1000+ lines to organized, maintainable components** ✅

**Key Achievement**: Complete CRUD system with visual change tracking, demonstrating:
- **Professional UX**: Real-time modification indicators and professional forms
- **Consistent Patterns**: All modals follow same structure and error handling
- **Advanced Features**: Change tracking, dynamic enums, auto-vectorization
- **Enterprise Quality**: Production-ready with comprehensive validation

### **🔄 Continuous Improvement**

**Every session should improve component architecture:**
- Look for decomposition opportunities
- Extract reusable patterns
- Simplify complex components
- Improve type safety and interfaces

**This is NOT optional - it's a core development requirement for maintainable, scalable code.**

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

#### **Intelligent Refinement System**
- **Detection**: Frontend automatically identifies refinement scenarios
- **Prompt Switching**: Backend uses appropriate prompts (creation vs refinement)
- **Context Passing**: Current content sent to AI for informed improvements
- **Seamless UX**: Users experience natural conversation flow

#### **Vector Search Integration**
- **Primary**: Semantic similarity search using pgvector
- **Fallback**: Text-based search when vector search insufficient
- **Emergency**: Warren database service as final fallback
- **Performance**: Sub-second response times with intelligent caching

## 🚀 **Deployment & Production**

### **Production Environment Setup**

#### **Environment Configuration**
```bash
# Production environment variables
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/fiducia
REDIS_URL=redis://prod-redis:6379/0
OPENAI_API_KEY=sk-prod-openai-key
ANTHROPIC_API_KEY=sk-ant-prod-anthropic-key

# Security settings
JWT_SECRET_KEY=secure-random-key
CORS_ORIGINS=https://admin.fiducia.ai,https://app.fiducia.ai
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
```

#### **Docker Production Build**
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile (Admin Portal)
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

#### **Production Docker Compose**
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://fiducia:${DB_PASSWORD}@postgres:5432/fiducia_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  admin-portal:
    build: ./frontend-admin
    ports:
      - "3001:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.fiducia.ai

  advisor-portal:
    build: ./frontend-advisor  
    ports:
      - "3002:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://api.fiducia.ai

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=fiducia_db
      - POSTGRES_USER=fiducia
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### **Scaling Considerations**

#### **Horizontal Scaling**
- **API Server**: Multiple FastAPI instances behind load balancer
- **Database**: Read replicas for improved performance
- **Redis**: Redis Cluster for high availability
- **Frontend**: CDN deployment with edge caching

#### **Performance Optimization**
- **Database Indexing**: Optimized indexes for vector operations
- **API Caching**: Redis caching for frequently accessed data
- **Frontend Optimization**: Code splitting and lazy loading
- **CDN Integration**: Static asset delivery optimization

### **Monitoring & Observability**

#### **Application Monitoring**
```python
# Example: Application metrics
from prometheus_client import Counter, Histogram, generate_latest

content_generation_counter = Counter('warren_content_generated_total', 'Total content generated')
response_time_histogram = Histogram('api_response_time_seconds', 'API response time')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response_time_histogram.observe(time.time() - start_time)
    return response
```

#### **Health Check Endpoints**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "10.0",
        "services": {
            "database": await check_db_connection(),
            "redis": await check_redis_connection(),
            "vector_search": await check_vector_search(),
            "ai_services": await check_ai_services()
        }
    }
```

## 📈 **Advanced Features & Roadmap**

### **Phase 2: Enhanced Content Management**
- **File Upload System**: Document context for Warren (separate from vector search)
- **Advanced Content Persistence**: Database storage with version history
- **Content Analytics**: Performance tracking and optimization suggestions
- **Bulk Operations**: Mass content processing and management

### **Phase 3: Multi-Channel Distribution**
- **LinkedIn API Integration**: Direct posting with compliance tracking
- **Email Marketing Integration**: Automated newsletter and campaign distribution
- **Website Integration**: Direct publishing to advisor websites
- **Social Media Automation**: Multi-platform scheduling and posting

### **Phase 4: Advanced Collaboration**
- **Real-time Collaboration**: Multiple users editing content simultaneously
- **Advanced Approval Workflows**: Multi-level approval with role-based permissions
- **Compliance Analytics**: Automated compliance scoring and risk assessment
- **Team Management**: Multi-tenant support with firm hierarchy

### **Phase 5: AI Enhancement**
- **Image Generation**: AI-powered graphics for social media posts
- **Video Content**: Automated video creation for marketing campaigns
- **Voice Integration**: AI-generated podcast and radio content
- **Advanced Personalization**: AI-driven content customization

### **Technical Debt & Improvements**
- **Test Coverage**: Comprehensive unit and integration tests
- **Performance Optimization**: Database query optimization and caching
- **Security Hardening**: Advanced authentication and authorization
- **Documentation**: Interactive API documentation and user guides

## 🔐 **Security & Compliance**

### **Data Security**
- **Encryption**: All data encrypted in transit and at rest
- **API Security**: JWT-based authentication with role-based access
- **Database Security**: Encrypted connections and secure credentials
- **File Handling**: Secure upload and processing with virus scanning

### **Compliance Features**
- **Audit Trails**: Complete logging of all content creation and modifications
- **Content Versioning**: Track all changes with rollback capabilities
- **Approval Workflows**: Enforced compliance review processes
- **Regulatory Updates**: Automated integration of regulatory changes

### **Privacy Protection**
- **Data Isolation**: Complete separation between different firms
- **Access Controls**: Granular permissions for different user roles
- **Data Retention**: Configurable retention policies for compliance
- **Export Capabilities**: Data portability for regulatory requirements

## 🎯 **Best Practices**

### **Code Quality**
- **Component Decomposition**: Maximum 200 lines per component
- **Type Safety**: Complete TypeScript coverage
- **Error Handling**: Graceful degradation and user feedback
- **Performance**: Optimized rendering and API calls

### **API Design**
- **RESTful Principles**: Consistent endpoint naming and HTTP methods
- **Error Responses**: Standardized error format with helpful messages
- **Documentation**: Interactive API docs with examples
- **Versioning**: API versioning strategy for backward compatibility

### **Database Management**
- **Migrations**: Versioned database schema changes
- **Indexing**: Optimized indexes for performance
- **Backup Strategy**: Regular automated backups with restoration testing
- **Monitoring**: Database performance and health monitoring

### **Deployment**
- **CI/CD Pipeline**: Automated testing and deployment
- **Environment Parity**: Consistent development, staging, and production
- **Rollback Strategy**: Quick rollback capabilities for failed deployments
- **Monitoring**: Comprehensive application and infrastructure monitoring

---

## 📞 **Support & Resources**

### **Getting Help**
- **Documentation**: Start with this development guide
- **Current Status**: Check `docs/CURRENT_STATE.md` for latest updates
- **Architecture**: See `docs/vector-search.md` for technical details
- **API Reference**: Interactive docs at http://localhost:8000/docs

### **Development Resources**
- **Component Guidelines**: See component architecture section above
- **Testing Workflows**: Comprehensive testing section
- **Troubleshooting**: Detailed problem-solving guide
- **Performance**: Monitoring and optimization guidelines

### **Technical Support**
- **GitHub Issues**: Report bugs and request features
- **Development Logs**: Check application logs for debugging
- **API Testing**: Use interactive API documentation
- **Performance Monitoring**: Real-time system health checks

---

**This development guide provides everything needed to build, deploy, and maintain FiduciaMVP as the world's leading AI compliance platform.** 🚀

*Ready to revolutionize financial compliance with intelligent AI assistance.*