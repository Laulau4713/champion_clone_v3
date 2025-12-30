"""Tests pour ContentAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from agents.content_agent.agent import ContentAgent


class TestContentAgent:
    """Tests du ContentAgent."""

    @pytest.fixture
    def mock_db(self):
        """Mock de session DB."""
        db = AsyncMock()
        db.scalar = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def mock_skill(self):
        """Mock de Skill."""
        skill = MagicMock()
        skill.id = 1
        skill.slug = "ecoute_active"
        skill.name = "Ecoute Active"
        skill.description = "Capacite a ecouter le prospect"
        skill.evaluation_criteria = [
            {"name": "Signaux d'ecoute", "weight": 20, "description": "Test"},
            {"name": "Retention", "weight": 25, "description": "Test"}
        ]
        skill.prospect_instructions = "Tu es un prospect curieux"
        return skill

    @pytest.fixture
    def mock_sector(self):
        """Mock de Sector."""
        sector = MagicMock()
        sector.id = 1
        sector.slug = "immo"
        sector.name = "Immobilier"
        sector.vocabulary = [{"term": "DPE", "definition": "Diagnostic"}]
        sector.typical_objections = [{"objection": "C'est cher"}]
        sector.prospect_personas = [{"name": "Primo-accedant", "description": "Test"}]
        sector.agent_context_prompt = "Contexte immo"
        return sector

    @pytest.fixture
    def agent(self, mock_db):
        return ContentAgent(db=mock_db, llm_client=None)

    # ===================================================================
    # TESTS CACHE KEY
    # ===================================================================

    def test_generate_cache_key_unique(self, agent):
        """Cache key doit etre unique par combinaison."""
        key1 = agent._generate_cache_key(1, "easy", None, 0)
        key2 = agent._generate_cache_key(1, "medium", None, 0)
        key3 = agent._generate_cache_key(2, "easy", None, 0)
        key4 = agent._generate_cache_key(1, "easy", 1, 0)

        assert key1 != key2
        assert key1 != key3
        assert key1 != key4

    def test_generate_cache_key_deterministic(self, agent):
        """Cache key doit etre deterministe."""
        key1 = agent._generate_cache_key(1, "easy", None, 0)
        key2 = agent._generate_cache_key(1, "easy", None, 0)

        assert key1 == key2

    def test_cache_key_length(self, agent):
        """Cache key doit avoir 16 caracteres."""
        key = agent._generate_cache_key(1, "easy", None, 0)
        assert len(key) == 16

    def test_cache_key_with_sector(self, agent):
        """Cache key avec secteur."""
        key_without = agent._generate_cache_key(1, "easy", None, 0)
        key_with = agent._generate_cache_key(1, "easy", 1, 0)

        assert key_without != key_with

    # ===================================================================
    # TESTS JSON PARSING
    # ===================================================================

    def test_parse_json_response_valid(self, agent):
        """Parser JSON valide."""
        response = '{"title": "Test", "value": 123}'
        result = agent._parse_json_response(response)

        assert result["title"] == "Test"
        assert result["value"] == 123

    def test_parse_json_response_with_markdown(self, agent):
        """Parser JSON avec backticks markdown."""
        response = '```json\n{"title": "Test"}\n```'
        result = agent._parse_json_response(response)

        assert result["title"] == "Test"

    def test_parse_json_response_with_markdown_no_json(self, agent):
        """Parser JSON avec backticks sans 'json'."""
        response = '```\n{"title": "Test"}\n```'
        result = agent._parse_json_response(response)

        assert result["title"] == "Test"

    def test_parse_json_response_invalid(self, agent):
        """Parser JSON invalide retourne default."""
        response = "This is not JSON"
        result = agent._parse_json_response(response)

        # Doit retourner le scenario par defaut
        assert "title" in result
        assert "prospect" in result

    def test_parse_json_response_empty(self, agent):
        """Parser JSON vide."""
        response = ""
        result = agent._parse_json_response(response)

        assert "title" in result  # Scenario par defaut

    # ===================================================================
    # TESTS DEFAULT SCENARIO
    # ===================================================================

    def test_default_scenario_structure(self, agent):
        """Verifier la structure du scenario par defaut."""
        scenario = agent._get_default_scenario()

        assert "title" in scenario
        assert "prospect" in scenario
        assert "context" in scenario
        assert "opening_message" in scenario

        prospect = scenario["prospect"]
        assert "name" in prospect
        assert "role" in prospect
        assert "company" in prospect
        assert "personality" in prospect
        assert "pain_points" in prospect

    def test_default_scenario_json(self, agent):
        """Verifier que le JSON par defaut est valide."""
        scenario_json = agent._get_default_scenario_json()
        scenario = json.loads(scenario_json)

        assert "title" in scenario
        assert "prospect" in scenario

    # ===================================================================
    # TESTS DIFFICULTY PERSONALIZATION
    # ===================================================================

    @pytest.mark.asyncio
    async def test_personalize_difficulty_excellent_student(self, agent):
        """Personnaliser pour eleve excellent -> plus dur."""
        base = {
            "prospect": {"mood": "neutral", "personality": "neutral"},
            "difficulty_score": 50
        }
        stats = {"average_score": 90}

        result = await agent.personalize_difficulty(base, stats)

        assert result["prospect"]["mood"] == "skeptical"
        assert result["difficulty_score"] > 50

    @pytest.mark.asyncio
    async def test_personalize_difficulty_struggling_student(self, agent):
        """Personnaliser pour eleve en difficulte -> plus facile."""
        base = {
            "prospect": {"mood": "neutral", "personality": "neutral"},
            "difficulty_score": 50
        }
        stats = {"average_score": 40}

        result = await agent.personalize_difficulty(base, stats)

        assert result["prospect"]["mood"] == "curious"
        assert result["difficulty_score"] < 50

    @pytest.mark.asyncio
    async def test_personalize_difficulty_average_student(self, agent):
        """Personnaliser pour eleve moyen -> pas de changement."""
        base = {
            "prospect": {"mood": "neutral", "personality": "neutral"},
            "difficulty_score": 50
        }
        stats = {"average_score": 70}

        result = await agent.personalize_difficulty(base, stats)

        assert result["prospect"]["mood"] == "neutral"
        assert result["difficulty_score"] == 50

    @pytest.mark.asyncio
    async def test_personalize_difficulty_clamps_max(self, agent):
        """Score de difficulte ne depasse pas 100."""
        base = {
            "prospect": {"mood": "neutral", "personality": "neutral"},
            "difficulty_score": 95
        }
        stats = {"average_score": 95}

        result = await agent.personalize_difficulty(base, stats)

        assert result["difficulty_score"] <= 100

    @pytest.mark.asyncio
    async def test_personalize_difficulty_clamps_min(self, agent):
        """Score de difficulte ne descend pas sous 20."""
        base = {
            "prospect": {"mood": "neutral", "personality": "neutral"},
            "difficulty_score": 25
        }
        stats = {"average_score": 30}

        result = await agent.personalize_difficulty(base, stats)

        assert result["difficulty_score"] >= 20

    # ===================================================================
    # TESTS LLM CALL
    # ===================================================================

    @pytest.mark.asyncio
    async def test_call_llm_with_client(self, mock_db):
        """Appel LLM avec client injecte."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value='{"title": "Test"}')

        agent = ContentAgent(db=mock_db, llm_client=mock_llm)
        result = await agent._call_llm("Test prompt")

        mock_llm.generate.assert_called_once_with("Test prompt")
        assert result == '{"title": "Test"}'

    @pytest.mark.asyncio
    async def test_call_llm_without_client(self, agent):
        """Appel LLM sans client retourne defaut."""
        result = await agent._call_llm("Test prompt")

        # Doit retourner le JSON du scenario par defaut
        scenario = json.loads(result)
        assert "title" in scenario

    @pytest.mark.asyncio
    async def test_call_llm_client_error(self, mock_db):
        """Appel LLM avec erreur retourne defaut."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("API Error"))

        agent = ContentAgent(db=mock_db, llm_client=mock_llm)
        result = await agent._call_llm("Test prompt")

        # Doit retourner le JSON du scenario par defaut
        scenario = json.loads(result)
        assert "title" in scenario

    # ===================================================================
    # TESTS SCENARIO GENERATION
    # ===================================================================

    @pytest.mark.asyncio
    async def test_generate_scenario_uses_cache(self, mock_db, mock_skill):
        """Generation de scenario utilise le cache."""
        # Setup mock cached scenario
        cached = MagicMock()
        cached.scenario_json = {"title": "Cached Scenario"}
        cached.use_count = 0
        mock_db.scalar = AsyncMock(return_value=cached)

        agent = ContentAgent(db=mock_db, llm_client=None)
        result = await agent.generate_scenario(mock_skill, "easy", use_cache=True)

        assert result["title"] == "Cached Scenario"
        assert cached.use_count == 1

    @pytest.mark.asyncio
    async def test_generate_scenario_no_cache(self, mock_db, mock_skill):
        """Generation de scenario sans cache."""
        mock_db.scalar = AsyncMock(return_value=None)

        agent = ContentAgent(db=mock_db, llm_client=None)
        result = await agent.generate_scenario(mock_skill, "easy", use_cache=False)

        # Should return default scenario since no LLM client
        assert "title" in result
        assert "prospect" in result

    @pytest.mark.asyncio
    async def test_generate_scenario_with_sector(
        self, mock_db, mock_skill, mock_sector
    ):
        """Generation de scenario avec secteur."""
        mock_db.scalar = AsyncMock(return_value=None)

        agent = ContentAgent(db=mock_db, llm_client=None)
        result = await agent.generate_scenario(
            mock_skill, "easy", sector=mock_sector, use_cache=False
        )

        assert "title" in result

    # ===================================================================
    # TESTS EXAMPLE SCRIPT
    # ===================================================================

    @pytest.mark.asyncio
    async def test_generate_example_script_good(self, mock_db, mock_skill):
        """Generation script exemple bon."""
        agent = ContentAgent(db=mock_db, llm_client=None)
        result = await agent.generate_example_script(mock_skill, good_example=True)

        assert "title" in result  # Default scenario structure

    @pytest.mark.asyncio
    async def test_generate_example_script_bad(self, mock_db, mock_skill):
        """Generation script exemple mauvais."""
        agent = ContentAgent(db=mock_db, llm_client=None)
        result = await agent.generate_example_script(mock_skill, good_example=False)

        assert "title" in result  # Default scenario structure

    # ===================================================================
    # TESTS VARIANTS
    # ===================================================================

    @pytest.mark.asyncio
    async def test_get_scenario_variants(self, mock_db, mock_skill):
        """Generation de plusieurs variantes."""
        mock_db.scalar = AsyncMock(return_value=None)

        agent = ContentAgent(db=mock_db, llm_client=None)
        variants = await agent.get_scenario_variants(mock_skill, "easy", count=3)

        assert len(variants) == 3
        for v in variants:
            assert "title" in v
