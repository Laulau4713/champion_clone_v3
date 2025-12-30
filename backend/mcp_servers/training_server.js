#!/usr/bin/env node
/**
 * MCP Server for Training Agent
 *
 * Exposes training session management via Model Context Protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  {
    name: 'champion-clone-training',
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
    name: 'start_training',
    description: 'Start a new training session',
    inputSchema: {
      type: 'object',
      properties: {
        champion_id: {
          type: 'integer',
          description: 'Champion ID to train against',
        },
        scenario_index: {
          type: 'integer',
          default: 0,
          description: 'Scenario index to use',
        },
        user_id: {
          type: 'string',
          default: 'anonymous',
          description: 'User identifier',
        },
      },
      required: ['champion_id'],
    },
  },
  {
    name: 'send_response',
    description: 'Send a response in the training session',
    inputSchema: {
      type: 'object',
      properties: {
        session_id: {
          type: 'string',
          description: 'Session ID',
        },
        user_response: {
          type: 'string',
          description: 'User response message',
        },
      },
      required: ['session_id', 'user_response'],
    },
  },
  {
    name: 'end_training',
    description: 'End a training session and get summary',
    inputSchema: {
      type: 'object',
      properties: {
        session_id: {
          type: 'string',
          description: 'Session ID to end',
        },
      },
      required: ['session_id'],
    },
  },
  {
    name: 'get_session',
    description: 'Get current session state',
    inputSchema: {
      type: 'object',
      properties: {
        session_id: {
          type: 'string',
          description: 'Session ID',
        },
      },
      required: ['session_id'],
    },
  },
  {
    name: 'list_sessions',
    description: 'List training sessions',
    inputSchema: {
      type: 'object',
      properties: {
        user_id: {
          type: 'string',
          description: 'Filter by user ID',
        },
        status: {
          type: 'string',
          enum: ['active', 'completed', 'abandoned'],
          description: 'Filter by status',
        },
      },
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
      case 'start_training':
        result = await callBackend('/training/start', 'POST', {
          champion_id: args.champion_id,
          scenario_index: args.scenario_index || 0,
          user_id: args.user_id || 'anonymous',
        });
        break;

      case 'send_response':
        result = await callBackend('/training/respond', 'POST', {
          session_id: args.session_id,
          user_response: args.user_response,
        });
        break;

      case 'end_training':
        result = await callBackend('/training/end', 'POST', {
          session_id: args.session_id,
        });
        break;

      case 'get_session':
        result = await callBackend(`/training/sessions/${args.session_id}`);
        break;

      case 'list_sessions':
        let query = [];
        if (args.user_id) query.push(`user_id=${args.user_id}`);
        if (args.status) query.push(`status=${args.status}`);
        const queryStr = query.length ? `?${query.join('&')}` : '';
        result = await callBackend(`/training/sessions${queryStr}`);
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
  console.error('Champion Clone Training MCP Server running on stdio');
}

main().catch(console.error);
