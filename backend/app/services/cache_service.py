"""Cache Service for semantic caching using Redis"""

import json
import hashlib
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class CacheService:
    """Service for semantic caching of LLM responses"""

    def __init__(self):
        """Initialize cache service"""
        self.redis_client = None
        self.embedding_model = None
        self.initialized = False

    async def initialize(self):
        """Initialize Redis connection and embedding model"""
        if self.initialized:
            return

        # Connect to Redis
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False
        )

        # Load embedding model for semantic similarity
        # Using a lightweight model for fast caching
        if settings.semantic_cache_enabled:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        self.initialized = True

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _create_cache_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """Create a hash key for exact match caching"""
        # Create a stable string representation
        messages_str = json.dumps(messages, sort_keys=True)
        combined = f"{model}:{messages_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for semantic search"""
        if not self.embedding_model:
            return None

        # Generate embedding
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def get_cached_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        use_semantic: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for messages

        Args:
            messages: List of conversation messages
            model: Model identifier
            use_semantic: Whether to use semantic similarity matching

        Returns:
            Cached response dict or None if not found
        """
        if not self.initialized:
            await self.initialize()

        # Try exact match first
        exact_key = self._create_cache_key(messages, model)
        exact_match = await self.redis_client.get(f"cache:exact:{exact_key}")

        if exact_match:
            return json.loads(exact_match)

        # Try semantic match if enabled
        if use_semantic and settings.semantic_cache_enabled and self.embedding_model:
            # Get the last user message for semantic matching
            user_message = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break

            if user_message:
                query_embedding = await self._get_embedding(user_message)

                # Search for similar cached prompts
                cache_keys = await self.redis_client.keys(f"cache:semantic:{model}:*")

                best_match = None
                best_similarity = 0.0

                for cache_key in cache_keys[:100]:  # Limit search to 100 most recent
                    cached_data = await self.redis_client.get(cache_key)
                    if cached_data:
                        cached = json.loads(cached_data)
                        cached_embedding = np.array(cached["embedding"])

                        similarity = self._cosine_similarity(query_embedding, cached_embedding)

                        if similarity > best_similarity and similarity >= settings.semantic_cache_threshold:
                            best_similarity = similarity
                            best_match = cached["response"]

                if best_match:
                    return best_match

        return None

    async def cache_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """
        Cache a response

        Args:
            messages: List of conversation messages
            model: Model identifier
            response: Response to cache
            ttl: Time to live in seconds (default from settings)
        """
        if not self.initialized:
            await self.initialize()

        ttl = ttl or settings.cache_ttl_seconds

        # Store exact match
        exact_key = self._create_cache_key(messages, model)
        await self.redis_client.setex(
            f"cache:exact:{exact_key}",
            ttl,
            json.dumps(response)
        )

        # Store for semantic matching if enabled
        if settings.semantic_cache_enabled and self.embedding_model:
            user_message = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break

            if user_message:
                embedding = await self._get_embedding(user_message)
                semantic_key = f"cache:semantic:{model}:{exact_key}"

                cache_data = {
                    "embedding": embedding.tolist(),
                    "response": response
                }

                await self.redis_client.setex(
                    semantic_key,
                    ttl,
                    json.dumps(cache_data)
                )

    async def invalidate_cache(self, pattern: str = "*"):
        """
        Invalidate cache entries matching pattern

        Args:
            pattern: Redis key pattern to match
        """
        if not self.initialized:
            await self.initialize()

        keys = await self.redis_client.keys(f"cache:*:{pattern}")
        if keys:
            await self.redis_client.delete(*keys)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.initialized:
            await self.initialize()

        exact_keys = await self.redis_client.keys("cache:exact:*")
        semantic_keys = await self.redis_client.keys("cache:semantic:*")

        return {
            "exact_cache_entries": len(exact_keys),
            "semantic_cache_entries": len(semantic_keys),
            "total_entries": len(exact_keys) + len(semantic_keys)
        }
