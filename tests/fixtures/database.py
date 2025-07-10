"""
Test database management utilities for Warren integration tests.
"""

import asyncio
import pytest
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import AsyncGenerator, Dict, Any, List

from config.test_settings import get_settings_for_test
from src.core.database import get_db
from src.models.refactored_database import (
    Base, ContentType, AudienceType, MarketingContent, ComplianceRules, 
    UserContentQueue, WarrenInteractions, ContentTags, Conversation, ConversationMessage
)


class TestDatabaseManager:
    """Manages test database lifecycle and data."""
    
    def __init__(self):
        self.settings = get_settings_for_test()
        self.engine = None
        self.session_factory = None
        self.created_data_ids = []
        
    async def setup_database(self):
        """Initialize test database and create tables."""
        # Create async engine for test database
        self.engine = create_async_engine(
            self.settings.database_url,
            echo=self.settings.debug,
            future=True
        )
        
        # Create session factory
        self.session_factory = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Ensure pgvector extension is available
        await self._ensure_pgvector_extension()
        
    async def _ensure_pgvector_extension(self):
        """Ensure pgvector extension is installed in test database."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception as e:
            print(f"Warning: Could not create vector extension: {e}")
            
    async def cleanup_database(self):
        """Clean up test database."""
        if self.engine:
            async with self.engine.begin() as conn:
                # Drop all tables
                await conn.run_sync(Base.metadata.drop_all)
            await self.engine.dispose()
            
    async def get_session(self) -> AsyncSession:
        """Get a test database session."""
        if not self.session_factory:
            await self.setup_database()
        return self.session_factory()
        
    async def insert_test_data(self, session: AsyncSession, data_type: str, data: List[Dict[str, Any]]) -> List[str]:
        """Insert test data and track IDs for cleanup."""
        created_ids = []
        
        try:
            if data_type == "knowledge_base":
                for item in data:
                    # Create MarketingContent entries
                    marketing_entry = MarketingContent(
                        title=item["title"],
                        content_text=item["content_text"],
                        content_type=item.get("content_type", "example"),
                        tags=item.get("tags", ""),
                        metadata=item.get("metadata", {}),
                        embedding=item.get("embedding", [0.1] * 1536)  # Dummy embedding
                    )
                    session.add(marketing_entry)
                    await session.flush()
                    created_ids.append(f"marketing_{marketing_entry.id}")
                    
            elif data_type == "compliance":
                for item in data:
                    # Create compliance entries
                    compliance_entry = ComplianceRules(
                        title=item["title"], 
                        content_text=item["content_text"],
                        content_type="disclaimer",
                        tags=item.get("tags", ""),
                        metadata={"compliance": True}
                    )
                    session.add(compliance_entry)
                    await session.flush()
                    created_ids.append(f"compliance_{compliance_entry.id}")
                    
            elif data_type == "conversation":
                # Create conversation entries if needed
                # Implementation depends on your conversation model structure
                pass
                
            await session.commit()
            self.created_data_ids.extend(created_ids)
            return created_ids
            
        except Exception as e:
            await session.rollback()
            raise e
            
    async def cleanup_test_data(self, session: AsyncSession, preserve_on_failure: bool = True):
        """Clean up test data, optionally preserving on test failure."""
        if preserve_on_failure and hasattr(pytest, "current_test_failed") and pytest.current_test_failed():
            print(f"Test failed - preserving test data: {self.created_data_ids}")
            return
            
        try:
            # Clean up created data
            for data_id in self.created_data_ids:
                if data_id.startswith("marketing_"):
                    marketing_id = data_id.replace("marketing_", "")
                    await session.execute(text(f"DELETE FROM marketing_content WHERE id = {marketing_id}"))
                elif data_id.startswith("compliance_"):
                    compliance_id = data_id.replace("compliance_", "")
                    await session.execute(text(f"DELETE FROM compliance_rules WHERE id = {compliance_id}"))
                    
            await session.commit()
            self.created_data_ids.clear()
            
        except Exception as e:
            await session.rollback()
            print(f"Error cleaning up test data: {e}")


# Global test database manager
test_db_manager = TestDatabaseManager()


@pytest.fixture(scope="session")
async def test_database():
    """Session-scoped test database setup."""
    await test_db_manager.setup_database()
    yield test_db_manager
    await test_db_manager.cleanup_database()


@pytest.fixture
async def db_session(test_database: TestDatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped database session with automatic cleanup."""
    session = await test_database.get_session()
    try:
        yield session
    finally:
        await test_database.cleanup_test_data(session)
        await session.close()


@pytest.fixture
async def db_session_with_test_data(test_database: TestDatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """Database session pre-populated with test data."""
    from tests.fixtures.test_data import get_test_data
    
    # Get a session
    db_session = await test_database.get_session()
    
    try:
        # Insert sample test data
        vector_data = get_test_data("vector_results")
        compliance_data = get_test_data("compliance_results")
        
        await test_database.insert_test_data(db_session, "knowledge_base", vector_data)
        await test_database.insert_test_data(db_session, "compliance", compliance_data)
        
        yield db_session
        
    finally:
        await test_database.cleanup_test_data(db_session)
        await db_session.close()
    
    
# Helper function for tests that need database override
async def override_get_db():
    """Override function for FastAPI dependency injection in tests."""
    session = await test_db_manager.get_session()
    try:
        yield session
    finally:
        await session.close()
