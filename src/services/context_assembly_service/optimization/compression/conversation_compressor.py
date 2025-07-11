"""
Conversation Compression Strategy

"""

import logging
from typing import List, Tuple

from ...models import ContextType
from .compression_strategy import BaseCompressionStrategy

logger = logging.getLogger(__name__)


class ConversationCompressor(BaseCompressionStrategy):
    
    async def _compress_implementation(self, content: str, target_tokens: int, context_type: ContextType) -> str:

        if not content.strip():
            return content
        
        lines = content.split('\n')
        
        # Parse conversation into exchanges
        exchanges = self._parse_conversation_exchanges(lines)
        
        if not exchanges:
            # Fallback to simple truncation
            return self._truncate_to_token_limit(content, target_tokens)
        
        # Select most recent exchanges that fit within budget
        selected_exchanges = await self._select_recent_exchanges(exchanges, target_tokens)
        
        # Reconstruct conversation
        result_lines = []
        
        if len(selected_exchanges) < len(exchanges):
            result_lines.append("[Earlier conversation truncated]")
            result_lines.append("")
        
        for exchange in selected_exchanges:
            result_lines.extend(exchange['lines'])
            result_lines.append("")  # Add spacing between exchanges
        
        # Clean up extra newlines and join
        result = '\n'.join(result_lines).strip()
        
        # Final check and truncation if needed
        if self.token_manager.count_tokens(result) > target_tokens:
            result = self._truncate_to_token_limit(result, target_tokens)
        
        return result
    
    def _parse_conversation_exchanges(self, lines: List[str]) -> List[dict]:
        exchanges = []
        current_exchange = []
        current_speaker = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_exchange:
                    # End of exchange - save it
                    exchanges.append({
                        'lines': current_exchange.copy(),
                        'speaker': current_speaker,
                        'token_count': self.token_manager.count_tokens('\n'.join(current_exchange)),
                        'exchange_id': len(exchanges)
                    })
                    current_exchange = []
                    current_speaker = None
                continue
            
            # Detect speaker changes
            detected_speaker = self._detect_speaker(line)
            
            if detected_speaker and detected_speaker != current_speaker:
                # Speaker changed - save previous exchange
                if current_exchange:
                    exchanges.append({
                        'lines': current_exchange.copy(),
                        'speaker': current_speaker,
                        'token_count': self.token_manager.count_tokens('\n'.join(current_exchange)),
                        'exchange_id': len(exchanges)
                    })
                    current_exchange = []
                
                current_speaker = detected_speaker
            
            current_exchange.append(line)
        
        # Save final exchange
        if current_exchange:
            exchanges.append({
                'lines': current_exchange.copy(),
                'speaker': current_speaker,
                'token_count': self.token_manager.count_tokens('\n'.join(current_exchange)),
                'exchange_id': len(exchanges)
            })
        
        return exchanges
    
    def _detect_speaker(self, line: str) -> str:
        line_lower = line.lower()
        
        # Common conversation markers
        if line.startswith(('user:', 'advisor:', 'human:')):
            return 'advisor'
        elif line.startswith(('warren:', 'assistant:', 'ai:')):
            return 'warren'
        elif line.startswith(('cco:', 'compliance:')):
            return 'compliance'
        
        # Contextual clues
        if any(phrase in line_lower for phrase in [
            'please create', 'help me', 'i need', 'can you'
        ]):
            return 'advisor'
        elif any(phrase in line_lower for phrase in [
            "i'll help", "here's", "based on", "let me"
        ]):
            return 'warren'
        
        return None
    
    async def _select_recent_exchanges(
        self, 
        exchanges: List[dict], 
        target_tokens: int
    ) -> List[dict]:
        if not exchanges:
            return []
        
        # Start from most recent and work backwards
        selected = []
        used_tokens = 0
        
        # Reserve tokens for truncation notice if needed
        reserve_tokens = 50
        available_tokens = target_tokens - reserve_tokens
        
        for exchange in reversed(exchanges):
            exchange_tokens = exchange['token_count']
            
            if used_tokens + exchange_tokens <= available_tokens:
                selected.insert(0, exchange)  # Insert at beginning to maintain order
                used_tokens += exchange_tokens
            else:
                # Try to include a partial exchange if there's room
                if available_tokens - used_tokens > 100:
                    partial_exchange = await self._create_partial_exchange(
                        exchange, available_tokens - used_tokens
                    )
                    if partial_exchange:
                        selected.insert(0, partial_exchange)
                break
        
        return selected
    
    async def _create_partial_exchange(self, exchange: dict, available_tokens: int) -> dict:
        lines = exchange['lines']
        
        # Try to keep the most important lines from the exchange
        important_lines = []
        used_tokens = 0
        
        for line in lines:
            line_tokens = self.token_manager.count_tokens(line)
            
            if used_tokens + line_tokens <= available_tokens:
                important_lines.append(line)
                used_tokens += line_tokens
            elif available_tokens - used_tokens > 20:
                # Try to truncate the line
                truncated = self._truncate_to_token_limit(line, available_tokens - used_tokens)
                if truncated and len(truncated) > 10:
                    important_lines.append(truncated)
                break
            else:
                break
        
        if not important_lines:
            return None
        
        return {
            'lines': important_lines,
            'speaker': exchange['speaker'],
            'token_count': self.token_manager.count_tokens('\n'.join(important_lines)),
            'exchange_id': exchange['exchange_id'],
            'partial': True
        }
    
    def estimate_compression_ratio(self, content: str, context_type: ContextType) -> float:
        lines = content.split('\n')
        
        # Count non-empty lines
        content_lines = [line for line in lines if line.strip()]
        
        if len(content_lines) < 10:
            return 0.2  # Short conversations compress poorly
        elif len(content_lines) < 50:
            return 0.5  # Moderate compression
        else:
            return 0.7  # Good compression potential for long conversations
    
    def _calculate_exchange_priority(self, exchange: dict, position_from_end: int) -> float:
        # Base priority - recent exchanges are more important
        priority = 10.0 - (position_from_end * 0.5)
        
        # Warren responses are valuable
        if exchange.get('speaker') == 'warren':
            priority += 1.0
        
        # Longer exchanges might have more context
        if exchange.get('token_count', 0) > 200:
            priority += 0.5
        
        return max(0.0, priority)
