# Context Assembler Refactoring Project Plan

**Project**: FiduciaMVP Context Assembler God Class Refactoring  
**Epic**: SCRUM-105 - Refactor Context Assembler God Classes into SRP Services  
**Timeline**: 3-4 weeks (28 story points)  
**Phase**: Phase 1 (Basic ContextAssembler replacement)  

## 🎯 Project Overview

### Problem Statement
The current context assembler implementation violates Single Responsibility Principle with two monolithic classes:
- **ContextAssembler**: 664 lines with 8+ responsibilities
- **AdvancedContextAssembler**: 924 lines with runtime errors and tight coupling

### Solution Approach
Refactor into focused, single-responsibility services following established Warren and Advisor Workflow patterns. Create lightweight orchestrator similar to existing WorkflowOrchestrator pattern.

### Success Criteria
- Reduce largest class from 924 lines to <100 lines
- Achieve 90% unit test coverage for all services
- Zero runtime errors from missing attributes or session issues
- Context assembly time under 2 seconds for large contexts
- Maintain backward compatibility during migration

## 📁 Key Project Files

### Current Implementation
- `src/services/context_assembler.py` - Basic context assembler (664 lines) - **PRIMARY TARGET**
- `src/services/advanced_context_assembler.py` - Advanced features (924 lines) - **PHASE 2**
- `src/services/token_manager.py` - Existing token management service - **INTEGRATION REQUIRED**

### Related Services (Study for Patterns)
- `src/services/warren/` - Warren service patterns to follow
- `src/services/advisor_workflow/` - Advisor workflow patterns to follow
- `src/services/conversation_manager.py` - Database session patterns
- `src/models/advisor_workflow_models.py` - Model patterns

### Documentation
- `docs/Context Assembler Migration Strategy.md` - Migration approach

## 🎫 Jira Epic and User Stories

### Epic
**SCRUM-105**: Refactor Context Assembler God Classes into SRP Services  
**URL**: [Jira Epic](https://curtiss18.atlassian.net/browse/SCRUM-105)

### User Stories (Priority Order)

#### **Phase 1A: Foundation & Analysis (Week 1)**
1. **SCRUM-106** - Create Context Assembler Service Foundation Structure (2 pts)
   - Create directory structure matching Warren patterns
   - Extract base models and enums
   - Set up testing infrastructure

2. **SCRUM-114** - Analyze Existing TokenManager Service Integration (2 pts) 
   - **CRITICAL**: Must complete before SCRUM-110
   - Analyze existing `token_manager.py` service
   - Plan integration strategy to avoid conflicts

3. **SCRUM-107** - Extract Budget Allocation Service (3 pts)
   - Extract `allocate_token_budget()` logic
   - Create `BudgetAllocator` service
   - Ensure identical results to original

#### **Phase 1B: Core Services (Week 2)**
4. **SCRUM-108** - Extract Request Type Analysis Service (2 pts)
   - Extract `_determine_request_type()` logic
   - Create `RequestTypeAnalyzer` service
   - 95% test coverage for keyword patterns

5. **SCRUM-109** - Extract Basic Context Gathering Services (3 pts)
   - Extract conversation and compliance gathering
   - Create `ConversationGatherer` and `ComplianceGatherer`
   - Fix database session management anti-pattern

6. **SCRUM-115** - Add Document Context Integration (3 pts)
   - Add support for session documents from SCRUM-51
   - Integrate `ContextType.DOCUMENT_SUMMARIES`
   - Bridge gap between basic and advanced assemblers

#### **Phase 1C: Optimization & Assembly (Week 3)**
7. **SCRUM-110** - Extract Basic Token Management and Compression (3 pts)
   - **DEPENDS ON**: SCRUM-114 completion
   - Create basic compression strategies
   - Implement `BasicContextOptimizer`
   - 60%+ performance improvement through caching

8. **SCRUM-111** - Create Basic Context Assembly and Orchestrator (5 pts)
   - Create `BasicContextAssemblyOrchestrator`
   - Implement backward compatibility
   - Replace basic ContextAssembler functionality

#### **Phase 1D: Validation & Production (Week 4)**
9. **SCRUM-112** - Phase 1 Integration Testing and Validation (5 pts)
   - End-to-end integration testing
   - Performance comparison with original
   - Production readiness validation
   - Feature flag implementation testing

## 🏗️ Target Architecture

### Service Structure
```
src/services/context_assembler/
├── orchestrator.py                 # Main coordinator (<100 lines)
├── budget/
│   ├── budget_allocator.py         # Token budget allocation
│   └── request_type_analyzer.py    # Request type determination
├── gathering/
│   ├── conversation_gatherer.py    # Conversation history
│   ├── compliance_gatherer.py      # Compliance sources
│   └── document_gatherer.py        # Session documents (NEW)
├── optimization/
│   ├── context_optimizer.py        # Multi-source optimization
│   └── compression/
│       ├── compression_strategy.py # Base compression interface
│       └── [strategy implementations]
├── assembly/
│   ├── context_builder.py          # Final context assembly
│   └── quality_assessor.py         # Context quality metrics
└── tests/
    ├── unit/                       # Service-level tests
    └── integration/                # Workflow tests
```

### Integration Points
- **Existing TokenManager**: Must integrate without conflicts
- **Document Management**: SCRUM-51 session documents
- **Conversation Manager**: Database session patterns
- **Vector Search Service**: Context data integration
- **Warren Services**: Follow established patterns

## 🧪 Testing Strategy

### Unit Testing (Integrated with Development)
- 90-95% coverage required for each service
- Regression testing against original implementation
- Performance benchmarking
- Error handling and edge cases

### Integration Testing (SCRUM-112)
- End-to-end workflow validation
- Database integration testing
- Feature flag switching
- Production readiness assessment

## ⚠️ Critical Dependencies & Risks

### **SCRUM-114 Dependency**
**CRITICAL**: Must complete TokenManager analysis before SCRUM-110 to prevent conflicts with existing service.

### **Database Session Anti-Pattern**
Current ContextAssembler takes db_session in constructor causing lifecycle issues. Must fix in SCRUM-109.

### **Backward Compatibility**
Must maintain exact same interface as original ContextAssembler.build_warren_context() method.

### **Document Context Integration**
SCRUM-115 addresses functionality gap between basic and advanced assemblers.

## 🎯 Phase 2 Scope (Future Epic)

### Advanced Features Not in Current Epic
- **RelevanceAnalyzer**: 300+ lines of scoring algorithms
- **Advanced Compression**: Multiple strategy implementations
- **Quality Metrics**: Context quality assessment
- **Enhanced Context Elements**: Priority/relevance scoring
- **Multi-Source Optimization**: Advanced prioritization

**Estimated Phase 2**: 15-20 additional story points

## 🚀 Getting Started Checklist

### For New AI Assistant
## **MUST DO THIS!!! DONT SKIP**
1. **Review Epic**: Read SCRUM-105 epic description and success criteria
2. **Study Current Code**: Analyze `context_assembler.py` (664 lines)
3. **Understand Patterns**: Review Warren and Advisor Workflow services
4. **Check Dependencies**: Verify TokenManager service exists and understand its functionality
5. **Start with Foundation**: Begin with SCRUM-106 to set up project structure

### Key Questions to Ask
- Have you analyzed the existing TokenManager service integration requirements?
- Do you understand the database session management anti-pattern that needs fixing?
- Are you familiar with the Warren service patterns being followed?
- Do you understand the backward compatibility requirements?

## 📞 Project Contacts & Resources

### Documentation Resources
- Migration strategy document provides detailed approach
- Architecture diagrams show system integration points

### Development Patterns
- Follow Warren service patterns for consistency
- Use dependency injection throughout
- Implement comprehensive error handling
- Maintain detailed logging for debugging

---

**Last Updated**: July 9, 2025  
**Project Status**: Ready to Begin - All tickets refined and ready for execution  
**Next Action**: Execute SCRUM-106 (Foundation Structure) to validate approach