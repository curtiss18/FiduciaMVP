# Refactored Database Models for Content Management System

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

Base = declarative_base()

# Enums for controlled vocabularies
class ContentType(enum.Enum):
    WEBSITE_BLOG = "WEBSITE_BLOG"
    NEWSLETTER = "NEWSLETTER"
    DIRECT_MAILING = "DIRECT_MAILING"
    X_POST = "X_POST"
    FACEBOOK_POST = "FACEBOOK_POST"
    LINKEDIN_POST = "LINKEDIN_POST"
    YOUTUBE_VIDEO = "YOUTUBE_VIDEO"
    INSTAGRAM_POST = "INSTAGRAM_POST"
    TIKTOK_VIDEO = "TIKTOK_VIDEO"
    RADIO_SCRIPT = "RADIO_SCRIPT"
    TV_SCRIPT = "TV_SCRIPT"
    EMAIL_TEMPLATE = "EMAIL_TEMPLATE"
    WEBSITE_COPY = "WEBSITE_COPY"

class AudienceType(enum.Enum):
    CLIENT_COMMUNICATION = "CLIENT_COMMUNICATION"
    PROSPECT_ADVERTISING = "PROSPECT_ADVERTISING"
    GENERAL_EDUCATION = "GENERAL_EDUCATION"
    EXISTING_CLIENTS = "EXISTING_CLIENTS"
    NEW_PROSPECTS = "NEW_PROSPECTS"

class ApprovalStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"

class SourceType(enum.Enum):
    FIDUCIA_CREATED = "FIDUCIA_CREATED"
    USER_CONTRIBUTED = "USER_CONTRIBUTED"
    THIRD_PARTY_LICENSED = "THIRD_PARTY_LICENSED"
    WARREN_GENERATED = "WARREN_GENERATED"


class MarketingContent(Base):
    """Individual marketing content pieces - granular, channel-specific"""
    __tablename__ = "marketing_content"
    
    # Core identification
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    
    # Content classification
    content_type = Column(Enum(ContentType), nullable=False, index=True)
    audience_type = Column(Enum(AudienceType), nullable=False, index=True)
    
    # Content metadata
    tone = Column(String(50), nullable=True)  # professional, casual, educational, promotional
    topic_focus = Column(String(100), nullable=True)  # retirement, investing, tax, estate
    target_demographics = Column(String(100), nullable=True)  # millennials, boomers, high_net_worth
    
    # Approval and quality
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.APPROVED, index=True)
    compliance_score = Column(Float, default=1.0)  # 0-1 scale
    fiducia_approved_by = Column(String(100), nullable=True)
    fiducia_approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Source tracking
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    original_source = Column(Text, nullable=True)  # URL, file path, or description
    contributed_by_user_id = Column(String(50), nullable=True)  # If user-contributed
    
    # Performance and usage
    usage_count = Column(Integer, default=0)
    effectiveness_score = Column(Float, nullable=True)  # Based on user feedback
    
    # Tags for RAG efficiency
    tags = Column(Text, nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Vector embedding for semantic search (future)
    embedding = Column(Vector(1536), nullable=True)


class ComplianceRules(Base):
    """Regulatory knowledge separate from marketing content"""
    __tablename__ = "compliance_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    regulation_name = Column(String(100), nullable=False)  # SEC Marketing Rule, FINRA 2210
    rule_section = Column(String(50), nullable=True)  # 206(4)-1, 2210(d)(1)
    requirement_text = Column(Text, nullable=False)
    
    # Applicability
    applies_to_content_types = Column(Text, nullable=True)  # JSON array of content types
    applicability_scope = Column(String(100), nullable=True)  # all_advisors, broker_dealers, etc.
    
    # Classification
    prohibition_type = Column(String(50), nullable=True)  # performance_claims, testimonials, etc.
    required_disclaimers = Column(Text, nullable=True)
    
    # Metadata
    effective_date = Column(DateTime(timezone=True), nullable=True)
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Vector embedding for semantic search
    embedding = Column(Vector(1536), nullable=True)


class UserContentQueue(Base):
    """Queue for CCO-approved user content awaiting Fiducia review"""
    __tablename__ = "user_content_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User submission details
    user_id = Column(String(50), nullable=False)
    firm_name = Column(String(100), nullable=True)
    user_email = Column(String(100), nullable=True)
    
    # Content details
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    audience_type = Column(Enum(AudienceType), nullable=False)
    
    # User-provided metadata
    user_provided_tags = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)
    
    # CCO approval details
    cco_name = Column(String(100), nullable=False)
    cco_email = Column(String(100), nullable=False)
    cco_approved_at = Column(DateTime(timezone=True), nullable=False)
    cco_notes = Column(Text, nullable=True)
    
    # Fiducia review status
    fiducia_review_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # If approved, reference to created content
    approved_content_id = Column(Integer, ForeignKey('marketing_content.id'), nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WarrenInteractions(Base):
    """Track Warren usage and generated content"""
    __tablename__ = "warren_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User and session info
    user_id = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), nullable=True)
    
    # Request details
    user_request = Column(Text, nullable=False)
    requested_content_type = Column(Enum(ContentType), nullable=True)
    requested_audience = Column(Enum(AudienceType), nullable=True)
    
    # Warren's response
    generated_content = Column(Text, nullable=False)
    content_sources_used = Column(Text, nullable=True)  # JSON array of content IDs used
    generation_confidence = Column(Float, nullable=True)  # 0-1 scale
    
    # User feedback
    user_approved = Column(Boolean, nullable=True)
    user_modified_content = Column(Text, nullable=True)  # If user edited Warren's output
    user_feedback_score = Column(Integer, nullable=True)  # 1-5 rating
    user_feedback_notes = Column(Text, nullable=True)
    
    # CCO approval tracking (if user wants to contribute back)
    submitted_for_cco_approval = Column(Boolean, default=False)
    cco_approved = Column(Boolean, nullable=True)
    added_to_queue = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContentTags(Base):
    """Predefined tags for efficient categorization"""
    __tablename__ = "content_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String(50), nullable=False, unique=True, index=True)
    tag_category = Column(String(50), nullable=True)  # topic, tone, demographic, etc.
    description = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Conversation tracking (from original schema - still useful)
class Conversation(Base):
    """User conversations with Warren"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationMessage(Base):
    """Individual messages in conversations"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    message_type = Column(String, nullable=False)  # user, warren, system
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
