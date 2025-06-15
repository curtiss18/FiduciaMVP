#!/usr/bin/env python3
"""
Database Migration Script: Advisor Workflow Schema
Migrates from old WarrenInteractions-based schema to new advisor workflow schema.
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Database imports
from src.core.database import AsyncSessionLocal, engine
from src.models.advisor_workflow_models import Base as AdvisorBase
from src.models.refactored_database import Base as MainBase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def drop_old_tables():
    """Drop tables that we're replacing with new advisor workflow tables."""
    tables_to_drop = [
        'warren_interactions',
        'user_content_queue', 
        'conversation_messages',
        'conversations'
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for table in tables_to_drop:
                logger.info(f"Dropping table: {table}")
                await db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            
            await db.commit()
            logger.info("✅ Successfully dropped old tables")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error dropping tables: {e}")
            await db.rollback()
            return False


async def create_advisor_workflow_tables():
    """Create new advisor workflow tables."""
    try:
        logger.info("Creating advisor workflow tables...")
        
        # This will create all tables defined in advisor_workflow_models.py
        async with engine.begin() as conn:
            await conn.run_sync(AdvisorBase.metadata.create_all)
        
        logger.info("✅ Successfully created advisor workflow tables")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Error creating advisor workflow tables: {e}")
        return False


async def verify_migration():
    """Verify that the migration completed successfully."""
    async with AsyncSessionLocal() as db:
        try:
            # Check that new tables exist
            new_tables = [
                'advisor_sessions',
                'advisor_messages', 
                'advisor_content',
                'compliance_reviews',
                'content_distribution'
            ]
            
            for table in new_tables:
                result = await db.execute(text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                ))
                exists = result.scalar()
                
                if exists:
                    logger.info(f"✅ Table {table} exists")
                else:
                    logger.error(f"❌ Table {table} missing")
                    return False
            
            # Check that old tables are gone
            old_tables = ['warren_interactions', 'user_content_queue']
            for table in old_tables:
                result = await db.execute(text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                ))
                exists = result.scalar()
                
                if not exists:
                    logger.info(f"✅ Old table {table} removed")
                else:
                    logger.warning(f"⚠️  Old table {table} still exists")
            
            logger.info("✅ Migration verification completed")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error verifying migration: {e}")
            return False


async def run_migration():
    """Run the complete database migration."""
    logger.info("🚀 Starting advisor workflow database migration...")
    
    # Step 1: Drop old tables
    logger.info("\n📋 Step 1: Dropping old tables...")
    if not await drop_old_tables():
        logger.error("❌ Migration failed at step 1")
        return False
    
    # Step 2: Create new tables
    logger.info("\n📋 Step 2: Creating new advisor workflow tables...")
    if not await create_advisor_workflow_tables():
        logger.error("❌ Migration failed at step 2")
        return False
    
    # Step 3: Verify migration
    logger.info("\n📋 Step 3: Verifying migration...")
    if not await verify_migration():
        logger.error("❌ Migration verification failed")
        return False
    
    logger.info("\n🎉 Database migration completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Update imports in services to use new models")
    logger.info("2. Create new API endpoints for advisor workflow")
    logger.info("3. Update frontend to save Warren conversations")
    
    return True


if __name__ == "__main__":
    asyncio.run(run_migration())
