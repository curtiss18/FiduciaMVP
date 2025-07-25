# Advisor Workflow Database Models
"""
Database schema focused on advisor-to-compliance workflow:
1. Advisor creates content with Warren
2. Advisor submits for compliance review  
3. Compliance officer reviews and approves/rejects
4. Advisor distributes approved content
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

# Import shared Base from main database models
from src.models.refactored_database import Base

# Enums for advisor workflow
class ContentStatus(enum.Enum):
    """Content progression through advisor workflow"""
    DRAFT = "draft"                    # Advisor working on it
    READY_FOR_REVIEW = "ready_for_review"  # Advisor saved, ready to submit
    SUBMITTED = "submitted"            # Submitted to compliance
    IN_REVIEW = "in_review"           # Compliance officer reviewing
    NEEDS_REVISION = "needs_revision"  # Compliance sent back changes
    APPROVED = "approved"             # Ready to distribute
    REJECTED = "rejected"             # Compliance rejected
    DISTRIBUTED = "distributed"       # Posted to channels
    ARCHIVED = "archived"             # Removed from active library

class ReviewDecision(enum.Enum):
    """Compliance officer review decisions"""
    APPROVED = "approved"
    NEEDS_CHANGES = "needs_changes"
    REJECTED = "rejected"

# Import existing enums from main models
from src.models.refactored_database import ContentType, AudienceType


class AdvisorSessions(Base):
    """Warren chat sessions for advisors"""
    __tablename__ = "advisor_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    advisor_id = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=True)  # User-provided or auto-generated
    
    # Session metadata
    last_activity = Column(DateTime(timezone=True), default=func.now())
    message_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class AdvisorMessages(Base):
    """Individual messages in Warren conversations"""
    __tablename__ = "advisor_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey('advisor_sessions.session_id'), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # 'user' or 'warren'
    content = Column(Text, nullable=False)
    
    # Warren-specific metadata (only for warren messages)
    sources_used = Column(Text, nullable=True)  # JSON array of source info
    generation_confidence = Column(Float, nullable=True)
    search_strategy = Column(String(20), nullable=True)  # 'vector', 'hybrid', 'fallback'
    total_sources = Column(Integer, nullable=True)
    marketing_examples = Column(Integer, nullable=True)
    compliance_rules = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())


class AdvisorContent(Base):
    """Content pieces advisors want to submit for compliance review"""
    __tablename__ = "advisor_content"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content basics
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # PostgreSQL enum: contenttype
    audience_type = Column(String(50), nullable=False)  # PostgreSQL enum: audiencetype
    intended_channels = Column(Text, nullable=True)  # JSON: ["linkedin", "email"]
    
    # Ownership
    advisor_id = Column(String(50), nullable=False, index=True)
    firm_id = Column(String(50), nullable=True, index=True)  # For future multi-tenancy
    
    # Warren source tracking (optional)
    source_session_id = Column(String(100), ForeignKey('advisor_sessions.session_id'), nullable=True)
    source_message_id = Column(Integer, ForeignKey('advisor_messages.id'), nullable=True)
    
    # Advisor workflow
    status = Column(String(30), default="draft", index=True)  # PostgreSQL enum: contentstatus
    advisor_notes = Column(Text, nullable=True)
    
    # Compliance workflow (NEW FIELDS - added during SCRUM-54)
    cco_review_status = Column(String(50), default="not_submitted", index=True)  # not_submitted, submitted, in_review, approved, rejected, revision_requested
    cco_email = Column(String(255), nullable=True, index=True)  # CCO email for review
    submitted_for_review_at = Column(DateTime(timezone=True), nullable=True)
    review_deadline = Column(DateTime(timezone=True), nullable=True)
    review_priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Legacy compliance fields (keeping for backward compatibility)
    assigned_to_compliance_id = Column(String(50), nullable=True, index=True)
    compliance_due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships (will be available after compliance_models import)
    # Note: The ContentReview -> AdvisorContent relationship is defined in compliance_models.py
    # This creates a backref called 'reviews' on AdvisorContent


class ComplianceReviews(Base):
    """Compliance officer reviews of advisor content"""
    __tablename__ = "compliance_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey('advisor_content.id'), nullable=False, index=True)
    
    # Review assignment
    compliance_officer_id = Column(String(50), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), default=func.now())
    assigned_by = Column(String(50), nullable=True)  # Who assigned the review
    
    # Review process
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Review decision
    decision = Column(Enum(ReviewDecision), nullable=True, index=True)
    review_comments = Column(Text, nullable=True)
    suggested_changes = Column(Text, nullable=True)
    
    # Warren integration for compliance fixes
    warren_assisted_review = Column(Boolean, default=False)
    warren_suggestions = Column(Text, nullable=True)
    
    # SLA tracking
    is_overdue = Column(Boolean, default=False, index=True)
    priority_level = Column(Integer, default=1)  # 1-5 scale
    
    created_at = Column(DateTime(timezone=True), default=func.now())


class ContentDistribution(Base):
    """Track where and when content was distributed"""
    __tablename__ = "content_distribution"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey('advisor_content.id'), nullable=False, index=True)
    
    # Distribution details
    channel = Column(String(50), nullable=False, index=True)  # linkedin, email, website, etc.
    distributed_at = Column(DateTime(timezone=True), default=func.now())
    distribution_notes = Column(Text, nullable=True)
    
    # Performance tracking (future)
    views = Column(Integer, default=0)
    engagement_score = Column(Float, nullable=True)
    
    advisor_id = Column(String(50), nullable=False, index=True)


class ConversationContext(Base):
    """Manage conversation context and memory for Warren sessions"""
    __tablename__ = "conversation_context"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey('advisor_sessions.session_id'), nullable=False, index=True)
    
    # Context management
    context_type = Column(String(20), nullable=False, index=True)  # 'full_history', 'compressed', 'summary'
    content = Column(Text, nullable=False)  # The actual context content
    token_count = Column(Integer, nullable=False)  # Number of tokens this context uses
    
    # Context metadata
    message_start_id = Column(Integer, nullable=True)  # First message ID this context covers
    message_end_id = Column(Integer, nullable=True)    # Last message ID this context covers
    compression_ratio = Column(Float, nullable=True)   # Original tokens / compressed tokens
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration for cleanup


class SessionDocuments(Base):
    """Documents uploaded by advisors for Warren context (SCRUM-33)"""
    __tablename__ = "session_documents"
    
    id = Column(String(50), primary_key=True, index=True)  # UUID as string for consistency
    session_id = Column(String(100), ForeignKey('advisor_sessions.session_id'), nullable=False, index=True)
    
    # Document metadata
    title = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False, index=True)  # 'pdf', 'docx', 'txt', 'video_transcript'
    original_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Document content
    full_content = Column(Text, nullable=False)  # Complete extracted text
    summary = Column(Text, nullable=True)  # AI-generated summary (~800 tokens)
    word_count = Column(Integer, nullable=False)
    
    # Processing metadata
    document_metadata = Column(Text, nullable=True)  # JSON metadata (extraction info, themes, etc.)
    processing_status = Column(String(20), default="pending", index=True)  # 'pending', 'processed', 'failed'
    processing_error = Column(Text, nullable=True)  # Error details if processing failed
    
    # Context usage tracking
    times_referenced = Column(Integer, default=0)  # How often Warren used this document
    last_referenced_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
