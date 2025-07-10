"""Unit tests for ComplianceGatherer"""

import pytest
from unittest.mock import AsyncMock

from src.services.context_assembler.gathering.compliance_gatherer import ComplianceGatherer
from src.services.context_assembler.models import ContextType


@pytest.mark.asyncio
async def test_compliance_gatherer_success():
    """Test successful compliance sources extraction"""
    gatherer = ComplianceGatherer()
    
    context_data = {
        "rules": [
            {"title": "SEC Rule 206", "content_text": "Investment advisors must comply with fiduciary duty requirements when providing advice to clients."},
            {"title": "FINRA Rule 2210", "content_text": "All communications must be fair and balanced and not misleading to investors."}
        ],
        "disclaimers": [
            {"title": "Risk Disclaimer", "content_text": "Past performance does not guarantee future results. All investments carry risk of loss."}
        ]
    }
    
    elements = await gatherer.gather_context(context_data=context_data)
    
    assert len(elements) == 1
    assert elements[0].context_type == ContextType.COMPLIANCE_SOURCES
    assert "## COMPLIANCE RULES:" in elements[0].content
    assert "SEC Rule 206" in elements[0].content
    assert "## REQUIRED DISCLAIMERS:" in elements[0].content
    assert "Risk Disclaimer" in elements[0].content
    assert elements[0].priority_score == 9.0
    assert elements[0].relevance_score == 1.0


@pytest.mark.asyncio
async def test_compliance_gatherer_rules_only():
    """Test extraction with only rules, no disclaimers"""
    gatherer = ComplianceGatherer()
    
    context_data = {
        "rules": [
            {"title": "SEC Rule 206", "content_text": "Investment advisors must comply with fiduciary duty requirements."}
        ]
    }
    
    elements = await gatherer.gather_context(context_data=context_data)
    
    assert len(elements) == 1
    assert "## COMPLIANCE RULES:" in elements[0].content
    assert "SEC Rule 206" in elements[0].content
    assert "## REQUIRED DISCLAIMERS:" not in elements[0].content


@pytest.mark.asyncio
async def test_compliance_gatherer_no_context_data():
    """Test when no context data provided"""
    gatherer = ComplianceGatherer()
    
    elements = await gatherer.gather_context(context_data=None)
    
    assert len(elements) == 0


@pytest.mark.asyncio
async def test_compliance_gatherer_empty_context_data():
    """Test when context data is empty"""
    gatherer = ComplianceGatherer()
    
    context_data = {}
    
    elements = await gatherer.gather_context(context_data=context_data)
    
    assert len(elements) == 0


@pytest.mark.asyncio
async def test_compliance_gatherer_error_handling():
    """Test error handling with malformed context data"""
    gatherer = ComplianceGatherer()
    
    # Malformed context data that could cause exceptions
    context_data = {
        "rules": [
            {"title": None, "content_text": None}  # None values
        ]
    }
    
    elements = await gatherer.gather_context(context_data=context_data)
    
    # Should handle gracefully and return empty list since no valid content
    assert len(elements) == 0


def test_supported_context_types():
    """Test supported context types"""
    gatherer = ComplianceGatherer()
    supported = gatherer.get_supported_context_types()
    
    assert supported == [ContextType.COMPLIANCE_SOURCES]
