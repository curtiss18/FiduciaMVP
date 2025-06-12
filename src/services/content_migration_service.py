# Migration Service to Break Up Existing Documents into Individual Content Pieces

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from src.models.refactored_database import (
    MarketingContent, ComplianceRules, ContentType, 
    AudienceType, SourceType, ApprovalStatus
)
from src.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class ContentMigrationService:
    """Service to migrate existing knowledge base into granular content pieces"""
    
    def __init__(self):
        self.knowledge_base_path = Path("data/knowledge_base")
    
    async def migrate_linkedin_examples(self, db: AsyncSession) -> List[MarketingContent]:
        """Extract individual LinkedIn posts from the examples file"""
        file_path = self.knowledge_base_path / "approved_examples" / "LinkedIn_Marketing_Examples.md"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse individual examples
            examples = self._parse_linkedin_examples(content)
            content_pieces = []
            
            for i, example in enumerate(examples):
                content_piece = MarketingContent(
                    title=f"LinkedIn Example {i+1}: {example['title']}",
                    content_text=example['content'],
                    content_type=ContentType.LINKEDIN_POST,
                    audience_type=example['audience_type'],
                    tone=example['tone'],
                    topic_focus=example['topic'],
                    approval_status=ApprovalStatus.APPROVED,
                    compliance_score=1.0,
                    fiducia_approved_by="fiducia_content_team",
                    fiducia_approved_at=datetime.utcnow(),
                    source_type=SourceType.FIDUCIA_CREATED,
                    original_source=str(file_path),
                    tags=example['tags'],
                    created_at=datetime.utcnow()
                )
                
                db.add(content_piece)
                content_pieces.append(content_piece)
            
            await db.commit()
            logger.info(f"Migrated {len(content_pieces)} LinkedIn examples")
            return content_pieces
            
        except Exception as e:
            logger.error(f"Error migrating LinkedIn examples: {str(e)}")
            await db.rollback()
            return []
    
    def _parse_linkedin_examples(self, content: str) -> List[Dict[str, Any]]:
        """Parse individual LinkedIn examples from the markdown file"""
        examples = []
        
        # Split by example headers
        sections = content.split("## Example")
        
        for section in sections[1:]:  # Skip the header section
            lines = section.split('\n')
            
            # Extract title (first line after "Example X:")
            title_line = lines[0] if lines else ""
            title = title_line.split(': ', 1)[1] if ': ' in title_line else "LinkedIn Post"
            
            # Find content section
            content_text = ""
            in_content = False
            for line in lines:
                if line.strip().startswith('```') and not in_content:
                    in_content = True
                    continue
                elif line.strip().startswith('```') and in_content:
                    break
                elif in_content:
                    content_text += line + '\n'
            
            # Determine audience type and topic from title/content
            audience_type = AudienceType.GENERAL_EDUCATION
            if "client" in title.lower():
                audience_type = AudienceType.CLIENT_COMMUNICATION
            elif "market" in title.lower() or "commentary" in title.lower():
                audience_type = AudienceType.GENERAL_EDUCATION
            
            # Extract topic
            topic = "general"
            if "retirement" in title.lower() or "retirement" in content_text.lower():
                topic = "retirement_planning"
            elif "market" in title.lower():
                topic = "market_commentary"
            elif "economic" in title.lower():
                topic = "economic_analysis"
            elif "holiday" in title.lower():
                topic = "seasonal_planning"
            
            # Determine tone
            tone = "educational"
            if "update" in title.lower():
                tone = "informational"
            elif "tip" in title.lower():
                tone = "helpful"
            
            examples.append({
                'title': title,
                'content': content_text.strip(),
                'audience_type': audience_type,
                'topic': topic,
                'tone': tone,
                'tags': f"linkedin,{topic},approved_example"
            })
        
        return examples
    
    async def migrate_disclaimer_templates(self, db: AsyncSession) -> List[MarketingContent]:
        """Extract individual disclaimer templates"""
        file_path = self.knowledge_base_path / "disclaimers" / "Compliance_Disclaimer_Templates.md"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            disclaimers = self._parse_disclaimer_templates(content)
            content_pieces = []
            
            for disclaimer in disclaimers:
                content_piece = MarketingContent(
                    title=disclaimer['title'],
                    content_text=disclaimer['content'],
                    content_type=ContentType.EMAIL_TEMPLATE,  # Generic template type
                    audience_type=AudienceType.GENERAL_EDUCATION,
                    tone="legal",
                    topic_focus="compliance",
                    approval_status=ApprovalStatus.APPROVED,
                    compliance_score=1.0,
                    fiducia_approved_by="fiducia_compliance_team",
                    fiducia_approved_at=datetime.utcnow(),
                    source_type=SourceType.FIDUCIA_CREATED,
                    original_source=str(file_path),
                    tags=disclaimer['tags'],
                    created_at=datetime.utcnow()
                )
                
                db.add(content_piece)
                content_pieces.append(content_piece)
            
            await db.commit()
            logger.info(f"Migrated {len(content_pieces)} disclaimer templates")
            return content_pieces
            
        except Exception as e:
            logger.error(f"Error migrating disclaimers: {str(e)}")
            await db.rollback()
            return []
    
    def _parse_disclaimer_templates(self, content: str) -> List[Dict[str, Any]]:
        """Parse individual disclaimer templates"""
        disclaimers = []
        
        # Find all disclaimer sections
        lines = content.split('\n')
        current_disclaimer = None
        in_code_block = False
        
        for line in lines:
            if line.startswith('### ') and 'Disclaimer' in line:
                if current_disclaimer:
                    disclaimers.append(current_disclaimer)
                
                title = line.replace('### ', '').strip()
                current_disclaimer = {
                    'title': title,
                    'content': '',
                    'tags': 'disclaimer,compliance,template'
                }
            elif line.strip().startswith('```') and current_disclaimer:
                in_code_block = not in_code_block
                if not in_code_block and current_disclaimer['content']:
                    # End of disclaimer content
                    continue
            elif in_code_block and current_disclaimer:
                current_disclaimer['content'] += line + '\n'
        
        # Add the last disclaimer
        if current_disclaimer:
            disclaimers.append(current_disclaimer)
        
        return disclaimers
    
    async def migrate_compliance_rules(self, db: AsyncSession) -> List[ComplianceRules]:
        """Extract compliance rules from SEC and FINRA documents"""
        rules = []
        
        # Migrate SEC Marketing Rule
        sec_file = self.knowledge_base_path / "regulations" / "SEC_Marketing_Rule_206-4-1.md"
        if sec_file.exists():
            sec_rules = await self._extract_sec_rules(sec_file, db)
            rules.extend(sec_rules)
        
        # Migrate FINRA Rule 2210
        finra_file = self.knowledge_base_path / "regulations" / "FINRA_Rule_2210_Communications.md"
        if finra_file.exists():
            finra_rules = await self._extract_finra_rules(finra_file, db)
            rules.extend(finra_rules)
        
        await db.commit()
        logger.info(f"Migrated {len(rules)} compliance rules")
        return rules
    
    async def _extract_sec_rules(self, file_path: Path, db: AsyncSession) -> List[ComplianceRules]:
        """Extract SEC rule sections"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = []
        
        # Extract the seven general prohibitions
        prohibitions = [
            ("Material Misstatements", "No untrue statements of material fact or omissions that make statements misleading"),
            ("Unsubstantiated Claims", "No material statements without reasonable basis for belief that they can be substantiated upon SEC demand"),
            ("SEC Implications", "Cannot imply SEC approval, sponsorship, or endorsement of the adviser"),
            ("Past Recommendations", "Cannot reference specific profitable recommendations unless presentation is fair and balanced"),
            ("Charts and Formulas", "Cannot reference investment analysis tools without explaining their limitations"),
            ("Free Services", "Cannot claim services are 'free' unless truly provided without cost or condition"),
            ("Misleading Claims", "Cannot include statements that are materially misleading about the adviser or its services")
        ]
        
        for i, (name, text) in enumerate(prohibitions):
            rule = ComplianceRules(
                regulation_name="SEC Marketing Rule",
                rule_section=f"206(4)-1 Prohibition {i+1}",
                requirement_text=text,
                applies_to_content_types="all",
                applicability_scope="sec_registered_advisors",
                prohibition_type="general_prohibition",
                effective_date=datetime(2021, 5, 4),
                source_url="https://www.sec.gov/rules/final/2020/ia-5653.pdf"
            )
            db.add(rule)
            rules.append(rule)
        
        return rules
    
    async def _extract_finra_rules(self, file_path: Path, db: AsyncSession) -> List[ComplianceRules]:
        """Extract FINRA rule requirements"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = []
        
        # Key FINRA requirements
        finra_requirements = [
            ("Fair and Balanced", "All communications must be fair and balanced, not misleading"),
            ("Principal Approval", "Retail communications must be approved by qualified registered principal"),
            ("Record Keeping", "Must maintain copies of all communications and approval records"),
            ("Filing Requirements", "Certain communications must be filed with FINRA before or after use"),
            ("Content Standards", "Must provide sound basis for evaluating facts and include material qualifications")
        ]
        
        for name, text in finra_requirements:
            rule = ComplianceRules(
                regulation_name="FINRA Rule 2210",
                rule_section="2210",
                requirement_text=text,
                applies_to_content_types="retail_communications",
                applicability_scope="finra_member_firms",
                prohibition_type="content_standard",
                source_url="https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210"
            )
            db.add(rule)
            rules.append(rule)
        
        return rules
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """Run complete migration of existing content"""
        async with AsyncSessionLocal() as db:
            try:
                results = {
                    "linkedin_examples": [],
                    "disclaimer_templates": [],
                    "compliance_rules": [],
                    "total_migrated": 0
                }
                
                # Migrate LinkedIn examples
                linkedin_content = await self.migrate_linkedin_examples(db)
                results["linkedin_examples"] = len(linkedin_content)
                
                # Migrate disclaimer templates
                disclaimer_content = await self.migrate_disclaimer_templates(db)
                results["disclaimer_templates"] = len(disclaimer_content)
                
                # Migrate compliance rules
                compliance_rules = await self.migrate_compliance_rules(db)
                results["compliance_rules"] = len(compliance_rules)
                
                results["total_migrated"] = (
                    results["linkedin_examples"] + 
                    results["disclaimer_templates"] + 
                    results["compliance_rules"]
                )
                
                return {
                    "status": "success",
                    "migration_results": results
                }
                
            except Exception as e:
                logger.error(f"Migration failed: {str(e)}")
                await db.rollback()
                return {
                    "status": "error",
                    "error": str(e)
                }

# Service instance
migration_service = ContentMigrationService()
