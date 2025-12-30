"""
Pattern Agent Tools - LLM analysis and pattern extraction.

Uses Groq (FREE) with Llama 3.1 70B instead of Claude API.
Can fallback to Anthropic if ANTHROPIC_API_KEY is set and Groq fails.
"""

import os
import json
from typing import Optional
import uuid

import structlog

logger = structlog.get_logger()

# Try to import Groq (FREE)
try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Fallback to Anthropic
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class PatternTools:
    """Collection of pattern extraction tools."""

    EXTRACTION_PROMPT = """Tu es un expert en analyse de vente et coaching commercial.

Analyse ce transcript d'un champion de la vente et extrais ses patterns de succès.

TRANSCRIPT:
{transcript}

---

Analyse en profondeur et retourne un JSON structuré avec:

1. **openings** (array of strings): Les techniques d'ouverture utilisées
   - Comment il/elle établit le rapport
   - Phrases d'accroche
   - Questions initiales

2. **objection_handlers** (array of objects): Gestion des objections
   Chaque objet: {{"objection": "type d'objection", "response": "technique de réponse", "example": "exemple du transcript"}}

3. **closes** (array of strings): Techniques de closing
   - Assumptive close
   - Alternative close
   - Urgence, Social proof

4. **key_phrases** (array of strings): Phrases signature

5. **tone_style** (string): Description du style de communication

6. **success_patterns** (array of strings): Patterns de succès identifiés

7. **communication_techniques** (array of objects): Techniques de communication
   Chaque objet: {{"name": "nom technique", "description": "comment elle est utilisée", "examples": ["exemple1", "exemple2"]}}

Retourne UNIQUEMENT le JSON, sans commentaires ni markdown."""

    SCENARIO_PROMPT = """Tu es un expert en formation commerciale.

Basé sur ces patterns d'un champion de la vente, génère {count} scénarios d'entraînement réalistes.

PATTERNS DU CHAMPION:
{patterns}

---

Pour chaque scénario, fournis:
1. **context**: Contexte business détaillé
2. **prospect_type**: Type de prospect avec personnalité
3. **challenge**: Le défi principal à surmonter
4. **objectives**: 3-4 objectifs d'apprentissage
5. **difficulty**: easy, medium, ou hard
6. **expected_patterns**: Patterns du champion à utiliser dans ce scénario

Retourne un JSON array de scénarios, sans markdown."""

    def __init__(self):
        # Use Groq by default (FREE), fallback to Anthropic
        self.use_groq = GROQ_AVAILABLE and os.getenv("GROQ_API_KEY")
        self.use_anthropic = ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY")

        if self.use_groq:
            self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info("pattern_tools_init", provider="groq", model=self.model)
        elif self.use_anthropic:
            self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("CLAUDE_OPUS_MODEL", "claude-opus-4-20250514")
            logger.info("pattern_tools_init", provider="anthropic", model=self.model)
        else:
            self.client = None
            self.model = None
            logger.warning("pattern_tools_init", msg="No LLM provider available. Set GROQ_API_KEY (free) or ANTHROPIC_API_KEY")

    async def _call_llm(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.3) -> str:
        """Call LLM (Groq or Anthropic) and return text response."""
        if not self.client:
            raise RuntimeError("No LLM provider configured. Set GROQ_API_KEY (free) or ANTHROPIC_API_KEY")

        if self.use_groq:
            # Groq uses OpenAI-compatible API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        else:
            # Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.content[0].text.strip()

    async def extract_patterns(self, transcript: str) -> dict:
        """
        Extract sales patterns from transcript using LLM.

        Args:
            transcript: Full transcript text

        Returns:
            Dict with extracted patterns
        """
        if not transcript or len(transcript.strip()) < 100:
            return {
                "success": False,
                "error": "Transcript too short for meaningful analysis"
            }

        logger.info("extracting_patterns", transcript_length=len(transcript))

        try:
            response_text = await self._call_llm(
                prompt=self.EXTRACTION_PROMPT.format(transcript=transcript),
                max_tokens=4096,
                temperature=0.3
            )

            # Clean JSON from markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            patterns = json.loads(response_text)
            patterns = self._validate_patterns(patterns)

            return {
                "success": True,
                "patterns": patterns,
                "model_used": self.model
            }

        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e))
            return {"success": False, "error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            logger.error("extraction_error", error=str(e))
            return {"success": False, "error": str(e)}

    def _validate_patterns(self, patterns: dict) -> dict:
        """Validate and normalize patterns structure."""
        default = {
            "openings": [],
            "objection_handlers": [],
            "closes": [],
            "key_phrases": [],
            "tone_style": "",
            "success_patterns": [],
            "communication_techniques": []
        }

        validated = {**default, **patterns}

        # Ensure arrays
        for key in ["openings", "objection_handlers", "closes", "key_phrases", "success_patterns", "communication_techniques"]:
            if not isinstance(validated[key], list):
                validated[key] = []

        return validated

    async def generate_scenarios(self, patterns: dict, count: int = 3) -> dict:
        """
        Generate training scenarios from patterns.

        Args:
            patterns: Extracted champion patterns
            count: Number of scenarios to generate

        Returns:
            Dict with scenarios
        """
        logger.info("generating_scenarios", count=count)

        try:
            response_text = await self._call_llm(
                prompt=self.SCENARIO_PROMPT.format(
                    patterns=json.dumps(patterns, ensure_ascii=False, indent=2),
                    count=count
                ),
                max_tokens=4096,
                temperature=0.7
            )

            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            scenarios = json.loads(response_text)
            if not isinstance(scenarios, list):
                scenarios = [scenarios]

            return {
                "success": True,
                "scenarios": [self._validate_scenario(s) for s in scenarios]
            }

        except Exception as e:
            logger.error("scenario_generation_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "scenarios": [self._get_default_scenario()]
            }

    def _validate_scenario(self, scenario: dict) -> dict:
        return {
            "id": str(uuid.uuid4())[:8],
            "context": scenario.get("context", "Situation de vente standard"),
            "prospect_type": scenario.get("prospect_type", "Prospect indécis"),
            "challenge": scenario.get("challenge", "Convaincre le prospect"),
            "objectives": scenario.get("objectives", ["Pratiquer les techniques"]),
            "difficulty": scenario.get("difficulty", "medium"),
            "expected_patterns": scenario.get("expected_patterns", [])
        }

    def _get_default_scenario(self) -> dict:
        return self._validate_scenario({
            "context": "Appel à un prospect qui a téléchargé un livre blanc.",
            "prospect_type": "Responsable marketing d'une PME, curieux mais occupé",
            "challenge": "Obtenir un rendez-vous de découverte",
            "objectives": ["Créer un rapport", "Identifier les besoins", "Obtenir un engagement"],
            "difficulty": "medium"
        })

    async def find_similar_patterns(
        self,
        query: str,
        patterns_db: list[dict],
        limit: int = 5
    ) -> dict:
        """
        Find patterns similar to a query (semantic search simulation).

        Args:
            query: Search query
            patterns_db: List of patterns to search
            limit: Max results

        Returns:
            Dict with similar patterns
        """
        # Simple keyword matching for now
        # In production, this would use vector embeddings
        query_lower = query.lower()
        results = []

        for pattern in patterns_db:
            content = pattern.get("content", "").lower()
            if any(word in content for word in query_lower.split()):
                results.append(pattern)
                if len(results) >= limit:
                    break

        return {
            "success": True,
            "patterns": results,
            "total_found": len(results)
        }

    async def analyze_response_against_patterns(
        self,
        response: str,
        patterns: dict,
        context: str
    ) -> dict:
        """
        Analyze a user response against champion patterns.

        Args:
            response: User's response
            patterns: Champion patterns
            context: Conversation context

        Returns:
            Analysis with score and feedback
        """
        prompt = f"""Analyse cette réponse d'un commercial en formation.

PATTERNS DU CHAMPION À APPRENDRE:
{json.dumps(patterns, ensure_ascii=False, indent=2)}

CONTEXTE DE LA CONVERSATION:
{context}

RÉPONSE DE L'UTILISATEUR:
"{response}"

---

Évalue et retourne un JSON:
{{
  "score": 1-10,
  "patterns_used": ["pattern1", "pattern2"],
  "patterns_missed": ["pattern3"],
  "feedback": "feedback constructif",
  "strengths": ["point fort 1"],
  "improvements": ["amélioration 1"],
  "champion_alternative": "ce que le champion aurait dit"
}}

JSON uniquement."""

        try:
            text = await self._call_llm(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.4
            )
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            analysis = json.loads(text)
            return {"success": True, **analysis}

        except Exception as e:
            logger.error("response_analysis_error", error=str(e))
            return {
                "success": False,
                "score": 5,
                "feedback": "Analyse non disponible",
                "error": str(e)
            }
