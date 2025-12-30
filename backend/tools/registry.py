"""
Tool Registry - Discovery and management of agent tools.
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class ToolDefinition:
    """Tool definition structure."""
    name: str
    description: str
    agent: str
    input_schema: dict
    output_schema: Optional[dict] = None
    examples: list[dict] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "agent": self.agent,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples or []
        }


class ToolRegistry:
    """
    Central registry for all agent tools.

    Provides:
    - Tool discovery from JSON definitions
    - Tool lookup by name or agent
    - Validation of tool calls
    """

    def __init__(self, definitions_dir: Optional[str] = None):
        self.definitions_dir = Path(
            definitions_dir or
            os.path.join(os.path.dirname(__file__), "definitions")
        )
        self.tools: dict[str, ToolDefinition] = {}
        self.tools_by_agent: dict[str, list[str]] = {}

        self._load_definitions()

    def _load_definitions(self):
        """Load tool definitions from JSON files."""
        if not self.definitions_dir.exists():
            self.definitions_dir.mkdir(parents=True, exist_ok=True)

        # Check if directory is empty and create defaults
        json_files = list(self.definitions_dir.glob("*.json"))
        if not json_files:
            self._create_default_definitions()
            json_files = list(self.definitions_dir.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                agent = data.get("agent", json_file.stem.replace("_tools", ""))

                for tool_data in data.get("tools", []):
                    tool = ToolDefinition(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        agent=agent,
                        input_schema=tool_data["input_schema"],
                        output_schema=tool_data.get("output_schema"),
                        examples=tool_data.get("examples")
                    )

                    self.tools[tool.name] = tool

                    if agent not in self.tools_by_agent:
                        self.tools_by_agent[agent] = []
                    self.tools_by_agent[agent].append(tool.name)

                logger.info("tools_loaded", file=json_file.name, count=len(data.get("tools", [])))

            except Exception as e:
                logger.error("tool_load_error", file=json_file.name, error=str(e))

    def _create_default_definitions(self):
        """Create default tool definition files."""
        # Audio tools
        audio_tools = {
            "agent": "audio",
            "tools": [
                {
                    "name": "extract_audio",
                    "description": "Extract audio from video file",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "video_path": {"type": "string"},
                            "output_format": {"type": "string", "enum": ["mp3", "wav"]}
                        },
                        "required": ["video_path"]
                    }
                },
                {
                    "name": "transcribe",
                    "description": "Transcribe audio to text",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {"type": "string"},
                            "language": {"type": "string"}
                        },
                        "required": ["audio_path"]
                    }
                }
            ]
        }

        # Pattern tools
        pattern_tools = {
            "agent": "pattern",
            "tools": [
                {
                    "name": "extract_patterns",
                    "description": "Extract sales patterns from transcript",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "transcript": {"type": "string"}
                        },
                        "required": ["transcript"]
                    }
                },
                {
                    "name": "generate_scenarios",
                    "description": "Generate training scenarios",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "patterns": {"type": "object"},
                            "count": {"type": "integer"}
                        },
                        "required": ["patterns"]
                    }
                }
            ]
        }

        # Training tools
        training_tools = {
            "agent": "training",
            "tools": [
                {
                    "name": "start_session",
                    "description": "Start training session",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "champion_id": {"type": "integer"},
                            "scenario": {"type": "object"},
                            "patterns": {"type": "object"}
                        },
                        "required": ["champion_id", "scenario", "patterns"]
                    }
                },
                {
                    "name": "process_response",
                    "description": "Process user response",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "user_response": {"type": "string"}
                        },
                        "required": ["session_id", "user_response"]
                    }
                }
            ]
        }

        # Write files
        for name, data in [
            ("audio_tools.json", audio_tools),
            ("pattern_tools.json", pattern_tools),
            ("training_tools.json", training_tools)
        ]:
            with open(self.definitions_dir / name, "w") as f:
                json.dump(data, f, indent=2)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name."""
        return self.tools.get(name)

    def get_agent_tools(self, agent: str) -> list[ToolDefinition]:
        """Get all tools for an agent."""
        tool_names = self.tools_by_agent.get(agent, [])
        return [self.tools[name] for name in tool_names]

    def list_tools(self) -> list[dict]:
        """List all tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    def validate_tool_call(self, tool_name: str, input_data: dict) -> tuple[bool, Optional[str]]:
        """Validate a tool call against its schema."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False, f"Unknown tool: {tool_name}"

        schema = tool.input_schema
        required = schema.get("required", [])

        for field in required:
            if field not in input_data:
                return False, f"Missing required field: {field}"

        return True, None

    def get_tool_for_task(self, task_description: str) -> list[str]:
        """Suggest tools that might be useful for a task."""
        # Simple keyword matching - could be enhanced with embeddings
        task_lower = task_description.lower()
        suggestions = []

        for tool in self.tools.values():
            desc_lower = tool.description.lower()
            if any(word in desc_lower for word in task_lower.split()):
                suggestions.append(tool.name)

        return suggestions[:5]


# Global registry instance
_registry = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
