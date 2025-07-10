"""
Conversation Manager for Warren Chat Sessions

Handles conversation memory, context compression, and token management
for maintaining context across Warren interactions within Claude's 200K token limits.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, func
from sqlalchemy.orm import selectinload

from src.models.advisor_workflow_models import (
    AdvisorSessions, 
    AdvisorMessages, 
    ConversationContext
)

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages conversation context and memory for Warren sessions.
    
    Features:
    - Intelligent context compression for token management
    - Conversation history retrieval and storage
    - Context type management (full_history, compressed, summary)
    - Token counting and optimization
    """
    
    # Token limits for context management
    MAX_CONTEXT_TOKENS = 180000  # Leave 20K for response generation
    COMPRESSION_THRESHOLD = 150000  # Start compressing when context exceeds this
    RECENT_MESSAGES_PRESERVE = 5  # Always keep last N messages in full detail
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_conversation_context(self, session_id: str) -> str:
        """
        Retrieve conversation context for a session, handling token limits intelligently.
        
        Returns formatted context string ready for Warren's system prompt.
        """
        try:
            # Get session info
            session_result = await self.db.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return ""
            
            # Get all messages for this session
            messages_result = await self.db.execute(
                select(AdvisorMessages)
                .where(AdvisorMessages.session_id == session_id)
                .order_by(AdvisorMessages.created_at.asc())
            )
            messages = messages_result.scalars().all()
            
            if not messages:
                return ""
            
            # Check if we need to compress based on message count and content
            total_context = self._build_full_context(messages)
            total_tokens = self._estimate_tokens(total_context)
            
            if total_tokens <= self.COMPRESSION_THRESHOLD:
                # Context is manageable, return full history
                await self._save_context(session_id, "full_history", total_context, total_tokens)
                return total_context
            
            # Need compression - use intelligent compression strategy
            compressed_context = await self._compress_conversation_intelligently(session_id, messages)
            return compressed_context
            
        except Exception as e:
            logger.error(f"Error getting conversation context for session {session_id}: {e}")
            return ""
    
    async def _compress_conversation_intelligently(self, session_id: str, messages: List[AdvisorMessages]) -> str:
        """
        Intelligent conversation compression that preserves recent exchanges and key context.
        """
        try:
            if len(messages) <= self.RECENT_MESSAGES_PRESERVE * 2:  # user + warren pairs
                # Too few messages to compress meaningfully
                return self._build_full_context(messages)
            
            # Split messages into recent and older
            recent_messages = messages[-self.RECENT_MESSAGES_PRESERVE * 2:]  # Last N user+warren pairs
            older_messages = messages[:-self.RECENT_MESSAGES_PRESERVE * 2]
            
            # Build full context for recent messages
            recent_context = self._build_full_context(recent_messages)
            recent_tokens = self._estimate_tokens(recent_context)
            
            # Available tokens for compressed history
            available_tokens = self.MAX_CONTEXT_TOKENS - recent_tokens - 1000  # Buffer
            
            if available_tokens <= 0:
                # Recent messages take too much space, only use summary
                compressed_older = await self._create_conversation_summary(older_messages)
            else:
                # Compress older messages to fit available space
                compressed_older = await self._compress_conversation_history(older_messages, available_tokens)
            
            # Combine compressed older context with recent full context
            combined_context = f"""Previous conversation summary:
{compressed_older}

Recent conversation:
{recent_context}"""
            
            # Save compressed context
            total_tokens = self._estimate_tokens(combined_context)
            await self._save_context(session_id, "compressed", combined_context, total_tokens)
            
            return combined_context
            
        except Exception as e:
            logger.error(f"Error compressing conversation for session {session_id}: {e}")
            # Fallback to recent messages only
            return self._build_full_context(messages[-self.RECENT_MESSAGES_PRESERVE * 2:])
    
    async def _compress_conversation_history(self, messages: List[AdvisorMessages], target_tokens: int) -> str:
        """
        Compress older conversation history to fit within target token count.
        """
        # Group messages into conversation pairs (user + warren)
        conversation_pairs = []
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i] if messages[i].message_type == 'user' else messages[i + 1]
                warren_msg = messages[i + 1] if messages[i + 1].message_type == 'warren' else messages[i]
                conversation_pairs.append((user_msg, warren_msg))
        
        # Create compressed summaries of each pair
        compressed_pairs = []
        for user_msg, warren_msg in conversation_pairs:
            # Extract key information from each exchange
            user_intent = self._extract_user_intent(user_msg.content)
            warren_response_type = self._extract_response_type(warren_msg.content)
            
            compressed_pair = f"User requested: {user_intent} → Warren: {warren_response_type}"
            compressed_pairs.append(compressed_pair)
        
        # Combine and fit within token limit
        compressed_text = " | ".join(compressed_pairs)
        
        # If still too long, truncate intelligently
        estimated_tokens = self._estimate_tokens(compressed_text)
        if estimated_tokens > target_tokens:
            # Keep most recent compressed pairs that fit
            truncated_pairs = []
            current_tokens = 0
            
            for pair in reversed(compressed_pairs):
                pair_tokens = self._estimate_tokens(pair)
                if current_tokens + pair_tokens <= target_tokens:
                    truncated_pairs.insert(0, pair)
                    current_tokens += pair_tokens
                else:
                    break
            
            compressed_text = " | ".join(truncated_pairs)
            if truncated_pairs != compressed_pairs:
                compressed_text = f"[Earlier messages truncated] | {compressed_text}"
        
        return compressed_text
    
    async def _create_conversation_summary(self, messages: List[AdvisorMessages]) -> str:
        """
        Create a high-level summary when compression isn't enough.
        """
        if not messages:
            return "No previous conversation."
        
        # Analyze conversation themes
        user_requests = [msg.content for msg in messages if msg.message_type == 'user']
        content_types_mentioned = set()
        topics_mentioned = set()
        
        # Simple keyword extraction for summary
        for request in user_requests:
            request_lower = request.lower()
            
            # Content types
            if 'linkedin' in request_lower:
                content_types_mentioned.add('LinkedIn posts')
            if 'email' in request_lower:
                content_types_mentioned.add('email content')
            if 'newsletter' in request_lower:
                content_types_mentioned.add('newsletter content')
            if 'blog' in request_lower:
                content_types_mentioned.add('blog posts')
            
            # Topics
            if 'retirement' in request_lower:
                topics_mentioned.add('retirement planning')
            if 'investment' in request_lower:
                topics_mentioned.add('investment advice')
            if 'tax' in request_lower:
                topics_mentioned.add('tax planning')
            if 'estate' in request_lower:
                topics_mentioned.add('estate planning')
        
        # Build summary
        summary_parts = []
        summary_parts.append(f"Previous conversation included {len(user_requests)} requests")
        
        if content_types_mentioned:
            summary_parts.append(f"Content types: {', '.join(content_types_mentioned)}")
        
        if topics_mentioned:
            summary_parts.append(f"Topics covered: {', '.join(topics_mentioned)}")
        
        return ". ".join(summary_parts) + "."
    
    def _build_full_context(self, messages: List[AdvisorMessages]) -> str:
        """
        Build full conversation context from messages.
        """
        context_parts = []
        
        for message in messages:
            if message.message_type == 'user':
                context_parts.append(f"User: {message.content}")
            elif message.message_type == 'warren':
                context_parts.append(f"Warren: {message.content}")
        
        return "\n\n".join(context_parts)
    
    def _extract_user_intent(self, user_message: str) -> str:
        """
        Extract the main intent from a user message for compression.
        """
        # Simple intent extraction - can be enhanced with NLP
        message_lower = user_message.lower()
        
        if 'create' in message_lower or 'write' in message_lower:
            return "content creation request"
        elif 'edit' in message_lower or 'change' in message_lower or 'modify' in message_lower:
            return "content modification request"
        elif 'help' in message_lower or 'how' in message_lower:
            return "guidance request"
        else:
            # Truncate long messages
            return user_message[:50] + "..." if len(user_message) > 50 else user_message
    
    def _extract_response_type(self, warren_message: str) -> str:
        """
        Extract the response type from Warren's message for compression.
        """
        # Check if Warren generated content (contains delimiters or structured content)
        if '##MARKETINGCONTENT##' in warren_message:
            return "generated marketing content"
        elif len(warren_message) > 200:
            return "detailed guidance response"
        else:
            return "brief response"
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text. Using rough approximation: 1 token ≈ 4 characters.
        This is conservative for Claude tokenization.
        """
        return len(text) // 4
    
    async def _save_context(self, session_id: str, context_type: str, content: str, token_count: int):
        """
        Save conversation context to database for auditing and optimization.
        """
        try:
            context_record = ConversationContext(
                session_id=session_id,
                context_type=context_type,
                content=content,
                token_count=token_count,
                created_at=datetime.utcnow()
            )
            
            self.db.add(context_record)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving context for session {session_id}: {e}")
            await self.db.rollback()
    
    async def save_conversation_turn(self, session_id: str, user_input: str, warren_response: str, warren_metadata: Optional[Dict] = None):
        """
        Save a complete conversation turn (user input + Warren response).
        Automatically creates session if it doesn't exist.
        """
        try:
            # First, ensure the session exists (create if needed)
            await self._ensure_session_exists(session_id)
            
            # Save user message
            user_message = AdvisorMessages(
                session_id=session_id,
                message_type='user',
                content=user_input,
                created_at=datetime.utcnow()
            )
            self.db.add(user_message)
            
            # Save Warren message with metadata
            warren_message = AdvisorMessages(
                session_id=session_id,
                message_type='warren',
                content=warren_response,
                created_at=datetime.utcnow()
            )
            
            # Add Warren-specific metadata if provided
            if warren_metadata:
                warren_message.sources_used = json.dumps(warren_metadata.get('sources_used', []))
                warren_message.generation_confidence = warren_metadata.get('generation_confidence')
                warren_message.search_strategy = warren_metadata.get('search_strategy')
                warren_message.total_sources = warren_metadata.get('total_sources')
                warren_message.marketing_examples = warren_metadata.get('marketing_examples')
                warren_message.compliance_rules = warren_metadata.get('compliance_rules')
            
            self.db.add(warren_message)
            
            # Update session activity
            session_result = await self.db.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if session:
                session.last_activity = datetime.utcnow()
                session.message_count = (session.message_count or 0) + 2  # user + warren
            
            await self.db.commit()
            
            logger.info(f"Saved conversation turn for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation turn for session {session_id}: {e}")
            await self.db.rollback()
            raise
    
    async def _ensure_session_exists(self, session_id: str):
        """
        Ensure session exists in database, create if it doesn't exist.
        """
        try:
            # Check if session exists
            session_result = await self.db.execute(
                select(AdvisorSessions).where(AdvisorSessions.session_id == session_id)
            )
            existing_session = session_result.scalar_one_or_none()
            
            if not existing_session:
                # Create new session
                new_session = AdvisorSessions(
                    advisor_id="demo-advisor",  # Default advisor ID
                    session_id=session_id,
                    title="Warren Conversation",  # Default title
                    message_count=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_session)
                await self.db.flush()  # Ensure session is created before messages
                logger.info(f"Created new session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error ensuring session exists {session_id}: {e}")
            raise
    
    async def cleanup_old_contexts(self, days_to_keep: int = 30):
        """
        Clean up old conversation contexts to manage database size.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.db.execute(
                select(ConversationContext).where(ConversationContext.created_at < cutoff_date)
            )
            old_contexts = result.scalars().all()
            
            for context in old_contexts:
                await self.db.delete(context)
            
            await self.db.commit()
            
            logger.info(f"Cleaned up {len(old_contexts)} old conversation contexts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old contexts: {e}")
            await self.db.rollback()
