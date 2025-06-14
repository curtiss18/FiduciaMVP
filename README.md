# 🏛️ FiduciaMVP

> **AI-Powered Financial Compliance Content Generation Platform**  
> **World's First Source Transparency System for Financial Compliance AI**

An enterprise-grade SaaS platform that generates SEC/FINRA-compliant marketing content for financial advisors using advanced semantic search, context-aware AI technology, and revolutionary source transparency features that show users exactly how many compliance sources informed their content.

## 🎯 **What is FiduciaMVP?**

FiduciaMVP solves a critical problem in financial services: creating compliant marketing content is expensive and time-consuming. Financial advisors typically pay $8K-$15K/month for compliance experts, while our platform provides automated compliance at $99-$599/month - saving customers $120K-$250K annually.

**Revolutionary Feature**: The world's first AI system that shows users exactly how many compliance sources informed their content generation, building trust through transparency while delivering context-aware assistance throughout the entire content lifecycle.

**Built for**: Investment Advisor Representatives (IARs), Registered Investment Advisors (RIAs), and financial services firms requiring SEC/FINRA-compliant marketing content.

## 🚀 **Revolutionary Features**

### **Source Transparency Revolution**
- **Real-time Source Counting**: See exactly how many compliance sources informed your content
- **Professional Source Badges**: Color-coded indicators showing marketing examples vs compliance rules
- **Search Strategy Transparency**: Visual indicators for VECTOR/HYBRID/FALLBACK search methods
- **Trust Building**: Financial advisors can confidently show the research backing their content
- **Quality Indicators**: Source count badges with intelligent color coding based on coverage

### **Warren AI with Pure Vector Search**
- **Complete Vector Database**: Both marketing content and compliance rules fully vectorized
- **Pure Vector Search**: Achieved **🔵 VECTOR** search across entire compliance database
- **Context-Aware Content Generation**: Automatically switches between creation and refinement modes
- **Smart Prompt Selection**: Uses different AI prompts for new content vs. content refinements
- **Intelligent Content Lifecycle**: Warren understands when you're creating vs. improving content
- **Compliance-First**: Built-in SEC/FINRA expertise with automatic disclaimers

### **Dual Professional Portals**
- **Split-Screen Advisor Interface**: Chat with Warren + content preview with source transparency
- **Enterprise Admin Portal**: Complete content management with visual change tracking
- **Source Transparency Integration**: Professional badges seamlessly integrated into content preview
- **Clean Content Separation**: Marketing content isolated from conversation using delimiter system
- **Professional UX**: Enterprise-grade design with real-time source transparency

### **Centralized AI Management**
- **Single Source of Truth**: All AI prompts managed centrally for consistency
- **Context-Aware Prompting**: Dynamic prompts based on platform, content type, and conversation stage
- **Multi-Service Ready**: Architecture prepared for image, video, and audio AI generation
- **Easy Maintenance**: Update AI behavior globally from one location

## ⚡ **Quick Start**

### **Prerequisites**
- Python 3.11+, Node.js 18+, Docker & Docker Compose
- OpenAI API key (for embeddings) + Anthropic API key (for Claude AI)

### **5-Minute Setup**
```bash
# 1. Clone and setup backend
git clone https://github.com/curtiss18/FiduciaMVP.git
cd FiduciaMVP
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Add your API keys to .env
cp .env.example .env
# Edit .env: OPENAI_API_KEY=your-key, ANTHROPIC_API_KEY=your-key

# 3. Start infrastructure and backend
docker-compose up -d
uvicorn src.main:app --reload

# 4. Start admin portal (new terminal)
cd frontend-admin && npm install && npm run dev

# 5. Start advisor portal (new terminal)  
cd frontend-advisor && npm install && npm run dev
```

## 🌐 **Access Your System**

| Portal | URL | Purpose |
|--------|-----|---------|
| **Admin Portal** | http://localhost:3001 | Content management, system monitoring, analytics |
| **Advisor Portal** | http://localhost:3002 | Warren AI chat with intelligent refinement |
| **API Backend** | http://localhost:8000 | REST API with 20+ endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |

## 🧪 **Test the Revolutionary Source Transparency**

### **Experience Source Transparency**

1. **Visit Advisor Portal**: http://localhost:3002
2. **Create Content**: "Create a LinkedIn post about retirement planning"
   - Warren uses pure vector search across complete compliance database
   - Content appears in right panel with **revolutionary source transparency**
   - See: **📚 6 sources** **💼 3 examples** **🛡️ 3 rules** **🔵 VECTOR**
3. **Intelligent Refinement**: "Make it more conversational"
   - Warren automatically switches to refinement mode with source transparency
   - References your current content for targeted improvements
   - Source badges update showing research backing refinements
4. **Professional Output**: Copy clean marketing content with full confidence in compliance research

### **Manage Your System**

1. **Visit Admin Portal**: http://localhost:3001
2. **Content Database**: Manage 29+ compliance content pieces
3. **System Monitoring**: Real-time performance metrics
4. **Professional UI**: Dark mode with VS Code-inspired design

## 🏆 **Competitive Advantages**

- **World's First Source Transparency**: Real-time display of compliance sources informing content generation
- **Trust Building Technology**: Financial advisors see exactly how many sources back their content
- **Pure Vector Search**: Achieved **🔵 VECTOR** search across complete compliance database
- **Professional Source Badges**: Enterprise-grade UI showing source breakdown and search quality
- **Complete Vectorization**: Both marketing content and compliance rules semantically searchable
- **Context-Aware AI Prompting**: Warren adapts behavior throughout content lifecycle with source transparency
- **Professional Split-Screen UX**: Unique chat + preview design with integrated source display
- **Centralized Prompt Management**: Single source of truth for all AI interactions
- **Clean Content Architecture**: Delimiter-based extraction with enterprise UI
- **Complete Content Lifecycle**: Creation → Refinement → Distribution workflow with source research

## 💼 **Business Impact**

### **Market Opportunity**
- **117,500+ potential customers** across SEC advisors, FINRA reps, insurance agents
- **$421M Total Addressable Market** with strong unit economics
- **$120K-$250K annual savings** per customer vs. traditional compliance solutions

### **Technology Leadership**
- **First-to-Market**: No competitor has source transparency or pure vector search capabilities
- **Trust Building**: Users see exactly how many compliance sources inform their content
- **Enterprise Ready**: Production-quality implementation with source transparency ready for deployment
- **Demo Perfect**: Complete workflow showcases revolutionary source transparency capabilities
- **Scalable Architecture**: Built for multi-tenant enterprise deployment with source research display

## 🏗️ **Architecture**

### **Backend**
- **FastAPI**: 20+ async endpoints with intelligent refinement support
- **PostgreSQL + pgvector**: Vector database with 1536-dimensional embeddings
- **Centralized Prompts**: All AI interactions managed in `prompt_service.py`
- **Warren V3**: Context-aware AI with automatic prompt switching

### **Frontend**
- **Dual Portal Architecture**: Admin (3001) + Advisor (3002) interfaces
- **Next.js 14**: Modern React with App Router and TypeScript
- **Professional Design**: Tailwind CSS + Shadcn/ui component library
- **Real-time Features**: Live chat, content processing, system monitoring

### **AI & Intelligence**
- **Claude AI**: Primary content generation with context-aware prompting and source transparency
- **OpenAI**: Embeddings (text-embedding-3-large) + GPT-4o backup
- **Complete Vector Search**: Sub-second similarity matching across marketing content and compliance rules
- **Pure Vector Search**: Achieved **🔵 VECTOR** search with automatic source counting and transparency
- **Smart Source Discovery**: Semantic intelligence finds most relevant compliance sources automatically

## 📚 **Documentation**

| Resource | Purpose |
|----------|---------|
| **[Development Guide](docs/development-guide.md)** | Complete setup, testing, troubleshooting |
| **[Current Status](docs/CURRENT_STATE.md)** | Latest features and development progress |
| **[Architecture Guide](docs/vector-search.md)** | Technical implementation details |
| **[Admin Portal Guide](docs/admin-portal-reference.md)** | Complete admin interface reference |

## 🚀 **Getting Started**

1. **Quick Setup**: Follow the 5-minute setup above
2. **Read the Docs**: Check out the [Development Guide](docs/development-guide.md) for comprehensive instructions
3. **Test the System**: Experience the revolutionary advisor portal
4. **Explore Admin**: Manage content and monitor system performance

---

**Built for the financial services industry** 🏛️  
*The world's first truly intelligent AI compliance platform with revolutionary source transparency and context-aware assistance*

**Ready for**: Enterprise deployment, customer demos, investor presentations, and market leadership

> 📋 **For detailed development instructions, testing workflows, and troubleshooting**, see the **[Development Guide](docs/development-guide.md)**  
> 🔍 **For revolutionary source transparency features**, see the **[Current State](docs/CURRENT_STATE.md)**