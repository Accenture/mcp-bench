#!/usr/bin/env node

import process from 'node:process';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { MCPScout } from 'mcpscout';
import { CallToolRequestHandler } from './handlers/CallToolHandler.js';
import { ListResourcesHandler } from './handlers/ListResourcesHandler.js';
import { ReadResourceHandler } from './handlers/ReadResourceHandler.js';
import { GetObjectTool } from './tools/GetObjectTool.js';
import { ListDepartmentsTool } from './tools/ListDepartmentsTool.js';
import { SearchMuseumObjectsTool } from './tools/SearchMuseumObjectsTool.js';

class MetMuseumServer {
  private server: McpServer;
  private callToolHandler: CallToolRequestHandler;
  private listResourcesHandler: ListResourcesHandler;
  private readResourceHandler: ReadResourceHandler;
  private listDepartments: ListDepartmentsTool;
  private search: SearchMuseumObjectsTool;
  private getMuseumObject: GetObjectTool;

  constructor() {
    this.server = new McpServer(
      {
        name: 'met-museum-mcp',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      },
    );
    this.listDepartments = new ListDepartmentsTool();
    this.search = new SearchMuseumObjectsTool();
    this.getMuseumObject = new GetObjectTool(this.server);
    this.callToolHandler = new CallToolRequestHandler(
      this.listDepartments,
      this.search,
      this.getMuseumObject,
    );
    this.listResourcesHandler = new ListResourcesHandler(
      this.getMuseumObject,
    );
    this.readResourceHandler = new ReadResourceHandler(
      this.getMuseumObject,
    );
    this.setupErrorHandling();
    this.setupTools();
    this.setupRequestHandlers();
  }

  private setupTools(): void {
    this.server.tool(
      this.listDepartments.name,
      this.listDepartments.description,
      this.listDepartments.inputSchema.shape,
      this.listDepartments.execute.bind(this.listDepartments),
    );
    this.server.tool(
      this.search.name,
      this.search.description,
      this.search.inputSchema.shape,
      this.search.execute.bind(this.search),
    );
    this.server.tool(
      this.getMuseumObject.name,
      this.getMuseumObject.description,
      this.getMuseumObject.inputSchema.shape,
      this.getMuseumObject.execute.bind(this.getMuseumObject),
    );
  }

  private setupRequestHandlers(): void {
    this.server.server.setRequestHandler(
      CallToolRequestSchema,
      async (request) => {
        return await this.callToolHandler.handleCallTool(request);
      },
    );
    this.server.server.setRequestHandler(
      ListResourcesRequestSchema,
      async () => {
        return await this.listResourcesHandler.handleListResources();
      },
    );
    this.server.server.setRequestHandler(
      ReadResourceRequestSchema,
      async (request) => {
        return await this.readResourceHandler.handleReadResource(
          request,
        );
      },
    );
  }

  private setupErrorHandling(): void {
    this.server.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    new MCPScout('pk_Q0S2vyVMJXIKo8IRfioCAC1aLKh6SIwJ').track(this.server);
    await this.server.connect(transport);
    console.error('Met Museum MCP server running on stdio');
  }
}

const server = new MetMuseumServer();
server.run().catch((error) => {
  console.error('[MCP Server Error]', error);
  process.exit(1);
});
