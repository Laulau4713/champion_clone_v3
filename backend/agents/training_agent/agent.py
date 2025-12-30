"""
Training Agent - Autonomous agent for training sessions.
"""

import os
import uuid
from typing import Optional
from datetime import datetime

from agents.base_agent import BaseAgent, ToolResult
from .tools import TrainingTools
from .memory import TrainingAgentMemory
from memory.schemas import SessionState, ConversationTurn


class TrainingAgent(BaseAgent):
    """
    Training session agent.

    Capabilities:
    - Start training sessions
    - Simulate prospect conversations
    - Evaluate user responses
    - Generate feedback and scoring
    - Session management
    """

    SYSTEM_PROMPT = """Tu es le Training Agent de Champion Clone.

Ton rôle est de gérer les sessions d'entraînement où les utilisateurs pratiquent leurs techniques de vente.

CAPACITÉS:
1. start_session: Démarrer une nouvelle session d'entraînement
   - Input: champion_id, user_id, scenario, patterns
   - Output: session_id, first_message, tips

2. process_response: Traiter la réponse de l'utilisateur
   - Input: session_id, user_response
   - Output: prospect_response, feedback, score, session_complete

3. end_session: Terminer une session et générer un résumé
   - Input: session_id
   - Output: summary avec score global, forces, améliorations

4. get_session: Récupérer l'état d'une session
   - Input: session_id
   - Output: session state complet

5. generate_tips: Générer des conseils pour l'utilisateur
   - Input: scenario, patterns
   - Output: liste de tips contextuels

WORKFLOW:
1. Recevoir une demande de session
2. Créer la session en mémoire Redis
3. Générer la première réponse du prospect
4. Pour chaque réponse utilisateur:
   - Évaluer la réponse
   - Générer la réponse du prospect
   - Mettre à jour le score
5. À la fin, générer un résumé complet

RÈGLES:
- Toujours stocker l'état en Redis
- Évaluer chaque réponse utilisateur
- Être encourageant mais honnête dans le feedback
- Signaler quand la session doit se terminer

Choisis les outils appropriés pour accomplir la tâche."""

    def __init__(self):
        super().__init__(
            name="Training Agent",
            model=os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-20250514")
        )

        self.tools_impl = TrainingTools()
        self.memory = TrainingAgentMemory()

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "start_session",
                "description": "Start a new training session",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "champion_id": {
                            "type": "integer",
                            "description": "Champion ID"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "scenario": {
                            "type": "object",
                            "description": "Training scenario"
                        },
                        "patterns": {
                            "type": "object",
                            "description": "Champion patterns"
                        }
                    },
                    "required": ["champion_id", "scenario", "patterns"]
                }
            },
            {
                "name": "process_response",
                "description": "Process user response and get prospect reply",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID"
                        },
                        "user_response": {
                            "type": "string",
                            "description": "User's response"
                        }
                    },
                    "required": ["session_id", "user_response"]
                }
            },
            {
                "name": "end_session",
                "description": "End session and generate summary",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "get_session",
                "description": "Get current session state",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "generate_tips",
                "description": "Generate contextual tips for the user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "scenario": {
                            "type": "object",
                            "description": "Training scenario"
                        },
                        "patterns": {
                            "type": "object",
                            "description": "Champion patterns"
                        }
                    },
                    "required": ["scenario", "patterns"]
                }
            },
            {
                "name": "list_active_sessions",
                "description": "List all active training sessions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Filter by user ID"
                        }
                    }
                }
            }
        ]

    async def execute_tool(self, name: str, input_data: dict) -> ToolResult:
        """Execute a tool and return the result."""
        try:
            if name == "start_session":
                result = await self._start_session(
                    champion_id=input_data["champion_id"],
                    user_id=input_data.get("user_id", "anonymous"),
                    scenario=input_data["scenario"],
                    patterns=input_data["patterns"]
                )

            elif name == "process_response":
                result = await self._process_response(
                    session_id=input_data["session_id"],
                    user_response=input_data["user_response"]
                )

            elif name == "end_session":
                result = await self._end_session(
                    session_id=input_data["session_id"]
                )

            elif name == "get_session":
                session = await self.memory.get_session(input_data["session_id"])
                if session:
                    result = {"success": True, "session": session.to_dict()}
                else:
                    result = {"success": False, "error": "Session not found"}

            elif name == "generate_tips":
                tips = await self.tools_impl.generate_tips(
                    scenario=input_data["scenario"],
                    patterns=input_data["patterns"]
                )
                result = {"success": True, "tips": tips}

            elif name == "list_active_sessions":
                sessions = await self.memory.get_active_sessions(
                    user_id=input_data.get("user_id")
                )
                result = {
                    "success": True,
                    "sessions": [s.to_dict() for s in sessions]
                }

            else:
                return ToolResult(
                    tool_name=name,
                    success=False,
                    output=None,
                    error=f"Unknown tool: {name}"
                )

            return ToolResult(
                tool_name=name,
                success=result.get("success", True),
                output=result,
                error=result.get("error")
            )

        except Exception as e:
            return ToolResult(
                tool_name=name,
                success=False,
                output=None,
                error=str(e)
            )

    async def _start_session(
        self,
        champion_id: int,
        user_id: str,
        scenario: dict,
        patterns: dict
    ) -> dict:
        """Start a new training session."""
        session_id = str(uuid.uuid4())[:8]

        # Build system prompt for prospect
        system_prompt = self.tools_impl.PROSPECT_SYSTEM_PROMPT.format(
            scenario=str(scenario),
            patterns=str(patterns),
            difficulty=scenario.get("difficulty", "medium").upper()
        )

        # Get first prospect message
        first_response = await self.tools_impl.generate_prospect_response(
            user_message="START",
            conversation_history=[],
            scenario=scenario,
            patterns=patterns,
            system_prompt=system_prompt
        )

        if not first_response.get("success"):
            return {"success": False, "error": first_response.get("error")}

        # Generate tips
        tips = await self.tools_impl.generate_tips(scenario, patterns)

        # Create session state
        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            champion_id=champion_id,
            scenario=scenario,
            tips=tips,
            system_prompt=system_prompt
        )

        # Add first message
        session.add_turn(
            role="champion",
            content=first_response["response"]
        )

        # Store in Redis
        await self.memory.create_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "first_message": first_response["response"],
            "tips": tips
        }

    async def _process_response(
        self,
        session_id: str,
        user_response: str
    ) -> dict:
        """Process user response in session."""
        # Get session
        session = await self.memory.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if session.status != "active":
            return {"success": False, "error": "Session is not active"}

        # Convert to conversation format
        conversation = [t.to_dict() for t in session.conversation]

        # Evaluate response
        evaluation = await self.tools_impl.evaluate_response(
            user_response=user_response,
            patterns=session.scenario.get("patterns", {}),
            scenario=session.scenario,
            conversation_history=conversation
        )

        # Add user message with feedback
        session.add_turn(
            role="user",
            content=user_response,
            feedback=evaluation.get("feedback"),
            score=evaluation.get("score")
        )

        # Check if session should end
        is_complete = self.tools_impl.check_session_complete(
            [t.to_dict() for t in session.conversation],
            session.scenario
        )

        if is_complete:
            session.status = "completed"
            await self.memory.update_session(session)

            return {
                "success": True,
                "feedback": evaluation.get("feedback"),
                "score": evaluation.get("score"),
                "suggestions": evaluation.get("suggestions", []),
                "session_complete": True,
                "prospect_response": None
            }

        # Get prospect response
        prospect = await self.tools_impl.generate_prospect_response(
            user_message=user_response,
            conversation_history=conversation,
            scenario=session.scenario,
            patterns=session.scenario.get("patterns", {}),
            system_prompt=session.system_prompt
        )

        # Add prospect message
        session.add_turn(
            role="champion",
            content=prospect.get("response", "...")
        )

        # Update session
        await self.memory.update_session(session)

        return {
            "success": True,
            "prospect_response": prospect.get("response"),
            "feedback": evaluation.get("feedback"),
            "score": evaluation.get("score"),
            "suggestions": evaluation.get("suggestions", []),
            "session_complete": False
        }

    async def _end_session(self, session_id: str) -> dict:
        """End session and generate summary."""
        session = await self.memory.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Generate summary
        conversation = [t.to_dict() for t in session.conversation]
        summary = await self.tools_impl.generate_session_summary(
            conversation=conversation,
            patterns=session.scenario.get("patterns", {}),
            scenario=session.scenario
        )

        # Update session
        session.status = "completed"
        await self.memory.update_session(session)

        return {
            "success": True,
            "session_id": session_id,
            "total_exchanges": len([m for m in conversation if m.get("role") == "user"]),
            **summary
        }

    # ============================================
    # Convenience methods for direct API access
    # ============================================

    async def start_session(self, scenario: dict, patterns: dict) -> dict:
        """
        Start a new training session.

        Convenience method for API routers.

        Args:
            scenario: Training scenario
            patterns: Champion patterns

        Returns:
            Dict with session_id, first_message, tips, system_prompt
        """
        system_prompt = self.tools_impl.PROSPECT_SYSTEM_PROMPT.format(
            scenario=str(scenario),
            patterns=str(patterns),
            difficulty=scenario.get("difficulty", "medium").upper()
        )

        # Get first prospect message
        first_response = await self.tools_impl.generate_prospect_response(
            user_message="START",
            conversation_history=[],
            scenario=scenario,
            patterns=patterns,
            system_prompt=system_prompt
        )

        if not first_response.get("success"):
            raise ValueError(first_response.get("error", "Failed to start session"))

        # Generate tips
        tips = await self.tools_impl.generate_tips(scenario, patterns)

        return {
            "first_message": first_response["response"],
            "tips": tips,
            "system_prompt": system_prompt
        }

    async def get_prospect_response(
        self,
        user_message: str,
        conversation_history: list,
        system_prompt: str
    ) -> str:
        """
        Get prospect's response to user message.

        Convenience method for API routers.

        Args:
            user_message: What the user said
            conversation_history: Previous messages
            system_prompt: Pre-built system prompt

        Returns:
            Prospect's response text
        """
        result = await self.tools_impl.generate_prospect_response(
            user_message=user_message,
            conversation_history=conversation_history,
            scenario={},
            patterns={},
            system_prompt=system_prompt
        )
        if result.get("success"):
            return result.get("response", "...")
        raise ValueError(result.get("error", "Failed to generate response"))

    async def evaluate_response(
        self,
        user_response: str,
        patterns: dict,
        scenario: dict,
        conversation_history: list
    ) -> dict:
        """
        Evaluate user's response.

        Convenience method for API routers.

        Args:
            user_response: User's message
            patterns: Champion patterns
            scenario: Training scenario
            conversation_history: Previous messages

        Returns:
            Dict with score, feedback, suggestions
        """
        result = await self.tools_impl.evaluate_response(
            user_response=user_response,
            patterns=patterns,
            scenario=scenario,
            conversation_history=conversation_history
        )
        return {
            "score": result.get("score", 5),
            "feedback": result.get("feedback", ""),
            "suggestions": result.get("suggestions", [])
        }

    async def check_session_complete(self, messages: list, scenario: dict) -> bool:
        """
        Check if session should end.

        Convenience method for API routers.

        Args:
            messages: Conversation messages
            scenario: Training scenario

        Returns:
            True if session should complete
        """
        return self.tools_impl.check_session_complete(messages, scenario)

    async def generate_session_summary(
        self,
        messages: list,
        patterns: dict,
        scenario: dict
    ) -> dict:
        """
        Generate summary for completed session.

        Convenience method for API routers.

        Args:
            messages: Full conversation
            patterns: Champion patterns
            scenario: Training scenario

        Returns:
            Dict with overall_score, feedback_summary, strengths, areas_for_improvement
        """
        result = await self.tools_impl.generate_session_summary(
            conversation=messages,
            patterns=patterns,
            scenario=scenario
        )
        return {
            "overall_score": result.get("overall_score", 5),
            "feedback_summary": result.get("feedback_summary", ""),
            "strengths": result.get("strengths", []),
            "areas_for_improvement": result.get("areas_for_improvement", [])
        }
