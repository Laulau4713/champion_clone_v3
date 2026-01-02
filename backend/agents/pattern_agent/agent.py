"""
Pattern Agent - Autonomous agent for sales pattern extraction and analysis.
"""

import os

from agents.base_agent import BaseAgent, ToolResult

from .memory import PatternAgentMemory
from .tools import PatternTools


class PatternAgent(BaseAgent):
    """
    Pattern extraction and analysis agent.

    Capabilities:
    - Extract patterns from transcripts (Claude Opus)
    - Generate training scenarios
    - Semantic pattern search
    - Response analysis against patterns
    """

    SYSTEM_PROMPT = """Tu es le Pattern Agent de Champion Clone.

Ton rôle est d'analyser les transcriptions de champions commerciaux et d'extraire leurs techniques de vente.

CAPACITÉS:
1. extract_patterns: Extraire les patterns d'une transcription
   - Input: transcript (texte complet)
   - Output: patterns structurés (openings, objections, closes, key_phrases, etc.)

2. generate_scenarios: Générer des scénarios d'entraînement basés sur les patterns
   - Input: patterns, count
   - Output: liste de scénarios avec contexte, prospect_type, challenge, objectifs

3. store_patterns: Stocker les patterns dans la mémoire vectorielle
   - Input: champion_id, patterns
   - Output: confirmation et statistiques de stockage

4. find_patterns: Rechercher des patterns similaires
   - Input: query, champion_id (optionnel), pattern_type (optionnel)
   - Output: patterns pertinents avec scores de similarité

5. analyze_response: Analyser une réponse utilisateur contre les patterns
   - Input: response, patterns, context
   - Output: score, feedback, patterns utilisés/manqués

TYPES DE PATTERNS:
- opening: Techniques d'ouverture et d'accroche
- objection: Gestion des objections (objection + réponse)
- close: Techniques de closing
- key_phrase: Phrases signature impactantes
- success_pattern: Patterns de succès globaux

WORKFLOW TYPIQUE:
1. Recevoir une transcription
2. Extraire les patterns avec Claude Opus
3. Stocker dans Qdrant avec embeddings
4. Générer des scénarios d'entraînement

RÈGLES:
- Utiliser Claude Opus pour l'extraction (haute qualité)
- Toujours valider la structure des patterns
- Stocker avec métadonnées pour filtrage
- Retourner des scores de confiance quand possible

Choisis les outils appropriés pour accomplir la tâche."""

    def __init__(self):
        super().__init__(name="Pattern Agent", model=os.getenv("CLAUDE_OPUS_MODEL", "claude-opus-4-20250514"))

        self.tools_impl = PatternTools()
        self.memory = PatternAgentMemory()

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "extract_patterns",
                "description": "Extract sales patterns from a transcript using Claude Opus",
                "input_schema": {
                    "type": "object",
                    "properties": {"transcript": {"type": "string", "description": "Full transcript text to analyze"}},
                    "required": ["transcript"],
                },
            },
            {
                "name": "generate_scenarios",
                "description": "Generate training scenarios based on champion patterns",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "patterns": {"type": "object", "description": "Champion patterns dictionary"},
                        "count": {"type": "integer", "default": 3, "description": "Number of scenarios to generate"},
                    },
                    "required": ["patterns"],
                },
            },
            {
                "name": "store_patterns",
                "description": "Store patterns in vector memory for later retrieval",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "champion_id": {"type": "integer", "description": "Champion ID"},
                        "patterns": {"type": "object", "description": "Patterns to store"},
                    },
                    "required": ["champion_id", "patterns"],
                },
            },
            {
                "name": "find_patterns",
                "description": "Search for patterns similar to a query",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "champion_id": {"type": "integer", "description": "Filter by champion ID"},
                        "pattern_type": {
                            "type": "string",
                            "enum": ["opening", "objection", "close", "key_phrase", "success_pattern"],
                            "description": "Filter by pattern type",
                        },
                        "limit": {"type": "integer", "default": 5, "description": "Maximum results"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "analyze_response",
                "description": "Analyze a user response against champion patterns",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "response": {"type": "string", "description": "User's response to analyze"},
                        "patterns": {"type": "object", "description": "Champion patterns to compare against"},
                        "context": {"type": "string", "description": "Conversation context"},
                    },
                    "required": ["response", "patterns", "context"],
                },
            },
            {
                "name": "get_champion_patterns",
                "description": "Retrieve all stored patterns for a champion",
                "input_schema": {
                    "type": "object",
                    "properties": {"champion_id": {"type": "integer", "description": "Champion ID"}},
                    "required": ["champion_id"],
                },
            },
        ]

    async def execute_tool(self, name: str, input_data: dict) -> ToolResult:
        """Execute a tool and return the result."""
        try:
            if name == "extract_patterns":
                result = await self.tools_impl.extract_patterns(transcript=input_data["transcript"])

            elif name == "generate_scenarios":
                result = await self.tools_impl.generate_scenarios(
                    patterns=input_data["patterns"], count=input_data.get("count", 3)
                )

            elif name == "store_patterns":
                stored = await self.memory.store_patterns_batch(
                    champion_id=input_data["champion_id"], patterns=input_data["patterns"]
                )
                result = {"success": True, "stored": stored}

            elif name == "find_patterns":
                patterns = await self.memory.find_relevant_patterns(
                    query=input_data["query"],
                    champion_id=input_data.get("champion_id"),
                    pattern_type=input_data.get("pattern_type"),
                    limit=input_data.get("limit", 5),
                )
                result = {"success": True, "patterns": patterns}

            elif name == "analyze_response":
                result = await self.tools_impl.analyze_response_against_patterns(
                    response=input_data["response"], patterns=input_data["patterns"], context=input_data["context"]
                )

            elif name == "get_champion_patterns":
                patterns = await self.memory.get_champion_patterns(champion_id=input_data["champion_id"])
                result = {"success": True, "patterns": patterns}

            else:
                return ToolResult(tool_name=name, success=False, output=None, error=f"Unknown tool: {name}")

            return ToolResult(
                tool_name=name, success=result.get("success", True), output=result, error=result.get("error")
            )

        except Exception as e:
            return ToolResult(tool_name=name, success=False, output=None, error=str(e))

    # ============================================
    # Convenience methods for direct API access
    # ============================================

    async def generate_scenarios(self, patterns: dict, count: int = 3) -> list[dict]:
        """
        Generate training scenarios from patterns.

        Convenience method for API routers.

        Args:
            patterns: Extracted champion patterns
            count: Number of scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        result = await self.tools_impl.generate_scenarios(patterns, count)
        if result.get("success"):
            return result.get("scenarios", [])
        return [self.tools_impl._get_default_scenario()]

    async def extract_patterns(self, transcript: str) -> dict:
        """
        Extract sales patterns from transcript.

        Convenience method for API routers.

        Args:
            transcript: Full transcript text

        Returns:
            Dictionary with extracted patterns
        """
        result = await self.tools_impl.extract_patterns(transcript)
        if result.get("success"):
            return result.get("patterns", {})
        raise ValueError(result.get("error", "Pattern extraction failed"))
