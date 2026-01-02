"""
Vector Memory - Semantic storage with Qdrant.

Used for:
- Sales patterns (searchable by similarity)
- Transcripts (for context retrieval)
- Champion profiles
"""

import os
import uuid
from datetime import datetime

import structlog

logger = structlog.get_logger()

# Try to import Qdrant and sentence transformers
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
    from qdrant_client.http.exceptions import UnexpectedResponse

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant_not_available", message="Qdrant client not installed")

try:
    from sentence_transformers import SentenceTransformer

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("embeddings_not_available", message="sentence-transformers not installed")


class VectorMemory:
    """
    Vector-based memory using Qdrant for semantic search.

    Features:
    - Store text with embeddings
    - Semantic similarity search
    - Filtering by metadata
    - Batch operations
    """

    DEFAULT_COLLECTION = "champion_patterns"
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    VECTOR_SIZE = 384  # MiniLM output dimension

    def __init__(
        self, collection_name: str = DEFAULT_COLLECTION, embedding_model: str = DEFAULT_MODEL, url: str | None = None
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # Initialize Qdrant client
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")

        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(url=self.url)
                self._ensure_collection()
            except Exception as e:
                logger.error("qdrant_connection_error", error=str(e))
                self.client = None
        else:
            self.client = None

        # Initialize embedding model
        if EMBEDDINGS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(embedding_model)
            except Exception as e:
                logger.error("embeddings_load_error", error=str(e))
                self.encoder = None
        else:
            self.encoder = None

        logger.info(
            "vector_memory_initialized",
            collection=collection_name,
            qdrant_available=self.client is not None,
            embeddings_available=self.encoder is not None,
        )

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
        except (UnexpectedResponse, Exception):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self.VECTOR_SIZE, distance=qdrant_models.Distance.COSINE
                ),
            )
            logger.info("collection_created", name=self.collection_name)

    def _generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text."""
        if not self.encoder:
            return None

        try:
            embedding = self.encoder.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error("embedding_generation_error", error=str(e))
            return None

    async def store(self, key: str, content: str, metadata: dict | None = None) -> bool:
        """
        Store content with embedding.

        Args:
            key: Unique identifier
            content: Text content to store
            metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.client or not self.encoder:
            logger.warning("vector_store_unavailable")
            return False

        try:
            embedding = self._generate_embedding(content)
            if not embedding:
                return False

            payload = {"content": content, "key": key, "created_at": datetime.utcnow().isoformat(), **(metadata or {})}

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    qdrant_models.PointStruct(
                        id=key if key.isdigit() else abs(hash(key)) % (10**12), vector=embedding, payload=payload
                    )
                ],
            )

            logger.debug("vector_stored", key=key, content_length=len(content))
            return True

        except Exception as e:
            logger.error("vector_store_error", key=key, error=str(e))
            return False

    async def store_batch(self, items: list[dict]) -> int:
        """
        Store multiple items in batch.

        Args:
            items: List of {"key": str, "content": str, "metadata": dict}

        Returns:
            Number of successfully stored items
        """
        if not self.client or not self.encoder:
            return 0

        points = []
        for item in items:
            embedding = self._generate_embedding(item["content"])
            if not embedding:
                continue

            key = item["key"]
            payload = {
                "content": item["content"],
                "key": key,
                "created_at": datetime.utcnow().isoformat(),
                **(item.get("metadata", {})),
            }

            points.append(
                qdrant_models.PointStruct(
                    id=key if isinstance(key, int) else abs(hash(key)) % (10**12), vector=embedding, payload=payload
                )
            )

        if not points:
            return 0

        try:
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info("batch_stored", count=len(points))
            return len(points)

        except Exception as e:
            logger.error("batch_store_error", error=str(e))
            return 0

    async def retrieve(
        self, query: str, limit: int = 5, filters: dict | None = None, score_threshold: float = 0.5
    ) -> list[dict]:
        """
        Retrieve similar content.

        Args:
            query: Search query
            limit: Maximum results
            filters: Metadata filters
            score_threshold: Minimum similarity score

        Returns:
            List of matching entries with scores
        """
        if not self.client or not self.encoder:
            return []

        try:
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []

            # Build Qdrant filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            qdrant_models.FieldCondition(key=key, match=qdrant_models.MatchAny(any=value))
                        )
                    else:
                        conditions.append(
                            qdrant_models.FieldCondition(key=key, match=qdrant_models.MatchValue(value=value))
                        )
                qdrant_filter = qdrant_models.Filter(must=conditions)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
            )

            return [{**hit.payload, "score": hit.score, "id": hit.id} for hit in results]

        except Exception as e:
            logger.error("vector_retrieve_error", query=query[:50], error=str(e))
            return []

    async def delete(self, key: str) -> bool:
        """Delete an entry by key."""
        if not self.client:
            return False

        try:
            point_id = key if isinstance(key, int) else abs(hash(key)) % (10**12)
            self.client.delete(
                collection_name=self.collection_name, points_selector=qdrant_models.PointIdsList(points=[point_id])
            )
            return True
        except Exception as e:
            logger.error("vector_delete_error", key=key, error=str(e))
            return False

    async def delete_by_filter(self, filters: dict) -> int:
        """Delete entries matching filters."""
        if not self.client:
            return 0

        try:
            conditions = [
                qdrant_models.FieldCondition(key=key, match=qdrant_models.MatchValue(value=value))
                for key, value in filters.items()
            ]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(filter=qdrant_models.Filter(must=conditions)),
            )
            return 1  # Qdrant doesn't return count
        except Exception as e:
            logger.error("vector_delete_filter_error", error=str(e))
            return 0

    async def get_stats(self) -> dict:
        """Get collection statistics."""
        if not self.client:
            return {"status": "unavailable"}

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "status": "available",
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "segments_count": info.segments_count,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


class PatternVectorMemory(VectorMemory):
    """Specialized vector memory for sales patterns."""

    def __init__(self):
        super().__init__(collection_name="sales_patterns")

    async def store_pattern(
        self,
        champion_id: int,
        pattern_type: str,
        content: str,
        context: str | None = None,
        examples: list[str] | None = None,
    ) -> str:
        """Store a sales pattern."""
        pattern_id = str(uuid.uuid4())[:8]

        metadata = {
            "champion_id": champion_id,
            "pattern_type": pattern_type,
            "context": context,
            "examples": examples or [],
            "usage_count": 0,
        }

        success = await self.store(pattern_id, content, metadata)
        return pattern_id if success else ""

    async def find_similar_patterns(
        self, query: str, champion_id: int | None = None, pattern_type: str | None = None, limit: int = 5
    ) -> list[dict]:
        """Find similar patterns."""
        filters = {}
        if champion_id:
            filters["champion_id"] = champion_id
        if pattern_type:
            filters["pattern_type"] = pattern_type

        return await self.retrieve(query, limit=limit, filters=filters if filters else None)

    async def get_patterns_by_champion(self, champion_id: int) -> list[dict]:
        """Get all patterns for a champion."""
        return await self.retrieve(
            query="sales patterns techniques",  # Generic query
            limit=100,
            filters={"champion_id": champion_id},
            score_threshold=0.0,  # Get all
        )
