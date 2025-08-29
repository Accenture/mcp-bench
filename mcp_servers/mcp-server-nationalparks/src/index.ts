#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import dotenv from 'dotenv';
import { createServer } from './server.js';

// Load environment variables
dotenv.config();

// Check for API key
if (!process.env.NPS_API_KEY) {
  console.warn('Warning: NPS_API_KEY is not set in environment variables.');
  console.warn('Get your API key at: https://www.nps.gov/subjects/developer/get-started.htm');
}

// Start the server
async function runServer() {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("National Parks MCP Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});