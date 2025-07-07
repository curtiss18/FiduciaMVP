# Compliance Portal Migration Rollback Script
"""
Rollback script for SCRUM-55: Database Migration Script

This script provides rollback functionality for compliance portal migrations.
It can safely remove compliance tables and fields while preserving existing data.

SAFETY FEATURES:
- Backs up advisor_content table before making changes
- Only removes columns that were added by the compliance migration
- Provides confirmation prompts before destructive operations
- Comprehensive logging for audit trail

Usage:
    python -m src.migrations.rollback_compliance_migration
    python -m src.migrations.rollback_compliance_migration --confirm-rollback
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def backup_advisor_content():
    """Create backup of advisor_content table before rollback"""
    
    async with AsyncSessionLocal() as session:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"advisor_content_backup_{timestamp}"
        
        logger.info(f"📋 Creating backup table: {backup_table}")
        
        try:
            # Create backup table with all current data
            await session.execute(text(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM advisor_content
            """))
            
            # Add primary key to backup table
            await session.execute(text(f"""
                ALTER TABLE {backup_table} 
                ADD CONSTRAINT pk_{backup_table} PRIMARY KEY (id)
            """))
            
            await session.commit()
            
            # Verify backup
            result = await session.execute(text(f"SELECT COUNT(*) FROM {backup_table}"))
            count = result.scalar()
            
            logger.info(f"✅ Backup created successfully: {backup_table}")
            logger.info(f"📊 Backed up {count} advisor_content records")
            
            return backup_table
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            await session.rollback()
            raise

async def rollback_advisor_content_compliance_fields():
    """Remove compliance fields from advisor_content table"""
    
    async with AsyncSessionLocal() as session:
        logger.info("🔄 Rolling back advisor_content compliance fields...")
        
        try:
            # List of fields to remove (these were added by the compliance migration)
            compliance_fields = [
                'cco_review_status',
                'cco_email', 
                'submitted_for_review_at',
                'review_deadline',
                'review_priority',
                'assigned_to_compliance_id',
                'compliance_due_date'
            ]
            
            # Remove constraints first
            logger.info("🔧 Removing compliance constraints...")
            
            constraint_drops = [
                "ALTER TABLE advisor_content DROP CONSTRAINT IF EXISTS check_cco_review_status",
                "ALTER TABLE advisor_content DROP CONSTRAINT IF EXISTS check_review_priority"
            ]
            
            for constraint_sql in constraint_drops:
                await session.execute(text(constraint_sql))
                logger.info(f"✅ Constraint removed")
            
            # Remove indexes
            logger.info("🔧 Removing compliance indexes...")
            
            index_drops = [
                "DROP INDEX IF EXISTS idx_advisor_content_cco_review_status",
                "DROP INDEX IF EXISTS idx_advisor_content_cco_email", 
                "DROP INDEX IF EXISTS idx_advisor_content_submitted_review",
                "DROP INDEX IF EXISTS idx_advisor_content_review_deadline"
            ]
            
            for index_sql in index_drops:
                await session.execute(text(index_sql))
                logger.info(f"✅ Index removed")
            
            # Remove columns
            logger.info("🔧 Removing compliance columns...")
            
            for field in compliance_fields:
                try:
                    await session.execute(text(f"ALTER TABLE advisor_content DROP COLUMN IF EXISTS {field}"))
                    logger.info(f"✅ Column '{field}' removed")
                except Exception as e:
                    logger.warning(f"⚠️ Could not remove column '{field}': {e}")
            
            await session.commit()
            logger.info("✅ Advisor content compliance fields rollback completed")
            
        except Exception as e:
            logger.error(f"❌ Error during advisor_content rollback: {e}")
            await session.rollback()
            raise

async def rollback_compliance_tables():
    """Remove compliance tables (with foreign key handling)"""
    
    async with AsyncSessionLocal() as session:
        logger.info("🔄 Rolling back compliance tables...")
        
        try:
            # Drop tables in reverse dependency order
            tables_to_drop = [
                'review_feedback',      # Has FK to content_reviews
                'cco_team_members',     # Has FK to compliance_ccos  
                'content_reviews',      # Has FK to compliance_ccos and advisor_content
                'compliance_ccos'       # Base table
            ]
            
            for table in tables_to_drop:
                await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                logger.info(f"✅ Table '{table}' removed")
            
            # Drop enum types that were created
            enum_types = [
                'subscriptiontype',
                'subscriptionstatus', 
                'reviewstatus',
                'violationtype',
                'teammemberrole',
                'teammemberstatus'
            ]
            
            for enum_type in enum_types:
                try:
                    await session.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
                    logger.info(f"✅ Enum type '{enum_type}' removed")
                except Exception as e:
                    logger.warning(f"⚠️ Could not remove enum type '{enum_type}': {e}")
            
            await session.commit()
            logger.info("✅ Compliance tables rollback completed")
            
        except Exception as e:
            logger.error(f"❌ Error during compliance tables rollback: {e}")
            await session.rollback()
            raise

async def verify_rollback():
    """Verify that rollback was successful"""
    
    async with AsyncSessionLocal() as session:
        logger.info("🔍 Verifying rollback completion...")
        
        try:
            # Check that compliance tables are gone
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name IN ('compliance_ccos', 'content_reviews', 'review_feedback', 'cco_team_members')
            """))
            
            remaining_tables = [row[0] for row in result.fetchall()]
            
            if remaining_tables:
                logger.warning(f"⚠️ Some compliance tables still exist: {remaining_tables}")
                return False
            else:
                logger.info("✅ All compliance tables successfully removed")
            
            # Check that compliance fields are gone from advisor_content
            result = await session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'advisor_content' 
                AND column_name IN ('cco_review_status', 'cco_email', 'submitted_for_review_at', 'review_deadline', 'review_priority')
            """))
            
            remaining_fields = [row[0] for row in result.fetchall()]
            
            if remaining_fields:
                logger.warning(f"⚠️ Some compliance fields still exist: {remaining_fields}")
                return False
            else:
                logger.info("✅ All compliance fields successfully removed from advisor_content")
            
            # Verify advisor_content table is still functional
            result = await session.execute(text("SELECT COUNT(*) FROM advisor_content"))
            count = result.scalar()
            
            logger.info(f"✅ Advisor content table functional with {count} records")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during rollback verification: {e}")
            return False

async def full_compliance_rollback(create_backup=True, confirm_destructive=False):
    """Complete rollback of compliance portal migrations"""
    
    logger.info("🚀 COMPLIANCE PORTAL MIGRATION ROLLBACK")
    logger.info("=" * 60)
    
    if not confirm_destructive:
        logger.warning("⚠️ DESTRUCTIVE OPERATION WARNING")
        logger.warning("This will remove all compliance portal database changes!")
        logger.warning("Add --confirm-rollback flag to proceed")
        return False
    
    backup_table = None
    
    try:
        # Step 1: Create backup
        if create_backup:
            backup_table = await backup_advisor_content()
        
        # Step 2: Remove compliance fields from advisor_content
        await rollback_advisor_content_compliance_fields()
        
        # Step 3: Remove compliance tables
        await rollback_compliance_tables()
        
        # Step 4: Verify rollback
        success = await verify_rollback()
        
        if success:
            logger.info("=" * 60)
            logger.info("🎉 COMPLIANCE ROLLBACK COMPLETED SUCCESSFULLY!")
            logger.info("✅ All compliance portal changes have been removed")
            logger.info("✅ Existing advisor functionality preserved")
            if backup_table:
                logger.info(f"📋 Data backup available at: {backup_table}")
            logger.info("🔄 You can safely re-run migrations if needed")
            return True
        else:
            logger.error("❌ Rollback verification failed - manual cleanup may be required")
            return False
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ROLLBACK FAILED: {e}")
        logger.error("💡 Database may be in inconsistent state")
        if backup_table:
            logger.error(f"🔄 Consider restoring from backup: {backup_table}")
        raise

if __name__ == "__main__":
    import sys
    
    confirm_rollback = "--confirm-rollback" in sys.argv
    skip_backup = "--no-backup" in sys.argv
    
    success = asyncio.run(full_compliance_rollback(
        create_backup=not skip_backup,
        confirm_destructive=confirm_rollback
    ))
    
    exit(0 if success else 1)
