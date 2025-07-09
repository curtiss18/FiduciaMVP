# Advisor Workflow Service Refactor Plan
## Comprehensive Implementation Guide for AI Assistants

**Created**: July 9, 2025  
**Epic**: SCRUM-97 - Refactor Advisor Workflow Service  
**Purpose**: Break down monolithic advisor_workflow_service.py (744 lines) into focused, testable services

---

## 📋 **Table of Contents**

1. [Project Overview](#project-overview)
2. [Current State Analysis](#current-state-analysis)
3. [Refactoring Architecture](#refactoring-architecture)
4. [Warren Pattern Guidelines](#warren-pattern-guidelines)
5. [Implementation Phases](#implementation-phases)
6. [Service Specifications](#service-specifications)
7. [Database Considerations](#database-considerations)
8. [Testing Strategy](#testing-strategy)
9. [Migration Strategy](#migration-strategy)
10. [Code Examples](#code-examples)

---

## 🎯 **Project Overview**

### **Objective**
Transform the monolithic `advisor_workflow_service.py` into 6 focused services following the established Warren service pattern, improving testability, maintainability, and extensibility.

### **Success Criteria**
- ✅ All 6 services extracted and independently testable
- ✅ Comprehensive unit test coverage (>90%) for each service
- ✅ Integration tests validate full workflow
- ✅ No performance regressions
- ✅ Backward compatibility maintained during migration
- ✅ Clear separation of concerns with defined interfaces

### **Business Impact**
- **Reduced Development Time**: New advisor features without touching core logic
- **Improved Code Quality**: Clear separation of concerns and testable components
- **Better Error Handling**: Graceful degradation and recovery strategies
- **Enhanced Performance**: Independent optimization of each service layer
- **Compliance Confidence**: Better testing for regulatory requirements

---

## 🔍 **Current State Analysis**

### **Current File Location**
```
C:\Users\curti\OneDrive\Desktop\WebDev\FiduciaMVP\src\services\advisor_workflow_service.py
```

### **Current Service Structure (744 lines)**
```python
class AdvisorWorkflowService:
    # Warren Conversation Management (Lines 85-195)
    async def create_advisor_session()
    async def save_warren_message()
    async def get_session_messages()
    async def get_advisor_sessions()
    
    # Content Library Management (Lines 200-420)
    async def save_advisor_content()
    async def get_advisor_content_library()
    async def update_content()
    async def get_content_statistics()
    
    # Compliance Review Workflow (Lines 480-600)
    async def submit_content_for_review()
    async def update_content_status()
    async def _send_review_notification()
    
    # Utility Methods (Lines 640-744)
    def _generate_review_token()
    # Various helper methods
```

### **Identified Problems**
1. **Single Responsibility Violation**: One class handles 4+ distinct domains
2. **Testing Complexity**: 744 lines in one file makes unit testing difficult
3. **Dependency Coupling**: Direct database access mixed with business logic
4. **Error Handling**: Inconsistent error handling patterns throughout
5. **Database Logic**: Raw SQL mixed with ORM queries inconsistently
6. **Email Integration**: Tightly coupled to email service within content submission
7. **Token Management**: External dependency on token_manager called within methods

### **Dependencies Currently Used**
```python
# Database Models
from src.models.advisor_workflow_models import (
    AdvisorSessions, AdvisorMessages, AdvisorContent,
    ComplianceReviews, ContentDistribution,
    ContentStatus, ReviewDecision
)
from src.models.refactored_database import ContentType, AudienceType
from src.core.database import AsyncSessionLocal

# External Services  
from src.services.email_service import email_service
from src.services.token_manager import token_manager
```

---

## 🏗️ **Refactoring Architecture**

### **Target Service Structure**
```
src/services/advisor_workflow/
├── __init__.py                           # Main entry point & service factory
├── workflow_orchestrator.py             # Main coordinator (like ContentGenerationOrchestrator)
├── conversation_manager_service.py      # Warren chat session management
├── content_library_service.py           # Content CRUD and library operations
├── compliance_workflow_service.py       # Review workflow and approval process
├── content_status_manager.py            # Status management and transitions
├── notification_coordinator.py          # Email notifications coordinator
└── strategies/
    ├── __init__.py
    ├── status_transition_strategy.py    # Different strategies for status transitions
    ├── review_strategy.py               # Different review workflow strategies
    └── strategy_factory.py              # Factory for workflow strategies
```

### **Service Responsibilities Matrix**

| Service | Primary Responsibility | Dependencies | Key Methods |
|---------|----------------------|-------------|-------------|
| **WorkflowOrchestrator** | Main coordinator, public interface | All other services | All existing public methods |
| **ConversationManagerService** | Warren chat sessions & messages | AdvisorSessions, AdvisorMessages | create_session, save_message, get_sessions |
| **ContentLibraryService** | Advisor content library CRUD | AdvisorContent, enums | save_content, get_library, update_content |
| **ComplianceWorkflowService** | Review submission & approval | token_manager, NotificationCoordinator | submit_for_review, update_review_status |
| **ContentStatusManager** | Status transitions & business rules | ContentStatus enum, strategies | transition_status, validate_transition |
| **NotificationCoordinator** | Email notifications & templates | email_service | send_review_notification, send_status_update |

---

## 🎯 **Warren Pattern Guidelines**

### **Established Warren Pattern (Reference)**
The Warren service refactoring was completed successfully using these patterns that MUST be followed:

#### **1. Orchestrator Pattern**
```python
# Warren Example: ContentGenerationOrchestrator
class ContentGenerationOrchestrator:
    def __init__(self,
                 search_orchestrator=None,
                 conversation_service=None,
                 quality_assessor=None):
        # Dependency injection for testing
        self.search_orchestrator = search_orchestrator or SearchOrchestrator()
        self.conversation_service = conversation_service or ConversationContextService()
        self.quality_assessor = quality_assessor or ContextQualityAssessor()
```

#### **2. Direct Database Access (No Repository Layer)**
```python
# Warren services call database directly, like this:
async with AsyncSessionLocal() as db:
    result = await db.execute(select(SomeModel)...)
    # Handle results directly
```

#### **3. Strategy Pattern for Complex Logic**
```python
# Warren Example: Multiple generation strategies
class ContentGenerationStrategy(ABC):
    @abstractmethod
    async def generate_content(context_data: Dict) -> GenerationResult
    
    @abstractmethod
    def can_handle(context_data: Dict) -> bool
```

#### **4. Service Composition**
```python
# Warren services call existing services directly
from src.services.vector_search_service import VectorSearchService
from src.services.email_service import email_service
# No abstraction layers
```

### **Key Warren Principles to Follow**

1. ✅ **Single Orchestrator** - One main entry point coordinating specialized services
2. ✅ **Dependency Injection** - All services accept injected dependencies for testing
3. ✅ **Direct Database Access** - No repository abstraction layer
4. ✅ **Strategy Pattern** - Different strategies for complex workflows
5. ✅ **Service Composition** - Services call existing services (email_service, token_manager)
6. ✅ **Simple Architecture** - Focused services with clear boundaries
7. ✅ **Backward Compatibility** - Drop-in replacement through orchestrator

### **What NOT to Do (Anti-patterns)**
❌ **Repository Layer** - Warren doesn't use repositories  
❌ **Over-abstraction** - Keep it simple like Warren  
❌ **Complex Interfaces** - Warren uses straightforward service calls  
❌ **Domain Models** - Warren uses anemic models with service logic  

---

## 📅 **Implementation Phases**

### Tickets are located in Jira. Epic is SCRUM-97

### **Phase 1: Extract Core Services** (SCRUM-98, 99, 100)
**Estimated Time**: 8-12 hours  
**Goal**: Extract the three main domain services

1. **SCRUM-98**: ConversationManagerService (Warren chat sessions)
2. **SCRUM-99**: ContentLibraryService (advisor content library)  
3. **SCRUM-100**: ComplianceWorkflowService (review workflow)

**Success Criteria**:
- Each service handles its domain independently
- All existing functionality preserved
- Unit tests written for each service
- Database operations properly isolated

### **Phase 2: Support Services** (SCRUM-101, 102)
**Estimated Time**: 6-8 hours  
**Goal**: Create supporting services for complex logic

1. **SCRUM-101**: ContentStatusManager (status transitions & business rules)
2. **SCRUM-102**: NotificationCoordinator (email notifications & templates)

**Success Criteria**:
- Status transitions follow business rules
- Notification system is flexible and testable
- Strategy pattern implemented for status transitions
- Email templates are professional and customizable

### **Phase 3: Orchestration Layer** (SCRUM-103)
**Estimated Time**: 4-6 hours  
**Goal**: Create main orchestrator coordinating all services

1. **SCRUM-103**: WorkflowOrchestrator (main coordinator)

**Success Criteria**:
- Public interface matches existing service exactly
- All services properly coordinated
- Backward compatibility maintained
- Cross-cutting concerns handled

### **Phase 4: Testing & Migration** 
**Estimated Time**: 4-6 hours  
**Goal**: Comprehensive testing and production migration

**Tasks**:
- Integration testing across all services
- Performance benchmarking
- Backward compatibility validation
- Production migration with feature flags

---

## 🔧 **Service Specifications**

### **1. ConversationManagerService** (SCRUM-98)

#### **Purpose**
Manage Warren chat sessions and message threading for advisors.

#### **Current Code Location**
```python
# Lines 85-195 in advisor_workflow_service.py
async def create_advisor_session(advisor_id: str, title: Optional[str] = None)
async def save_warren_message(session_id: str, message_type: str, content: str, metadata: Optional[Dict] = None)
async def get_session_messages(session_id: str, advisor_id: str)
async def get_advisor_sessions(advisor_id: str, limit: int = 20, offset: int = 0)
```

#### **Key Implementation Details**
```python
class ConversationManagerService:
    """Warren chat session management following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def create_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create Warren chat session with unique session_id generation."""
        session_id = f"session_{advisor_id}_{uuid.uuid4().hex[:8]}"
        # Database operations directly (Warren pattern)
        
    async def save_message(self, session_id: str, message_type: str, content: str, 
                          metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Save Warren message with metadata handling."""
        # Handle Warren-specific metadata: sources_used, generation_confidence, etc.
        
    async def get_session_messages(self, session_id: str, advisor_id: str) -> Dict[str, Any]:
        """Get conversation history with access control."""
        # Verify session belongs to advisor (security)
        
    async def get_advisor_sessions(self, advisor_id: str, limit: int = 20, 
                                  offset: int = 0) -> Dict[str, Any]:
        """Get advisor's sessions with pagination."""
        # Order by last_activity DESC
```

#### **Warren Metadata Handling**
```python
# Warren messages include specific metadata:
if message_type == 'warren' and metadata:
    message.sources_used = json.dumps(metadata.get('sources_used', []))
    message.generation_confidence = metadata.get('generation_confidence')
    message.search_strategy = metadata.get('search_strategy')
    message.total_sources = metadata.get('total_sources')
    message.marketing_examples = metadata.get('marketing_examples')
    message.compliance_rules = metadata.get('compliance_rules')
```

### **2. ContentLibraryService** (SCRUM-99)

#### **Purpose**
Manage advisor's personal content library with complex filtering and enum handling.

#### **Current Code Location**
```python
# Lines 200-420 in advisor_workflow_service.py
async def save_advisor_content(advisor_id: str, title: str, content_text: str, content_type: str, ...)
async def get_advisor_content_library(advisor_id: str, status_filter: Optional[str] = None, ...)
async def update_content(content_id: int, advisor_id: str, **updates)
async def get_content_statistics(advisor_id: str)
```

#### **Critical PostgreSQL Enum Handling**
```python
# IMPORTANT: Current service uses raw SQL for enum casting
# This MUST be preserved in the refactored service

query = text("""
    INSERT INTO advisor_content 
    (advisor_id, title, content_text, content_type, audience_type, status, ...)
    VALUES 
    (:advisor_id, :title, :content_text, :content_type, :audience_type, :status, ...)
    RETURNING id, created_at, updated_at
""")

# For updates with enum casting:
query = text("""
    UPDATE advisor_content 
    SET status = CAST(:status AS contentstatus),
        updated_at = NOW()
    WHERE id = :content_id
""")
```

#### **Archive Filtering Logic**
```python
# CRITICAL: Default behavior excludes archived content
if status_filter:
    # If specific status requested, show only that status
    if status_filter.lower() == 'archived':
        query = query.where(AdvisorContent.status == 'archived')
    else:
        status_enum = ContentStatus(status_filter.lower())
        query = query.where(AdvisorContent.status == status_enum.value)
else:
    # Default: exclude archived content from results
    query = query.where(AdvisorContent.status != ContentStatus.ARCHIVED.value)
```

### **3. ComplianceWorkflowService** (SCRUM-100)

#### **Purpose**
Handle compliance review submission, token generation, and approval workflow.

#### **Current Code Location**
```python
# Lines 480-600 in advisor_workflow_service.py
async def submit_content_for_review(content_id: int, advisor_id: str, cco_email: str, notes: Optional[str] = None)
async def update_content_status(content_id: int, advisor_id: str, new_status: str, ...)
def _generate_review_token(content_id: int, cco_email: str)
async def _send_review_notification(...)
```

#### **Token Generation Integration**
```python
# IMPORTANT: Uses existing token_manager service
def _generate_review_token(self, content_id: int, cco_email: str) -> str:
    """Generate review token using centralized token manager."""
    from src.services.token_manager import token_manager
    
    return token_manager.generate_review_token(
        content_id=content_id,
        cco_email=cco_email,
        expires_hours=24 * 7  # 7 days
    )
```

#### **Review URL Generation**
```python
# Current review URL pattern (customize as needed):
review_url = f"http://localhost:3003/review/{review_token}"
```

### **4. ContentStatusManager** (SCRUM-101)

#### **Purpose**
Manage content status transitions with business rules and validation.

#### **Strategy Pattern Implementation**
```python
from abc import ABC, abstractmethod

class StatusTransitionStrategy(ABC):
    @abstractmethod
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """Check if transition is allowed."""
        pass
    
    @abstractmethod
    async def execute_transition(self, content_id: int, new_status: str, context: Dict) -> Dict:
        """Execute the status transition."""
        pass

class AdvisorTransitionStrategy(StatusTransitionStrategy):
    """Handle advisor-initiated transitions."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        # Advisors can: draft -> submitted, approved -> draft, archived -> draft
        allowed_transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],
            'archived': ['draft']
        }
        return new_status in allowed_transitions.get(current_status, [])

class CCOTransitionStrategy(StatusTransitionStrategy):
    """Handle CCO review decisions."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        # CCOs can: submitted -> approved/rejected, any -> any (admin privileges)
        if context.get('user_role') == 'cco':
            return True  # CCOs have full privileges
        return False
```

### **5. NotificationCoordinator** (SCRUM-102)

#### **Purpose**
Handle all email notifications with professional templates.

#### **Email Template Structure**
```python
def get_notification_template(self, notification_type: str) -> Dict[str, str]:
    """Get email template for notification type."""
    templates = {
        'review_request': {
            'subject': 'Content Review Required - {content_title}',
            'body': '''
Dear CCO,

A new piece of content has been submitted for compliance review:

Title: {content_title}
Type: {content_type}
Advisor: {advisor_id}
Submitted: {submitted_date}

{advisor_notes}

Please review the content at: {review_url}

Best regards,
Fiducia Platform
'''
        },
        'approval_notification': {
            'subject': 'Content Approved - {content_title}',
            'body': '''
Dear {advisor_name},

Your content has been approved for distribution:

Title: {content_title}
Approved by: {reviewer_name}
Approved on: {approval_date}

{approval_notes}

You can now distribute this content through your selected channels.

Best regards,
Fiducia Platform
'''
        }
        # Add more templates...
    }
    return templates.get(notification_type, {})
```

### **6. WorkflowOrchestrator** (SCRUM-103)

#### **Purpose**
Main coordinator providing the exact same public interface as current service.

#### **Dependency Injection Structure**
```python
class WorkflowOrchestrator:
    """Main advisor workflow coordinator following Warren orchestrator pattern."""
    
    def __init__(self,
                 conversation_manager=None,
                 content_library=None,
                 compliance_workflow=None,
                 content_status_manager=None,
                 notification_coordinator=None):
        """Initialize with dependency injection for testing (Warren pattern)."""
        self.conversation_manager = conversation_manager or ConversationManagerService()
        self.content_library = content_library or ContentLibraryService()
        self.compliance_workflow = compliance_workflow or ComplianceWorkflowService()
        self.content_status_manager = content_status_manager or ContentStatusManager()
        self.notification_coordinator = notification_coordinator or NotificationCoordinator()
    
    # Delegate all existing methods to appropriate services
    async def create_advisor_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Delegate to conversation_manager."""
        return await self.conversation_manager.create_session(advisor_id, title)
    
    async def save_advisor_content(self, advisor_id: str, title: str, content_text: str, 
                                  content_type: str, **kwargs) -> Dict[str, Any]:
        """Delegate to content_library."""
        return await self.content_library.save_content(advisor_id, title, content_text, content_type, **kwargs)
    
    # ... All other existing methods delegated to appropriate services
```

---

## 🗄️ **Database Considerations**

### **Models Used**
```python
# Primary models (from advisor_workflow_models.py):
- AdvisorSessions      # Warren chat sessions
- AdvisorMessages      # Warren conversation messages  
- AdvisorContent       # Advisor content library
- ComplianceReviews    # Review history (if used)
- ContentDistribution  # Distribution tracking (if used)

# Enums (from refactored_database.py):
- ContentStatus        # draft, submitted, approved, rejected, archived
- ContentType          # linkedin_post, newsletter, blog_post, etc.
- AudienceType         # general_education, professional, etc.
```

### **Critical Database Patterns**

#### **1. PostgreSQL Enum Handling**
```python
# MUST use raw SQL for enum casting in PostgreSQL
query = text("""
    UPDATE advisor_content 
    SET status = CAST(:status AS contentstatus)
    WHERE id = :content_id
""")
await db.execute(query, {"status": "approved", "content_id": 123})
```

#### **2. Session Management**
```python
# Always use AsyncSessionLocal for database connections
async with AsyncSessionLocal() as db:
    try:
        # Database operations
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise
```

#### **3. JSON Field Handling**
```python
# Handle JSON fields properly
intended_channels = json.dumps(channels) if channels else None
# When retrieving:
channels = json.loads(item.intended_channels) if item.intended_channels else None
```

### **Performance Considerations**
- Use `selectinload()` for eager loading relationships
- Implement proper pagination with `limit()` and `offset()`
- Order results by appropriate fields (`desc(updated_at)`, `desc(last_activity)`)
- Use `func.count()` for counting queries

---

## 🧪 **Testing Strategy**

### **Unit Testing Requirements**

#### **Test Coverage Goals**
- **Target**: >90% coverage for each service
- **Focus**: Business logic, error handling, edge cases
- **Pattern**: 3-4x test code to service code ratio (financial compliance standard)

#### **Test Structure Pattern**
```python
# test_conversation_manager_service.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.advisor_workflow.conversation_manager_service import ConversationManagerService

class TestConversationManagerService:
    @pytest.fixture
    def service(self):
        return ConversationManagerService()
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, service):
        # Test successful session creation
        pass
    
    @pytest.mark.asyncio  
    async def test_create_session_database_error(self, service):
        # Test database error handling
        pass
    
    # ... More comprehensive tests
```

#### **Mock Patterns**
```python
# Mock database operations
@patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
async def test_with_mock_db(mock_session_local):
    mock_db = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = mock_db
    # Test logic
```

### **Integration Testing Strategy**

#### **Full Workflow Tests**
```python
@pytest.mark.asyncio
async def test_full_content_workflow():
    """Test complete workflow: create session -> save content -> submit for review -> approve."""
    orchestrator = WorkflowOrchestrator()
    
    # 1. Create session
    session_result = await orchestrator.create_advisor_session("advisor_123", "Test Session")
    
    # 2. Save content  
    content_result = await orchestrator.save_advisor_content(
        advisor_id="advisor_123",
        title="Test Content",
        content_text="Test content text",
        content_type="linkedin_post"
    )
    
    # 3. Submit for review
    review_result = await orchestrator.submit_content_for_review(
        content_id=content_result['content']['id'],
        advisor_id="advisor_123", 
        cco_email="cco@example.com"
    )
    
    # 4. Verify workflow completion
    assert all results are successful
```

### **Test Data Management**
```python
# test_fixtures.py
@pytest.fixture
async def sample_advisor_session():
    """Create sample advisor session for testing."""
    return {
        "advisor_id": "test_advisor_123",
        "session_id": "session_test_12345678", 
        "title": "Test Warren Session",
        "message_count": 0
    }

@pytest.fixture  
async def sample_advisor_content():
    """Create sample advisor content for testing."""
    return {
        "advisor_id": "test_advisor_123",
        "title": "Test LinkedIn Post",
        "content_text": "Sample content for testing...",
        "content_type": "linkedin_post",
        "audience_type": "general_education",
        "status": "draft"
    }
```

---

## 🚀 **Migration Strategy**

### **Backward Compatibility Approach**

#### **Phase 1: Side-by-Side Implementation**
```python
# Keep original service working while building new services
# src/services/advisor_workflow_service.py (original)
# src/services/advisor_workflow/ (new services)
```

#### **Phase 2: Feature Flag Migration**
```python
# In __init__.py
USE_REFACTORED_WORKFLOW = os.getenv('USE_REFACTORED_WORKFLOW', 'false').lower() == 'true'

if USE_REFACTORED_WORKFLOW:
    from .workflow_orchestrator import WorkflowOrchestrator
    advisor_workflow_service = WorkflowOrchestrator()
else:
    from ..advisor_workflow_service import advisor_workflow_service
```

#### **Phase 3: Gradual Cutover**
```python
# Route specific operations to new services for testing
class HybridWorkflowService:
    def __init__(self):
        self.original_service = advisor_workflow_service
        self.new_orchestrator = WorkflowOrchestrator()
    
    async def create_advisor_session(self, *args, **kwargs):
        if FEATURE_FLAG_CONVERSATIONS:
            return await self.new_orchestrator.create_advisor_session(*args, **kwargs)
        else:
            return await self.original_service.create_advisor_session(*args, **kwargs)
```

### **Testing Migration**
1. **Unit Tests**: New services must pass all unit tests
2. **Integration Tests**: Full workflow tests must pass  
3. **Performance Tests**: No regression in response times
4. **Backward Compatibility**: All existing API calls work identically
5. **Production Validation**: Gradual rollout with monitoring

---

## 💻 **Code Examples**

### **Example 1: Service Extraction Pattern**

#### **Before (Current advisor_workflow_service.py)**
```python
class AdvisorWorkflowService:
    async def create_advisor_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        async with AsyncSessionLocal() as db:
            try:
                session_id = f"session_{advisor_id}_{uuid.uuid4().hex[:8]}"
                session = AdvisorSessions(
                    advisor_id=advisor_id,
                    session_id=session_id,
                    title=title or f"Chat Session {datetime.now().strftime('%m/%d %H:%M')}"
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                return {
                    "status": "success",
                    "session": {
                        "id": session.id,
                        "session_id": session.session_id,
                        # ... more fields
                    }
                }
            except Exception as e:
                await db.rollback()
                return {"status": "error", "error": str(e)}
```

#### **After (ConversationManagerService)**
```python
class ConversationManagerService:
    """Warren chat session management following Warren pattern."""
    
    def __init__(self):
        """Initialize with no dependencies (Warren pattern)."""
        pass
    
    async def create_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new Warren chat session for advisor."""
        async with AsyncSessionLocal() as db:
            try:
                session_id = f"session_{advisor_id}_{uuid.uuid4().hex[:8]}"
                session = AdvisorSessions(
                    advisor_id=advisor_id,
                    session_id=session_id,
                    title=title or f"Chat Session {datetime.now().strftime('%m/%d %H:%M')}"
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"Created new advisor session: {session_id}")
                
                return {
                    "status": "success",
                    "session": {
                        "id": session.id,
                        "session_id": session.session_id,
                        "advisor_id": session.advisor_id,
                        "title": session.title,
                        "created_at": session.created_at.isoformat(),
                        "message_count": session.message_count
                    }
                }
            except Exception as e:
                logger.error(f"Error creating advisor session: {e}")
                await db.rollback()
                return {"status": "error", "error": str(e)}
```

### **Example 2: Orchestrator Delegation Pattern**

#### **WorkflowOrchestrator Implementation**
```python
class WorkflowOrchestrator:
    """Main advisor workflow coordinator following Warren orchestrator pattern."""
    
    def __init__(self,
                 conversation_manager=None,
                 content_library=None,
                 compliance_workflow=None,
                 content_status_manager=None,
                 notification_coordinator=None):
        """Initialize with dependency injection for testing."""
        self.conversation_manager = conversation_manager or ConversationManagerService()
        self.content_library = content_library or ContentLibraryService()
        self.compliance_workflow = compliance_workflow or ComplianceWorkflowService()
        self.content_status_manager = content_status_manager or ContentStatusManager()
        self.notification_coordinator = notification_coordinator or NotificationCoordinator()
    
    # === PUBLIC INTERFACE (Maintains backward compatibility) ===
    
    async def create_advisor_session(self, advisor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new Warren chat session - delegate to ConversationManagerService."""
        return await self.conversation_manager.create_session(advisor_id, title)
    
    async def save_warren_message(self, session_id: str, message_type: str, content: str, 
                                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Save Warren message - delegate to ConversationManagerService."""
        return await self.conversation_manager.save_message(session_id, message_type, content, metadata)
    
    async def save_advisor_content(self, advisor_id: str, title: str, content_text: str, 
                                  content_type: str, audience_type: str = "general_education",
                                  source_session_id: Optional[str] = None,
                                  source_message_id: Optional[int] = None,
                                  advisor_notes: Optional[str] = None,
                                  intended_channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Save advisor content - delegate to ContentLibraryService."""
        return await self.content_library.save_content(
            advisor_id=advisor_id,
            title=title,
            content_text=content_text,
            content_type=content_type,
            audience_type=audience_type,
            source_session_id=source_session_id,
            source_message_id=source_message_id,
            advisor_notes=advisor_notes,
            intended_channels=intended_channels
        )
    
    async def submit_content_for_review(self, content_id: int, advisor_id: str, cco_email: str,
                                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Submit content for review - coordinate ComplianceWorkflowService and NotificationCoordinator."""
        return await self.compliance_workflow.submit_for_review(content_id, advisor_id, cco_email, notes)
    
    # ... All other existing methods delegated to appropriate services
```

### **Example 3: Strategy Pattern Implementation**

#### **Status Transition Strategies**
```python
# strategies/status_transition_strategy.py
from abc import ABC, abstractmethod
from typing import Dict, List

class StatusTransitionStrategy(ABC):
    """Abstract base class for status transition strategies."""
    
    @abstractmethod
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """Check if status transition is allowed."""
        pass
    
    @abstractmethod
    async def execute_transition(self, content_id: int, new_status: str, context: Dict) -> Dict:
        """Execute the status transition with appropriate side effects."""
        pass
    
    @abstractmethod
    def get_allowed_transitions(self, current_status: str) -> List[str]:
        """Get list of allowed transitions from current status."""
        pass

# strategies/advisor_transition_strategy.py
class AdvisorTransitionStrategy(StatusTransitionStrategy):
    """Handle status transitions initiated by advisors."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """Advisors can only perform specific transitions."""
        allowed_transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],  # Can modify approved content
            'rejected': ['draft'],               # Can revise rejected content
            'archived': ['draft']                # Can restore archived content
        }
        return new_status in allowed_transitions.get(current_status, [])
    
    async def execute_transition(self, content_id: int, new_status: str, context: Dict) -> Dict:
        """Execute advisor-initiated transition."""
        # Implementation with appropriate timestamp updates
        pass
    
    def get_allowed_transitions(self, current_status: str) -> List[str]:
        transitions = {
            'draft': ['submitted', 'archived'],
            'approved': ['draft', 'archived'],
            'rejected': ['draft'],
            'archived': ['draft']
        }
        return transitions.get(current_status, [])

# strategies/cco_transition_strategy.py  
class CCOTransitionStrategy(StatusTransitionStrategy):
    """Handle status transitions initiated by CCOs (compliance officers)."""
    
    def can_transition(self, current_status: str, new_status: str, context: Dict) -> bool:
        """CCOs have broader permissions for review decisions."""
        if context.get('user_role') != 'cco':
            return False
        
        # CCOs can approve/reject submitted content, and have admin privileges
        if current_status == 'submitted' and new_status in ['approved', 'rejected']:
            return True
        
        # CCOs have admin privileges for any transition (emergency cases)
        return context.get('admin_override', False)
    
    async def execute_transition(self, content_id: int, new_status: str, context: Dict) -> Dict:
        """Execute CCO review decision with audit trail."""
        # Implementation with reviewer tracking and audit logging
        pass
```

### **Example 4: Testing Pattern**

#### **Unit Test Example**
```python
# tests/services/advisor_workflow/test_conversation_manager_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from src.services.advisor_workflow.conversation_manager_service import ConversationManagerService

class TestConversationManagerService:
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ConversationManagerService()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_create_session_success(self, mock_session_local, service):
        """Test successful session creation."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.session_id = "session_advisor_123_abcd1234"
        mock_session.advisor_id = "advisor_123"
        mock_session.title = "Test Session"
        mock_session.created_at = datetime.now()
        mock_session.message_count = 0
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # Act
        result = await service.create_session("advisor_123", "Test Session")
        
        # Assert
        assert result["status"] == "success"
        assert result["session"]["advisor_id"] == "advisor_123"
        assert result["session"]["title"] == "Test Session"
        assert "session_advisor_123_" in result["session"]["session_id"]
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_create_session_database_error(self, mock_session_local, service):
        """Test database error handling during session creation."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.add.side_effect = Exception("Database connection failed")
        
        # Act
        result = await service.create_session("advisor_123", "Test Session")
        
        # Assert
        assert result["status"] == "error"
        assert "Database connection failed" in result["error"]
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.advisor_workflow.conversation_manager_service.AsyncSessionLocal')
    async def test_save_message_with_warren_metadata(self, mock_session_local, service):
        """Test saving Warren message with metadata."""
        # Arrange
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        
        warren_metadata = {
            'sources_used': [{'title': 'SEC Rule', 'relevance': 0.95}],
            'generation_confidence': 0.87,
            'search_strategy': 'vector_search',
            'total_sources': 5
        }
        
        mock_message = MagicMock()
        mock_message.id = 1
        mock_message.session_id = "session_123"
        mock_message.message_type = "warren"
        mock_message.content = "Generated compliance content..."
        mock_message.created_at = datetime.now()
        
        # Act
        result = await service.save_message(
            session_id="session_123",
            message_type="warren", 
            content="Generated compliance content...",
            metadata=warren_metadata
        )
        
        # Assert
        assert result["status"] == "success"
        assert result["message"]["message_type"] == "warren"
        mock_db.add.assert_called_once()
        mock_db.execute.assert_called_once()  # For session update
        mock_db.commit.assert_called_once()
```

---

## 🎯 **Implementation Checklist**

### **Pre-Implementation**
### **This MUST be done!!! DONT SKIP THIS**
- [ ] Read and understand Warren service pattern
- [ ] Review current advisor_workflow_service.py thoroughly
- [ ] Understand database models and enum handling
- [ ] Set up testing environment

### **Phase 1: Core Services (SCRUM-98, 99, 100)**
- [ ] **SCRUM-98**: ConversationManagerService
  - [ ] Extract session management methods
  - [ ] Handle Warren metadata correctly
  - [ ] Write comprehensive unit tests
  - [ ] Test access control and security
- [ ] **SCRUM-99**: ContentLibraryService  
  - [ ] Extract content library methods
  - [ ] Preserve PostgreSQL enum handling
  - [ ] Implement archive filtering logic
  - [ ] Write unit tests for complex filtering
- [ ] **SCRUM-100**: ComplianceWorkflowService
  - [ ] Extract review submission logic
  - [ ] Integrate with token_manager
  - [ ] Coordinate with NotificationCoordinator
  - [ ] Write unit tests for workflow

### **Phase 2: Support Services (SCRUM-101, 102)**
- [ ] **SCRUM-101**: ContentStatusManager
  - [ ] Implement strategy pattern for transitions
  - [ ] Define business rules clearly
  - [ ] Write unit tests for all transition scenarios
- [ ] **SCRUM-102**: NotificationCoordinator
  - [ ] Extract email notification logic
  - [ ] Create professional email templates
  - [ ] Write unit tests for all notification types

### **Phase 3: Orchestration (SCRUM-103)**
- [ ] **SCRUM-103**: WorkflowOrchestrator
  - [ ] Implement dependency injection pattern
  - [ ] Delegate all existing methods
  - [ ] Maintain exact backward compatibility
  - [ ] Write integration tests

### **Phase 4: Testing & Migration**
- [ ] Comprehensive integration testing
- [ ] Performance benchmarking
- [ ] Backward compatibility validation
- [ ] Production migration planning

---

## 📚 **Additional Resources**

### **Reference Files**
- **Warren Services**: `src/services/warren/` (successful refactoring example)
- **Current Service**: `src/services/advisor_workflow_service.py`
- **Database Models**: `src/models/advisor_workflow_models.py`
- **Enums**: `src/models/refactored_database.py`

### **Key Dependencies**
- **Database**: `src/core/database.py` (AsyncSessionLocal)
- **Email Service**: `src/services/email_service.py`
- **Token Manager**: `src/services/token_manager.py`

### **Testing References**
- **Warren Tests**: `tests/services/warren/` (testing patterns)
- **Test Configuration**: `pytest.ini`, `conftest.py`

---

## 🏁 **Conclusion**

This refactor plan provides complete guidance for transforming the monolithic advisor_workflow_service.py into a well-structured, testable, and maintainable service architecture. By following the established Warren pattern and implementing each phase systematically, the resulting architecture will significantly improve code quality, testability, and development velocity.

**Key Success Factors:**
1. **Follow Warren Pattern Exactly** - Don't deviate from established successful patterns
2. **Preserve Existing Functionality** - Maintain backward compatibility throughout
3. **Test Comprehensively** - Ensure >90% test coverage for each service
4. **Implement Gradually** - Use feature flags and gradual migration
5. **Document Everything** - Maintain clear documentation for future maintenance

The resulting architecture will provide a solid foundation for future advisor workflow features while maintaining the reliability and compliance focus required for financial services applications.
