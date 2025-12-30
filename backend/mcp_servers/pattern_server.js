#!/usr/bin/env node
/**
 * MCP Server for Pattern Agent
 *
 * Exposes pattern extraction and search via Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  {
    name: 'champion-clone-pattern',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TOOLS = [
  {
    name: 'extract_patterns',
    description: 'Extract sales patterns from a transcript using Claude Opus',
    inputSchema: {
      type: 'object',
      properties: {
        transcript: {
          type: 'string',
          description: 'Full transcript text to analyze',
        },
      },
      required: ['transcript'],
    },
  },
  {
    name: 'generate_scenarios',
    description: 'Generate training scenarios from champion patterns',
    inputSchema: {
      type: 'object',
      properties: {
        champion_id: {
          type: 'integer',
          description: 'Champion ID',
        },
        count: {
          type: 'integer',
          default: 3,
          description: 'Number of scenarios to generate',
        },
      },
      required: ['champion_id'],
    },
  },
  {
    name: 'find_patterns',
    description: 'Search for similar patterns in the vector database',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query',
        },
        champion_id: {
          type: 'integer',
          description: 'Filter by champion ID',
        },
        pattern_type: {
          type: 'string',
          enum: ['opening', 'objection', 'close', 'key_phrase'],
          description: 'Filter by pattern type',
        },
        limit: {
          type: 'integer',
          default: 5,
          description: 'Max results',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'analyze_champion',
    description: 'Full champion analysis pipeline',
    inputSchema: {
      type: 'object',
      properties: {
        champion_id: {
          type: 'integer',
          description: 'Champion ID to analyze',
        },
      },
      required: ['champion_id'],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'extract_patterns':
        result = await callBackendAgent('pattern', 'extract_patterns', args);
        break;

      case 'generate_scenarios':
        result = await callBackend(`/scenarios/${args.champion_id}?count=${args.count || 3}`);
        break;

      case 'find_patterns':
        result = await callBackendAgent('pattern', 'find_patterns', args);
        break;

      case 'analyze_champion':
        result = await callBackend(`/analyze/${args.champion_id}`, 'POST');
        break;

      default:
        return {
          content: [{ type: 'text', text: JSON.stringify({ error: `Unknown tool: ${name}` }) }],
          isError: true,
        };
    }

    return {
      content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
    };
  } catch (error) {
    return {
      content: [{ type: 'text', text: JSON.stringify({ error: error.message }) }],
      isError: true,
    };
  }
});

async function callBackendAgent(agent, tool, args) {
  const response = await fetch(`${API_URL}/agents/${agent}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool, input: args }),
  });

  if (!response.ok) throw new Error(`Backend error: ${response.statusText}`);
  return await response.json();
}

async function callBackend(path, method = 'GET', body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) throw new Error(`Backend error: ${response.statusText}`);
  return await response.json();
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Champion Clone Pattern MCP Server running on stdio');
}

main().catch(console.error);
