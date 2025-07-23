"""
Test script to verify database seeding
Run this after seeding to confirm all data was created successfully
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from src.core.database import get_db
from src.models import (
    ContentTags, ComplianceRules, MarketingContent,
    AdvisorSessions, AdvisorContent, ComplianceCCO,
    AdvisorContact, AdvisorAudience, WarrenInteractions
)


async def verify_seeding():
    """Verify that all expected seed data exists"""
    
    async for session in get_db():
        try:
            print("🔍 Verifying Database Seed Data")
            print("=" * 50)
            
            # Check each table
            tables_to_check = [
                ("Content Tags", ContentTags),
                ("Compliance Rules", ComplianceRules),
                ("Marketing Content", MarketingContent),
                ("Advisor Sessions", AdvisorSessions),
                ("Advisor Content", AdvisorContent),
                ("Compliance CCOs", ComplianceCCO),
                ("Advisor Contacts", AdvisorContact),
                ("Advisor Audiences", AdvisorAudience),
                ("Warren Interactions", WarrenInteractions)
            ]
            
            all_good = True
            
            for table_name, model_class in tables_to_check:
                result = await session.execute(select(func.count()).select_from(model_class))
                count = result.scalar()
                
                if count > 0:
                    print(f"✅ {table_name}: {count} records")
                else:
                    print(f"❌ {table_name}: NO DATA FOUND")
                    all_good = False
            
            print("=" * 50)
            
            if all_good:
                print("✅ All seed data verified successfully!")
                
                # Show demo accounts
                print("\n📧 Demo Accounts Available:")
                
                # Get CCO accounts
                result = await session.execute(select(ComplianceCCO))
                ccos = result.scalars().all()
                
                print("\nCCO Accounts:")
                for cco in ccos:
                    print(f"  - {cco.email} ({cco.subscription_type.value})")
                
                # Get advisor sessions
                result = await session.execute(
                    select(AdvisorSessions.advisor_id).distinct()
                )
                advisor_ids = [row[0] for row in result]
                
                print("\nAdvisor Accounts:")
                for advisor_id in advisor_ids:
                    print(f"  - {advisor_id}")
                    
            else:
                print("❌ Some seed data is missing!")
                print("💡 Run: python scripts/init_db_with_seed.py --seed")
            
            break
            
        except Exception as e:
            print(f"❌ Error verifying seed data: {e}")
            break


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(verify_seeding())
