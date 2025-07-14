# src/models/audiences.py
"""
Audience and Contact Models for FiduciaMVP
Handles advisor contact management and audience grouping functionality
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.refactored_database import Base

# Association table for many-to-many relationship between audiences and contacts
audience_contacts = Table(
    'audience_contacts',
    Base.metadata,
    Column('audience_id', Integer, ForeignKey('advisor_audiences.id', ondelete='CASCADE'), primary_key=True),
    Column('contact_id', Integer, ForeignKey('advisor_contacts.id', ondelete='CASCADE'), primary_key=True)
)

class AdvisorContact(Base):
    """
    Individual contacts in advisor's CRM
    Stores prospect and client information for audience targeting
    """
    __tablename__ = "advisor_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    advisor_id = Column(String, nullable=False, default='demo_advisor_001', index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(20))
    company = Column(String(255))
    title = Column(String(255))
    status = Column(String(50), default='prospect')  # prospect, client, inactive
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to audiences (many-to-many)
    audiences = relationship("AdvisorAudience", secondary=audience_contacts, back_populates="contacts")
    
    def __repr__(self):
        return f"<AdvisorContact(id={self.id}, name='{self.first_name} {self.last_name}', company='{self.company}')>"

class AdvisorAudience(Base):
    """
    Audience groups for targeted content generation
    Groups contacts by shared characteristics for Warren AI targeting
    """
    __tablename__ = "advisor_audiences"
    
    id = Column(Integer, primary_key=True, index=True)
    advisor_id = Column(String, nullable=False, default='demo_advisor_001', index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    occupation = Column(String(255))  # doctors, CPAs, tech workers, etc.
    relationship_type = Column(String(255))  # church, pickleball, professional, etc.
    characteristics = Column(Text)  # detailed characteristics for Warren context
    contact_count = Column(Integer, default=0)  # cached count for performance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to contacts (many-to-many)
    contacts = relationship("AdvisorContact", secondary=audience_contacts, back_populates="audiences")
    
    def __repr__(self):
        return f"<AdvisorAudience(id={self.id}, name='{self.name}', contact_count={self.contact_count})>"
    
    def update_contact_count(self):
        """Update the cached contact count"""
        self.contact_count = len(self.contacts)
