#!/usr/bin/env node

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
  console.log('Starting DexPaprika MCP server test...');
  
  // Start server process
  const serverProcess = spawn('node', [path.join(__dirname, 'index.js')], {
    stdio: 'inherit'
  });
  
  // Wait for server to start
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log('\nServer started successfully! Press Ctrl+C to exit.');
  
  // Handle process exit
  process.on('SIGINT', () => {
    console.log('\nStopping server...');
    if (serverProcess && !serverProcess.killed) {
      serverProcess.kill();
    }
    process.exit(0);
  });
}

main(); 