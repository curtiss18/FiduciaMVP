# Migration: Create Compliance Tables
"""
Migration script to create the new compliance portal tables.
This creates all the core compliance tables needed for the lite version workflow.

Tables created:
- compliance_ccos: CCO account management
- content_reviews: Review workflow with token-based access
- review_feedback: Section-specific feedback
- cco_team_members: Team management for full version
"""

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import engine
from src.models.compliance_models import (
    ComplianceCCO, 
    ContentReview, 
    ReviewFeedback, 
    CCOTeamMember,
    Base
)
import logging

logger = logging.getLogger(__name__)

async def create_compliance_tables():
    """
    Create all compliance tables.
    Safe to run multiple times - will only create tables that don't exist.
    """
    async with engine.begin() as conn:
        logger.info("Starting compliance tables creation...")
        
        # Create the tables
        try:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info("🎉 All compliance tables created successfully!")
            
            # Log created tables
            tables_created = [
                "compliance_ccos",
                "content_reviews", 
                "review_feedback",
                "cco_team_members"
            ]
            
            for table in tables_created:
                logger.info(f"✅ Table '{table}' ready")
                
        except Exception as e:
            logger.error(f"❌ Failed to create compliance tables: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_compliance_tables())
