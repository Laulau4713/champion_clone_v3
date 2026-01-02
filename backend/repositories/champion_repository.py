"""
Champion Repository.

Database operations for Champion model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AnalysisLog, Champion
from repositories.base import BaseRepository


class ChampionRepository(BaseRepository[Champion]):
    """Repository for Champion model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Champion)

    async def get_by_status(self, status: str) -> list[Champion]:
        """Get all champions with a specific status."""
        result = await self.session.execute(
            select(Champion).where(Champion.status == status).order_by(Champion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_ordered(self, status: str | None = None) -> list[Champion]:
        """Get all champions ordered by creation date, optionally filtered by status."""
        query = select(Champion).order_by(Champion.created_at.desc())

        if status:
            query = query.where(Champion.status == status)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_ready_champion(self, champion_id: int) -> Champion | None:
        """Get a champion that has been analyzed and is ready for training."""
        result = await self.session.execute(
            select(Champion).where(Champion.id == champion_id, Champion.patterns_json.isnot(None))
        )
        return result.scalar_one_or_none()


class AnalysisLogRepository(BaseRepository[AnalysisLog]):
    """Repository for AnalysisLog model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AnalysisLog)

    async def get_champion_logs(self, champion_id: int) -> list[AnalysisLog]:
        """Get all logs for a champion."""
        result = await self.session.execute(
            select(AnalysisLog).where(AnalysisLog.champion_id == champion_id).order_by(AnalysisLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def log_step(
        self, champion_id: int, step: str, status: str, details: dict = None, error_message: str = None
    ) -> AnalysisLog:
        """Create a new analysis log entry."""
        log = AnalysisLog(
            champion_id=champion_id, step=step, status=status, details=details, error_message=error_message
        )
        return await self.create(log)
