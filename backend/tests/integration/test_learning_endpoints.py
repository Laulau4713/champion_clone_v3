"""Tests d'integration pour les endpoints /learning."""
import pytest
import pytest_asyncio
import json
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Skill, Sector, Course, Quiz, DifficultyLevel


# ===================================================================
# FIXTURES
# ===================================================================

@pytest_asyncio.fixture(scope="function")
async def learning_content(db_session: AsyncSession):
    """Charge le contenu pedagogique dans la DB de test."""
    content_dir = Path(__file__).parent.parent.parent / "content"

    # Import skills
    skills_path = content_dir / "skills.json"
    if skills_path.exists():
        with open(skills_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for skill_data in data.get("skills", [])[:5]:  # Only first 5 for tests
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
            db_session.add(skill)

    # Import sectors
    sectors_path = content_dir / "sectors.json"
    if sectors_path.exists():
        with open(sectors_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for sector_data in data.get("sectors", [])[:3]:  # Only first 3 for tests
            sector = Sector(
                slug=sector_data["slug"],
                name=sector_data["name"],
                description=sector_data.get("description", ""),
                icon=sector_data.get("icon", ""),
                vocabulary=sector_data.get("vocabulary", []),
                prospect_personas=sector_data.get("prospect_personas", []),
                typical_objections=sector_data.get("typical_objections", []),
                agent_context_prompt=sector_data.get("agent_context_prompt", "")
            )
            db_session.add(sector)

    # Import difficulty levels
    levels_path = content_dir / "difficulty_levels.json"
    if levels_path.exists():
        with open(levels_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for level_data in data.get("difficulty_levels", []):
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
            db_session.add(level)

    # Import courses
    courses_path = content_dir / "courses.json"
    if courses_path.exists():
        with open(courses_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for course_data in data.get("courses", [])[:5]:  # Only first 5 for tests
            course = Course(
                day=course_data["day"],
                level=course_data["level"],
                skill_id=None,  # Simplified for tests
                title=course_data["title"],
                objective=course_data.get("objective", ""),
                duration_minutes=course_data.get("duration_minutes", 5),
                key_points=course_data.get("key_points", []),
                common_mistakes=course_data.get("common_mistakes", []),
                emotional_tips=course_data.get("emotional_tips", []),
                takeaways=course_data.get("takeaways", [])
            )
            db_session.add(course)

    await db_session.commit()

    # Now add quizzes (after skills are committed)
    quizzes_path = content_dir / "quizzes.json"
    if quizzes_path.exists():
        with open(quizzes_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for quiz_data in data.get("quizzes", [])[:3]:  # Only first 3 for tests
            from sqlalchemy import select
            skill = await db_session.scalar(
                select(Skill).where(Skill.slug == quiz_data["skill_id"])
            )
            if skill:
                quiz = Quiz(
                    skill_id=skill.id,
                    questions=quiz_data["questions"]
                )
                db_session.add(quiz)

        await db_session.commit()

    yield


# ===================================================================
# TESTS ENDPOINTS PUBLICS
# ===================================================================

class TestLearningEndpointsPublic:
    """Tests des endpoints publics (sans auth)."""

    @pytest.mark.asyncio
    async def test_get_skills(self, client: AsyncClient, learning_content):
        """GET /learning/skills retourne tous les skills."""
        response = await client.get("/learning/skills")

        assert response.status_code == 200
        skills = response.json()
        assert len(skills) >= 1

        # Verifier la structure
        skill = skills[0]
        assert "id" in skill
        assert "slug" in skill
        assert "name" in skill
        assert "level" in skill

    @pytest.mark.asyncio
    async def test_get_skills_filtered_by_level(self, client: AsyncClient, learning_content):
        """GET /learning/skills?level=easy filtre par niveau."""
        response = await client.get("/learning/skills?level=easy")

        assert response.status_code == 200
        skills = response.json()
        assert all(s["level"] == "easy" for s in skills)

    @pytest.mark.asyncio
    async def test_get_skill_by_slug(self, client: AsyncClient, learning_content):
        """GET /learning/skills/{slug} retourne le detail."""
        # Get first skill
        skills_response = await client.get("/learning/skills")
        skills = skills_response.json()
        if not skills:
            pytest.skip("No skills in database")

        slug = skills[0]["slug"]
        response = await client.get(f"/learning/skills/{slug}")

        assert response.status_code == 200
        skill = response.json()
        assert skill["slug"] == slug
        assert "name" in skill

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client: AsyncClient, learning_content):
        """GET /learning/skills/{slug} retourne 404 si non trouve."""
        response = await client.get("/learning/skills/unknown_skill_xyz")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sectors(self, client: AsyncClient, learning_content):
        """GET /learning/sectors retourne tous les secteurs."""
        response = await client.get("/learning/sectors")

        assert response.status_code == 200
        sectors = response.json()
        assert len(sectors) >= 1

    @pytest.mark.asyncio
    async def test_get_sector_detail(self, client: AsyncClient, learning_content):
        """GET /learning/sectors/{slug} retourne le detail."""
        # Get first sector
        sectors_response = await client.get("/learning/sectors")
        sectors = sectors_response.json()
        if not sectors:
            pytest.skip("No sectors in database")

        slug = sectors[0]["slug"]
        response = await client.get(f"/learning/sectors/{slug}")

        assert response.status_code == 200
        sector = response.json()
        assert sector["slug"] == slug
        assert "name" in sector

    @pytest.mark.asyncio
    async def test_get_sector_not_found(self, client: AsyncClient, learning_content):
        """GET /learning/sectors/{slug} retourne 404 si non trouve."""
        response = await client.get("/learning/sectors/unknown_sector")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_courses(self, client: AsyncClient, learning_content):
        """GET /learning/courses retourne tous les cours."""
        response = await client.get("/learning/courses")

        assert response.status_code == 200
        courses = response.json()
        assert len(courses) >= 1

    @pytest.mark.asyncio
    async def test_get_course_by_day(self, client: AsyncClient, learning_content):
        """GET /learning/courses/day/{day} retourne le cours."""
        response = await client.get("/learning/courses/day/1")

        assert response.status_code == 200
        course = response.json()
        assert course["day"] == 1
        assert "title" in course

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, client: AsyncClient, learning_content):
        """GET /learning/courses/day/{day} retourne 404 si non trouve."""
        response = await client.get("/learning/courses/day/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_difficulty_levels(self, client: AsyncClient, learning_content):
        """GET /learning/difficulty-levels retourne les niveaux."""
        response = await client.get("/learning/difficulty-levels")

        assert response.status_code == 200
        levels = response.json()
        assert len(levels) == 3  # easy, medium, expert

    @pytest.mark.asyncio
    async def test_get_quiz(self, client: AsyncClient, learning_content):
        """GET /learning/quiz/{skill_slug} retourne le quiz sans reponses."""
        # Get first skill with quiz
        skills_response = await client.get("/learning/skills")
        skills = skills_response.json()
        if not skills:
            pytest.skip("No skills in database")

        for skill in skills:
            response = await client.get(f"/learning/quiz/{skill['slug']}")
            if response.status_code == 200:
                quiz = response.json()
                assert "questions" in quiz

                # Verifier qu'il n'y a pas les reponses
                for q in quiz["questions"]:
                    assert "correct" not in q
                    assert "explanation" not in q
                break
        else:
            pytest.skip("No quizzes in database")


# ===================================================================
# TESTS ENDPOINTS AUTHENTIFIES
# ===================================================================

class TestLearningEndpointsAuth:
    """Tests des endpoints authentifies."""

    @pytest.mark.asyncio
    async def test_get_progress_requires_auth(self, client: AsyncClient, learning_content):
        """GET /learning/progress necessite authentification."""
        response = await client.get("/learning/progress")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_progress_authenticated(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """GET /learning/progress avec auth retourne la progression."""
        response = await client.get("/learning/progress", headers=auth_headers)

        assert response.status_code == 200
        progress = response.json()
        assert "current_level" in progress
        assert "current_day" in progress
        assert "skills_validated" in progress
        assert "skills_total" in progress

    @pytest.mark.asyncio
    async def test_get_skills_progress(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """GET /learning/progress/skills retourne la progression par skill."""
        response = await client.get("/learning/progress/skills", headers=auth_headers)

        assert response.status_code == 200
        skills = response.json()
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_select_sector(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/progress/select-sector selectionne un secteur."""
        # Get first sector
        sectors_response = await client.get("/learning/sectors")
        sectors = sectors_response.json()
        if not sectors:
            pytest.skip("No sectors in database")

        response = await client.post(
            "/learning/progress/select-sector",
            json={"sector_slug": sectors[0]["slug"]},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "sector" in response.json()

    @pytest.mark.asyncio
    async def test_select_sector_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/progress/select-sector avec secteur inexistant."""
        response = await client.post(
            "/learning/progress/select-sector",
            json={"sector_slug": "unknown_sector"},
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_start_session(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/session/start demarre une session."""
        response = await client.post(
            "/learning/session/start",
            headers=auth_headers
        )

        assert response.status_code == 200
        session = response.json()
        assert "session_id" in session
        assert "day" in session
        assert "course" in session

    @pytest.mark.asyncio
    async def test_complete_course(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/session/{id}/complete-course marque le cours lu."""
        # D'abord demarrer une session
        start_response = await client.post(
            "/learning/session/start",
            headers=auth_headers
        )
        session_id = start_response.json()["session_id"]

        # Marquer le cours comme lu
        response = await client.post(
            f"/learning/session/{session_id}/complete-course",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_complete_course_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/session/{id}/complete-course avec session inexistante."""
        response = await client.post(
            "/learning/session/9999/complete-course",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_listen_script(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/session/{id}/listen-script incremente le compteur."""
        # D'abord demarrer une session
        start_response = await client.post(
            "/learning/session/start",
            headers=auth_headers
        )
        session_id = start_response.json()["session_id"]

        # Ecouter un script
        response = await client.post(
            f"/learning/session/{session_id}/listen-script",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["scripts_listened"] == 1

    @pytest.mark.asyncio
    async def test_submit_quiz(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/quiz/{slug}/submit soumet le quiz."""
        # Get first skill with quiz
        skills_response = await client.get("/learning/skills")
        skills = skills_response.json()

        for skill in skills:
            quiz_response = await client.get(f"/learning/quiz/{skill['slug']}")
            if quiz_response.status_code == 200:
                quiz = quiz_response.json()
                num_questions = len(quiz["questions"])

                # Submit with answers
                answers = ["A"] * num_questions  # All A's
                response = await client.post(
                    f"/learning/quiz/{skill['slug']}/submit",
                    json={"answers": answers},
                    headers=auth_headers
                )

                assert response.status_code == 200
                result = response.json()
                assert "score" in result
                assert "passed" in result
                assert "correct_count" in result
                assert "details" in result
                break
        else:
            pytest.skip("No quizzes in database")

    @pytest.mark.asyncio
    async def test_submit_quiz_wrong_count(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """POST /learning/quiz/{slug}/submit avec mauvais nombre de reponses."""
        # Get first skill with quiz
        skills_response = await client.get("/learning/skills")
        skills = skills_response.json()

        for skill in skills:
            quiz_response = await client.get(f"/learning/quiz/{skill['slug']}")
            if quiz_response.status_code == 200:
                response = await client.post(
                    f"/learning/quiz/{skill['slug']}/submit",
                    json={"answers": ["A", "B"]},  # Wrong number
                    headers=auth_headers
                )

                assert response.status_code == 400
                break
        else:
            pytest.skip("No quizzes in database")

    @pytest.mark.asyncio
    async def test_get_today_session(
        self,
        client: AsyncClient,
        auth_headers: dict,
        learning_content
    ):
        """GET /learning/session/today retourne la session du jour."""
        # D'abord creer une session
        await client.post("/learning/session/start", headers=auth_headers)

        response = await client.get("/learning/session/today", headers=auth_headers)

        assert response.status_code == 200


# ===================================================================
# TESTS SECURITE
# ===================================================================

class TestLearningEndpointsSecurity:
    """Tests de securite des endpoints."""

    @pytest.mark.asyncio
    async def test_progress_requires_auth(self, client: AsyncClient, learning_content):
        """GET /learning/progress necessite authentification."""
        response = await client.get("/learning/progress")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_progress_skills_requires_auth(self, client: AsyncClient, learning_content):
        """GET /learning/progress/skills necessite authentification."""
        response = await client.get("/learning/progress/skills")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_select_sector_requires_auth(self, client: AsyncClient, learning_content):
        """POST /learning/progress/select-sector necessite authentification."""
        response = await client.post(
            "/learning/progress/select-sector",
            json={"sector_slug": "immo"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_start_requires_auth(self, client: AsyncClient, learning_content):
        """POST /learning/session/start necessite authentification."""
        response = await client.post("/learning/session/start")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_complete_requires_auth(self, client: AsyncClient, learning_content):
        """POST /learning/session/{id}/complete-course necessite authentification."""
        response = await client.post("/learning/session/1/complete-course")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_today_requires_auth(self, client: AsyncClient, learning_content):
        """GET /learning/session/today necessite authentification."""
        response = await client.get("/learning/session/today")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_quiz_submit_requires_auth(self, client: AsyncClient, learning_content):
        """POST /learning/quiz/{slug}/submit necessite authentification."""
        response = await client.post(
            "/learning/quiz/ecoute_active/submit",
            json={"answers": ["A"]}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient, learning_content):
        """Token invalide retourne 401."""
        response = await client.get(
            "/learning/progress",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
