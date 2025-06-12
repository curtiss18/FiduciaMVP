# Database Setup Script for Refactored Schema

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from src.models.refactored_database import Base
from src.services.content_migration_service import migration_service
from config.settings import settings

logger = logging.getLogger(__name__)

async def drop_old_tables():
    """Drop old tables to start fresh"""
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        from sqlalchemy import text
        # Drop old tables
        await conn.execute(text("DROP TABLE IF EXISTS knowledge_base_documents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS document_chunks CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS generated_content CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS conversation_messages CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS conversations CASCADE"))
        logger.info("Dropped old tables")

async def create_new_tables():
    """Create new refactored tables"""
    engine = create_async_engine(settings.database_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Created new refactored tables")

async def run_migration():
    """Run the complete database refactor and migration"""
    try:
        print("Starting database refactor...")
        
        # Step 1: Drop old tables
        print("1. Dropping old tables...")
        await drop_old_tables()
        
        # Step 2: Create new tables
        print("2. Creating new refactored tables...")
        await create_new_tables()
        
        # Step 3: Migrate existing content
        print("3. Migrating existing content...")
        result = await migration_service.run_full_migration()
        
        if result["status"] == "success":
            migration_results = result["migration_results"]
            print(f"Migration successful!")
            print(f"   LinkedIn examples: {migration_results['linkedin_examples']}")
            print(f"   Disclaimer templates: {migration_results['disclaimer_templates']}")
            print(f"   Compliance rules: {migration_results['compliance_rules']}")
            print(f"   Total migrated: {migration_results['total_migrated']}")
        else:
            print(f"Migration failed: {result['error']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Database refactor failed: {str(e)}")
        print(f"Database refactor failed: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(run_migration())
