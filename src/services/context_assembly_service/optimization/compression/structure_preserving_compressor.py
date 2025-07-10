"""
Structure Preserving Compression Strategy

"""

import logging
from typing import List

from ...models import ContextType
from .compression_strategy import BaseCompressionStrategy

logger = logging.getLogger(__name__)


class StructurePreservingCompressor(BaseCompressionStrategy):
    
    async def _compress_implementation(self, content: str, target_tokens: int, context_type: ContextType) -> str:
        if not content.strip():
            return content
        
        lines = content.split('\n')
        
        # Identify structural elements
        structural_lines = []
        content_lines = []
        
        for i, line in enumerate(lines):
            if self._is_structural_element(line):
                structural_lines.append((i, line))
            else:
                content_lines.append((i, line))
        
        # Calculate tokens for structural elements
        structural_text = '\n'.join([line for _, line in structural_lines])
        structural_tokens = self.token_manager.count_tokens(structural_text)
        
        # Allocate remaining tokens for content
        available_content_tokens = max(100, target_tokens - structural_tokens)
        
        # Compress content lines while preserving structure
        compressed_content_lines = await self._compress_content_lines(
            content_lines, available_content_tokens
        )
        
        # Reassemble with structure preserved
        final_lines = [None] * len(lines)
        
        # Place structural elements
        for i, line in structural_lines:
            final_lines[i] = line
        
        # Place compressed content
        content_iter = iter(compressed_content_lines)
        for i, _ in content_lines:
            try:
                final_lines[i] = next(content_iter)
            except StopIteration:
                final_lines[i] = "[Content truncated]"
        
        # Filter out None values and join
        result = '\n'.join([line for line in final_lines if line is not None])
        
        # Final truncation if still too long
        if self.token_manager.count_tokens(result) > target_tokens:
            result = self._truncate_to_token_limit(result, target_tokens)
        
        return result
    
    def _is_structural_element(self, line: str) -> bool:
        line = line.strip()
        
        if not line:
            return False
        
        # Headings (markdown style)
        if line.startswith('#'):
            return True
        
        # Bullet points
        if line.startswith(('*', '-', '•', '1.', '2.', '3.', '4.', '5.')):
            return True
        
        # Section markers
        if line.startswith(('**', '__')) and (line.endswith(('**', '__', ':'))):
            return True
        
        # All caps short lines (likely headers)
        if len(line) < 50 and line.isupper() and ':' in line:
            return True
        
        return False
    
    async def _compress_content_lines(
        self, 
        content_lines: List[tuple], 
        available_tokens: int
    ) -> List[str]:
        if not content_lines:
            return []
        
        # Extract just the line content
        lines = [line for _, line in content_lines]
        
        # Calculate current tokens
        current_text = '\n'.join(lines)
        current_tokens = self.token_manager.count_tokens(current_text)
        
        if current_tokens <= available_tokens:
            return lines
        
        # Need compression - prioritize lines by length and importance
        prioritized_lines = self._prioritize_lines(lines)
        
        # Select lines that fit within budget
        selected_lines = []
        used_tokens = 0
        
        for line_info in prioritized_lines:
            line = line_info['line']
            tokens = line_info['tokens']
            
            if used_tokens + tokens <= available_tokens:
                selected_lines.append((line_info['original_index'], line))
                used_tokens += tokens
            elif available_tokens - used_tokens > 50:
                # Try to fit a truncated version
                remaining_tokens = available_tokens - used_tokens
                truncated = self._truncate_to_token_limit(line, remaining_tokens)
                if truncated and truncated != "...":
                    selected_lines.append((line_info['original_index'], truncated))
                break
            else:
                break
        
        # Sort back to original order and return lines
        selected_lines.sort(key=lambda x: x[0])
        return [line for _, line in selected_lines]
    
    def _prioritize_lines(self, lines: List[str]) -> List[dict]:
        line_info = []
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            tokens = self.token_manager.count_tokens(line)
            
            # Calculate priority score
            priority_score = self._calculate_line_priority(line)
            
            line_info.append({
                'original_index': i,
                'line': line,
                'tokens': tokens,
                'priority': priority_score
            })
        
        # Sort by priority (higher is better)
        return sorted(line_info, key=lambda x: x['priority'], reverse=True)
    
    def _calculate_line_priority(self, line: str) -> float:
        line = line.strip()
        score = 5.0  # Base score
        
        # Longer lines often have more content
        if len(line) > 100:
            score += 1.0
        
        # Lines with keywords are important
        important_keywords = [
            'compliance', 'sec', 'finra', 'regulation', 'rule',
            'required', 'must', 'shall', 'disclaimer', 'risk'
        ]
        
        line_lower = line.lower()
        for keyword in important_keywords:
            if keyword in line_lower:
                score += 0.5
        
        # Lines with specific formatting
        if ':' in line and len(line) < 200:  # Likely definitions or key points
            score += 0.5
        
        # Very short lines are less important
        if len(line) < 20:
            score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def estimate_compression_ratio(self, content: str, context_type: ContextType) -> float:
        lines = content.split('\n')
        structural_lines = sum(1 for line in lines if self._is_structural_element(line))
        
        # More structural elements = less compression possible
        structural_ratio = structural_lines / len(lines) if lines else 0
        
        if structural_ratio > 0.5:
            return 0.2  # Low compression due to high structure
        elif structural_ratio > 0.3:
            return 0.4  # Moderate compression
        else:
            return 0.6  # Good compression potential
