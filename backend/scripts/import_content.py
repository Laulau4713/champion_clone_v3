#!/usr/bin/env python3
"""
Import pedagogical content from JSON files.

Usage:
    python scripts/import_content.py /path/to/content/

The content directory must contain:
  - skills.json
  - difficulty_levels.json
  - sectors.json
  - courses.json
  - quizzes.json
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from database import AsyncSessionLocal as async_session_maker
from models import Skill, DifficultyLevel, Sector, Course, Quiz


async def import_skills(content_dir: Path):
    """Import skills from JSON file."""
    file_path = content_dir / "skills.json"
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    async with async_session_maker() as db:
        for skill_data in data.get("skills", []):
            # Check if already exists
            existing = await db.scalar(
                select(Skill).where(Skill.slug == skill_data.get("id", skill_data.get("slug")))
            )

            if existing:
                print(f"  ⏭️  Skill exists: {skill_data.get('id', skill_data.get('slug'))}")
                continue

            skill = Skill(
                slug=skill_data.get("id", skill_data.get("slug")),
                name=skill_data["name"],
                level=skill_data["level"],
                description=skill_data.get("description", ""),
                order=skill_data.get("order", 0),
                theory_duration_minutes=skill_data.get("theory_duration_minutes", 5),
                practice_duration_minutes=skill_data.get("practice_duration_minutes", 15),
                learning_objectives=skill_data.get("learning_objectives", []),
                key_concepts=skill_data.get("key_concepts", []),
                evaluation_criteria=skill_data.get("evaluation_criteria", []),
                pass_threshold=skill_data.get("pass_threshold", 65),
                scenarios_required=skill_data.get("scenarios_required", 3),
                prospect_instructions=skill_data.get("prospect_instructions", ""),
                emotional_focus=skill_data.get("emotional_focus", []),
                common_mistakes=skill_data.get("common_mistakes", [])
            )
            db.add(skill)
            count += 1
            print(f"  ✅ Skill added: {skill_data.get('id', skill_data.get('slug'))}")

        await db.commit()

    return count


async def import_difficulty_levels(content_dir: Path):
    """Import difficulty levels from JSON file."""
    file_path = content_dir / "difficulty_levels.json"
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    async with async_session_maker() as db:
        for level_data in data.get("difficulty_levels", []):
            existing = await db.scalar(
                select(DifficultyLevel).where(DifficultyLevel.level == level_data["level"])
            )

            if existing:
                print(f"  ⏭️  Level exists: {level_data['level']}")
                continue

            days_range = level_data.get("days_range", [1, 30])

            level = DifficultyLevel(
                level=level_data["level"],
                name=level_data["name"],
                description=level_data.get("description", ""),
                days_range_start=days_range[0] if isinstance(days_range, list) else 1,
                days_range_end=days_range[1] if isinstance(days_range, list) else 30,
                ai_behavior=level_data.get("ai_behavior", {}),
                prospect_personality=level_data.get("prospect_personality", {}),
                conversation_dynamics=level_data.get("conversation_dynamics", {}),
                feedback_settings=level_data.get("feedback_settings", {}),
                interruption_phrases=level_data.get("interruption_phrases", [])
            )
            db.add(level)
            count += 1
            print(f"  ✅ Level added: {level_data['level']}")

        await db.commit()

    return count


async def import_sectors(content_dir: Path):
    """Import sectors from JSON file."""
    file_path = content_dir / "sectors.json"
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    async with async_session_maker() as db:
        for sector_data in data.get("sectors", []):
            existing = await db.scalar(
                select(Sector).where(Sector.slug == sector_data["slug"])
            )

            if existing:
                print(f"  ⏭️  Sector exists: {sector_data['slug']}")
                continue

            sector = Sector(
                slug=sector_data["slug"],
                name=sector_data["name"],
                description=sector_data.get("description", ""),
                icon=sector_data.get("icon", "🏢"),
                vocabulary=sector_data.get("vocabulary", []),
                prospect_personas=sector_data.get("prospect_personas", []),
                typical_objections=sector_data.get("typical_objections", []),
                agent_context_prompt=sector_data.get("agent_context_prompt", "")
            )
            db.add(sector)
            count += 1
            print(f"  ✅ Sector added: {sector_data['slug']}")

        await db.commit()

    return count


async def import_courses(content_dir: Path):
    """Import courses from JSON file."""
    file_path = content_dir / "courses.json"
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    async with async_session_maker() as db:
        for course_data in data.get("courses", []):
            existing = await db.scalar(
                select(Course).where(Course.day == course_data["day"])
            )

            if existing:
                print(f"  ⏭️  Course exists: day {course_data['day']}")
                continue

            # Get skill_id if provided
            skill_id = None
            if course_data.get("skill_id"):
                skill = await db.scalar(
                    select(Skill).where(Skill.slug == course_data["skill_id"])
                )
                skill_id = skill.id if skill else None

            course = Course(
                day=course_data["day"],
                level=course_data["level"],
                skill_id=skill_id,
                title=course_data["title"],
                objective=course_data.get("objective", ""),
                duration_minutes=course_data.get("duration_minutes", 5),
                key_points=course_data.get("key_points", []),
                common_mistakes=course_data.get("common_mistakes", []),
                emotional_tips=course_data.get("emotional_tips", []),
                takeaways=course_data.get("takeaways", [])
            )
            db.add(course)
            count += 1
            print(f"  ✅ Course added: day {course_data['day']}")

        await db.commit()

    return count


async def import_quizzes(content_dir: Path):
    """Import quizzes from JSON file."""
    file_path = content_dir / "quizzes.json"
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    async with async_session_maker() as db:
        for quiz_data in data.get("quizzes", []):
            # Get skill
            skill = await db.scalar(
                select(Skill).where(Skill.slug == quiz_data["skill_id"])
            )

            if not skill:
                print(f"  ⚠️  Skill not found: {quiz_data['skill_id']}")
                continue

            existing = await db.scalar(
                select(Quiz).where(Quiz.skill_id == skill.id)
            )

            if existing:
                print(f"  ⏭️  Quiz exists: {quiz_data['skill_id']}")
                continue

            quiz = Quiz(
                skill_id=skill.id,
                questions=quiz_data["questions"]
            )
            db.add(quiz)
            count += 1
            print(f"  ✅ Quiz added: {quiz_data['skill_id']}")

        await db.commit()

    return count


async def verify_import():
    """Verify import counts."""
    from sqlalchemy import func

    async with async_session_maker() as db:
        skills = await db.scalar(select(func.count(Skill.id)))
        sectors = await db.scalar(select(func.count(Sector.id)))
        courses = await db.scalar(select(func.count(Course.id)))
        quizzes = await db.scalar(select(func.count(Quiz.id)))
        levels = await db.scalar(select(func.count(DifficultyLevel.id)))

        print(f"\n📊 VERIFICATION:")
        print(f"   Skills: {skills}")
        print(f"   Sectors: {sectors}")
        print(f"   Courses: {courses}")
        print(f"   Quizzes: {quizzes}")
        print(f"   Levels: {levels}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_content.py /path/to/content/")
        print("\nThe directory must contain:")
        print("  - skills.json")
        print("  - difficulty_levels.json")
        print("  - sectors.json")
        print("  - courses.json")
        print("  - quizzes.json")
        sys.exit(1)

    content_dir = Path(sys.argv[1])

    if not content_dir.exists():
        print(f"❌ Directory not found: {content_dir}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("   PEDAGOGICAL CONTENT IMPORT")
    print("=" * 50 + "\n")

    print(f"📁 Source: {content_dir}\n")

    print("📚 Importing skills...")
    skills_count = await import_skills(content_dir)
    print(f"   → {skills_count} skills imported\n")

    print("🎚️  Importing difficulty levels...")
    levels_count = await import_difficulty_levels(content_dir)
    print(f"   → {levels_count} levels imported\n")

    print("🏢 Importing sectors...")
    sectors_count = await import_sectors(content_dir)
    print(f"   → {sectors_count} sectors imported\n")

    print("📖 Importing courses...")
    courses_count = await import_courses(content_dir)
    print(f"   → {courses_count} courses imported\n")

    print("❓ Importing quizzes...")
    quizzes_count = await import_quizzes(content_dir)
    print(f"   → {quizzes_count} quizzes imported")

    await verify_import()

    print("\n" + "=" * 50)
    print("   ✅ IMPORT COMPLETE")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
