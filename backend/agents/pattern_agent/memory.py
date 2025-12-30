"""
Pattern Agent Memory - Vector storage for patterns.
"""

from typing import Optional

from memory.vector_store import PatternVectorMemory
from memory.schemas import PatternMemory


class PatternAgentMemory:
    """
    Memory interface for Pattern Agent.

    Uses Qdrant for semantic pattern storage and retrieval.
    """

    def __init__(self):
        self.vector_memory = PatternVectorMemory()

    async def store(self, key: str, value: dict, metadata: Optional[dict] = None) -> bool:
        """Store a pattern."""
        return await self.vector_memory.store(key, str(value), metadata)

    async def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        """Retrieve similar patterns."""
        return await self.vector_memory.retrieve(query, limit=limit)

    async def store_patterns_batch(
        self,
        champion_id: int,
        patterns: dict
    ) -> dict:
        """
        Store all patterns for a champion.

        Args:
            champion_id: Champion ID
            patterns: Extracted patterns dict

        Returns:
            Dict with storage results
        """
        stored = {
            "openings": 0,
            "objection_handlers": 0,
            "closes": 0,
            "key_phrases": 0,
            "success_patterns": 0
        }

        # Store openings
        for i, opening in enumerate(patterns.get("openings", [])):
            pattern_id = await self.vector_memory.store_pattern(
                champion_id=champion_id,
                pattern_type="opening",
                content=opening,
                context=f"Opening technique {i+1}"
            )
            if pattern_id:
                stored["openings"] += 1

        # Store objection handlers
        for i, handler in enumerate(patterns.get("objection_handlers", [])):
            content = f"Objection: {handler.get('objection', '')} | Response: {handler.get('response', '')}"
            pattern_id = await self.vector_memory.store_pattern(
                champion_id=champion_id,
                pattern_type="objection",
                content=content,
                context=handler.get("example", ""),
                examples=[handler.get("example", "")] if handler.get("example") else []
            )
            if pattern_id:
                stored["objection_handlers"] += 1

        # Store closes
        for i, close in enumerate(patterns.get("closes", [])):
            pattern_id = await self.vector_memory.store_pattern(
                champion_id=champion_id,
                pattern_type="close",
                content=close,
                context=f"Closing technique {i+1}"
            )
            if pattern_id:
                stored["closes"] += 1

        # Store key phrases
        for i, phrase in enumerate(patterns.get("key_phrases", [])):
            pattern_id = await self.vector_memory.store_pattern(
                champion_id=champion_id,
                pattern_type="key_phrase",
                content=phrase
            )
            if pattern_id:
                stored["key_phrases"] += 1

        # Store success patterns
        for i, pattern in enumerate(patterns.get("success_patterns", [])):
            pattern_id = await self.vector_memory.store_pattern(
                champion_id=champion_id,
                pattern_type="success_pattern",
                content=pattern
            )
            if pattern_id:
                stored["success_patterns"] += 1

        return stored

    async def get_champion_patterns(self, champion_id: int) -> list[dict]:
        """Get all patterns for a champion."""
        return await self.vector_memory.get_patterns_by_champion(champion_id)

    async def find_relevant_patterns(
        self,
        query: str,
        champion_id: Optional[int] = None,
        pattern_type: Optional[str] = None,
        limit: int = 5
    ) -> list[dict]:
        """Find patterns relevant to a query."""
        return await self.vector_memory.find_similar_patterns(
            query=query,
            champion_id=champion_id,
            pattern_type=pattern_type,
            limit=limit
        )

    async def get_stats(self) -> dict:
        """Get memory statistics."""
        return await self.vector_memory.get_stats()
