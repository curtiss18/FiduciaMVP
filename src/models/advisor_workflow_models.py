# Advisor Workflow Database Models
"""
Database schema focused on advisor-to-compliance workflow:
1. Advisor creates content with Warren
2. Advisor submits for compliance review  
3. Compliance officer reviews and approves/rejects
4. Advisor distributes approved content
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

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
    
    # Compliance workflow
    submitted_for_review_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to_compliance_id = Column(String(50), nullable=True, index=True)
    compliance_due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


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
