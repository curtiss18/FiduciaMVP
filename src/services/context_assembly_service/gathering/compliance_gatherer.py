"""Compliance sources gathering service"""

import logging
from typing import List, Optional, Dict, Any

from ..interfaces import ContextGatheringStrategy
from ..models import ContextType, ContextElement

logger = logging.getLogger(__name__)


class ComplianceGatherer(ContextGatheringStrategy):
    
    def __init__(self):
        pass
    
    async def gather_context(
        self, 
        session_id: str = None,
        db_session=None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> List[ContextElement]:
        
        elements = []
        
        if not context_data:
            return elements
        
        try:
            compliance_content = self._extract_compliance_sources(context_data)
            
            if compliance_content:
                element = ContextElement(
                    content=compliance_content,
                    context_type=ContextType.COMPLIANCE_SOURCES,
                    priority_score=9.0,  # Very high priority for compliance
                    relevance_score=1.0,  # Always relevant for compliance
                    token_count=len(compliance_content) // 4,  # Rough estimation
                    source_metadata={"source": "compliance_rules_and_disclaimers"}
                )
                elements.append(element)
                
        except Exception as e:
            logger.warning(f"Could not extract compliance sources: {e}")
        
        return elements
    
    def _extract_compliance_sources(self, context_data: Dict) -> str:
        """Extract and format compliance sources from context data."""
        compliance_parts = []
        
        # Rules
        rules = context_data.get("rules", [])
        valid_rules = []
        for rule in rules[:3]:  # Limit to most relevant
            title = rule.get('title') or 'Rule'
            content = rule.get('content_text') or ''
            if content:
                valid_rules.append(f"**{title}**: {content[:200]}...")
        
        if valid_rules:
            compliance_parts.append("## COMPLIANCE RULES:")
            compliance_parts.extend(valid_rules)
        
        # Disclaimers
        disclaimers = context_data.get("disclaimers", [])
        valid_disclaimers = []
        for disclaimer in disclaimers[:2]:
            title = disclaimer.get('title') or 'Disclaimer'
            content = disclaimer.get('content_text') or ''
            if content:
                valid_disclaimers.append(f"**{title}**: {content[:200]}...")
        
        if valid_disclaimers:
            compliance_parts.append("\n## REQUIRED DISCLAIMERS:")
            compliance_parts.extend(valid_disclaimers)
        
        return "\n".join(compliance_parts)
    
    def get_supported_context_types(self) -> List[ContextType]:
        return [ContextType.COMPLIANCE_SOURCES]
