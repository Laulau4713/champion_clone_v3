"""
Tools and utilities for ContentAgent.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Course, Quiz, Sector, Skill


class ContentTools:
    """Utility tools for ContentAgent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_skill_by_slug(self, slug: str) -> Skill | None:
        """Get a skill by its slug."""
        return await self.db.scalar(select(Skill).where(Skill.slug == slug))

    async def get_skill_by_id(self, skill_id: int) -> Skill | None:
        """Get a skill by its ID."""
        return await self.db.get(Skill, skill_id)

    async def get_sector_by_slug(self, slug: str) -> Sector | None:
        """Get a sector by its slug."""
        return await self.db.scalar(select(Sector).where(Sector.slug == slug))

    async def get_sector_by_id(self, sector_id: int) -> Sector | None:
        """Get a sector by its ID."""
        return await self.db.get(Sector, sector_id)

    async def get_course_for_day(self, day: int) -> Course | None:
        """Get the course for a given day."""
        return await self.db.scalar(select(Course).where(Course.day == day))

    async def get_quiz_for_skill(self, skill_id: int) -> Quiz | None:
        """Get the quiz for a skill."""
        return await self.db.scalar(select(Quiz).where(Quiz.skill_id == skill_id))

    async def get_skills_for_level(self, level: str) -> list[Skill]:
        """Get all skills for a level."""
        result = await self.db.execute(select(Skill).where(Skill.level == level).order_by(Skill.order))
        return list(result.scalars().all())

    async def get_all_skills(self) -> list[Skill]:
        """Get all skills ordered by level and order."""
        result = await self.db.execute(select(Skill).order_by(Skill.level, Skill.order))
        return list(result.scalars().all())

    async def get_all_sectors(self) -> list[Sector]:
        """Get all sectors."""
        result = await self.db.execute(select(Sector).order_by(Sector.name))
        return list(result.scalars().all())

    async def get_courses_for_level(self, level: str) -> list[Course]:
        """Get all courses for a level."""
        result = await self.db.execute(select(Course).where(Course.level == level).order_by(Course.day))
        return list(result.scalars().all())
