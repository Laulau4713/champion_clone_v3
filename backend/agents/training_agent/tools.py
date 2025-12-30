"""
Training Agent Tools - Session management and AI conversation.

Uses Groq (FREE) with Llama 3.1 70B instead of Claude API.
Can fallback to Anthropic if ANTHROPIC_API_KEY is set and Groq fails.
"""

import os
import json
from typing import Optional
from datetime import datetime

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


class TrainingTools:
    """Collection of training session tools."""

    PROSPECT_SYSTEM_PROMPT = """Tu es un prospect dans un scénario de formation commerciale.

CONTEXTE DU SCÉNARIO:
{scenario}

PATTERNS DU CHAMPION (pour créer des défis appropriés):
{patterns}

---

RÈGLES:
1. Tu joues le rôle du PROSPECT, pas du vendeur
2. Sois réaliste - pose des questions, hésite, objecte
3. Adapte ton niveau de difficulté ({difficulty})
4. Utilise les objections que le champion sait gérer
5. Réponds de manière concise (1-3 phrases max)
6. Ne sois pas trop facile - challenge l'utilisateur

DIFFICULTÉ:
- easy: Prospect plutôt ouvert, quelques hésitations
- medium: Prospect sceptique, objections standards
- hard: Prospect difficile, multiples objections

Commence quand on te dit "START"."""

    FEEDBACK_PROMPT = """Évalue cette réponse d'un commercial en formation.

PATTERNS DU CHAMPION:
{patterns}

SCÉNARIO:
{scenario}

HISTORIQUE:
{history}

RÉPONSE DE L'UTILISATEUR:
"{response}"

---

Retourne un JSON avec:
{{
  "score": 1-10,
  "feedback": "feedback constructif (2-3 phrases)",
  "suggestions": ["suggestion 1", "suggestion 2"],
  "patterns_used": ["pattern utilisé"],
  "patterns_to_try": ["pattern à essayer"]
}}

Sois bienveillant mais exigeant. JSON uniquement."""

    SUMMARY_PROMPT = """Analyse cette session de formation complète.

SCÉNARIO:
{scenario}

PATTERNS DU CHAMPION:
{patterns}

CONVERSATION:
{conversation}

---

Retourne un JSON:
{{
  "overall_score": 1-10,
  "feedback_summary": "résumé en 3-4 phrases",
  "strengths": ["point fort 1", "point fort 2"],
  "areas_for_improvement": ["amélioration 1", "amélioration 2"],
  "patterns_mastered": ["pattern maîtrisé"],
  "patterns_to_practice": ["pattern à travailler"],
  "next_steps": ["recommandation 1", "recommandation 2"]
}}

JSON uniquement."""

    def __init__(self):
        # Use Groq by default (FREE), fallback to Anthropic
        self.use_groq = GROQ_AVAILABLE and os.getenv("GROQ_API_KEY")
        self.use_anthropic = ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY")

        if self.use_groq:
            self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            logger.info("training_tools_init", provider="groq", model=self.model)
        elif self.use_anthropic:
            self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514")
            logger.info("training_tools_init", provider="anthropic", model=self.model)
        else:
            self.client = None
            self.model = None
            logger.warning("training_tools_init", msg="No LLM provider available. Set GROQ_API_KEY (free) or ANTHROPIC_API_KEY")

    async def _call_llm(
        self,
        messages: list,
        system: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.5
    ) -> str:
        """Call LLM (Groq or Anthropic) and return text response."""
        if not self.client:
            raise RuntimeError("No LLM provider configured. Set GROQ_API_KEY (free) or ANTHROPIC_API_KEY")

        if self.use_groq:
            # Groq uses OpenAI-compatible API
            groq_messages = []
            if system:
                groq_messages.append({"role": "system", "content": system})
            groq_messages.extend(messages)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        else:
            # Anthropic API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or "",
                messages=messages,
                temperature=temperature
            )
            return response.content[0].text.strip()

    async def generate_prospect_response(
        self,
        user_message: str,
        conversation_history: list,
        scenario: dict,
        patterns: dict,
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        Generate prospect's response to user message.

        Args:
            user_message: What the user (salesperson) said
            conversation_history: Previous messages
            scenario: Training scenario
            patterns: Champion patterns
            system_prompt: Pre-built system prompt

        Returns:
            Dict with prospect response
        """
        if not system_prompt:
            system_prompt = self.PROSPECT_SYSTEM_PROMPT.format(
                scenario=json.dumps(scenario, ensure_ascii=False),
                patterns=json.dumps(patterns, ensure_ascii=False),
                difficulty=scenario.get("difficulty", "medium").upper()
            )

        # Build messages
        messages = [{"role": "user", "content": "START"}]

        for msg in conversation_history:
            role = "assistant" if msg.get("role") == "champion" else "user"
            messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        try:
            response_text = await self._call_llm(
                messages=messages,
                system=system_prompt,
                max_tokens=256,
                temperature=0.7
            )

            return {
                "success": True,
                "response": response_text
            }

        except Exception as e:
            logger.error("prospect_response_error", error=str(e))
            return {"success": False, "error": str(e)}

    async def evaluate_response(
        self,
        user_response: str,
        patterns: dict,
        scenario: dict,
        conversation_history: list
    ) -> dict:
        """
        Evaluate user's response.

        Args:
            user_response: User's message
            patterns: Champion patterns
            scenario: Training scenario
            conversation_history: Previous messages

        Returns:
            Dict with score and feedback
        """
        prompt = self.FEEDBACK_PROMPT.format(
            patterns=json.dumps(patterns, ensure_ascii=False, indent=2),
            scenario=json.dumps(scenario, ensure_ascii=False, indent=2),
            history=json.dumps(conversation_history[-4:], ensure_ascii=False, indent=2),
            response=user_response
        )

        try:
            text = await self._call_llm(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.3
            )
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            evaluation = json.loads(text)

            return {
                "success": True,
                "score": min(10, max(1, float(evaluation.get("score", 5)))),
                "feedback": evaluation.get("feedback", "Continuez à pratiquer."),
                "suggestions": evaluation.get("suggestions", []),
                "patterns_used": evaluation.get("patterns_used", []),
                "patterns_to_try": evaluation.get("patterns_to_try", [])
            }

        except Exception as e:
            logger.error("evaluation_error", error=str(e))
            return {
                "success": False,
                "score": 5,
                "feedback": "Évaluation non disponible.",
                "suggestions": [],
                "error": str(e)
            }

    async def generate_session_summary(
        self,
        conversation: list,
        patterns: dict,
        scenario: dict
    ) -> dict:
        """
        Generate summary for completed session.

        Args:
            conversation: Full conversation
            patterns: Champion patterns
            scenario: Training scenario

        Returns:
            Dict with summary
        """
        prompt = self.SUMMARY_PROMPT.format(
            scenario=json.dumps(scenario, ensure_ascii=False, indent=2),
            patterns=json.dumps(patterns, ensure_ascii=False, indent=2),
            conversation=json.dumps(conversation, ensure_ascii=False, indent=2)
        )

        try:
            text = await self._call_llm(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            summary = json.loads(text)

            return {
                "success": True,
                "overall_score": min(10, max(1, float(summary.get("overall_score", 5)))),
                "feedback_summary": summary.get("feedback_summary", "Session terminée."),
                "strengths": summary.get("strengths", []),
                "areas_for_improvement": summary.get("areas_for_improvement", []),
                "patterns_mastered": summary.get("patterns_mastered", []),
                "patterns_to_practice": summary.get("patterns_to_practice", []),
                "next_steps": summary.get("next_steps", [])
            }

        except Exception as e:
            logger.error("summary_error", error=str(e))

            # Calculate from conversation
            scores = [
                msg.get("score", 5)
                for msg in conversation
                if msg.get("role") == "user" and msg.get("score")
            ]
            avg = sum(scores) / len(scores) if scores else 5

            return {
                "success": False,
                "overall_score": round(avg, 1),
                "feedback_summary": "Session terminée. Résumé automatique.",
                "strengths": [],
                "areas_for_improvement": [],
                "error": str(e)
            }

    async def generate_tips(
        self,
        scenario: dict,
        patterns: dict
    ) -> list[str]:
        """Generate tips for the user based on scenario."""
        tips = []

        difficulty = scenario.get("difficulty", "medium")
        if difficulty == "easy":
            tips.append("Ce prospect est ouvert - concentrez-vous sur la création de rapport")
        elif difficulty == "hard":
            tips.append("Prospect difficile - préparez-vous à gérer plusieurs objections")

        if patterns.get("openings"):
            tips.append(f"Technique d'ouverture à essayer: {patterns['openings'][0][:60]}...")

        if patterns.get("key_phrases"):
            tips.append(f"Phrase clé: \"{patterns['key_phrases'][0][:50]}...\"")

        objectives = scenario.get("objectives", [])
        if objectives:
            tips.append(f"Objectif principal: {objectives[0]}")

        return tips[:4]

    def check_session_complete(self, conversation: list, scenario: dict) -> bool:
        """Check if session should end."""
        user_messages = [m for m in conversation if m.get("role") == "user"]

        if len(user_messages) >= 10:
            return True

        if conversation:
            last = conversation[-1].get("content", "").lower()
            endings = [
                "d'accord", "on signe", "je prends", "marché conclu",
                "envoyez-moi", "je vous rappelle", "pas intéressé",
                "non merci", "au revoir"
            ]
            if any(end in last for end in endings):
                return True

        return False
