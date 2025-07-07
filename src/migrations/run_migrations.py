# Master Migration Runner for Compliance Portal
"""
Master script to run all compliance portal migrations in the correct order.
This ensures database schema is properly set up for development and testing.

Migration Order:
1. Add compliance fields to advisor_content table
2. Create new compliance tables
3. Create sample data for testing

Usage:
    python -m src.migrations.run_migrations
"""

import asyncio
import logging

# Import migration functions using clean file names
from src.migrations.advisor_content_compliance_fields import migrate_advisor_content_compliance_fields
from src.migrations.create_compliance_tables import create_compliance_tables

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_all_migrations():
    """Run all compliance portal migrations in correct order"""
    
    logger.info("🚀 Starting Compliance Portal Migration Suite")
    logger.info("=" * 60)
    
    try:
        # Migration 1: Add compliance fields to advisor_content
        logger.info("📝 Step 1: Adding compliance fields to advisor_content table...")
        await migrate_advisor_content_compliance_fields()
        logger.info("✅ Step 1 completed successfully!")
        
        # Migration 2: Create compliance tables
        logger.info("📝 Step 2: Creating compliance portal tables...")
        await create_compliance_tables()
        logger.info("✅ Step 2 completed successfully!")
        
        logger.info("=" * 60)
        logger.info("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        logger.info("📊 Database is now ready for compliance portal development")
        logger.info("🧪 Sample data available for testing")
        logger.info("")
        logger.info("📝 ROLLBACK INFORMATION:")
        logger.info("🔄 To rollback migrations: python -m src.migrations.rollback_compliance_migration --confirm-rollback")
        logger.info("📖 Full documentation: docs/migrations/SCRUM-55-Migration-Documentation.md")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ MIGRATION FAILED: {e}")
        logger.error("💡 Please check the error above and fix any issues")
        logger.error("🔄 Migrations are safe to re-run after fixing issues")
        raise

async def run_migrations_only():
    """Run only the schema migrations (no sample data)"""
    
    logger.info("🚀 Starting Compliance Portal Schema Migrations")
    logger.info("=" * 60)
    
    try:
        # Migration 1: Add compliance fields to advisor_content
        logger.info("📝 Step 1: Adding compliance fields to advisor_content table...")
        await migrate_advisor_content_compliance_fields()
        logger.info("✅ Step 1 completed successfully!")
        
        # Migration 2: Create compliance tables
        logger.info("📝 Step 2: Creating compliance portal tables...")
        await create_compliance_tables()
        logger.info("✅ Step 2 completed successfully!")
        
        logger.info("=" * 60)
        logger.info("🎉 SCHEMA MIGRATIONS COMPLETED SUCCESSFULLY!")
        logger.info("📊 Database schema is ready for compliance portal")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ MIGRATION FAILED: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schema-only":
        asyncio.run(run_migrations_only())
    else:
        asyncio.run(run_all_migrations())
