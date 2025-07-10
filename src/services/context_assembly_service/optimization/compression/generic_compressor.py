"""
Generic Compression Strategy

"""

import logging
from typing import List, Tuple

from ...models import ContextType
from .compression_strategy import BaseCompressionStrategy

logger = logging.getLogger(__name__)


class GenericCompressor(BaseCompressionStrategy):
    
    async def _compress_implementation(self, content: str, target_tokens: int, context_type: ContextType) -> str:
        if not content.strip():
            return content
        
        # Try different compression approaches in order of preference
        
        # 1. Try paragraph-based compression first
        paragraph_compressed = await self._compress_by_paragraphs(content, target_tokens)
        if paragraph_compressed:
            return paragraph_compressed
        
        # 2. Try sentence-based compression
        sentence_compressed = await self._compress_by_sentences(content, target_tokens)
        if sentence_compressed:
            return sentence_compressed
        
        # 3. Fallback to simple truncation
        return self._truncate_to_token_limit(content, target_tokens)
    
    async def _compress_by_paragraphs(self, content: str, target_tokens: int) -> str:
        paragraphs = content.split('\n\n')
        
        if len(paragraphs) <= 1:
            return ""  # Not suitable for paragraph compression
        
        # Score and prioritize paragraphs
        paragraph_info = []
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            tokens = self.token_manager.count_tokens(paragraph)
            priority = self._calculate_paragraph_priority(paragraph, i, len(paragraphs))
            
            paragraph_info.append({
                'text': paragraph,
                'tokens': tokens,
                'priority': priority,
                'original_index': i
            })
        
        # Sort by priority (highest first)
        paragraph_info.sort(key=lambda x: x['priority'], reverse=True)
        
        # Select paragraphs that fit within budget
        selected_paragraphs = []
        used_tokens = 0
        
        for para_info in paragraph_info:
            if used_tokens + para_info['tokens'] <= target_tokens:
                selected_paragraphs.append(para_info)
                used_tokens += para_info['tokens']
            elif target_tokens - used_tokens > 100:
                # Try to fit a truncated version
                remaining_tokens = target_tokens - used_tokens
                truncated = self._truncate_to_token_limit(para_info['text'], remaining_tokens)
                if truncated and len(truncated) > 50:
                    selected_paragraphs.append({
                        **para_info,
                        'text': truncated,
                        'tokens': self.token_manager.count_tokens(truncated)
                    })
                break
            else:
                break
        
        if not selected_paragraphs:
            return ""
        
        # Sort back to original order
        selected_paragraphs.sort(key=lambda x: x['original_index'])
        
        # Reconstruct content
        result_paragraphs = [para['text'] for para in selected_paragraphs]
        return '\n\n'.join(result_paragraphs)
    
    async def _compress_by_sentences(self, content: str, target_tokens: int) -> str:
        # Simple sentence splitting
        sentences = self._split_into_sentences(content)
        
        if len(sentences) <= 2:
            return ""  # Not suitable for sentence compression
        
        # Score sentences
        sentence_info = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            tokens = self.token_manager.count_tokens(sentence)
            priority = self._calculate_sentence_priority(sentence, i, len(sentences))
            
            sentence_info.append({
                'text': sentence,
                'tokens': tokens,
                'priority': priority,
                'original_index': i
            })
        
        # Sort by priority
        sentence_info.sort(key=lambda x: x['priority'], reverse=True)
        
        # Select sentences that fit
        selected_sentences = []
        used_tokens = 0
        
        for sent_info in sentence_info:
            if used_tokens + sent_info['tokens'] <= target_tokens:
                selected_sentences.append(sent_info)
                used_tokens += sent_info['tokens']
            else:
                break
        
        if not selected_sentences:
            return ""
        
        # Sort back to original order
        selected_sentences.sort(key=lambda x: x['original_index'])
        
        # Reconstruct with proper spacing
        result = ' '.join([sent['text'] for sent in selected_sentences])
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        # Simple sentence splitting - can be improved with NLP library
        import re
        
        # Split on sentence endings, but preserve common abbreviations
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+', text)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_paragraph_priority(self, paragraph: str, index: int, total_paragraphs: int) -> float:
        score = 5.0  # Base score
        
        # First and last paragraphs are often important
        if index == 0:
            score += 2.0  # Introduction
        elif index == total_paragraphs - 1:
            score += 1.5  # Conclusion
        
        # Length indicates substance
        if len(paragraph) > 200:
            score += 1.0
        elif len(paragraph) < 50:
            score -= 1.0
        
        # Content quality indicators
        paragraph_lower = paragraph.lower()
        
        # Important compliance terms
        compliance_terms = [
            'compliance', 'sec', 'finra', 'regulation', 'rule',
            'required', 'must', 'disclaimer', 'risk', 'prohibited'
        ]
        for term in compliance_terms:
            if term in paragraph_lower:
                score += 0.5
        
        # Structure indicators
        if ':' in paragraph and len(paragraph) < 300:  # Likely key definitions
            score += 0.5
        
        if paragraph.startswith(('Note:', 'Important:', 'Warning:', 'Disclaimer:')):
            score += 1.0
        
        return max(0.0, min(10.0, score))
    
    def _calculate_sentence_priority(self, sentence: str, index: int, total_sentences: int) -> float:
        score = 5.0  # Base score
        
        # First sentences are often topic sentences
        if index < total_sentences * 0.1:  # First 10%
            score += 1.5
        
        # Last sentences might be conclusions
        if index > total_sentences * 0.9:  # Last 10%
            score += 1.0
        
        # Length indicates content
        if len(sentence) > 100:
            score += 0.5
        elif len(sentence) < 20:
            score -= 1.0
        
        # Important keywords
        sentence_lower = sentence.lower()
        
        compliance_keywords = [
            'must', 'required', 'prohibited', 'rule', 'regulation',
            'compliance', 'sec', 'finra', 'disclaimer'
        ]
        
        for keyword in compliance_keywords:
            if keyword in sentence_lower:
                score += 0.3
        
        # Sentence structure indicators
        if sentence.strip().endswith((':',)):
            score += 0.5  # Likely introduces important info
        
        if sentence.startswith(('However,', 'Therefore,', 'Additionally,', 'Furthermore,')):
            score += 0.3  # Transition sentences with important connections
        
        return max(0.0, min(10.0, score))
    
    def estimate_compression_ratio(self, content: str, context_type: ContextType) -> float:
        # Count paragraphs and sentences for compression potential
        paragraphs = content.split('\n\n')
        sentences = self._split_into_sentences(content)
        
        # More structure = better compression potential
        if len(paragraphs) > 5:
            return 0.6  # Good paragraph-based compression
        elif len(sentences) > 10:
            return 0.4  # Moderate sentence-based compression
        else:
            return 0.2  # Limited compression potential
