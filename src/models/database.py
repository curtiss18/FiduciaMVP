from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class KnowledgeBaseDocument(Base):
    """Stores compliance documents and content"""
    __tablename__ = "knowledge_base_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    document_type = Column(String, nullable=False)  # regulation, example, violation, template
    source = Column(String, nullable=True)
    platform = Column(String, nullable=True)  # linkedin, twitter, website, email
    compliance_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentChunk(Base):
    """Stores chunked documents with embeddings for vector search"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False)  # Foreign key to KnowledgeBaseDocument
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding dimension
    chunk_metadata = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    """Stores user conversations with Warren"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True)  # For future user management
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ConversationMessage(Base):
    """Stores individual messages in conversations"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, nullable=False)  # Foreign key to Conversation
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON metadata (tokens, sources, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GeneratedContent(Base):
    """Stores generated content for compliance tracking"""
    __tablename__ = "generated_content"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, nullable=True)
    prompt = Column(Text, nullable=False)
    generated_text = Column(Text, nullable=False)
    platform = Column(String, nullable=True)
    compliance_score = Column(Float, nullable=True)
    sources_used = Column(Text, nullable=True)  # JSON array of source document IDs
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Import all models to ensure tables are created
from src.models.advisor_workflow_models import *
from src.models.refactored_database import *
from src.models.audiences import *
from src.models.compliance_models import *
