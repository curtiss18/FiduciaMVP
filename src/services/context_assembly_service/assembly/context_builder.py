"""Context Builder Service - Final context assembly from ContextElements"""

import logging
from typing import List, Dict, Optional
from ..models import ContextElement, ContextType, FormattingOptions
from ..optimization.text_token_manager import TextTokenManager

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds final context string from ContextElements with proper formatting.
    
    Responsibilities:
    - Convert List[ContextElement] to formatted context string
    - Handle sectioning and proper ordering
    - Ensure readable output for Warren
    - Maintain token efficiency
    """
    
    def __init__(self, token_manager: Optional[TextTokenManager] = None):
        self.token_manager = token_manager or TextTokenManager()
        
        # Context type ordering for consistent assembly
        self.context_order = [
            ContextType.SYSTEM_PROMPT,
            ContextType.CURRENT_CONTENT,
            ContextType.DOCUMENT_SUMMARIES,
            ContextType.COMPLIANCE_SOURCES,
            ContextType.VECTOR_SEARCH_RESULTS,
            ContextType.YOUTUBE_CONTEXT,
            ContextType.CONVERSATION_HISTORY,
            ContextType.USER_INPUT
        ]
    
    def build_context_string(
        self, 
        context_elements: List[ContextElement],
        formatting_options: Optional[FormattingOptions] = None
    ) -> str:
        """
        Build final context string from context elements.
        
        Args:
            context_elements: List of context elements to assemble
            formatting_options: Optional formatting preferences
            
        Returns:
            Formatted context string ready for Warren
        """
        if not context_elements:
            logger.warning("No context elements provided for assembly")
            return ""
        
        try:
            # Group elements by context type
            grouped_elements = self._group_elements_by_type(context_elements)
            
            # Build sections in proper order
            context_sections = []
            
            for context_type in self.context_order:
                if context_type in grouped_elements:
                    section = self._build_context_section(
                        context_type, 
                        grouped_elements[context_type],
                        formatting_options
                    )
                    if section.strip():  # Only add non-empty sections
                        context_sections.append(section)
            
            # Join sections with proper separators
            final_context = self._join_context_sections(context_sections)
            
            # Log assembly results
            total_tokens = self.token_manager.count_tokens(final_context)
            logger.info(f"Context assembled: {len(context_elements)} elements, {total_tokens} tokens")
            
            return final_context
            
        except Exception as e:
            logger.error(f"Error building context string: {e}")
            return self._build_fallback_context(context_elements)
    
    def _group_elements_by_type(self, elements: List[ContextElement]) -> Dict[ContextType, List[ContextElement]]:
        """Group context elements by their type."""
        grouped = {}
        
        for element in elements:
            if element.context_type not in grouped:
                grouped[element.context_type] = []
            grouped[element.context_type].append(element)
        
        # Sort elements within each group by priority
        for context_type in grouped:
            grouped[context_type].sort(key=lambda x: x.effective_priority, reverse=True)
        
        return grouped
    
    def _build_context_section(
        self, 
        context_type: ContextType, 
        elements: List[ContextElement],
        formatting_options: Optional[FormattingOptions] = None
    ) -> str:
        """Build a formatted section for a specific context type."""
        
        if not elements:
            return ""
        
        # Get section header
        section_header = self._get_section_header(context_type)
        section_content = []
        
        for element in elements:
            if element.content.strip():
                # Add source attribution if available
                content = element.content.strip()
                if element.source_metadata and element.source_metadata.get('source_type'):
                    source_info = element.source_metadata.get('source_type', 'unknown')
                    content = f"[Source: {source_info}]\n{content}"
                
                section_content.append(content)
        
        if not section_content:
            return ""
        
        # Join content based on context type
        if context_type == ContextType.CONVERSATION_HISTORY:
            # Preserve conversation structure
            joined_content = "\n\n".join(section_content)
        elif context_type in [ContextType.VECTOR_SEARCH_RESULTS, ContextType.COMPLIANCE_SOURCES]:
            # Separate multiple sources clearly
            joined_content = "\n\n---\n\n".join(section_content)
        else:
            # Standard joining
            joined_content = "\n\n".join(section_content)
        
        return f"{section_header}\n{joined_content}\n"
    
    def _get_section_header(self, context_type: ContextType) -> str:
        """Get formatted section header for context type."""
        headers = {
            ContextType.SYSTEM_PROMPT: "=== SYSTEM INSTRUCTIONS ===",
            ContextType.CURRENT_CONTENT: "=== CURRENT CONTENT FOR EDITING ===",
            ContextType.DOCUMENT_SUMMARIES: "=== UPLOADED DOCUMENTS ===",
            ContextType.COMPLIANCE_SOURCES: "=== COMPLIANCE GUIDELINES ===",
            ContextType.VECTOR_SEARCH_RESULTS: "=== RELEVANT EXAMPLES ===",
            ContextType.YOUTUBE_CONTEXT: "=== VIDEO TRANSCRIPT CONTEXT ===",
            ContextType.CONVERSATION_HISTORY: "=== CONVERSATION HISTORY ===",
            ContextType.USER_INPUT: "=== USER REQUEST ==="
        }
        
        return headers.get(context_type, f"=== {context_type.value.upper().replace('_', ' ')} ===")
    
    def _join_context_sections(self, sections: List[str]) -> str:
        """Join context sections with proper separators."""
        if not sections:
            return ""
        
        # Use double newlines between sections for clear separation
        return "\n\n".join(section.strip() for section in sections if section.strip())
    
    def _build_fallback_context(self, elements: List[ContextElement]) -> str:
        """Build basic fallback context if main assembly fails."""
        try:
            # Simple concatenation as fallback
            content_parts = []
            for element in sorted(elements, key=lambda x: x.effective_priority, reverse=True):
                if element.content.strip():
                    content_parts.append(f"[{element.context_type.value}]\n{element.content.strip()}")
            
            return "\n\n".join(content_parts) if content_parts else "No context available"
            
        except Exception as e:
            logger.error(f"Fallback context assembly failed: {e}")
            return "Context assembly failed - using minimal fallback"
    
    def get_context_summary(self, context_elements: List[ContextElement]) -> Dict[str, int]:
        """Get summary statistics about context elements."""
        summary = {}
        total_tokens = 0
        
        for element in context_elements:
            context_type_key = element.context_type.value
            if context_type_key not in summary:
                summary[context_type_key] = 0
            summary[context_type_key] += element.token_count
            total_tokens += element.token_count
        
        summary['total_tokens'] = total_tokens
        summary['total_elements'] = len(context_elements)
        
        return summary
