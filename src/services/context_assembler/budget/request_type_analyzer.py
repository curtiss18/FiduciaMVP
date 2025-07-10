"""Request Type Analysis Service"""

import logging
from typing import Optional, Dict, Any

from ..interfaces import RequestAnalysisStrategy
from ..models import RequestType

logger = logging.getLogger(__name__)


class RequestTypeAnalyzer(RequestAnalysisStrategy):
    
    def __init__(self):
        self.refinement_keywords = [
            'edit', 'change', 'modify', 'update', 'revise', 'improve', 'make it', 'adjust'
        ]
        self.analysis_keywords = [
            'analyze', 'review', 'compare', 'evaluate', 'assess', 'what do you think'
        ]
        self.creation_keywords = [
            'create', 'write', 'generate', 'draft', 'compose', 'help me with'
        ]
    
    def analyze_request_type(self, user_input: str, current_content: Optional[str] = None) -> RequestType:
        if not user_input:
            return RequestType.CONVERSATION
            
        user_input_lower = user_input.lower()
        
        # Check for refinement indicators
        if current_content or any(keyword in user_input_lower for keyword in self.refinement_keywords):
            return RequestType.REFINEMENT
        
        # Check for analysis requests
        if any(keyword in user_input_lower for keyword in self.analysis_keywords):
            return RequestType.ANALYSIS
        
        # Check for creation requests
        if any(keyword in user_input_lower for keyword in self.creation_keywords):
            return RequestType.CREATION
        
        # Default to conversation mode
        return RequestType.CONVERSATION
    
    def extract_requirements(self, user_input: str) -> Dict[str, Any]:
        """Extract additional requirements from user input."""
        if not user_input:
            return {}
            
        requirements = {
            'request_type': self.analyze_request_type(user_input),
            'input_length': len(user_input),
            'has_keywords': {
                'refinement': any(keyword in user_input.lower() for keyword in self.refinement_keywords),
                'analysis': any(keyword in user_input.lower() for keyword in self.analysis_keywords),
                'creation': any(keyword in user_input.lower() for keyword in self.creation_keywords)
            }
        }
        
        return requirements
