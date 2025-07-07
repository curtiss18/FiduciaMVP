# Migration: Add Compliance Fields to Advisor Content
"""
Migration script to add compliance review fields to existing advisor_content table.
This extends the existing table to support the compliance review workflow.

Run this migration after creating the compliance tables.
"""

from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import engine
import logging

logger = logging.getLogger(__name__)

# SQL statements to add compliance fields to advisor_content table
MIGRATION_SQL = [
    # Add compliance review status field
    """
    ALTER TABLE advisor_content 
    ADD COLUMN IF NOT EXISTS cco_review_status VARCHAR(50) DEFAULT 'not_submitted'
    """,
    
    # Add CCO email field
    """
    ALTER TABLE advisor_content 
    ADD COLUMN IF NOT EXISTS cco_email VARCHAR(255)
    """,
    
    # Add submission timestamp
    """
    ALTER TABLE advisor_content 
    ADD COLUMN IF NOT EXISTS submitted_for_review_at TIMESTAMP WITH TIME ZONE
    """,
    
    # Add review deadline field
    """
    ALTER TABLE advisor_content 
    ADD COLUMN IF NOT EXISTS review_deadline TIMESTAMP WITH TIME ZONE
    """,
    
    # Add review priority field
    """
    ALTER TABLE advisor_content 
    ADD COLUMN IF NOT EXISTS review_priority VARCHAR(20) DEFAULT 'normal'
    """,
]

# Constraints (separate from columns due to PostgreSQL limitations)
CONSTRAINT_SQL = [
    # Add check constraint for review status (only if it doesn't exist)
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'check_cco_review_status' 
            AND table_name = 'advisor_content'
        ) THEN
            ALTER TABLE advisor_content 
            ADD CONSTRAINT check_cco_review_status 
            CHECK (cco_review_status IN ('not_submitted', 'submitted', 'in_review', 'approved', 'rejected', 'revision_requested'));
        END IF;
    END $$;
    """,
    
    # Add check constraint for review priority
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'check_review_priority' 
            AND table_name = 'advisor_content'
        ) THEN
            ALTER TABLE advisor_content 
            ADD CONSTRAINT check_review_priority 
            CHECK (review_priority IN ('low', 'normal', 'high', 'urgent'));
        END IF;
    END $$;
    """,
]

# Indexes for performance optimization
INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_advisor_content_cco_review_status ON advisor_content(cco_review_status)",
    "CREATE INDEX IF NOT EXISTS idx_advisor_content_cco_email ON advisor_content(cco_email) WHERE cco_email IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS idx_advisor_content_submitted_review ON advisor_content(submitted_for_review_at) WHERE submitted_for_review_at IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS idx_advisor_content_review_deadline ON advisor_content(review_deadline) WHERE review_deadline IS NOT NULL",
]

async def migrate_advisor_content_compliance_fields():
    """
    Add compliance fields to advisor_content table.
    Safe to run multiple times - uses IF NOT EXISTS clauses.
    """
    async with engine.begin() as conn:
        logger.info("Starting advisor_content compliance fields migration...")
        
        # Add columns first
        for i, sql_statement in enumerate(MIGRATION_SQL, 1):
            try:
                await conn.execute(text(sql_statement))
                logger.info(f"✅ Migration step {i}/{len(MIGRATION_SQL)} completed")
            except Exception as e:
                logger.error(f"❌ Migration step {i} failed: {e}")
                raise
        
        # Add constraints
        for i, constraint_sql in enumerate(CONSTRAINT_SQL, 1):
            try:
                await conn.execute(text(constraint_sql))
                logger.info(f"✅ Constraint {i}/{len(CONSTRAINT_SQL)} added")
            except Exception as e:
                logger.error(f"❌ Constraint {i} failed: {e}")
                raise
        
        # Add indexes
        for i, index_sql in enumerate(INDEX_SQL, 1):
            try:
                await conn.execute(text(index_sql))
                logger.info(f"✅ Index {i}/{len(INDEX_SQL)} created")
            except Exception as e:
                logger.error(f"❌ Index {i} creation failed: {e}")
                raise
        
        logger.info("🎉 Advisor content compliance fields migration completed successfully!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_advisor_content_compliance_fields())
