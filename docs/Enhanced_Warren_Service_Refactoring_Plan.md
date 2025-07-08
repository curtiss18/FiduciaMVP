# Enhanced Warren Service Refactoring Plan
**Project**: FiduciaMVP  
**Created**: July 8, 2025  
**Status**: Ready to Begin  
**Epic**: [SCRUM-76] Refactor Enhanced Warren Service - Break Down Monolithic Service

---

## **Overview & Context**

### **What is FiduciaMVP?**
FiduciaMVP is an AI-powered platform for financial advisors to generate SEC/FINRA-compliant marketing content. The core AI assistant "Warren" uses Retrieval-Augmented Generation (RAG) to create compliant content by combining user requests with approved compliance examples and regulations.

### **What is the Enhanced Warren Service?**
The `enhanced_warren_service.py` is the heart of the content generation system. It orchestrates:
- **Vector Search**: Finding relevant compliance examples using semantic similarity
- **Text Search**: Fallback search using traditional keyword matching
- **Context Assembly**: Combining search results into coherent context for AI generation
- **Conversation Memory**: Managing multi-turn conversations and session context
- **Document Integration**: Processing uploaded advisor documents for personalized content
- **Content Generation**: Using Claude AI to generate compliant marketing content
- **Quality Assessment**: Evaluating context quality and determining fallbacks
- **Error Handling**: Managing failures and degradation strategies

### **Why Refactor?**
The service has grown to **774 lines** and violates single responsibility principle:
- **Testing Challenges**: Impossible to unit test individual components
- **Tight Coupling**: Hard-coded dependencies on 11+ services
- **Complex Control Flow**: Nested try-catch blocks with multiple fallback paths
- **Maintainability Issues**: Adding features requires modifying core logic
- **Error Handling**: Inconsistent error handling across different code paths

---

## **Target Architecture**

### **Service Breakdown**
We're refactoring into **8 focused services** using Strategy and Chain of Responsibility patterns:

1. **ContentGenerationOrchestrator** - Main workflow coordinator
2. **SearchStrategyManager** - Manages vector/text/hybrid search strategies
3. **ContextRetrievalService** - Handles all context search operations
4. **ConversationContextService** - Manages session & conversation memory
5. **PromptConstructionService** - Builds prompts for generation scenarios
6. **ContentGenerationStrategy** - Interface for generation approaches (Advanced/Standard/Legacy)
7. **ContextQualityAssessor** - Evaluates context quality & sufficiency
8. **FallbackManager** - Centralizes error recovery & degradation strategies

### **Key Design Principles**
- **Single Responsibility**: Each service has one clear purpose
- **Dependency Injection**: Loose coupling through interfaces
- **Strategy Pattern**: Pluggable algorithms for generation and search
- **Chain of Responsibility**: Fallback strategies in priority order
- **Open/Closed Principle**: Extensible without modifying existing code

---

## **Jira Epic & Tasks**

### **Epic**: [SCRUM-76] Refactor Enhanced Warren Service
**URL**: https://curtiss18.atlassian.net/browse/SCRUM-76

### **Implementation Order** (by dependency):
1. **[SCRUM-77]** Extract ContextRetrievalService
2. **[SCRUM-78]** Extract ConversationContextService  
3. **[SCRUM-79]** Extract ContextQualityAssessor
4. **[SCRUM-80]** Create SearchStrategyManager
5. **[SCRUM-81]** Extract PromptConstructionService
6. **[SCRUM-82]** Create ContentGenerationStrategy Interface
7. **[SCRUM-83]** Create FallbackManager
8. **[SCRUM-84]** Create ContentGenerationOrchestrator

---

## **Current Code Analysis**

### **File Location**
```
C:\Users\curti\OneDrive\Desktop\WebDev\FiduciaMVP\src\services\enhanced_warren_service.py
```

### **Key Methods & Responsibilities**
```python
class EnhancedWarrenService:
    # Main public interface (lines 50-150)
    async def generate_content_with_enhanced_context(...)
    
    # Context retrieval (lines 150-300)
    async def _get_vector_search_context(...)
    async def _get_text_search_context(...)
    def _combine_contexts(...)
    
    # Quality assessment (lines 300-350)
    def _assess_context_quality(...)
    
    # Content generation (lines 350-650)
    async def _generate_with_enhanced_context(...)
    async def _generate_with_legacy_context(...)
    
    # Conversation management (lines 650-774)
    async def _get_conversation_context(...)
    async def _save_conversation_turn(...)
```

### **Current Dependencies**
```python
from src.services.embedding_service import embedding_service
from src.services.vector_search_service import vector_search_service
from src.services.warren_database_service import warren_db_service
from src.services.content_vectorization_service import content_vectorization_service
from src.services.claude_service import claude_service
from src.services.prompt_service import prompt_service
from src.services.conversation_manager import ConversationManager
from src.services.context_assembler import ContextAssembler, TokenManager
from src.services.advanced_context_assembler import AdvancedContextAssembler
from src.services.document_manager import DocumentManager
```

---

## **4-Phase Migration Strategy**

### **Phase 1: Foundation Services (Weeks 1-2)**
**Goal**: Extract core logic with minimal disruption

**Tasks**: [SCRUM-77], [SCRUM-78], [SCRUM-79]

**Process**:
1. **Copy & Extract**: Copy existing methods to new service files
2. **Maintain Interface**: Keep original methods as pass-through calls
3. **Add Tests**: Write comprehensive unit tests for extracted services
4. **Validate**: Ensure behavior is identical through integration tests

**Example**:
```python
# NEW: src/services/context_retrieval_service.py
class ContextRetrievalService:
    async def retrieve_marketing_context(self, query: str, content_type: ContentType, threshold: float = 0.1):
        # Moved from _get_vector_search_context()
        
# UPDATED: enhanced_warren_service.py
class EnhancedWarrenService:
    def __init__(self):
        self.context_retrieval = ContextRetrievalService()  # NEW
    
    async def _get_vector_search_context(self, ...):
        # CHANGED: Delegate to new service
        return await self.context_retrieval.retrieve_marketing_context(...)
```

### **Phase 2: Strategy Implementation (Weeks 2-3)**
**Goal**: Implement strategy patterns and remove hard-coded logic

**Tasks**: [SCRUM-80], [SCRUM-82], [SCRUM-81]

**Process**:
1. **Define Interfaces**: Create strategy interfaces with clear contracts
2. **Implement Strategies**: Move existing logic into strategy implementations
3. **Strategy Selection**: Replace hard-coded if/else with strategy selection
4. **Configuration**: Make strategy selection configurable

### **Phase 3: Orchestration Layer (Week 3-4)**
**Goal**: Create clean orchestration and centralized error handling

**Tasks**: [SCRUM-83], [SCRUM-84]

**Process**:
1. **Extract Error Handling**: Move all fallback logic to FallbackManager
2. **Create Orchestrator**: Build new main service using all extracted services
3. **Parallel Testing**: Run both old and new services in parallel
4. **Feature Flags**: Use flags to gradually shift traffic to new service

### **Phase 4: Complete Migration (Week 4)**
**Goal**: Full replacement and cleanup

**Process**:
1. **Switch Default**: Make new orchestrator the default service
2. **Remove Old Code**: Delete original enhanced_warren_service.py
3. **Update Imports**: Update all imports to use new orchestrator
4. **Performance Validation**: Ensure no performance regressions

---

## **Target File Structure**

### **Before Refactoring**
```
src/services/
└── enhanced_warren_service.py (774 lines - everything)
```

### **After Refactoring**
```
src/services/
├── content_generation_orchestrator.py          # Main coordinator (~100 lines)
├── search_strategy_manager.py                  # Search strategy management (~80 lines)
├── context_retrieval_service.py               # Context retrieval (~120 lines)
├── conversation_context_service.py            # Session management (~90 lines)
├── prompt_construction_service.py             # Prompt building (~100 lines)
├── context_quality_assessor.py               # Quality assessment (~70 lines)
├── fallback_manager.py                       # Error handling (~90 lines)
└── strategies/
    ├── content_generation_strategy.py         # Interface (~20 lines)
    ├── advanced_generation_strategy.py        # Phase 2 approach (~80 lines)
    ├── standard_generation_strategy.py        # Phase 1 approach (~70 lines)
    └── legacy_generation_strategy.py          # Original approach (~60 lines)
```

---

## **Detailed Service Specifications**

### **1. ContextRetrievalService [SCRUM-77]**
**Purpose**: Handle all context retrieval operations

**Key Methods**:
```python
class ContextRetrievalService:
    async def retrieve_marketing_context(query: str, content_type: ContentType, threshold: float) -> List[Dict]
    async def retrieve_compliance_context(query: str, content_type: str, threshold: float) -> List[Dict]
    async def combine_search_results(vector_results: List, text_results: List) -> Dict[str, Any]
    def assess_retrieval_quality(results: Dict) -> Dict[str, Any]
```

**Extracted From**:
- `_get_vector_search_context()` (lines 200-280)
- `_get_text_search_context()` (lines 280-320)
- `_combine_contexts()` (lines 320-350)

**Dependencies**: vector_search_service, warren_database_service, embedding_service

### **2. ConversationContextService [SCRUM-78]**
**Purpose**: Manage session & conversation memory

**Key Methods**:
```python
class ConversationContextService:
    async def get_session_context(session_id: str) -> Dict[str, Any]
    async def get_conversation_history(session_id: str) -> str
    async def get_session_documents(session_id: str) -> List[Dict]
    async def save_conversation_turn(session_id: str, user_input: str, warren_response: str, metadata: Dict)
    async def cleanup_expired_sessions() -> int
```

**Extracted From**:
- `_get_conversation_context()` (lines 700-720)
- `_save_conversation_turn()` (lines 720-774)
- Session document retrieval logic (lines 100-150)

**Dependencies**: ConversationManager, DocumentManager, AsyncSessionLocal

### **3. ContextQualityAssessor [SCRUM-79]**
**Purpose**: Evaluate context quality & sufficiency

**Key Methods**:
```python
class ContextQualityAssessor:
    def assess_context_quality(context_data: Dict[str, Any]) -> Dict[str, Any]
    def calculate_quality_score(marketing_count: int, disclaimer_count: int, vector_available: bool) -> float
    def is_context_sufficient(context_data: Dict) -> bool
    def get_quality_reason(context_data: Dict) -> str
    def suggest_improvements(context_data: Dict) -> List[str]
```

**Extracted From**:
- `_assess_context_quality()` (lines 380-420)

**Dependencies**: None (pure logic)

### **4. SearchStrategyManager [SCRUM-80]**
**Purpose**: Manage search strategies & fallbacks

**Key Methods**:
```python
class SearchStrategyManager:
    async def execute_search(user_request: str, content_type: str, audience_type: str) -> SearchResult
    def determine_strategy(request_context: Dict) -> SearchStrategyType
    async def execute_vector_strategy(params: SearchParams) -> SearchResult
    async def execute_text_strategy(params: SearchParams) -> SearchResult  
    async def execute_hybrid_strategy(params: SearchParams) -> SearchResult
    def should_fallback(current_result: SearchResult, strategy: SearchStrategyType) -> bool
```

**Strategy Types**:
- **Vector Strategy**: Primary approach using vector similarity search
- **Text Strategy**: Fallback using traditional text search
- **Hybrid Strategy**: Combines vector and text results intelligently
- **Emergency Strategy**: Basic fallback for system failures

**Dependencies**: ContextRetrievalService, ContextQualityAssessor

### **5. PromptConstructionService [SCRUM-81]**
**Purpose**: Build prompts for generation scenarios

**Key Methods**:
```python
class PromptConstructionService:
    async def build_generation_prompt(context_data: Dict, user_request: str, content_type: str, audience_type: str) -> str
    async def build_refinement_prompt(current_content: str, refinement_request: str, context_data: Dict) -> str
    def optimize_context_tokens(context_parts: List[str], max_tokens: int) -> List[str]
    def assemble_context_sections(context_data: Dict) -> Dict[str, str]
    def add_document_instructions(context_data: Dict) -> str
```

**Extracted From**:
- `_generate_with_enhanced_context()` (lines 500-600)
- `_generate_with_legacy_context()` (lines 600-700)

**Dependencies**: AdvancedContextAssembler, ContextAssembler, prompt_service, TokenManager

### **6. ContentGenerationStrategy Interface [SCRUM-82]**
**Purpose**: Abstract interface for generation approaches

**Interface**:
```python
from abc import ABC, abstractmethod

class ContentGenerationStrategy(ABC):
    @abstractmethod
    async def generate_content(context_data: Dict, user_request: str, content_type: str, 
                              audience_type: str, current_content: str = None, 
                              is_refinement: bool = False) -> GenerationResult
    
    @abstractmethod
    def can_handle(context_data: Dict) -> bool
    
    @abstractmethod
    def get_strategy_name() -> str
```

**Implementations**:
- **AdvancedGenerationStrategy**: Uses AdvancedContextAssembler (Phase 2 approach)
- **StandardGenerationStrategy**: Uses ContextAssembler (Phase 1 approach)
- **LegacyGenerationStrategy**: Original Warren database service approach

**Dependencies**: PromptConstructionService, claude_service, prompt_service

### **7. FallbackManager [SCRUM-83]**
**Purpose**: Centralize error recovery & degradation strategies

**Key Methods**:
```python
class FallbackManager:
    async def execute_fallback(original_error: Exception, context: FallbackContext) -> FallbackResult
    def classify_error(error: Exception, operation_type: str) -> ErrorClassification
    def select_recovery_strategy(error_class: ErrorClassification, context: FallbackContext) -> RecoveryStrategy
    async def execute_emergency_fallback(request: ContentRequest) -> ContentResult
    def should_attempt_fallback(error: Exception, attempt_count: int) -> bool
```

**Fallback Strategies**:
- **Context Assembly Fallback**: Phase 2 → Phase 1 → Legacy
- **Search Strategy Fallback**: Vector → Text → Emergency
- **Generation Strategy Fallback**: Advanced → Standard → Legacy
- **Emergency System Fallback**: Enhanced Warren → Original Warren Service

**Dependencies**: warren_database_service, ContentGenerationStrategy implementations

### **8. ContentGenerationOrchestrator [SCRUM-84]**
**Purpose**: Main workflow coordinator (replaces enhanced_warren_service)

**Key Methods**:
```python
class ContentGenerationOrchestrator:
    async def generate_content_with_enhanced_context(user_request: str, content_type: str, 
                                                   audience_type: str = None, user_id: str = None,
                                                   session_id: str = None, current_content: str = None,
                                                   is_refinement: bool = False, 
                                                   youtube_context: Dict = None,
                                                   use_conversation_context: bool = True) -> Dict[str, Any]
    
    def _validate_request(user_request: str, content_type: str) -> ValidationResult
    def _assemble_response(content: str, metadata: Dict) -> Dict[str, Any]
    async def _coordinate_generation_workflow(request: ContentRequest) -> ContentResult
```

**Dependencies**: ALL other services in this refactoring

---

## **Migration Patterns & Techniques**

### **1. Gradual Extraction Pattern**
```python
# Step 1: Extract service but keep original method
class EnhancedWarrenService:
    def __init__(self):
        self.context_retrieval = ContextRetrievalService()  # NEW
    
    async def _get_vector_search_context(self, ...):
        # OLD: return await vector_search_service.search_marketing_content(...)
        # NEW: Delegate to extracted service
        return await self.context_retrieval.retrieve_marketing_context(...)

# Step 2: Eventually remove the wrapper method entirely
# The orchestrator will call context_retrieval directly
```

### **2. Feature Flag Pattern**
```python
class ContentGenerationOrchestrator:
    def __init__(self):
        self.use_new_architecture = os.getenv('USE_NEW_WARREN_ARCHITECTURE', 'false').lower() == 'true'
        self.legacy_service = EnhancedWarrenService()  # Fallback
    
    async def generate_content_with_enhanced_context(self, ...):
        if self.use_new_architecture:
            return await self._new_generation_workflow(...)
        else:
            return await self.legacy_service.generate_content_with_enhanced_context(...)
```

### **3. Interface Preservation**
```python
# The public interface remains exactly the same
# OLD: enhanced_warren_service.generate_content_with_enhanced_context(...)
# NEW: content_generation_orchestrator.generate_content_with_enhanced_context(...)

# All existing callers continue to work without changes
# Only the import statement changes:
# OLD: from src.services.enhanced_warren_service import enhanced_warren_service
# NEW: from src.services.content_generation_orchestrator import content_generation_orchestrator
```

---

## **Testing Strategy**

### **Service-Level Testing**
Each extracted service gets comprehensive unit tests:
```python
class TestContextRetrievalService:
    @pytest.fixture
    async def service(self):
        return ContextRetrievalService()
    
    async def test_retrieve_marketing_context_success(self, service, mock_vector_search):
        mock_vector_search.search_marketing_content.return_value = [...]
        result = await service.retrieve_marketing_context("query", ContentType.LINKEDIN_POST)
        assert result['marketing_examples'] == [...]
        assert len(result['marketing_examples']) > 0
        
    async def test_retrieve_marketing_context_failure_fallback(self, service, mock_vector_search, mock_warren_db):
        mock_vector_search.search_marketing_content.side_effect = Exception("Vector search failed")
        mock_warren_db.search_marketing_content.return_value = [...]
        result = await service.retrieve_marketing_context("query", ContentType.LINKEDIN_POST)
        assert result['fallback_used'] == True
        assert result['fallback_reason'] == "vector_search_failed"
```

### **Integration Testing**
Test service interactions:
```python
class TestSearchStrategyManager:
    async def test_fallback_from_vector_to_text(self, manager, mock_services):
        mock_services.vector_search.side_effect = Exception("Vector search failed")
        result = await manager.execute_search("query", "linkedin_post")
        assert result.strategy_used == "text"
        assert result.fallback_reason == "vector_search_failed"
```

### **Behavioral Compatibility Testing**
Ensure new implementation produces identical results:
```python
class TestBackwardCompatibility:
    async def test_identical_output(self, old_service, new_orchestrator):
        request = {
            'user_request': 'Create LinkedIn post about retirement planning',
            'content_type': 'linkedin_post',
            'audience_type': 'retail_investors',
            'session_id': 'test-session-123'
        }
        
        old_result = await old_service.generate_content_with_enhanced_context(**request)
        new_result = await new_orchestrator.generate_content_with_enhanced_context(**request)
        
        # Content should be identical (modulo timestamps)
        assert old_result['content'] == new_result['content']
        assert old_result['search_strategy'] == new_result['search_strategy']
        assert old_result['total_knowledge_sources'] == new_result['total_knowledge_sources']
```

---

## **Important Implementation Notes**

### **Dependency Injection Setup**
```python
# Use dependency injection for loose coupling
class ContentGenerationOrchestrator:
    def __init__(self, 
                 search_manager: SearchStrategyManager = None,
                 conversation_service: ConversationContextService = None,
                 quality_assessor: ContextQualityAssessor = None,
                 prompt_service: PromptConstructionService = None,
                 fallback_manager: FallbackManager = None):
        
        # Allow injection for testing, but provide defaults
        self.search_manager = search_manager or SearchStrategyManager()
        self.conversation_service = conversation_service or ConversationContextService()
        self.quality_assessor = quality_assessor or ContextQualityAssessor()
        self.prompt_service = prompt_service or PromptConstructionService()
        self.fallback_manager = fallback_manager or FallbackManager()
```

### **Error Handling Preservation**
```python
# Maintain exact error handling behavior during migration
try:
    # New implementation
    result = await self.new_workflow(...)
except Exception as e:
    logger.error(f"New workflow failed: {e}")
    # Fall back to old implementation
    result = await self.legacy_workflow(...)
    result['emergency_fallback'] = True
    result['original_error'] = str(e)
```

### **Configuration Management**
```python
# Make strategies configurable
class SearchStrategyManager:
    def __init__(self):
        self.vector_similarity_threshold = float(os.getenv('VECTOR_SIMILARITY_THRESHOLD', '0.1'))
        self.min_results_threshold = int(os.getenv('MIN_RESULTS_THRESHOLD', '1'))
        self.enable_vector_search = os.getenv('ENABLE_VECTOR_SEARCH', 'true').lower() == 'true'
        self.search_strategy_priority = os.getenv('SEARCH_STRATEGY_PRIORITY', 'vector,text,emergency').split(',')
```

---

## **Risk Mitigation**

### **Behavioral Changes**
- **Risk**: New implementation produces different results
- **Mitigation**: Comprehensive behavioral testing with known inputs/outputs
- **Validation**: Side-by-side comparison testing in staging environment

### **Performance Regressions** 
- **Risk**: Additional service calls introduce latency
- **Mitigation**: Benchmark each phase against baseline performance
- **Optimization**: Async service calls and intelligent caching

### **Error Handling Changes**
- **Risk**: New error handling breaks existing fallback behavior
- **Mitigation**: Preserve exact error handling behavior during migration
- **Testing**: Error injection testing to validate fallback paths

### **Dependency Issues**
- **Risk**: Service dependencies create circular imports or coupling
- **Mitigation**: Clear dependency hierarchy and interface definitions
- **Architecture**: Dependency injection to avoid tight coupling

---

## **Success Criteria**

### **Technical Success**
- [ ] **Zero Functional Regressions**: All existing functionality preserved
- [ ] **Performance Maintained**: No significant latency increase (<10% overhead acceptable)
- [ ] **Test Coverage**: >90% unit test coverage for all new services
- [ ] **Error Handling**: All existing fallback scenarios still work
- [ ] **Memory Usage**: No significant memory increase

### **Code Quality Success**
- [ ] **Single Responsibility**: Each service has one clear purpose
- [ ] **Testability**: All services can be unit tested independently
- [ ] **Maintainability**: New features can be added without touching core logic
- [ ] **Extensibility**: New strategies can be plugged in easily
- [ ] **Documentation**: All services have clear API documentation

### **Business Success**
- [ ] **No Downtime**: Migration happens without service interruption
- [ ] **Feature Velocity**: New Warren features can be developed faster
- [ ] **Bug Resolution**: Issues can be isolated and fixed in specific services
- [ ] **Code Reviews**: Smaller, focused changes improve review quality

---

## **AI Assistant Guidelines**

### **When Working on Individual Tickets**

1. **Read This Document First**: Understand the overall architecture and migration strategy

2. **Check Current State**: 
   - Look at `enhanced_warren_service.py` to understand existing implementation
   - Check which services have already been extracted
   - Review existing tests to understand expected behavior

3. **Follow Extraction Pattern**:
   - Copy existing logic to new service file
   - Maintain original method as pass-through (initially)
   - Write comprehensive unit tests
   - Validate behavior is identical

4. **Preserve Interfaces**: 
   - Keep method signatures identical during migration
   - Maintain all existing error handling behavior
   - Preserve response format and metadata

5. **Test Thoroughly**:
   - Unit tests for the new service (>90% coverage)
   - Integration tests with existing services
   - Behavioral compatibility tests
   - Error injection tests for fallback scenarios

### **Key Files to Understand**

**Core Service**:
- `src/services/enhanced_warren_service.py` - Current monolithic implementation

**Dependencies**:
- `src/services/vector_search_service.py` - Vector similarity search
- `src/services/warren_database_service.py` - Original Warren service (fallback)
- `src/services/conversation_manager.py` - Conversation persistence
- `src/services/document_manager.py` - Document handling
- `src/services/claude_service.py` - AI content generation
- `src/services/prompt_service.py` - Prompt templates
- `src/services/context_assembler.py` - Phase 1 context building
- `src/services/advanced_context_assembler.py` - Phase 2 context building

**Models**:
- `src/models/refactored_database.py` - Database models and enums
- `src/core/database.py` - Database connection setup

**Configuration**:
- Environment variables for thresholds and feature flags
- Database connection settings
- API keys and external service configuration

### **Common Pitfalls to Avoid**

1. **Breaking Existing Behavior**: Always validate that new implementation produces identical results
2. **Circular Dependencies**: Be careful about service dependencies and import order
3. **Lost Error Handling**: Ensure all existing fallback scenarios are preserved
4. **Performance Regressions**: Monitor latency and optimize service interactions
5. **Test Coverage Gaps**: Each service needs comprehensive unit and integration tests

### **Project Structure Context**
```
FiduciaMVP/
├── src/
│   ├── api/                 # FastAPI endpoints
│   ├── core/               # Database and configuration
│   ├── models/             # Database models
│   └── services/           # Business logic services (refactoring target)
├── tests/                  # Test files
├── docs/                   # Documentation (this file)
└── requirements.txt        # Python dependencies
```

This refactoring transforms FiduciaMVP's core Warren service from a 774-line monolith into a clean, testable, maintainable architecture while preserving all existing functionality and maintaining backward compatibility throughout the migration process.
