#!/usr/bin/env node
/**
 * MCP Server for Audio Agent
 *
 * Exposes audio processing capabilities via Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  {
    name: 'champion-clone-audio',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Backend API URL
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Define available tools
const TOOLS = [
  {
    name: 'extract_audio',
    description: 'Extract audio from a video file using FFmpeg',
    inputSchema: {
      type: 'object',
      properties: {
        video_path: {
          type: 'string',
          description: 'Path to the video file',
        },
        output_format: {
          type: 'string',
          enum: ['mp3', 'wav'],
          default: 'mp3',
          description: 'Output audio format',
        },
      },
      required: ['video_path'],
    },
  },
  {
    name: 'transcribe',
    description: 'Transcribe audio file to text using OpenAI Whisper',
    inputSchema: {
      type: 'object',
      properties: {
        audio_path: {
          type: 'string',
          description: 'Path to the audio file',
        },
        language: {
          type: 'string',
          default: 'fr',
          description: 'Language code (fr, en, etc.)',
        },
      },
      required: ['audio_path'],
    },
  },
  {
    name: 'process_video',
    description: 'Full video processing pipeline: extract audio and transcribe',
    inputSchema: {
      type: 'object',
      properties: {
        video_path: {
          type: 'string',
          description: 'Path to the video file',
        },
        champion_name: {
          type: 'string',
          description: 'Name of the champion',
        },
      },
      required: ['video_path', 'champion_name'],
    },
  },
];

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'extract_audio':
        result = await callBackendAgent('audio', 'extract_audio', args);
        break;

      case 'transcribe':
        result = await callBackendAgent('audio', 'transcribe', args);
        break;

      case 'process_video':
        result = await callBackendAgent('audio', 'process_video', args);
        break;

      default:
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ error: `Unknown tool: ${name}` }),
            },
          ],
          isError: true,
        };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ error: error.message }),
        },
      ],
      isError: true,
    };
  }
});

/**
 * Call the backend agent via REST API
 */
async function callBackendAgent(agent, tool, args) {
  const response = await fetch(`${API_URL}/agents/${agent}/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      tool,
      input: args,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend error: ${response.statusText}`);
  }

  return await response.json();
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Champion Clone Audio MCP Server running on stdio');
}

main().catch(console.error);
