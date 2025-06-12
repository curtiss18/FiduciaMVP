# OpenAI Embeddings Service
"""
Service for generating and managing OpenAI embeddings for content vectorization.
Supports both individual and batch embedding generation.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken

import openai
from openai import AsyncOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating OpenAI embeddings for semantic search."""
    
    def __init__(self):
        """Initialize the embedding service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-large"  # 1536 dimensions, best quality
        self.dimensions = 1536
        self.max_tokens = 8191  # Model limit
        self.batch_size = 100   # API rate limiting
        
        # Initialize tokenizer for cost estimation
        try:
            self.tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")
        except Exception:
            # Fallback tokenizer
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def prepare_text_for_embedding(self, title: str, content: str, 
                                 content_type: str = None, 
                                 audience_type: str = None,
                                 tags: str = None) -> str:
        """
        Prepare text for embedding by combining title, content, and metadata.
        
        Args:
            title: Content title
            content: Main content text
            content_type: Type of content (linkedin_post, email_template, etc.)
            audience_type: Target audience
            tags: Content tags
            
        Returns:
            Combined text optimized for embedding
        """
        # Start with title and content
        combined_parts = []
        
        if title:
            combined_parts.append(f"Title: {title}")
        
        if content:
            combined_parts.append(f"Content: {content}")
        
        # Add metadata for better semantic understanding
        if content_type:
            combined_parts.append(f"Type: {content_type}")
            
        if audience_type:
            combined_parts.append(f"Audience: {audience_type}")
            
        if tags:
            combined_parts.append(f"Tags: {tags}")
        
        combined_text = "\n\n".join(combined_parts)
        
        # Truncate if too long (leave buffer for safety)
        tokens = self.tokenizer.encode(combined_text)
        if len(tokens) > self.max_tokens - 100:
            # Truncate tokens and decode back
            truncated_tokens = tokens[:self.max_tokens - 100]
            combined_text = self.tokenizer.decode(truncated_tokens)
            logger.warning(f"Text truncated from {len(tokens)} to {len(truncated_tokens)} tokens")
        
        return combined_text
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            
            # Log token usage for cost tracking
            token_count = response.usage.total_tokens
            cost = self.estimate_cost(token_count)
            
            logger.info(f"Generated embedding: {token_count} tokens, ${cost:.6f}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (None for failed items)
        """
        if not texts:
            return []
        
        try:
            # Process in batches to respect API limits
            all_embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                try:
                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                        dimensions=self.dimensions
                    )
                    
                    # Extract embeddings in order
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                    # Log batch usage
                    token_count = response.usage.total_tokens
                    cost = self.estimate_cost(token_count)
                    logger.info(f"Batch embedding: {len(batch)} items, {token_count} tokens, ${cost:.6f}")
                    
                    # Rate limiting pause
                    if i + self.batch_size < len(texts):
                        await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in batch {i//self.batch_size}: {str(e)}")
                    # Add None for each failed item in this batch
                    all_embeddings.extend([None] * len(batch))
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}")
            return [None] * len(texts)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost estimation."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Rough estimation if tokenizer fails
            return len(text.split()) * 1.3
    
    def estimate_cost(self, token_count: int) -> float:
        """
        Estimate cost for embedding generation.
        
        text-embedding-3-large: $0.00013 per 1K tokens
        """
        cost_per_1k_tokens = 0.00013
        return (token_count / 1000) * cost_per_1k_tokens
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection and embedding generation."""
        try:
            test_text = "This is a test for embedding generation."
            
            start_time = datetime.now()
            embedding = await self.generate_embedding(test_text)
            end_time = datetime.now()
            
            if embedding:
                return {
                    "status": "success",
                    "model": self.model,
                    "dimensions": len(embedding),
                    "response_time_ms": (end_time - start_time).total_seconds() * 1000,
                    "token_count": self.count_tokens(test_text),
                    "estimated_cost": self.estimate_cost(self.count_tokens(test_text))
                }
            else:
                return {
                    "status": "failed",
                    "error": "No embedding returned"
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }


# Service instance
embedding_service = EmbeddingService()
