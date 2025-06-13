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

### **Professional Content Management System**
- **Complete CRUD Operations**: Create, read, update, delete with professional UI/UX
- **Visual Change Tracking**: Real-time modification indicators with "Modified" badges
- **Dynamic Form System**: Real-time enum loading with custom type suggestions
- **Safe Operations**: Professional confirmation dialogs for destructive actions
- **Integrated Notifications**: In-app success/error messages (no browser popups)
- **Auto-Vectorization**: All content operations include automatic embedding generation
- **Advanced Search & Filtering**: Find content by title, type, tags, and approval status
- **Real-time Statistics**: Live dashboard showing content metrics and system health

### **Enterprise Admin Portal**
- **Complete CRUD Interface**: Create, read, update, and delete content with visual change tracking
- **Professional Dark Mode**: VS Code-inspired theme with smooth transitions
- **Theme System**: Light/Dark/System preference toggle with localStorage persistence
- **Dynamic Enum System**: Real-time dropdown population from backend
- **Professional Notifications**: In-app success/error messaging system
- **Safe Operations**: Confirmation dialogs for destructive actions with detailed previews
- **Real-time Monitoring**: Live system health and performance metrics
- **Seamless Navigation**: Professional routing between admin sections
- **Cost Transparency**: OpenAI API usage tracking (<$0.001/month operational costs)
- **Enterprise UI**: Next.js 14 + TypeScript + Tailwind CSS professional interface
- **Accessibility**: Proper contrast ratios and theme support for all users

## 🏗️ **Technical Architecture**

### **Backend**
- **FastAPI**: 20+ async endpoints including full CRUD operations
- **PostgreSQL + pgvector**: Vector database with 1536-dimensional embeddings
- **Redis**: Caching and session management
- **Docker**: Containerized infrastructure

### **Frontend**  
- **Next.js 14**: Modern React framework with App Router
- **Professional Theme System**: Light/Dark/System modes with VS Code-inspired aesthetics
- **Multi-Route Architecture**: Dashboard + Content Management interfaces
- **Professional UI**: Tailwind CSS + Shadcn/ui component library
- **Real-time Integration**: Live API monitoring with auto-refresh
- **Responsive Design**: Desktop and mobile optimized
- **Accessibility**: Full WCAG compliance with proper contrast ratios

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
- **Complete CRUD Content Management**: Professional create, read, update, delete operations vs. API-only competitors
- **Visual Change Tracking**: Real-time modification indicators with professional UX vs. basic form interfaces
- **Professional Dark Mode**: VS Code-inspired theme system vs. basic light-only interfaces
- **Dynamic Form System**: Real-time enum loading with custom type support vs. static forms
- **Professional User Experience**: In-app notifications and confirmations vs. basic alerts
- **Theme Flexibility**: Light/Dark/System modes with smooth transitions vs. single-theme competitors
- **Safe Operations**: Detailed confirmation dialogs vs. immediate destructive actions
- **Advanced Vector Search**: Semantic similarity with auto-vectorization vs. keyword-only systems
- **Enterprise-grade Design**: Professional appearance with consistent UX vs. basic admin panels
- **Integrated Workflow**: Seamless navigation and real-time feedback vs. disconnected tools
- **Developer-Friendly**: Comfortable interface for long development sessions vs. eye-straining competitors

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
- **Admin Portal**: http://localhost:3001 (system monitoring)
- **Content Management**: http://localhost:3001/content-management (content interface)
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (see all CRUD endpoints)

## 📊 **API Overview**

### **Content Management (CRUD)**
```
GET    /api/v1/content              # List with filtering/pagination
POST   /api/v1/content              # Create + auto-vectorize
GET    /api/v1/content/{id}         # Get specific item
PUT    /api/v1/content/{id}         # Update + re-vectorize  
DELETE /api/v1/content/{id}         # Safe delete + remove embeddings
GET    /api/v1/content/statistics   # Database metrics
GET    /api/v1/content/enums        # Dynamic form dropdown values
```

### **AI Content Generation**
```
POST   /api/v1/warren/generate-v3   # Warren AI with vector search
GET    /api/v1/vector-search/stats  # Search performance metrics
```

## 📱 **User Interface**

### **Admin Dashboard**
- **System Health Monitoring**: Real-time status of all services
- **Performance Metrics**: Vector search stats, response times, costs
- **Quick Actions**: Navigate to content management and other admin functions

### **Content Management Interface**
- **Complete CRUD Operations**: Create and delete content with professional modals
- **Dynamic Forms**: Real-time enum loading with custom type suggestions
- **Professional Confirmations**: Safe deletion with detailed content preview
- **Integrated Notifications**: Success/error messages with auto-dismiss
- **Advanced Search**: Filter content by title, type, tags, and status
- **Real-time Statistics**: Live stats cards showing totals and system health
- **Enterprise Design**: Consistent styling with responsive layout

## 📁 **Project Structure**

```
FiduciaMVP/
├── src/                              # FastAPI Backend
│   ├── api/endpoints.py             # 20+ API endpoints
│   ├── services/                    # Warren AI, Vector Search, Content Management
│   └── models/                      # Database models with vector support
├── frontend-admin/                  # Next.js 14 Admin Portal
│   ├── app/                         # App Router pages
│   │   ├── page.tsx                # Main dashboard
│   │   └── content-management/     # Content management interface
│   ├── components/ui/              # Reusable UI components
│   └── lib/api.ts                  # API client with CRUD operations
├── docs/                           # Documentation
│   ├── CURRENT_STATE.md           # Development status
│   ├── CONVERSATION_STARTER.md    # Claude development guide
│   └── [technical guides]
├── data/knowledge_base/            # Compliance content
└── docker-compose.yml             # Infrastructure
```

## 📈 **Current Status**

**Production-Ready Unified Content Management System with Complete Modal Consolidation** featuring:
- ✅ **Unified ContentModal**: Consolidated AddContentModal + EditContentModal into single component
- ✅ **Complete field support**: All 12 database fields (title, content, tone, demographics, etc.)
- ✅ **Visual change tracking**: Real-time modification indicators with professional blue accents
- ✅ **Browser autofill excellence**: Custom CSS handling for consistent dark mode styling
- ✅ **Backend integration**: Complete CRUD API support with all field updates working
- ✅ **TypeScript safety**: Updated interfaces eliminating all compilation errors
- ✅ **Professional UX**: Enterprise-grade modal system with smooth transitions
- ✅ **Dynamic enums**: Real-time loading with custom type support
- ✅ **Enhanced validation**: Comprehensive form validation and error handling
- ✅ **Dark mode polish**: VS Code-inspired theming with perfect contrast ratios
- ✅ **Component consolidation**: Reduced code duplication and improved maintainability

**Next Development Phase**: View modal, bulk operations, or advisor portal development

> 📋 **For detailed development status and priorities**, see [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)

## 🔧 **Development**

### **Testing the System**
```bash
# Verify all services
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/content/statistics

# Test content management
curl http://localhost:8000/api/v1/content

# Test Warren AI
curl -X POST http://localhost:8000/api/v1/warren/generate-v3 \
  -H "Content-Type: application/json" \
  -d '{"request": "LinkedIn post about retirement planning", "content_type": "linkedin_post"}'
```

### **Using the Interface**
1. **Visit Admin Portal**: http://localhost:3001 for system monitoring
2. **Manage Content**: Click "Manage Content Database" to access content interface
3. **View Live Data**: See all 29+ compliance content pieces in professional table
4. **Search & Filter**: Use search bar to find specific content
5. **Monitor System**: Real-time statistics and system health indicators

### **For Developers**
- **Architecture Details**: See technical guides in `/docs` directory
- **Development Workflow**: See [`docs/CONVERSATION_STARTER.md`](docs/CONVERSATION_STARTER.md)
- **API Reference**: Available at http://localhost:8000/docs when running

## 🏆 **Key Achievements**

### **Complete Content Management System**
- **Full CRUD Operations**: Professional create, read, update, delete with visual change tracking
- **Visual Change Tracking**: Real-time modification indicators with "Modified" badges and blue borders
- **Professional Edit Interface**: Pre-populated forms with change detection and summary display
- **Dynamic Form System**: Real-time enum loading with custom type suggestions and validation
- **Professional Notifications**: In-app success/error messaging (no browser popups)
- **Safe Operations**: Detailed confirmations for destructive actions with content previews
- **Auto-Vectorization**: All content operations include embedding generation and re-generation
- **Real-time Feedback**: Loading states, validation, and user guidance throughout

### **Enterprise-Ready Capabilities**
- **Professional User Interface**: Enterprise-grade modals, forms, and confirmations
- **Dynamic Data Loading**: Real-time statistics, form population, and live updates
- **Advanced Error Handling**: Detailed error messages and graceful degradation
- **Consistent Design System**: Cohesive styling across all admin interfaces with theme support
- **Scalable Architecture**: Ready for multi-tenant deployment with proper data isolation

## 📞 **Documentation**

**Key Resources**:
- **[Current Development Status](docs/CURRENT_STATE.md)** - Latest features and priorities
- **[Developer Guide](docs/CONVERSATION_STARTER.md)** - How to continue development  
- **[Admin Portal Guide](docs/admin-portal-reference.md)** - Using the admin interface
- **[Technical Implementation](docs/vector-search.md)** - Vector search details

---

**Built for the financial services industry** 🏛️  
*Transforming compliance from a cost center to a competitive advantage*

**Current Status**: Unified ContentModal system with complete CRUD operations, visual change tracking, and professional component consolidation - ready for business use and enterprise demonstrations.