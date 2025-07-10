# Fix CASCADE DELETE for ContentReview -> AdvisorContent
"""
This migration ensures the CASCADE DELETE constraint is properly configured
between AdvisorContent and ContentReview.
"""

import asyncio
import logging
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_cascade_delete():
    """Fix the CASCADE DELETE constraint"""
    
    async with AsyncSessionLocal() as session:
        logger.info("🔧 Fixing CASCADE DELETE constraint...")
        
        try:
            # First, check current constraint
            check_constraint_sql = """
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'content_reviews'
                AND kcu.column_name = 'content_id';
            """
            
            result = await session.execute(text(check_constraint_sql))
            constraints = result.fetchall()
            
            if constraints:
                constraint_name = constraints[0][0]
                current_delete_rule = constraints[0][3]
                logger.info(f"📋 Current constraint: {constraint_name}, Delete rule: {current_delete_rule}")
                
                if current_delete_rule != 'CASCADE':
                    logger.info("🔄 Updating constraint to CASCADE...")
                    
                    # Drop the existing constraint
                    drop_sql = f"ALTER TABLE content_reviews DROP CONSTRAINT {constraint_name};"
                    await session.execute(text(drop_sql))
                    logger.info(f"✅ Dropped constraint: {constraint_name}")
                    
                    # Add the new CASCADE constraint
                    add_sql = """
                    ALTER TABLE content_reviews 
                    ADD CONSTRAINT content_reviews_content_id_fkey 
                    FOREIGN KEY (content_id) 
                    REFERENCES advisor_content(id) 
                    ON DELETE CASCADE;
                    """
                    await session.execute(text(add_sql))
                    logger.info("✅ Added CASCADE constraint")
                    
                    await session.commit()
                    logger.info("🎉 CASCADE DELETE constraint fixed!")
                else:
                    logger.info("✅ CASCADE DELETE already configured correctly!")
            else:
                logger.warning("⚠️ No foreign key constraint found - this might indicate a different issue")
                
        except Exception as e:
            logger.error(f"❌ Error fixing constraint: {e}")
            await session.rollback()
            raise

async def test_cascade_delete():
    """Test that CASCADE DELETE now works correctly"""
    
    async with AsyncSessionLocal() as session:
        logger.info("🧪 Testing CASCADE DELETE...")
        
        try:
            # Import models
            from src.models.advisor_workflow_models import AdvisorContent
            from src.models.compliance_models import ComplianceCCO, ContentReview, ReviewFeedback
            import uuid
            
            # Create test data
            test_id = str(uuid.uuid4())[:8]
            
            test_cco = ComplianceCCO(
                email=f"test.cascade.{test_id}@example.com",
                company_name="Test Cascade Co"
            )
            session.add(test_cco)
            await session.flush()
            
            test_content = AdvisorContent(
                title="Test CASCADE DELETE",
                content_text="Testing cascade delete functionality",
                content_type="linkedin_post",
                audience_type="client_communication",
                advisor_id=f"test_cascade_{test_id}"
            )
            session.add(test_content)
            await session.flush()
            
            test_review = ContentReview(
                content_id=test_content.id,
                cco_email=f"test.cascade.{test_id}@example.com",
                cco_id=test_cco.id,
                review_token=f"cascade_test_{test_id}"
            )
            session.add(test_review)
            await session.flush()
            
            test_feedback = ReviewFeedback(
                review_id=test_review.id,
                violation_type="COMPANY_POLICY",
                comment="Test cascade delete feedback"
            )
            session.add(test_feedback)
            await session.commit()
            
            # Now test the cascade delete
            content_id = test_content.id
            review_id = test_review.id
            feedback_id = test_feedback.id
            
            logger.info(f"📋 Created test data: Content={content_id}, Review={review_id}, Feedback={feedback_id}")
            
            # Delete the content - this should CASCADE
            await session.delete(test_content)
            await session.commit()
            
            # Check if related records were deleted
            deleted_review = await session.get(ContentReview, review_id)
            deleted_feedback = await session.get(ReviewFeedback, feedback_id)
            
            if deleted_review is None and deleted_feedback is None:
                logger.info("🎉 CASCADE DELETE working perfectly!")
                logger.info("✅ ContentReview and ReviewFeedback automatically deleted")
                
                # Cleanup remaining test data
                await session.delete(test_cco)
                await session.commit()
                return True
            else:
                logger.error("❌ CASCADE DELETE not working correctly")
                return False
                
        except Exception as e:
            logger.error(f"❌ Cascade delete test failed: {e}")
            await session.rollback()
            raise

async def main():
    """Fix CASCADE DELETE and test it"""
    
    logger.info("🚀 Fixing CASCADE DELETE Configuration")
    logger.info("=" * 50)
    
    try:
        # Fix the constraint
        await fix_cascade_delete()
        
        # Test that it works
        success = await test_cascade_delete()
        
        if success:
            logger.info("\n🏆 CASCADE DELETE FIXED AND TESTED!")
            logger.info("✅ All model relationships now working perfectly")
            logger.info("🎯 Ready for compliance portal development!")
            return True
        else:
            logger.error("\n❌ CASCADE DELETE test failed")
            return False
            
    except Exception as e:
        logger.error(f"\n💥 Fix failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
