"""
Comprehensive database seeding script for FiduciaMVP
Fixed version with proper async handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import random
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

# Import all models
from src.models.refactored_database import (
    Base, MarketingContent, ComplianceRules, ContentTags, 
    WarrenInteractions, Conversation, ConversationMessage,
    ContentType, AudienceType, ApprovalStatus, SourceType
)
from src.models.advisor_workflow_models import (
    AdvisorSessions, AdvisorMessages, AdvisorContent,
    ComplianceReviews, ContentDistribution, ConversationContext,
    SessionDocuments, ContentStatus, ReviewDecision
)
from src.models.compliance_models import (
    ComplianceCCO, ContentReview, ReviewFeedback, CCOTeamMember,
    SubscriptionType, SubscriptionStatus, ReviewStatus, ViolationType,
    TeamMemberRole, TeamMemberStatus
)
from src.models.audiences import AdvisorContact, AdvisorAudience

from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def seed_database():
    """Main entry point for database seeding with proper async handling"""
    
    async with AsyncSessionLocal() as session:
        try:
            logger.info("🌱 Starting database seeding...")
            
            # Step 1: Core reference data
            await seed_content_tags(session)
            await seed_compliance_rules(session)
            await seed_marketing_content(session)
            
            # Step 2: User and session data
            await seed_advisor_sessions(session)
            await seed_advisor_content(session)
            
            # Step 3: Compliance workflow
            await seed_compliance_ccos(session)
            await seed_content_reviews(session)
            
            # Step 4: CRM data
            await seed_advisor_contacts(session)
            await seed_advisor_audiences(session)
            
            # Step 5: Usage data
            await seed_warren_interactions(session)
            await seed_content_distribution(session)
            
            await session.commit()
            logger.info("✅ Database seeding completed successfully!")
            
            # Print summary
            await print_seeding_summary(session)
            
        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            await session.rollback()
            raise


async def seed_content_tags(session: AsyncSession):
    """Seed content categorization tags"""
    logger.info("🏷️  Seeding content tags...")
    
    tags_data = [
        # Topic tags
        {"tag_name": "retirement_planning", "tag_category": "topic", "description": "Content about retirement strategies"},
        {"tag_name": "tax_planning", "tag_category": "topic", "description": "Tax optimization strategies"},
        {"tag_name": "estate_planning", "tag_category": "topic", "description": "Estate and legacy planning"},
        {"tag_name": "investment_basics", "tag_category": "topic", "description": "Fundamental investment concepts"},
        {"tag_name": "market_commentary", "tag_category": "topic", "description": "Market analysis and commentary"},
        {"tag_name": "financial_planning", "tag_category": "topic", "description": "General financial planning"},
        
        # Tone tags
        {"tag_name": "educational", "tag_category": "tone", "description": "Educational content tone"},
        {"tag_name": "professional", "tag_category": "tone", "description": "Professional business tone"},
        {"tag_name": "conversational", "tag_category": "tone", "description": "Friendly conversational tone"},
        {"tag_name": "urgent", "tag_category": "tone", "description": "Time-sensitive messaging"},
        
        # Demographic tags
        {"tag_name": "millennials", "tag_category": "demographic", "description": "Content for millennials"},
        {"tag_name": "gen_x", "tag_category": "demographic", "description": "Content for Gen X"},
        {"tag_name": "baby_boomers", "tag_category": "demographic", "description": "Content for baby boomers"},
        {"tag_name": "high_net_worth", "tag_category": "demographic", "description": "HNW individuals"},
        {"tag_name": "business_owners", "tag_category": "demographic", "description": "Business owner focus"},
    ]
    
    for tag_data in tags_data:
        tag = ContentTags(**tag_data)
        session.add(tag)
        
    await session.flush()
    logger.info(f"✅ Created {len(tags_data)} content tags")


async def seed_compliance_rules(session: AsyncSession):
    """Seed compliance rules and regulations"""
    logger.info("📋 Seeding compliance rules...")
    
    rules_data = [
        {
            "regulation_name": "SEC Marketing Rule",
            "rule_section": "206(4)-1",
            "requirement_text": "All advertisements must include fair and balanced presentation of risks and benefits. Performance claims must be substantiated.",
            "applies_to_content_types": json.dumps(["WEBSITE_BLOG", "NEWSLETTER", "EMAIL_TEMPLATE"]),
            "applicability_scope": "all_advisors",
            "prohibition_type": "performance_claims",
            "required_disclaimers": "Past performance is not indicative of future results. All investments involve risk.",
            "effective_date": datetime(2021, 5, 4)
        },
        {
            "regulation_name": "FINRA Rule 2210",
            "rule_section": "2210(d)(1)",
            "requirement_text": "Communications must be fair, balanced, and not misleading. Must provide sound basis for evaluating facts.",
            "applies_to_content_types": json.dumps(["LINKEDIN_POST", "FACEBOOK_POST", "X_POST"]),
            "applicability_scope": "broker_dealers",
            "prohibition_type": "misleading_statements",
            "required_disclaimers": "Securities offered through [Broker-Dealer Name], Member FINRA/SIPC.",
            "effective_date": datetime(2013, 2, 4)
        },
        {
            "regulation_name": "Investment Company Act",
            "rule_section": "Section 34(b)",
            "requirement_text": "Prohibits materially misleading sales literature for investment company securities.",
            "applies_to_content_types": json.dumps(["DIRECT_MAILING", "EMAIL_TEMPLATE"]),
            "applicability_scope": "mutual_fund_advisors",
            "prohibition_type": "misleading_statements",
            "required_disclaimers": "Please consider the investment objectives, risks, charges and expenses carefully before investing.",
            "effective_date": datetime(1940, 8, 22)
        },
        {
            "regulation_name": "SEC Testimonial Rule",
            "rule_section": "206(4)-1(a)(1)",
            "requirement_text": "Testimonials and endorsements must include specific disclosures about compensation and conflicts.",
            "applies_to_content_types": json.dumps(["WEBSITE_BLOG", "YOUTUBE_VIDEO", "WEBSITE_COPY"]),
            "applicability_scope": "all_advisors",
            "prohibition_type": "testimonials",
            "required_disclaimers": "This testimonial was provided by a current client. No compensation was provided.",
            "effective_date": datetime(2021, 5, 4)
        }
    ]
    
    for rule_data in rules_data:
        rule = ComplianceRules(**rule_data)
        session.add(rule)
        
    await session.flush()
    logger.info(f"✅ Created {len(rules_data)} compliance rules")


async def seed_marketing_content(session: AsyncSession):
    """Seed approved marketing content examples"""
    logger.info("📝 Seeding marketing content...")
    
    content_data = [
        # LinkedIn Posts
        {
            "title": "Retirement Planning Reminder",
            "content_text": "Did you know that starting your retirement savings just 5 years earlier can potentially double your nest egg? Time and compound interest are your greatest allies in building wealth. Let's discuss how to optimize your retirement strategy. #RetirementPlanning #FinancialPlanning",
            "content_type": ContentType.LINKEDIN_POST,
            "audience_type": AudienceType.PROSPECT_ADVERTISING,
            "tone": "professional",
            "topic_focus": "retirement",
            "target_demographics": "millennials,gen_x",
            "approval_status": ApprovalStatus.APPROVED,
            "compliance_score": 0.95,
            "fiducia_approved_by": "compliance_team",
            "fiducia_approved_at": datetime.now() - timedelta(days=30),
            "source_type": SourceType.FIDUCIA_CREATED,
            "tags": "retirement_planning,educational,professional"
        },
        {
            "title": "Tax Season Preparation Tips",
            "content_text": "Tax season is approaching! Here are 3 ways to prepare:\n\n1. Organize your documents early\n2. Review last year's return for missed deductions\n3. Consider tax-loss harvesting strategies\n\nNeed help navigating tax-efficient investment strategies? Let's connect!",
            "content_type": ContentType.LINKEDIN_POST,
            "audience_type": AudienceType.GENERAL_EDUCATION,
            "tone": "educational",
            "topic_focus": "tax",
            "target_demographics": "business_owners,high_net_worth",
            "approval_status": ApprovalStatus.APPROVED,
            "compliance_score": 0.92,
            "fiducia_approved_by": "compliance_team",
            "fiducia_approved_at": datetime.now() - timedelta(days=25),
            "source_type": SourceType.FIDUCIA_CREATED,
            "tags": "tax_planning,educational"
        },
        
        # Email Templates
        {
            "title": "Monthly Market Update Email",
            "content_text": "Subject: Your Monthly Market Update - [Month Year]\n\nDear [Client Name],\n\nI hope this message finds you well. As we review the market's performance this month, here are the key highlights:\n\n• S&P 500: [Performance]%\n• Bond Market: [Performance]%\n• International Markets: [Performance]%\n\nWhat this means for your portfolio:\n[Personalized insight based on client's strategy]\n\nI'm always here to discuss any questions or concerns you may have about your investment strategy.\n\nBest regards,\n[Advisor Name]\n\nImportant Disclosure: Past performance is not indicative of future results. All investments involve risk, including potential loss of principal.",
            "content_type": ContentType.EMAIL_TEMPLATE,
            "audience_type": AudienceType.CLIENT_COMMUNICATION,
            "tone": "professional",
            "topic_focus": "market_commentary",
            "target_demographics": "all_clients",
            "approval_status": ApprovalStatus.APPROVED,
            "compliance_score": 0.98,
            "fiducia_approved_by": "compliance_team",
            "fiducia_approved_at": datetime.now() - timedelta(days=20),
            "source_type": SourceType.FIDUCIA_CREATED,
            "tags": "market_commentary,professional"
        },
        
        # Blog Posts
        {
            "title": "Understanding Dollar-Cost Averaging",
            "content_text": "Dollar-cost averaging (DCA) is an investment strategy that can help reduce the impact of market volatility...\n\n[Full blog content would be here]\n\nKey Benefits:\n• Reduces timing risk\n• Builds disciplined investing habits\n• Smooths out market volatility\n\nRemember: This strategy works best as part of a long-term investment plan.\n\nDisclosure: This is for educational purposes only and not personalized investment advice.",
            "content_type": ContentType.WEBSITE_BLOG,
            "audience_type": AudienceType.GENERAL_EDUCATION,
            "tone": "educational",
            "topic_focus": "investment_basics",
            "target_demographics": "millennials,gen_x",
            "approval_status": ApprovalStatus.APPROVED,
            "compliance_score": 0.94,
            "fiducia_approved_by": "compliance_team",
            "fiducia_approved_at": datetime.now() - timedelta(days=15),
            "source_type": SourceType.FIDUCIA_CREATED,
            "tags": "investment_basics,educational"
        }
    ]
    
    for content in content_data:
        marketing_content = MarketingContent(**content)
        session.add(marketing_content)
        
    await session.flush()
    logger.info(f"✅ Created {len(content_data)} marketing content pieces")


async def seed_advisor_sessions(session: AsyncSession):
    """Seed advisor chat sessions with Warren"""
    logger.info("💬 Seeding advisor sessions and messages...")
    
    sessions_data = [
        {
            "advisor_id": "demo_advisor_001",
            "session_id": "session_001_retirement",
            "title": "Retirement Planning Content for Baby Boomers",
            "message_count": 6
        },
        {
            "advisor_id": "demo_advisor_001",
            "session_id": "session_002_tax",
            "title": "Tax-Efficient Investment Strategies",
            "message_count": 4
        },
        {
            "advisor_id": "demo_advisor_002",
            "session_id": "session_003_market",
            "title": "Q4 Market Commentary",
            "message_count": 5
        }
    ]
    
    for session_data in sessions_data:
        session_obj = AdvisorSessions(**session_data)
        session.add(session_obj)
        
    await session.flush()
    
    # Add sample messages for first session
    messages = [
        {
            "session_id": "session_001_retirement",
            "message_type": "user",
            "content": "I need to create a LinkedIn post about retirement planning for baby boomers"
        },
        {
            "session_id": "session_001_retirement",
            "message_type": "warren",
            "content": "I'll help you create a LinkedIn post about retirement planning for baby boomers. To ensure the content is compliant and relevant, I need to understand a few things:\n\n1. What specific aspect of retirement planning would you like to focus on?\n2. Are you targeting prospects or existing clients?\n3. What tone would you prefer - educational, motivational, or informative?",
            "sources_used": json.dumps(["compliance_rules", "marketing_examples"]),
            "generation_confidence": 0.95,
            "search_strategy": "vector",
            "total_sources": 5,
            "marketing_examples": 3,
            "compliance_rules": 2
        },
        {
            "session_id": "session_001_retirement",
            "message_type": "user",
            "content": "Focus on the importance of catch-up contributions for those over 50. This is for prospects, and I'd like an educational tone."
        },
        {
            "session_id": "session_001_retirement",
            "message_type": "warren",
            "content": "Here's a compliant LinkedIn post about catch-up contributions for baby boomers:\n\n---\n\n📊 Are you 50 or older? You have a powerful retirement planning tool at your disposal: catch-up contributions.\n\nIn 2024, you can contribute an extra:\n• $7,500 to your 401(k) (total: $30,500)\n• $1,000 to your IRA (total: $8,000)\n\nWhy this matters: Starting at 50, these additional contributions could potentially add $200,000+ to your retirement savings by age 65, assuming average market returns.\n\nThe key? Taking action today. Every year you wait is a missed opportunity for tax-advantaged growth.\n\nWant to explore how catch-up contributions fit into your retirement strategy? Let's have a conversation.\n\n#RetirementPlanning #FinancialPlanning #CatchUpContributions\n\n*This is for educational purposes only. Consult with a financial advisor for personalized advice.*",
            "sources_used": json.dumps(["marketing_content_001", "compliance_rule_001"]),
            "generation_confidence": 0.98,
            "search_strategy": "vector",
            "total_sources": 8,
            "marketing_examples": 5,
            "compliance_rules": 3
        }
    ]
    
    for msg_data in messages:
        message = AdvisorMessages(**msg_data)
        session.add(message)
        
    await session.flush()
    logger.info(f"✅ Created {len(sessions_data)} advisor sessions with messages")


async def seed_advisor_content(session: AsyncSession):
    """Seed advisor-created content in various approval states"""
    logger.info("📄 Seeding advisor content...")
    
    content_data = [
        {
            "title": "Why Diversification Matters More Than Ever",
            "content_text": "In today's volatile market, diversification isn't just smart—it's essential...",
            "content_type": "linkedin_post",
            "audience_type": "prospect_advertising",
            "intended_channels": json.dumps(["linkedin"]),
            "advisor_id": "demo_advisor_001",
            "source_session_id": "session_001_retirement",
            "status": "approved",
            "cco_review_status": "approved",
            "cco_email": "john.cco@firmcompliance.com",
            "submitted_for_review_at": datetime.now() - timedelta(days=3),
            "advisor_notes": "Created for Q4 prospect outreach campaign"
        },
        {
            "title": "Year-End Tax Planning Checklist",
            "content_text": "As we approach year-end, here are 5 tax-planning strategies to consider...",
            "content_type": "email_template",
            "audience_type": "client_communication",
            "intended_channels": json.dumps(["email"]),
            "advisor_id": "demo_advisor_001",
            "status": "submitted",
            "cco_review_status": "in_review",
            "cco_email": "john.cco@firmcompliance.com",
            "submitted_for_review_at": datetime.now() - timedelta(hours=6),
            "review_deadline": datetime.now() + timedelta(days=1),
            "review_priority": "high",
            "advisor_notes": "Urgent - need to send by end of week"
        },
        {
            "title": "Market Volatility: Stay the Course",
            "content_text": "When markets get rocky, it's natural to feel concerned about your investments...",
            "content_type": "website_blog",
            "audience_type": "general_education",
            "intended_channels": json.dumps(["website", "newsletter"]),
            "advisor_id": "demo_advisor_002",
            "status": "needs_revision",
            "cco_review_status": "revision_requested",
            "cco_email": "sarah.compliance@wealthadvisors.com",
            "submitted_for_review_at": datetime.now() - timedelta(days=2),
            "advisor_notes": "Educational piece for nervous clients"
        },
        {
            "title": "Social Security Optimization Strategies",
            "content_text": "Understanding when and how to claim Social Security can significantly impact your retirement income...",
            "content_type": "newsletter",
            "audience_type": "existing_clients",
            "intended_channels": json.dumps(["email", "website"]),
            "advisor_id": "demo_advisor_001",
            "status": "draft",
            "cco_review_status": "not_submitted",
            "advisor_notes": "Work in progress - need to add more examples"
        }
    ]
    
    for content in content_data:
        advisor_content = AdvisorContent(**content)
        session.add(advisor_content)
        
    await session.flush()
    logger.info(f"✅ Created {len(content_data)} advisor content pieces")


async def seed_compliance_ccos(session: AsyncSession):
    """Seed CCO accounts for compliance review"""
    logger.info("👮 Seeding compliance CCO accounts...")
    
    ccos_data = [
        {
            "email": "john.cco@firmcompliance.com",
            "subscription_type": SubscriptionType.FULL,
            "subscription_status": SubscriptionStatus.ACTIVE,
            "seats_purchased": 5,
            "seats_used": 2,
            "company_name": "Firm Compliance Services LLC",
            "billing_email": "billing@firmcompliance.com",
            "phone": "555-0100",
            "last_login_at": datetime.now() - timedelta(hours=2)
        },
        {
            "email": "sarah.compliance@wealthadvisors.com",
            "subscription_type": SubscriptionType.LITE,
            "subscription_status": SubscriptionStatus.ACTIVE,
            "company_name": "Wealth Advisors Inc",
            "last_login_at": datetime.now() - timedelta(days=1)
        },
        {
            "email": "trial.cco@testfirm.com",
            "subscription_type": SubscriptionType.FULL,
            "subscription_status": SubscriptionStatus.TRIAL,
            "seats_purchased": 3,
            "seats_used": 1,
            "trial_ends_at": datetime.now() + timedelta(days=14),
            "company_name": "Test Advisory Firm"
        }
    ]
    
    for cco_data in ccos_data:
        cco = ComplianceCCO(**cco_data)
        session.add(cco)
        
    await session.flush()
    
    # Add team members for full CCO account
    result = await session.execute(
        select(ComplianceCCO).where(ComplianceCCO.email == "john.cco@firmcompliance.com")
    )
    full_cco = result.scalar_one_or_none()
    
    if full_cco:
        team_members = [
            {
                "cco_id": full_cco.id,
                "email": "mary.reviewer@firmcompliance.com",
                "name": "Mary Reviewer",
                "role": TeamMemberRole.REVIEWER,
                "status": TeamMemberStatus.ACTIVE,
                "joined_at": datetime.now() - timedelta(days=30),
                "last_login_at": datetime.now() - timedelta(days=1)
            },
            {
                "cco_id": full_cco.id,
                "email": "tom.analyst@firmcompliance.com",
                "name": "Tom Analyst",
                "role": TeamMemberRole.VIEWER,
                "status": TeamMemberStatus.ACTIVE,
                "joined_at": datetime.now() - timedelta(days=20)
            }
        ]
        
        for member_data in team_members:
            member = CCOTeamMember(**member_data)
            session.add(member)
            
    await session.flush()
    logger.info(f"✅ Created {len(ccos_data)} CCO accounts with team members")


async def seed_content_reviews(session: AsyncSession):
    """Seed content review workflow data"""
    logger.info("📋 Seeding content reviews...")
    
    # Get advisor content IDs that need reviews
    result = await session.execute(
        select(AdvisorContent).where(
            AdvisorContent.cco_review_status.in_(["approved", "in_review", "revision_requested"])
        )
    )
    content_to_review = result.scalars().all()
    
    for content in content_to_review:
        # Create review record
        review_data = {
            "content_id": content.id,
            "cco_email": content.cco_email,
            "review_token": f"review_token_{content.id}_{random.randint(1000, 9999)}",
            "notification_sent_at": content.submitted_for_review_at
        }
        
        # Set review status based on content status
        if content.cco_review_status == "approved":
            review_data.update({
                "status": ReviewStatus.APPROVED,
                "decision": "approved",
                "overall_feedback": "Content looks good. All compliance requirements met.",
                "compliance_score": random.randint(85, 98),
                "review_started_at": content.submitted_for_review_at + timedelta(hours=1),
                "reviewed_at": content.submitted_for_review_at + timedelta(hours=2)
            })
        elif content.cco_review_status == "in_review":
            review_data.update({
                "status": ReviewStatus.IN_PROGRESS,
                "review_started_at": datetime.now() - timedelta(hours=1)
            })
        elif content.cco_review_status == "revision_requested":
            review_data.update({
                "status": ReviewStatus.REJECTED,
                "decision": "rejected",
                "overall_feedback": "Content needs revisions to meet compliance standards.",
                "compliance_score": random.randint(50, 70),
                "review_started_at": content.submitted_for_review_at + timedelta(minutes=30),
                "reviewed_at": content.submitted_for_review_at + timedelta(hours=1)
            })
        
        review = ContentReview(**review_data)
        session.add(review)
        await session.flush()
        
        # Add feedback items for rejected content
        if content.cco_review_status == "revision_requested":
            feedback_items = [
                {
                    "review_id": review.id,
                    "section_text": "guaranteed returns",
                    "section_start_pos": 50,
                    "section_end_pos": 68,
                    "violation_type": ViolationType.PERFORMANCE_GUARANTEE,
                    "comment": "Cannot use language that guarantees investment returns",
                    "suggested_fix": "Consider using 'potential returns' or 'historical returns'",
                    "regulation_reference": "SEC Marketing Rule 206(4)-1"
                },
                {
                    "review_id": review.id,
                    "violation_type": ViolationType.OMITTED_DISCLOSURE,
                    "comment": "Missing required risk disclosure for investment content",
                    "suggested_fix": "Add: 'All investments involve risk, including potential loss of principal.'",
                    "regulation_reference": "FINRA Rule 2210(d)(1)"
                }
            ]
            
            for feedback_data in feedback_items:
                feedback = ReviewFeedback(**feedback_data)
                session.add(feedback)
    
    await session.flush()
    logger.info(f"✅ Created {len(content_to_review)} content reviews with feedback")


async def seed_advisor_contacts(session: AsyncSession):
    """Seed advisor CRM contacts"""
    logger.info("👥 Seeding advisor contacts...")
    
    contacts_data = [
        # Prospects
        {
            "advisor_id": "demo_advisor_001",
            "first_name": "Robert",
            "last_name": "Johnson",
            "email": "rjohnson@techcorp.com",
            "phone": "555-0101",
            "company": "TechCorp Industries",
            "title": "CEO",
            "status": "prospect",
            "notes": "Met at industry conference. Interested in retirement planning."
        },
        {
            "advisor_id": "demo_advisor_001",
            "first_name": "Sarah",
            "last_name": "Williams",
            "email": "swilliams@email.com",
            "phone": "555-0102",
            "company": "Williams & Associates",
            "title": "Partner",
            "status": "prospect",
            "notes": "Referral from existing client. High net worth individual."
        },
        {
            "advisor_id": "demo_advisor_001",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "mchen@hospital.org",
            "phone": "555-0103",
            "company": "City General Hospital",
            "title": "Chief of Surgery",
            "status": "prospect",
            "notes": "Doctor referral network. Needs tax planning advice."
        },
        
        # Clients
        {
            "advisor_id": "demo_advisor_001",
            "first_name": "Jennifer",
            "last_name": "Davis",
            "email": "jdavis@email.com",
            "phone": "555-0201",
            "company": "Davis Consulting",
            "title": "Owner",
            "status": "client",
            "notes": "Client since 2020. Focus on business succession planning."
        },
        {
            "advisor_id": "demo_advisor_001",
            "first_name": "Thomas",
            "last_name": "Anderson",
            "email": "tanderson@lawfirm.com",
            "phone": "555-0202",
            "company": "Anderson Law Group",
            "title": "Senior Partner",
            "status": "client",
            "notes": "Long-term client. Estate planning and tax optimization."
        }
    ]
    
    for contact_data in contacts_data:
        contact = AdvisorContact(**contact_data)
        session.add(contact)
        
    await session.flush()
    logger.info(f"✅ Created {len(contacts_data)} advisor contacts")


async def seed_advisor_audiences(session: AsyncSession):
    """Seed advisor audience groups with simplified relationship handling"""
    logger.info("🎯 Seeding advisor audiences...")
    
    # Create audiences first
    audiences_data = [
        {
            "advisor_id": "demo_advisor_001",
            "name": "Medical Professionals",
            "description": "Doctors, surgeons, and healthcare executives",
            "occupation": "Healthcare professionals",
            "relationship_type": "Professional network",
            "characteristics": "High income earners, busy schedules, need tax-efficient strategies, interested in retirement planning and asset protection",
            "contact_count": 1
        },
        {
            "advisor_id": "demo_advisor_001",
            "name": "Business Owners",
            "description": "Small to medium business owners",
            "occupation": "Entrepreneurs and business owners",
            "relationship_type": "Professional network",
            "characteristics": "Need succession planning, tax strategies, retirement plans for employees, cash flow management",
            "contact_count": 2
        },
        {
            "advisor_id": "demo_advisor_001",
            "name": "Tech Executives",
            "description": "Technology company executives and employees",
            "occupation": "Technology professionals",
            "relationship_type": "Industry contacts",
            "characteristics": "Stock options, RSUs, high income, younger demographic, interested in aggressive growth strategies",
            "contact_count": 1
        }
    ]
    
    for audience_data in audiences_data:
        audience = AdvisorAudience(**audience_data)
        session.add(audience)
        
    await session.flush()
    logger.info(f"✅ Created {len(audiences_data)} advisor audiences")
    
    # Note: In a real implementation, we would properly assign contacts to audiences
    # For now, we've set contact_count manually to avoid async relationship issues


async def seed_warren_interactions(session: AsyncSession):
    """Seed Warren AI interaction history"""
    logger.info("🤖 Seeding Warren interactions...")
    
    interactions_data = [
        {
            "user_id": "demo_advisor_001",
            "session_id": "session_001_retirement",
            "user_request": "Create a LinkedIn post about catch-up contributions for baby boomers",
            "requested_content_type": ContentType.LINKEDIN_POST,
            "requested_audience": AudienceType.PROSPECT_ADVERTISING,
            "generated_content": "📊 Are you 50 or older? You have a powerful retirement planning tool...",
            "content_sources_used": json.dumps(["marketing_content_001", "compliance_rule_001"]),
            "generation_confidence": 0.98,
            "user_approved": True,
            "user_feedback_score": 5,
            "user_feedback_notes": "Perfect! Exactly what I needed."
        },
        {
            "user_id": "demo_advisor_001",
            "session_id": "session_002_tax",
            "user_request": "Help me write an email about year-end tax planning strategies",
            "requested_content_type": ContentType.EMAIL_TEMPLATE,
            "requested_audience": AudienceType.CLIENT_COMMUNICATION,
            "generated_content": "Subject: Important Year-End Tax Planning Strategies...",
            "content_sources_used": json.dumps(["marketing_content_002", "compliance_rule_002"]),
            "generation_confidence": 0.95,
            "user_approved": True,
            "user_modified_content": "Subject: Your Year-End Tax Planning Checklist...",
            "user_feedback_score": 4,
            "user_feedback_notes": "Good content, I just tweaked the subject line"
        }
    ]
    
    for interaction_data in interactions_data:
        interaction = WarrenInteractions(**interaction_data)
        session.add(interaction)
        
    await session.flush()
    logger.info(f"✅ Created {len(interactions_data)} Warren interactions")


async def seed_content_distribution(session: AsyncSession):
    """Seed content distribution records"""
    logger.info("📤 Seeding content distribution...")
    
    # Get approved content
    result = await session.execute(
        select(AdvisorContent).where(AdvisorContent.status == "approved")
    )
    approved_content = result.scalars().all()
    
    for content in approved_content:
        channels = json.loads(content.intended_channels) if content.intended_channels else ["linkedin"]
        
        for channel in channels:
            distribution = ContentDistribution(
                content_id=content.id,
                channel=channel,
                distributed_at=datetime.now() - timedelta(days=random.randint(1, 7)),
                distribution_notes=f"Posted to {channel} as scheduled",
                advisor_id=content.advisor_id,
                views=random.randint(50, 500),
                engagement_score=random.uniform(0.02, 0.15)
            )
            session.add(distribution)
    
    await session.flush()
    logger.info(f"✅ Created distribution records for approved content")


async def print_seeding_summary(session: AsyncSession):
    """Print summary of seeded data"""
    logger.info("\n📊 DATABASE SEEDING SUMMARY")
    logger.info("=" * 50)
    
    # Count records in each table
    tables_to_count = [
        ("Content Tags", ContentTags),
        ("Compliance Rules", ComplianceRules),
        ("Marketing Content", MarketingContent),
        ("Advisor Sessions", AdvisorSessions),
        ("Advisor Messages", AdvisorMessages),
        ("Advisor Content", AdvisorContent),
        ("Compliance CCOs", ComplianceCCO),
        ("Content Reviews", ContentReview),
        ("Review Feedback", ReviewFeedback),
        ("Advisor Contacts", AdvisorContact),
        ("Advisor Audiences", AdvisorAudience),
        ("Warren Interactions", WarrenInteractions),
        ("Content Distribution", ContentDistribution)
    ]
    
    for table_name, model_class in tables_to_count:
        result = await session.execute(select(model_class))
        count = len(result.scalars().all())
        logger.info(f"✅ {table_name}: {count} records")
    
    logger.info("=" * 50)
    logger.info("\n🎯 DEMO ACCOUNTS CREATED:")
    logger.info("Advisor Login: demo_advisor_001")
    logger.info("CCO Full Account: john.cco@firmcompliance.com")
    logger.info("CCO Lite Account: sarah.compliance@wealthadvisors.com")
    logger.info("\n💡 TIP: Use these accounts to test different workflows!")


if __name__ == "__main__":
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the seeding
    asyncio.run(seed_database())
