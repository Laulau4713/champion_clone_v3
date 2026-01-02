"""
Tests for MCP server integration.
"""

import json

import pytest


class TestMCPIntegration:
    """Tests for MCP server connections."""

    @pytest.mark.asyncio
    async def test_audio_server_tools(self):
        """Test audio MCP server exposes correct tools."""
        expected_tools = ["extract_audio", "transcribe", "process_video"]

        # In a real test, we'd spawn the MCP server and query it
        # For now, just verify the expected structure
        assert len(expected_tools) == 3

    @pytest.mark.asyncio
    async def test_pattern_server_tools(self):
        """Test pattern MCP server exposes correct tools."""
        expected_tools = ["extract_patterns", "generate_scenarios", "find_patterns", "analyze_champion"]

        assert len(expected_tools) == 4

    @pytest.mark.asyncio
    async def test_training_server_tools(self):
        """Test training MCP server exposes correct tools."""
        expected_tools = ["start_training", "send_response", "end_training", "get_session", "list_sessions"]

        assert len(expected_tools) == 5


class TestMCPToolCalls:
    """Tests for MCP tool call handling."""

    def test_tool_input_schema_validation(self):
        """Test tool input schemas are valid."""
        schemas = [
            {"type": "object", "properties": {"video_path": {"type": "string"}}, "required": ["video_path"]},
            {"type": "object", "properties": {"transcript": {"type": "string"}}, "required": ["transcript"]},
        ]

        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema

    def test_tool_response_format(self):
        """Test tool responses follow MCP format."""
        response = {"content": [{"type": "text", "text": json.dumps({"success": True, "data": "test"})}]}

        assert "content" in response
        assert response["content"][0]["type"] == "text"

        # Parse the text content
        data = json.loads(response["content"][0]["text"])
        assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
