# Compliance Portal Database Models
"""
Database schema for compliance portal workflow:
1. CCO account management (lite and full versions)
2. Content review workflow with token-based access
3. Detailed feedback tracking with violation types
4. Team management for full version CCOs
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
import enum

# Import shared Base from main database models
from src.models.refactored_database import Base
# Note: AdvisorContent will be referenced as string to avoid circular imports

# Enums for compliance workflow
class SubscriptionType(enum.Enum):
    """CCO subscription types"""
    LITE = "lite"           # Free version with email access
    FULL = "full"           # Paid version with dashboard

class SubscriptionStatus(enum.Enum):
    """CCO subscription status"""
    ACTIVE = "active"       # Currently active subscription
    TRIAL = "trial"         # In trial period
    EXPIRED = "expired"     # Trial or subscription expired
    CANCELLED = "cancelled" # Subscription cancelled

class ReviewStatus(enum.Enum):
    """Content review status progression"""
    PENDING = "pending"         # Waiting for CCO review
    IN_PROGRESS = "in_progress" # CCO actively reviewing
    APPROVED = "approved"       # CCO approved content
    REJECTED = "rejected"       # CCO rejected content

class ViolationType(enum.Enum):
    """Types of compliance violations"""
    COMPANY_POLICY = "company_policy"
    FINRA_RULE = "finra_rule"
    SEC_REGULATION = "sec_regulation"
    STATE_REGULATION = "state_regulation"
    MISLEADING_STATEMENT = "misleading_statement"
    PERFORMANCE_GUARANTEE = "performance_guarantee"
    OMITTED_DISCLOSURE = "omitted_disclosure"
    UNAUTHORIZED_TESTIMONIAL = "unauthorized_testimonial"
    UNAPPROVED_CLAIM = "unapproved_claim"
    OTHER = "other"

class TeamMemberRole(enum.Enum):
    """Roles for team members in full version"""
    ADMIN = "admin"         # Full administrative access
    REVIEWER = "reviewer"   # Can review and approve content
    VIEWER = "viewer"       # Read-only access

class TeamMemberStatus(enum.Enum):
    """Status of team member accounts"""
    ACTIVE = "active"       # Active team member
    INACTIVE = "inactive"   # Deactivated account
    PENDING = "pending"     # Invitation sent, not yet accepted


class ComplianceCCO(Base):
    """CCO account management for both lite and full versions"""
    __tablename__ = "compliance_ccos"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Subscription management
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.LITE, nullable=False, index=True)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)
    seats_purchased = Column(Integer, default=1)
    seats_used = Column(Integer, default=0)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Company information (full version)
    company_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('seats_used <= seats_purchased', name='check_seats_usage'),
        CheckConstraint("email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='check_valid_email'),
    )


class ContentReview(Base):
    """Content review workflow with token-based access"""
    __tablename__ = "content_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content being reviewed
    content_id = Column(Integer, ForeignKey('advisor_content.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # CCO information
    cco_email = Column(String(255), nullable=False, index=True)  # Supports both lite and full
    cco_id = Column(Integer, ForeignKey('compliance_ccos.id', ondelete='SET NULL'), nullable=True, index=True)  # NULL for lite version
    
    # Token-based access (lite version)
    review_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # NULL = no expiration for lite
    
    # Review workflow
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False, index=True)
    decision = Column(String(20), nullable=True)  # 'approved' or 'rejected'
    overall_feedback = Column(Text, nullable=True)
    compliance_score = Column(Integer, nullable=True)  # 1-100
    
    # Timing
    review_started_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notifications
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships - use lazy loading to avoid circular imports
    content = relationship("AdvisorContent", lazy="select", backref=backref("reviews", cascade="all, delete-orphan", lazy="select"))
    cco = relationship("ComplianceCCO", backref="reviews")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(decision IS NULL AND reviewed_at IS NULL) OR (decision IS NOT NULL AND reviewed_at IS NOT NULL)",
            name='check_decision_reviewed_at'
        ),
        CheckConstraint(
            "decision != 'rejected' OR (decision = 'rejected' AND overall_feedback IS NOT NULL AND length(overall_feedback) > 10)",
            name='check_rejected_requires_feedback'
        ),
        CheckConstraint(
            "compliance_score IS NULL OR (compliance_score >= 1 AND compliance_score <= 100)",
            name='check_compliance_score_range'
        ),
    )


class ReviewFeedback(Base):
    """Section-specific feedback for content reviews"""
    __tablename__ = "review_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey('content_reviews.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Text section being commented on
    section_text = Column(Text, nullable=True)  # The highlighted text
    section_start_pos = Column(Integer, nullable=True)  # Character position start
    section_end_pos = Column(Integer, nullable=True)    # Character position end
    
    # Violation details
    violation_type = Column(Enum(ViolationType), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    regulation_reference = Column(Text, nullable=True)  # Specific FINRA/SEC rule citation
    
    # AI assistance tracking
    ai_generated = Column(Boolean, default=False)
    warren_session_id = Column(String(100), nullable=True)  # Link to Warren AI session if applicable
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    review = relationship("ContentReview", backref=backref("feedback_items", cascade="all, delete-orphan"))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(section_start_pos IS NULL AND section_end_pos IS NULL) OR "
            "(section_start_pos IS NOT NULL AND section_end_pos IS NOT NULL AND section_end_pos > section_start_pos)",
            name='check_valid_section_positions'
        ),
        CheckConstraint(
            "length(trim(comment)) > 0",
            name='check_comment_not_empty'
        ),
    )


class CCOTeamMember(Base):
    """Team members for full version CCO accounts"""
    __tablename__ = "cco_team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    cco_id = Column(Integer, ForeignKey('compliance_ccos.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Member information
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    role = Column(Enum(TeamMemberRole), default=TeamMemberRole.REVIEWER, nullable=False, index=True)
    status = Column(Enum(TeamMemberStatus), default=TeamMemberStatus.ACTIVE, nullable=False, index=True)
    
    # Invitation and activation
    invitation_token = Column(String(255), unique=True, nullable=True)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permissions (JSON for flexibility)
    permissions = Column(Text, nullable=True)  # JSON array of permission strings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    cco = relationship("ComplianceCCO", backref="team_members")
    
    # Constraints - use unique constraint instead of check constraint
    __table_args__ = (
        # Unique constraint to prevent duplicate cco_id + email combinations
        UniqueConstraint('cco_id', 'email', name='uq_cco_team_member_email'),
    )


# Import AdvisorContent to ensure relationship works
# (This will be imported in database.py to avoid circular imports)
