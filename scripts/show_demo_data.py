#!/usr/bin/env python
"""
Display available demo accounts and sample data
Useful reference for developers testing the system
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from src.core.database import AsyncSessionLocal
from src.models import (
    ContentTags, ComplianceRules, MarketingContent,
    AdvisorSessions, AdvisorContent, ComplianceCCO,
    AdvisorContact, AdvisorAudience, WarrenInteractions,
    ContentReview, CCOTeamMember
)


async def show_demo_info():
    """Display information about demo accounts and sample data"""
    
    async with AsyncSessionLocal() as session:
        print("\n" + "="*60)
        print("🎯 FIDUCIAMVP DEMO DATA REFERENCE")
        print("="*60)
        
        # Demo Accounts
        print("\n📧 DEMO ACCOUNTS")
        print("-" * 40)
        print("\n1. ADVISOR ACCOUNTS:")
        print("   • ID: demo_advisor_001")
        print("     - Has active Warren sessions")
        print("     - Content in various approval states")
        print("     - CRM contacts and audiences")
        
        # CCO Accounts
        print("\n2. CCO ACCOUNTS:")
        result = await session.execute(select(ComplianceCCO))
        ccos = result.scalars().all()
        
        for cco in ccos:
            print(f"\n   • Email: {cco.email}")
            print(f"     - Type: {cco.subscription_type.value}")
            print(f"     - Status: {cco.subscription_status.value}")
            print(f"     - Company: {cco.company_name}")
            
            if cco.subscription_type.value == "full":
                # Get team members
                team_result = await session.execute(
                    select(CCOTeamMember).where(CCOTeamMember.cco_id == cco.id)
                )
                team_members = team_result.scalars().all()
                if team_members:
                    print("     - Team Members:")
                    for member in team_members:
                        print(f"       • {member.email} ({member.role.value})")
        
        # Sample Content
        print("\n\n📝 SAMPLE CONTENT")
        print("-" * 40)
        
        # Marketing Content
        mc_count = await session.execute(select(func.count()).select_from(MarketingContent))
        print(f"\n• Pre-approved Marketing Content: {mc_count.scalar()} pieces")
        
        # Advisor Content by Status
        print("\n• Advisor Content by Status:")
        statuses = ["draft", "submitted", "approved", "needs_revision"]
        for status in statuses:
            count_result = await session.execute(
                select(func.count()).select_from(AdvisorContent).where(
                    AdvisorContent.status == status
                )
            )
            count = count_result.scalar()
            if count > 0:
                print(f"  - {status.title()}: {count}")
        
        # Active Reviews
        review_count = await session.execute(
            select(func.count()).select_from(ContentReview).where(
                ContentReview.status == "IN_PROGRESS"
            )
        )
        print(f"\n• Active Compliance Reviews: {review_count.scalar()}")
        
        # Warren Sessions
        print("\n\n💬 WARREN AI SESSIONS")
        print("-" * 40)
        
        result = await session.execute(select(AdvisorSessions))
        sessions = result.scalars().all()
        
        for session_obj in sessions:
            print(f"\n• Session: {session_obj.session_id}")
            print(f"  - Title: {session_obj.title}")
            print(f"  - Messages: {session_obj.message_count}")
        
        # CRM Data
        print("\n\n👥 CRM DATA")
        print("-" * 40)
        
        contact_count = await session.execute(select(func.count()).select_from(AdvisorContact))
        audience_count = await session.execute(select(func.count()).select_from(AdvisorAudience))
        
        print(f"\n• Contacts: {contact_count.scalar()}")
        print(f"• Audiences: {audience_count.scalar()}")
        
        # Audiences
        result = await session.execute(select(AdvisorAudience))
        audiences = result.scalars().all()
        for audience in audiences:
            print(f"  - {audience.name} ({audience.contact_count} contacts)")
        
        # System Data
        print("\n\n⚙️  SYSTEM DATA")
        print("-" * 40)
        
        tag_count = await session.execute(select(func.count()).select_from(ContentTags))
        rule_count = await session.execute(select(func.count()).select_from(ComplianceRules))
        
        print(f"\n• Content Tags: {tag_count.scalar()}")
        print(f"• Compliance Rules: {rule_count.scalar()}")
        
        print("\n\n💡 TIPS FOR TESTING")
        print("-" * 40)
        print("\n1. Test content creation workflow:")
        print("   - Login as demo_advisor_001")
        print("   - Create content with Warren")
        print("   - Submit for compliance review")
        
        print("\n2. Test compliance review:")
        print("   - Login as john.cco@firmcompliance.com")
        print("   - Review pending content")
        print("   - Approve or request changes")
        
        print("\n3. Test audience targeting:")
        print("   - Use existing audiences for content creation")
        print("   - Warren will personalize based on audience characteristics")
        
        print("\n" + "="*60)
        print("For detailed documentation: docs/database/seeding-guide.md")
        print("="*60 + "\n")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(show_demo_info())
