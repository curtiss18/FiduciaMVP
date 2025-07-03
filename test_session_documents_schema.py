#!/usr/bin/env python3
"""
Test script for SCRUM-38: session_documents table schema validation
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import AsyncSessionLocal, engine
from src.models.database import Base
from src.models.advisor_workflow_models import SessionDocuments, AdvisorSessions


async def ensure_database_tables():
    """Ensure all database tables are created before testing."""
    print("🗄️ Ensuring database tables exist...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {str(e)}")
        return False


async def test_session_documents_schema():
    """Test that the session_documents table works correctly."""
    print("🧪 Testing session_documents table schema (SCRUM-38)...")
    
    async with AsyncSessionLocal() as session:
        try:
            # First, create a test advisor session
            test_session = AdvisorSessions(
                advisor_id="test_advisor_001",
                session_id=f"test_session_{uuid4()}",
                title="Test Session for Document Upload"
            )
            session.add(test_session)
            await session.flush()  # Get the session ID
            
            # Create a test document
            test_document = SessionDocuments(
                id=str(uuid4()),
                session_id=test_session.session_id,
                title="Test Document - Retirement Planning Guide",
                content_type="pdf",
                original_filename="retirement_guide.pdf",
                file_size_bytes=1024000,
                full_content="This is a sample document about retirement planning. It contains comprehensive information about 401k plans, IRA contributions, and retirement income strategies.",
                summary="A comprehensive guide covering 401k plans, IRA contributions, and retirement income strategies for financial advisors.",
                word_count=150,
                document_metadata='{"extraction_method": "test", "confidence": 0.95}',
                processing_status="processed"
            )
            
            session.add(test_document)
            await session.commit()
            
            print(f"✅ Successfully created test document: {test_document.id}")
            print(f"   - Title: {test_document.title}")
            print(f"   - Content Type: {test_document.content_type}")
            print(f"   - Word Count: {test_document.word_count}")
            print(f"   - Session ID: {test_document.session_id}")
            print(f"   - Processing Status: {test_document.processing_status}")
            
            # Test retrieval
            retrieved_doc = await session.get(SessionDocuments, test_document.id)
            if retrieved_doc:
                print(f"✅ Successfully retrieved document: {retrieved_doc.title}")
                print(f"   - Created at: {retrieved_doc.created_at}")
                print(f"   - Summary: {retrieved_doc.summary[:100]}...")
            else:
                print("❌ Failed to retrieve document")
                return False
            
            # Test foreign key relationship
            if retrieved_doc.session_id == test_session.session_id:
                print("✅ Foreign key relationship working correctly")
            else:
                print("❌ Foreign key relationship failed")
                return False
            
            # Cleanup test data (delete documents first due to foreign key constraint)
            await session.delete(test_document)
            await session.delete(test_session)
            await session.commit()
            print("🧹 Cleaned up test data")
            
            return True
            
        except Exception as e:
            print(f"❌ Database schema test failed: {str(e)}")
            await session.rollback()
            return False


async def test_document_metadata_fields():
    """Test all the document metadata fields work correctly."""
    print("\n🧪 Testing document metadata fields...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Test with video transcript type
            test_session = AdvisorSessions(
                advisor_id="test_advisor_002", 
                session_id=f"test_video_session_{uuid4()}",
                title="Video Transcript Test Session"
            )
            session.add(test_session)
            await session.flush()
            
            # Create video transcript document
            video_doc = SessionDocuments(
                id=str(uuid4()),
                session_id=test_session.session_id,
                title="Investment Basics - YouTube Transcript",
                content_type="video_transcript",
                original_filename="investment_basics_transcript.txt",
                file_size_bytes=50000,
                full_content="Welcome to investment basics. Today we'll discuss the fundamentals of portfolio diversification...",
                summary="Video transcript covering portfolio diversification fundamentals and basic investment principles.",
                word_count=2500,
                document_metadata='{"video_id": "xyz123", "duration_minutes": 15, "themes": ["diversification", "risk_management"]}',
                processing_status="processed",
                times_referenced=3,
                last_referenced_at=datetime.now(timezone.utc)
            )
            
            session.add(video_doc)
            await session.commit()
            
            print(f"✅ Successfully created video transcript document")
            print(f"   - Content Type: {video_doc.content_type}")
            print(f"   - Times Referenced: {video_doc.times_referenced}")
            print(f"   - Processing Status: {video_doc.processing_status}")
            print(f"   - Metadata: {video_doc.document_metadata}")
            
            # Cleanup (delete document first due to foreign key constraint)
            await session.delete(video_doc)
            await session.delete(test_session)
            await session.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Metadata fields test failed: {str(e)}")
            await session.rollback()
            return False


async def main():
    """Run all schema tests for SCRUM-38."""
    print("🚀 Starting SCRUM-38 Database Schema Tests")
    print("=" * 50)
    
    # Ensure database tables exist
    db_setup = await ensure_database_tables()
    if not db_setup:
        print("❌ Database setup failed!")
        return 1
    
    # Test basic schema
    basic_test = await test_session_documents_schema()
    
    # Test metadata fields
    metadata_test = await test_document_metadata_fields()
    
    print("\n" + "=" * 50)
    if basic_test and metadata_test:
        print("🎉 All SCRUM-38 database schema tests PASSED!")
        print("✅ session_documents table is ready for document storage")
        return 0
    else:
        print("❌ Some SCRUM-38 tests FAILED!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
