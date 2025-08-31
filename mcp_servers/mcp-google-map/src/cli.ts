#!/usr/bin/env node

import { config as dotenvConfig } from "dotenv";
import express from "express";
import path, { resolve } from "path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import serverConfigs from "./config.js";
import { BaseMcpServer } from "./core/BaseMcpServer.js";
import { Logger } from "./index.js";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { readFileSync } from 'fs';

// Get the directory of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Try to load .env from current directory first, then from package directory
dotenvConfig({ path: resolve(process.cwd(), ".env") });
// Also try to load from the package installation directory
dotenvConfig({ path: resolve(__dirname, "../.env") });

export async function startServer(port?: number, apiKey?: string): Promise<void> {
  // Override environment variables with CLI arguments if provided
  if (port) {
    process.env.MCP_SERVER_PORT = port.toString();
  }
  if (apiKey) {
    process.env.GOOGLE_MAPS_API_KEY = apiKey;
  }

  Logger.log("🚀 Starting Google Maps MCP Server...");
  Logger.log("📍 Available tools: search_nearby, get_place_details, maps_geocode, maps_reverse_geocode, maps_distance_matrix, maps_directions, maps_elevation, echo");
  Logger.log("");

  const startPromises = serverConfigs.map(async (config) => {
    const portString = process.env[config.portEnvVar];
    if (!portString) {
      Logger.error(
        `⚠️  [${config.name}] Port environment variable ${config.portEnvVar} not set.`
      );
      Logger.log(`💡 Please set ${config.portEnvVar} in your .env file or use --port parameter.`);
      Logger.log(`   Example: ${config.portEnvVar}=3000 or --port 3000`);
      return;
    }

    const serverPort = Number(portString);
    if (isNaN(serverPort) || serverPort <= 0) {
      Logger.error(
        `❌ [${config.name}] Invalid port number "${portString}" defined in ${config.portEnvVar}.`
      );
      return;
    }

    try {
      const server = new BaseMcpServer(config.name, config.tools);
      Logger.log(
        `🔧 [${config.name}] Initializing MCP Server in HTTP mode on port ${serverPort}...`
      );
      await server.startHttpServer(serverPort);
      Logger.log(
        `✅ [${config.name}] MCP Server started successfully!`
      );
      Logger.log(`   🌐 Endpoint: http://localhost:${serverPort}/mcp`);
      Logger.log(`   📚 Tools: ${config.tools.length} available`);
    } catch (error) {
      Logger.error(
        `❌ [${config.name}] Failed to start MCP Server on port ${serverPort}:`,
        error
      );
    }
  });

  await Promise.allSettled(startPromises);

  Logger.log("");
  Logger.log("🎉 Server initialization completed!");
  Logger.log("💡 Need help? Check the README.md for configuration details.");
}

// Check if this script is being run directly
// When installed globally via npm, process.argv[1] might be a symlink like /usr/local/bin/mcp-google-map
// So we check multiple conditions to ensure the script runs properly
const isRunDirectly = process.argv[1] && (
  process.argv[1].endsWith("cli.ts") || 
  process.argv[1].endsWith("cli.js") ||
  process.argv[1].endsWith("mcp-google-map") ||
  process.argv[1].includes("mcp-google-map")
);

// For ES modules, we can also check if this file is the entry point
const isMainModule = import.meta.url === `file://${process.argv[1]}`;

if (isRunDirectly || isMainModule) {
  // Read package.json to get version
  let packageVersion = "0.0.0";
  try {
    const packageJsonPath = resolve(__dirname, "../package.json");
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    packageVersion = packageJson.version;
  } catch (e) {
    // Fallback version if package.json can't be read
    packageVersion = "0.0.0";
  }

  // Parse command line arguments
  const argv = yargs(hideBin(process.argv))
    .option('port', {
      alias: 'p',
      type: 'number',
      description: 'Port to run the MCP server on',
      default: process.env.MCP_SERVER_PORT ? parseInt(process.env.MCP_SERVER_PORT) : 3000
    })
    .option('apikey', {
      alias: 'k',
      type: 'string',
      description: 'Google Maps API key',
      default: process.env.GOOGLE_MAPS_API_KEY
    })
    .option('help', {
      alias: 'h',
      type: 'boolean',
      description: 'Show help'
    })
    .version(packageVersion)
    .alias('version', 'v')
    .example([
      ['$0', 'Start server with default settings'],
      ['$0 --port 3000 --apikey "your_api_key"', 'Start server with custom port and API key'],
      ['$0 -p 3001 -k "your_api_key"', 'Start server with short options']
    ])
    .help()
    .parseSync();

  // Show welcome message
  Logger.log("🗺️  Google Maps MCP Server");
  Logger.log("   A Model Context Protocol server for Google Maps services");
  Logger.log("");
  
  // Check for Google Maps API key
  if (!argv.apikey) {
    Logger.log("⚠️  Google Maps API Key not found!");
    Logger.log("   Please provide --apikey parameter or set GOOGLE_MAPS_API_KEY in your .env file");
    Logger.log("   Example: mcp-google-map --apikey your_api_key_here");
    Logger.log("   Or: GOOGLE_MAPS_API_KEY=your_api_key_here");
    Logger.log("");
  }
  
  startServer(argv.port, argv.apikey).catch((error) => {
    Logger.error("❌ Failed to start server:", error);
    process.exit(1);
  });
}
