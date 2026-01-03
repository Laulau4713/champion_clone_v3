"""
ContentAgent - Generates and adapts pedagogical content.

Responsible for:
- Generating training scenarios adapted to skills and sectors
- Personalizing difficulty based on user performance
- Generating example scripts (good and bad examples)
- Caching scenarios for performance
"""

import hashlib
import json
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CachedScenario, Sector, Skill

from .prompts import EXAMPLE_SCRIPT_PROMPT, SCENARIO_GENERATION_PROMPT, SECTOR_ADAPTATION_PROMPT

logger = structlog.get_logger()


class ContentAgent:
    """
    Agent responsible for generating and adapting pedagogical content.

    - Generates training scenarios adapted to skills
    - Personalizes according to business sector
    - Generates example scripts
    - Uses cache to avoid regeneration
    """

    def __init__(self, db: AsyncSession, llm_client=None):
        self.db = db
        self.llm = llm_client  # Claude or Ollama
        self._current_level = "intermediate"  # Track current level for default scenario
        logger.info("content_agent_initialized")

    def _generate_cache_key(self, skill_id: int, level: str, sector_id: int | None = None, variant: int = 0) -> str:
        """Generate a unique cache key."""
        content = f"{skill_id}|{level}|{sector_id}|{variant}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def generate_scenario(
        self,
        skill: Skill,
        level: str,
        sector: Sector | None = None,
        user_history: dict | None = None,
        use_cache: bool = True,
    ) -> dict:
        """
        Generate an adapted training scenario.
        Uses cache if available.

        Args:
            skill: The skill to practice
            level: Difficulty level (beginner, intermediate, advanced)
            sector: Optional business sector for adaptation
            user_history: Optional user performance history
            use_cache: Whether to use/store in cache

        Returns:
            Generated scenario dictionary
        """
        sector_id = sector.id if sector else None

        # Store current level for default scenario fallback
        self._current_level = level

        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(skill.id, level, sector_id)
            cached = await self.db.scalar(select(CachedScenario).where(CachedScenario.cache_key == cache_key))
            if cached:
                cached.use_count += 1
                cached.last_used_at = datetime.utcnow()
                await self.db.commit()
                logger.info("scenario_cache_hit", cache_key=cache_key, use_count=cached.use_count)
                return cached.scenario_json

        # Generate the scenario
        evaluation_criteria = ""
        if skill.evaluation_criteria:
            evaluation_criteria = "\n".join(
                [
                    f"- {c.get('name', 'Critère')} ({c.get('weight', 0)}%): {c.get('description', '')}"
                    for c in skill.evaluation_criteria
                ]
            )

        prompt = SCENARIO_GENERATION_PROMPT.format(
            skill_name=skill.name,
            level=level,
            sector_name=sector.name if sector else "Générique",
            skill_description=skill.description,
            evaluation_criteria=evaluation_criteria,
            prospect_instructions=skill.prospect_instructions or "",
            user_history=json.dumps(user_history, ensure_ascii=False) if user_history else "Aucun",
        )

        # Call LLM
        response = await self._call_llm(prompt)
        scenario = self._parse_json_response(response)

        # Adapt to sector if specified
        if sector:
            scenario = await self._adapt_to_sector(scenario, sector)

        # Store in cache
        if use_cache:
            cache_key = self._generate_cache_key(skill.id, level, sector_id)
            cache_entry = CachedScenario(
                cache_key=cache_key, skill_id=skill.id, sector_id=sector_id, level=level, scenario_json=scenario
            )
            self.db.add(cache_entry)
            await self.db.commit()
            logger.info("scenario_cached", cache_key=cache_key)

        return scenario

    async def _adapt_to_sector(self, base_scenario: dict, sector: Sector) -> dict:
        """Adapt a scenario to a specific sector."""
        vocabulary = ""
        if sector.vocabulary:
            vocabulary = ", ".join([v.get("term", "") for v in sector.vocabulary[:10]])

        objections = ""
        if sector.typical_objections:
            objections = "\n".join([f"- {o.get('objection', '')}" for o in sector.typical_objections[:5]])

        personas = ""
        if sector.prospect_personas:
            personas = "\n".join(
                [f"- {p.get('name', '')}: {p.get('description', '')}" for p in sector.prospect_personas[:3]]
            )

        prompt = SECTOR_ADAPTATION_PROMPT.format(
            sector_name=sector.name,
            base_scenario=json.dumps(base_scenario, ensure_ascii=False),
            vocabulary=vocabulary,
            typical_objections=objections,
            prospect_personas=personas,
            agent_context_prompt=sector.agent_context_prompt or "",
        )

        response = await self._call_llm(prompt)
        return self._parse_json_response(response)

    async def generate_example_script(
        self, skill: Skill, sector: Sector | None = None, good_example: bool = True
    ) -> dict:
        """
        Generate an example script (good or bad).

        Args:
            skill: The skill to demonstrate
            sector: Optional sector context
            good_example: True for good example, False for bad

        Returns:
            Script dictionary with dialogue and annotations
        """
        prompt = EXAMPLE_SCRIPT_PROMPT.format(
            skill_name=skill.name,
            skill_description=skill.description,
            sector_context=sector.agent_context_prompt if sector else "Contexte générique",
            script_type="BON" if good_example else "MAUVAIS",
            script_type_description="BON exemple (à suivre)" if good_example else "MAUVAIS exemple (à éviter)",
        )

        response = await self._call_llm(prompt)
        return self._parse_json_response(response)

    async def personalize_difficulty(self, base_scenario: dict, user_stats: dict) -> dict:
        """
        Adjust difficulty based on user performance.

        Args:
            base_scenario: The base scenario to adjust
            user_stats: User performance statistics

        Returns:
            Adjusted scenario
        """
        avg_score = user_stats.get("average_score", 70)

        # Adjust prospect difficulty
        if avg_score > 85:
            # Excellent student → harder
            base_scenario["prospect"]["mood"] = "skeptical"
            base_scenario["prospect"]["personality"] = "analytical"
            base_scenario["difficulty_score"] = min(100, base_scenario.get("difficulty_score", 50) + 20)
            logger.info("difficulty_increased", avg_score=avg_score)
        elif avg_score < 50:
            # Struggling student → easier
            base_scenario["prospect"]["mood"] = "curious"
            base_scenario["prospect"]["personality"] = "friendly"
            base_scenario["difficulty_score"] = max(20, base_scenario.get("difficulty_score", 50) - 20)
            logger.info("difficulty_decreased", avg_score=avg_score)

        return base_scenario

    async def get_scenario_variants(
        self, skill: Skill, level: str, sector: Sector | None = None, count: int = 3
    ) -> list[dict]:
        """
        Generate multiple scenario variants for variety.

        Args:
            skill: The skill to practice
            level: Difficulty level
            sector: Optional sector
            count: Number of variants to generate

        Returns:
            List of scenario variants
        """
        variants = []
        for i in range(count):
            # Generate with different cache keys (variant number)
            scenario = await self.generate_scenario(
                skill=skill,
                level=level,
                sector=sector,
                use_cache=False,  # Don't cache variants
            )
            variants.append(scenario)

        return variants

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM (Claude or Ollama)."""
        if self.llm:
            # Use injected LLM client
            try:
                return await self.llm.generate(prompt)
            except Exception as e:
                logger.error("llm_call_error", error=str(e))
                return self._get_default_scenario_json(self._current_level)
        else:
            # Fallback: return default template
            logger.warning("no_llm_client_using_default")
            return self._get_default_scenario_json(self._current_level)

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON response from LLM."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e))
            return self._get_default_scenario(self._current_level)

    def _get_default_scenario_json(self, level: str = "intermediate") -> str:
        """Return default scenario as JSON string."""
        return json.dumps(self._get_default_scenario(level), ensure_ascii=False)

    def _get_default_scenario(self, level: str = "intermediate") -> dict:
        """
        Default scenario if generation fails.
        Adapts personality based on difficulty level for voice selection.

        Level mapping:
        - beginner: friendly, curious prospect (FRIENDLY voice)
        - intermediate: neutral, professional prospect (NEUTRAL voice)
        - advanced/expert: skeptical, busy, aggressive prospect (AGGRESSIVE voice)
        """
        # Adapt personality and mood based on level
        if level in ("beginner", "easy"):
            personality = "friendly"
            mood = "open"
            opening = (
                "Bonjour ! Merci de me rappeler. J'ai vu votre solution et je suis vraiment curieux d'en savoir plus !"
            )
            difficulty_score = 30
        elif level in ("advanced", "expert", "hard"):
            personality = "skeptical"
            mood = "busy"
            opening = "Oui ? J'ai très peu de temps, on m'a transféré votre appel. C'est pour quoi exactement ?"
            difficulty_score = 80
        else:  # intermediate
            personality = "neutral"
            mood = "professional"
            opening = "Bonjour. On m'a parlé de votre solution. Pouvez-vous me présenter ce que vous proposez ?"
            difficulty_score = 50

        return {
            "title": "Scénario de découverte",
            "prospect": {
                "name": "Marie Martin",
                "role": "Directrice Marketing",
                "company": "TechStart",
                "personality": personality,
                "mood": mood,
                "pain_points": ["manque de temps", "budget serré", "équipe réduite"],
                "hidden_need": "Cherche à automatiser les tâches répétitives",
                "budget_situation": "flexible",
                "decision_power": "decides",
            },
            "context": "Premier appel de découverte suite à une demande sur le site. Marie a téléchargé un livre blanc sur l'automatisation marketing.",
            "opening_message": opening,
            "solution": {
                "product_name": "MarketAuto Pro",
                "value_proposition": "Automatisez 80% de vos tâches marketing répétitives et gagnez 20h par semaine",
                "key_benefits": [
                    "Libère 20+ heures par semaine pour votre équipe",
                    "Augmente le volume de leads qualifiés de 40%",
                    "Interface intuitive, prise en main en 2 jours",
                ],
                "pricing_hint": "À partir de 199€/mois - ROI positif dès le 2ème mois",
                "differentiator": "Seule solution avec IA intégrée qui s'adapte à votre secteur",
            },
            "product_pitch": "Marie, d'après ce que vous me décrivez, votre équipe passe beaucoup de temps sur des tâches répétitives. MarketAuto Pro automatise tout ça : emailing, segmentation, reporting. Concrètement, avec une équipe de 3 personnes comme la vôtre, vous récupéreriez entre 15 et 20 heures par semaine. Et le meilleur ? Nos clients voient un ROI positif dès le deuxième mois.",
            "key_moments": [
                "Découverte des besoins réels",
                "Gestion de l'objection budget",
                "Qualification du décideur",
            ],
            "success_criteria": [
                "Identifier le besoin principal",
                "Comprendre le contexte de l'entreprise",
                "Obtenir un RDV de démo",
            ],
            "difficulty_score": difficulty_score,
        }
