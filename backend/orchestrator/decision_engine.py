"""
Decision Engine - Intelligent routing and workflow planning.

Uses Claude Opus to analyze tasks and create execution plans.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from anthropic import AsyncAnthropic
import structlog

logger = structlog.get_logger()


class AgentType(Enum):
    """Available agent types."""
    AUDIO = "audio"
    PATTERN = "pattern"
    TRAINING = "training"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    agent: AgentType
    task: str
    depends_on: list[str] = field(default_factory=list)
    priority: int = 1
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class Workflow:
    """Complete workflow with multiple steps."""
    id: str
    steps: list[WorkflowStep]
    reasoning: str
    parallel_groups: list[list[int]] = field(default_factory=list)  # Groups of step indices that can run in parallel


class DecisionEngine:
    """
    Analyzes tasks and creates optimal execution workflows.

    Uses Claude Opus for complex reasoning about:
    - Which agents to involve
    - Order of execution
    - Data flow between agents
    - Parallel execution opportunities
    """

    ROUTING_PROMPT = """Tu es le Decision Engine de Champion Clone, une plateforme d'entraînement commercial.

Tu dois analyser la requête utilisateur et créer un workflow d'exécution optimal.

AGENTS DISPONIBLES:

1. AUDIO AGENT
   - Capacités: Extraction audio, transcription Whisper, analyse vocale, clonage voix ElevenLabs
   - Utiliser pour: Upload vidéos, processing audio, génération vocale
   - Input: fichiers vidéo/audio, texte pour TTS
   - Output: transcriptions, fichiers audio, profils vocaux

2. PATTERN AGENT
   - Capacités: Extraction patterns de vente, analyse sémantique, embeddings, recherche vectorielle
   - Utiliser pour: Analyse de transcripts, identification techniques commerciales, matching de patterns
   - Input: transcriptions, requêtes de recherche
   - Output: patterns structurés (openings, objections, closes), embeddings

3. TRAINING AGENT
   - Capacités: Simulation de conversations, scoring de réponses, génération de scénarios, feedback
   - Utiliser pour: Sessions d'entraînement, évaluation, génération de contenu pédagogique
   - Input: patterns du champion, réponses utilisateur, contexte de session
   - Output: réponses simulées, scores, feedback, résumés de session

RÈGLES DE ROUTAGE:

1. Dépendances:
   - Pattern Agent a besoin d'une transcription (donc Audio Agent doit passer d'abord si on part d'une vidéo)
   - Training Agent a besoin de patterns (donc Pattern Agent doit analyser avant)

2. Parallélisation:
   - Si plusieurs tâches sont indépendantes, les grouper pour exécution parallèle

3. Efficacité:
   - Minimiser le nombre d'étapes
   - Réutiliser les résultats intermédiaires

REQUÊTE UTILISATEUR: {task}

CONTEXTE ADDITIONNEL: {context}

---

Analyse et retourne un JSON avec:
{{
  "reasoning": "Explication de ta décision de routage",
  "workflow": [
    {{
      "agent": "audio|pattern|training",
      "task": "Description précise de la tâche pour cet agent",
      "depends_on": ["step_0", "step_1"],  // Étapes dont celle-ci dépend
      "priority": 1-3,  // 1 = haute priorité
      "timeout_seconds": 300
    }}
  ],
  "parallel_groups": [[0, 1], [2]]  // Groupes d'indices d'étapes parallélisables
}}

JSON uniquement, pas de markdown."""

    def __init__(self, model: str = "claude-opus-4-20250514"):
        self.model = model
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def analyze(self, task: str, context: Optional[dict] = None) -> Workflow:
        """
        Analyze a task and create an execution workflow.

        Args:
            task: User's request
            context: Additional context (e.g., available data, user preferences)

        Returns:
            Workflow with ordered steps
        """
        logger.info("decision_engine_analyzing", task=task[:100])

        context_str = json.dumps(context, ensure_ascii=False) if context else "None"

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": self.ROUTING_PROMPT.format(task=task, context=context_str)
                }]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            workflow_data = json.loads(response_text)

            # Build workflow
            steps = []
            for i, step_data in enumerate(workflow_data.get("workflow", [])):
                agent_type = AgentType(step_data["agent"])
                step = WorkflowStep(
                    agent=agent_type,
                    task=step_data["task"],
                    depends_on=step_data.get("depends_on", []),
                    priority=step_data.get("priority", 1),
                    timeout_seconds=step_data.get("timeout_seconds", 300)
                )
                steps.append(step)

            workflow = Workflow(
                id=f"wf_{hash(task) % 10000:04d}",
                steps=steps,
                reasoning=workflow_data.get("reasoning", ""),
                parallel_groups=workflow_data.get("parallel_groups", [])
            )

            logger.info(
                "decision_engine_workflow_created",
                workflow_id=workflow.id,
                steps=len(steps),
                reasoning=workflow.reasoning[:100]
            )

            return workflow

        except json.JSONDecodeError as e:
            logger.error("decision_engine_json_error", error=str(e), response=response_text[:200])
            # Return a fallback single-step workflow
            return self._create_fallback_workflow(task)
        except Exception as e:
            logger.error("decision_engine_error", error=str(e))
            return self._create_fallback_workflow(task)

    def _create_fallback_workflow(self, task: str) -> Workflow:
        """Create a simple fallback workflow when routing fails."""
        # Try to determine agent from keywords
        task_lower = task.lower()

        if any(word in task_lower for word in ["vidéo", "video", "audio", "upload", "transcri"]):
            agent = AgentType.AUDIO
        elif any(word in task_lower for word in ["pattern", "analyse", "extract", "technique"]):
            agent = AgentType.PATTERN
        else:
            agent = AgentType.TRAINING

        return Workflow(
            id="wf_fallback",
            steps=[WorkflowStep(agent=agent, task=task)],
            reasoning="Fallback workflow - routing failed",
            parallel_groups=[[0]]
        )

    async def should_continue(
        self,
        current_results: dict,
        original_task: str,
        remaining_steps: list[WorkflowStep]
    ) -> tuple[bool, Optional[str]]:
        """
        Decide if workflow should continue or if task is complete.

        Args:
            current_results: Results from completed steps
            original_task: The original user request
            remaining_steps: Steps not yet executed

        Returns:
            Tuple of (should_continue, reason)
        """
        if not remaining_steps:
            return False, "All steps completed"

        # Check if any step failed critically
        for step_id, result in current_results.items():
            if isinstance(result, dict) and result.get("status") == "error":
                error = result.get("error", "Unknown error")
                # Decide if error is recoverable
                if "critical" in error.lower() or "permission" in error.lower():
                    return False, f"Critical error in {step_id}: {error}"

        return True, None

    def get_next_steps(self, workflow: Workflow, completed: set[int]) -> list[int]:
        """
        Get indices of steps that can be executed next.

        Args:
            workflow: The workflow
            completed: Set of completed step indices

        Returns:
            List of step indices ready for execution
        """
        ready = []

        for i, step in enumerate(workflow.steps):
            if i in completed:
                continue

            # Check if all dependencies are completed
            deps_met = True
            for dep in step.depends_on:
                # Parse dependency (e.g., "step_0" -> 0)
                try:
                    dep_idx = int(dep.replace("step_", ""))
                    if dep_idx not in completed:
                        deps_met = False
                        break
                except ValueError:
                    continue

            if deps_met:
                ready.append(i)

        # Sort by priority
        ready.sort(key=lambda i: workflow.steps[i].priority)

        return ready
