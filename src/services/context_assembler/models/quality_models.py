"""Quality and Formatting Models"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime


@dataclass
class QualityMetrics:
    """Context quality assessment data."""
    relevance_score: float
    completeness_score: float
    coherence_score: float
    diversity_score: float
    token_efficiency: float
    compression_ratio: float = 1.0
    assessment_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate quality metrics."""
        for name, value in [("relevance_score", self.relevance_score), ("completeness_score", self.completeness_score),
                           ("coherence_score", self.coherence_score), ("diversity_score", self.diversity_score),
                           ("token_efficiency", self.token_efficiency), ("compression_ratio", self.compression_ratio)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")
    
    @property
    def overall_quality_score(self) -> float:
        """Calculate overall quality score as weighted average."""
        return (self.relevance_score * 0.3 + self.completeness_score * 0.25 + 
                self.coherence_score * 0.2 + self.diversity_score * 0.15 + self.token_efficiency * 0.1)
    
    @property
    def quality_grade(self) -> str:
        """Get letter grade based on overall quality score."""
        score = self.overall_quality_score
        return "A" if score >= 0.9 else "B" if score >= 0.8 else "C" if score >= 0.7 else "D" if score >= 0.6 else "F"
    def is_high_quality(self) -> bool:
        """Check if context meets high quality standards."""
        return self.overall_quality_score >= 0.8
    
    def get_improvement_suggestions(self) -> List[str]:
        """Get suggestions for improving context quality."""
        suggestions = []
        if self.relevance_score < 0.7:
            suggestions.append("Improve relevance by filtering context more carefully")
        if self.completeness_score < 0.7:
            suggestions.append("Add more comprehensive context sources")
        if self.coherence_score < 0.7:
            suggestions.append("Improve context ordering and flow")
        if self.diversity_score < 0.5:
            suggestions.append("Include more diverse context sources")
        if self.token_efficiency < 0.6:
            suggestions.append("Apply more aggressive compression strategies")
        return suggestions


@dataclass
class FormattingOptions:
    """Context formatting preferences and options."""
    include_section_headers: bool = True
    include_source_attribution: bool = True
    include_token_counts: bool = False
    include_timestamps: bool = False
    max_line_length: int = None
    section_separator: str = "\n\n---\n\n"
    indent_nested_content: bool = False
    preserve_original_formatting: bool = True
    
    def __post_init__(self):
        """Validate formatting options."""
        if self.max_line_length is not None and self.max_line_length <= 0:
            raise ValueError("max_line_length must be positive if specified")
        if not self.section_separator:
            raise ValueError("section_separator cannot be empty")
    
    @property
    def has_debug_info(self) -> bool:
        """Check if debug information is enabled."""
        return self.include_token_counts or self.include_timestamps
    
    def create_section_header(self, section_name: str, token_count: int = None) -> str:
        """Create a formatted section header."""
        if not self.include_section_headers:
            return ""
        header = f"## {section_name}"
        if self.include_token_counts and token_count is not None:
            header += f" ({token_count} tokens)"
        if self.include_timestamps:
            header += f" - {datetime.now().strftime('%H:%M:%S')}"
        return header + "\n\n"
    
    def create_source_attribution(self, source_info: Dict[str, Any]) -> str:
        """Create formatted source attribution."""
        if not self.include_source_attribution:
            return ""
        parts = []
        if "source" in source_info:
            parts.append(f"Source: {source_info['source']}")
        if "type" in source_info:
            parts.append(f"Type: {source_info['type']}")
        if "confidence" in source_info:
            parts.append(f"Confidence: {source_info['confidence']:.2f}")
        return f"*{' | '.join(parts)}*\n\n" if parts else ""
    
    def format_content_block(self, content: str, indent_level: int = 0) -> str:
        """Format a content block according to preferences."""
        if not content.strip():
            return content
        
        # Apply line length limits
        if self.max_line_length:
            lines = []
            for line in content.split('\n'):
                if len(line) <= self.max_line_length:
                    lines.append(line)
                else:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= self.max_line_length:
                            current_line += " " + word if current_line else word
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)
            content = '\n'.join(lines)
        
        # Apply indentation
        if self.indent_nested_content and indent_level > 0:
            indent = "  " * indent_level
            content = '\n'.join(indent + line if line.strip() else line for line in content.split('\n'))
        
        return content
    @classmethod
    def create_debug_options(cls) -> "FormattingOptions":
        """Create formatting options optimized for debugging."""
        return cls(include_token_counts=True, include_timestamps=True,
                   section_separator="\n\n=== DEBUG SEPARATOR ===\n\n")
    
    @classmethod
    def create_production_options(cls) -> "FormattingOptions":
        """Create formatting options optimized for production use."""
        return cls(include_section_headers=False, include_source_attribution=False,
                   section_separator="\n\n")
