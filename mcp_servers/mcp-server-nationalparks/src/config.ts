/**
 * Configuration for the NPS MCP Server
 */

import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from .env file
dotenv.config({ path: path.resolve(__dirname, '../.env') });

export const config = {
  // NPS API Configuration
  npsApiKey: process.env.NPS_API_KEY || '',
  
  // Server Configuration
  serverName: 'mcp-server-nationalparks',
  serverVersion: '1.0.0',
  serverDescription: 'MCP server providing real-time data about U.S. national parks',
  
  // Logging Configuration
  logLevel: process.env.LOG_LEVEL || 'info',
};

// Validate required configuration
if (!config.npsApiKey) {
  console.warn('Warning: NPS_API_KEY is not set in environment variables. The server will not function correctly without an API key.');
  console.warn('Get your API key at: https://www.nps.gov/subjects/developer/get-started.htm');
}

export default config;