Hi Claude! I'm Curtis, continuing development on **FiduciaMVP** - an AI-powered financial compliance content generation platform.

## 📋 **Essential Reading First**

**BEFORE we start any development session, it is MANDATORY to review:**

1. **[`docs/CURRENT_STATE.md`](CURRENT_STATE.md)** - Latest achievements and current status
2. **[`../README.md`](../README.md)** - Full project overview and architecture
3. **[`docs/development-guide.md`](development-guide.md)** - Code quality standards and component architecture
4. **[`docs/advisor-portal-next-steps.md`](advisor-portal-next-steps.md)** - Immediate next tasks and implementation guide
5. **[`admin-portal-reference.md`](admin-portal-reference.md)** - Admin portal capabilities

**DO NOT PROCEED WITHOUT REVIEWING THESE FILES**

## 🎯 **What FiduciaMVP Is**

A SaaS platform helping financial advisors create SEC/FINRA-compliant marketing content:
- **Problem**: Compliance experts cost $8K-$15K/month
- **Solution**: AI-powered compliance at $99-$599/month  
- **Savings**: $120K-$250K annually per customer
- **Market**: 117,500+ potential customers, $421M TAM

## 🏗️ **Project Structure Overview**

**For current system status, capabilities, and latest achievements, see [`docs/CURRENT_STATE.md`](CURRENT_STATE.md)**

### **High-Level Architecture**
- **Backend**: FastAPI with Warren AI, vector search, and content management
- **Admin Portal**: Next.js 14 enterprise-grade interface  
- **Advisor Portal**: Next.js 14 conversational interface with Warren
- **Infrastructure**: PostgreSQL + pgvector, Redis, Docker

## 📂 **Project Structure & Key Files**

**Project Root**: `C:\Users\curti\OneDrive\Desktop\WebDev\FiduciaMVP`

```
FiduciaMVP/
├── src/api/endpoints.py              # API endpoints
├── src/services/                     # Warren AI, Vector Search, Content Management  
├── frontend-admin/                   # Next.js admin portal
├── frontend-advisor/                 # Next.js advisor portal
├── docs/                            # Documentation
└── docker-compose.yml              # PostgreSQL + Redis infrastructure
```

## 🚀 **System Startup (When Needed)**

```bash
# Navigate and activate
cd "C:\Users\curti\OneDrive\Desktop\WebDev\FiduciaMVP"
.\venv\Scripts\activate

# Start infrastructure  
docker-compose up -d

# Start backend
uvicorn src.main:app --reload

# Start advisor portal (new terminal)
cd frontend-advisor && npm run dev

# Access points:
# Advisor Portal: http://localhost:3002 (Warren chat interface)
# Admin Portal: http://localhost:3001 (content management)
# API Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🎯 **Development Planning**

**For specific current status, achievements, and immediate next steps, review [`docs/CURRENT_STATE.md`](CURRENT_STATE.md) first.**

## 📋 **Development Approach**

**Specific development options and priorities should be determined after reviewing the current system status in [`docs/CURRENT_STATE.md`](CURRENT_STATE.md).**

## 💼 **Business Context**

**Target Customers**: SEC advisors (~15K), FINRA reps (~625K), insurance agents (~400K)  
**Value Proposition**: $120K-$250K annual savings vs. traditional compliance solutions  
**Competitive Edge**: First conversational AI compliance platform with split-screen interface

## 🚨 **Critical Development Guidelines**

### **🛑 NEVER START CODING IMMEDIATELY**

**Always follow this process:**

1. **Review Documentation** - Read CURRENT_STATE.md and advisor-portal-next-steps.md
2. **Ask Clarifying Questions** - Understand the current state and my goals
3. **Create a Session Plan** - Outline what we'll build and how
4. **Get My Approval** - Confirm the plan before starting
5. **Then Begin Development** - Only after we agree on the approach

### **📋 Questions You Should Ask Me**

Before any development session:
- "What's your main priority for this session?"
- "What specific features should we focus on?"
- "How much time do you have for this development session?"
- "Should I test the current system first to understand the state?"

### **🎯 Session Planning Requirements**

When we agree on a direction, create a plan covering:
- **Objective**: What we're building and why
- **Approach**: Technical strategy and implementation steps
- **Time Estimate**: How long each step should take
- **Success Criteria**: How we'll know it worked
- **Integration Points**: How it connects to existing systems

## 🔧 **Technical Notes**

### **Current Tech Stack**
- **Backend**: Python 3.11, FastAPI, PostgreSQL + pgvector, Redis, Docker
- **Admin Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui
- **Advisor Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui (port 3002)
- **AI**: Claude AI (primary), OpenAI (embeddings + GPT-4o)
- **Vector Search**: OpenAI text-embedding-3-large (1536 dimensions)

### **Warren System Configuration**
Warren AI system with delimiter-based content extraction and professional UI integration.

**Configuration Files**: 
- System prompts and AI behavior
- API integration and response handling
- Content extraction and preview functionality

### **Development Patterns Established**
- **Component Architecture**: Mandatory decomposition practices (see development-guide.md)
- **API Design**: RESTful with comprehensive error handling
- **Database**: Async SQLAlchemy with rich models
- **Frontend**: Professional UI with real-time integration
- **Error Handling**: Graceful degradation and user feedback

## 🎯 **Current System Status**

**For detailed current achievements, system capabilities, and development status, see [`docs/CURRENT_STATE.md`](CURRENT_STATE.md)**

**Review [`docs/advisor-portal-next-steps.md`](advisor-portal-next-steps.md) for immediate implementation tasks.**

---

## 🚀 **Ready to Develop!**

**Remember**: 
1. 📖 Review the documentation first
2. 🤔 Ask questions about my priorities  
3. 📋 Create a plan together
4. ✅ Get approval before coding
5. 🛠️ Then let's build something amazing!

**Current system status and capabilities are detailed in [`docs/CURRENT_STATE.md`](CURRENT_STATE.md) - check there for the actual state of all features and systems.**
