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

---

**This development guide provides everything needed to contribute to FiduciaMVP's continued evolution as a leading AI compliance platform.**
