"""
MCP Connector Module

Manages connections to individual MCP servers and tool discovery.
"""

import asyncio
import json
import logging
import os
import random
import socket
import subprocess
from typing import List, Dict, Any, Optional

import config.config_loader as config_loader

import aiohttp
from mcp import ClientSession, StdioServerParameters

logger = logging.getLogger(__name__)

TOOL_CALL_ERROR = 35
logging.addLevelName(TOOL_CALL_ERROR, 'TOOL CALL ERROR')


class MCPConnector:
    """Manages the connection to an MCP server and tool discovery."""
    
    def __init__(self, server_name: str, server_command: List[str], server_env: Optional[Dict[str, str]] = None, 
                 cwd: Optional[str] = None, transport_type: str = "stdio", port: int = None, endpoint: str = "/mcp"):
        self.server_name = server_name
        self.transport_type = transport_type
        self.port = port
        self.endpoint = endpoint
        
        if transport_type == "stdio":
            self.server_params = StdioServerParameters(
                command=server_command[0],
                args=server_command[1:] if len(server_command) > 1 else None,
                env=server_env or {},
                cwd=cwd
            )
        else:
            self.server_command = server_command
            self.original_server_command = server_command.copy()
            self.server_env = server_env or {}
            self.cwd = cwd
            self.server_process = None
            
        self.discovered_tools: Dict[str, Any] = {}
        self.session_id: Optional[str] = None  # Store session ID for HTTP connections

    @staticmethod
    def find_available_port(start_port: int = None, max_attempts: int = None) -> int:
        """Find an available port starting from start_port."""
        if start_port is None:
            start_port = config_loader.config.get('mcp.ports.default_port', 3001)
        if max_attempts is None:
            max_attempts = config_loader.config.get('mcp.ports.port_search_attempts', 100)
        
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")

    async def discover_tools(self, session: ClientSession) -> Dict[str, Any]:
        """Discovers all available tools and their capabilities from the server (STDIO mode)."""
        logger.info(f"Discovering available tools from {self.server_name}...")
        tools_response = await session.list_tools()
        
        server_tools = {}
        for tool in tools_response.tools:
            tool_key = f"{self.server_name}:{tool.name}"
            server_tools[tool_key] = {
                "name": tool.name,
                "original_name": tool.name,
                "server": self.server_name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        
        logger.info(f"Discovered {len(server_tools)} tools from {self.server_name}")
        # Tool descriptions commented out to reduce output
        # for name, info in server_tools.items():
        #     logger.info(f"  - {name}: {info['description']}")
        
        self.discovered_tools = server_tools
        return server_tools


    async def start_http_server(self) -> bool:
        """Starts the HTTP MCP server process with automatic port conflict resolution."""
        if self.transport_type != "http":
            raise ValueError("This method is only for HTTP transport")
            
        original_port = self.port
        max_port_attempts = config_loader.config.get('mcp.ports.port_search_attempts', 100)
        
        # Start with configured port if available, then fallback to random ports
        if original_port:
            logger.info(f"Starting with configured port {original_port} for {self.server_name}")
        else:
            logger.info(f"No configured port, using random port search for {self.server_name}")
        
        for attempt in range(max_port_attempts):
            try:
                if attempt == 0 and original_port:
                    # First attempt: use configured port
                    current_port = original_port
                    logger.info(f"Attempt {attempt + 1}: Trying configured port {current_port} for {self.server_name}")
                else:
                    # Subsequent attempts or no configured port: use random ports
                    current_port = random.randint(
                        config_loader.config.get('mcp.ports.random_port_min', 10000),
                        config_loader.config.get('mcp.ports.random_port_max', 50000)
                    )
                    if attempt == 0:
                        logger.info(f"Attempt {attempt + 1}: No configured port, trying random port {current_port} for {self.server_name}")
                    else:
                        logger.info(f"Attempt {attempt + 1}: Configured port failed, trying random port {current_port} for {self.server_name}")
                
                self.port = current_port
                
                self._update_command_port(original_port, current_port)
                
                env = os.environ.copy()
                env.update(self.server_env)
                env['MCP_SERVER_PORT'] = str(self.port)
                
                logger.info(f"Command: {' '.join(self.server_command)}")
                
                self.server_process = subprocess.Popen(
                    self.server_command,
                    cwd=self.cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                await asyncio.sleep(3)
                
                if self.server_process.poll() is None:
                    try:
                        async with aiohttp.ClientSession() as session:
                            test_url = f"http://localhost:{self.port}{self.endpoint}"
                            async with session.get(test_url, timeout=config_loader.config.get('mcp.connection.health_check_timeout', 2)) as response:
                                logger.info(f"Successfully started HTTP server for {self.server_name} on port {self.port}")
                                return True
                    except Exception:
                        logger.info(f"HTTP server process running for {self.server_name} on port {self.port}")
                        return True
                else:
                    stdout, stderr = self.server_process.communicate()
                    if "EADDRINUSE" in stderr or "address already in use" in stderr:
                        logger.warning(f"Port {self.port} in use for {self.server_name}, trying next port...")
                        continue
                    else:
                        logger.error(f"HTTP server failed to start for {self.server_name}")
                        logger.error(f"stdout: {stdout}")
                        logger.error(f"stderr: {stderr}")
                        return False
                        
            except Exception as e:
                logger.error(f"ERROR in attempt {attempt + 1} for {self.server_name}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                if attempt < max_port_attempts - 1:
                    continue
        
        logger.error(f"Failed to start HTTP server for {self.server_name} after {max_port_attempts} attempts")
        return False
    
    def _update_command_port(self, original_port: int, new_port: int):
        """Update command arguments with new port number."""
        if original_port == new_port:
            return
            
        updated_command = []
        i = 0
        
        base_command = self.original_server_command.copy()
        
        while i < len(base_command):
            arg = base_command[i]
            if f"--port {original_port}" in arg:
                updated_command.append(arg.replace(f"--port {original_port}", f"--port {new_port}"))
            elif f"--port={original_port}" in arg:
                updated_command.append(arg.replace(f"--port={original_port}", f"--port={new_port}"))
            elif arg == "--port":
                updated_command.append(arg)
                i += 1
                if i < len(base_command) and base_command[i] == str(original_port):
                    updated_command.append(str(new_port))
                elif i < len(base_command):
                    updated_command.append(base_command[i])
            else:
                updated_command.append(arg)
            i += 1
        self.server_command = updated_command

    async def discover_tools_http(self) -> Dict[str, Any]:
        """Discovers tools from HTTP MCP server."""
        if self.transport_type != "http":
            raise ValueError("This method is only for HTTP transport")
            
        base_url = f"http://localhost:{self.port}{self.endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "mcp-benchmark", "version": "1.0.0"}
                    }
                }
                
                async with session.post(
                    base_url,
                    json=init_request,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'
                    },
                    timeout=config_loader.config.get('mcp.connection.tool_discovery_timeout', 10)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Initialization failed: {error_text}")
                    
                    self.session_id = response.headers.get('mcp-session-id')
                    
                    content_type = response.headers.get('content-type', '')
                    if 'text/event-stream' in content_type:
                        response_text = await response.text()
                        lines = response_text.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    json.loads(line[6:])
                                    break
                                except json.JSONDecodeError:
                                    continue
                
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream'
                }
                if self.session_id:
                    headers['mcp-session-id'] = self.session_id
                
                async with session.post(base_url, json=tools_request, headers=headers, timeout=config_loader.config.get('mcp.connection.tool_discovery_timeout', 10)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Tools list failed: {error_text}")
                    
                    content_type = response.headers.get('content-type', '')
                    if 'text/event-stream' in content_type:
                        response_text = await response.text()
                        lines = response_text.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                try:
                                    result = json.loads(line[6:])
                                    break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        result = await response.json()
                
                tools = result.get('result', {}).get('tools', [])
                server_tools = {}
                
                for tool in tools:
                    tool_key = f"{self.server_name}:{tool['name']}"
                    server_tools[tool_key] = {
                        "name": tool['name'],
                        "original_name": tool['name'],
                        "server": self.server_name,
                        "description": tool.get('description', ''),
                        "input_schema": tool.get('inputSchema', {})
                    }
                
                logger.info(f"Discovered {len(server_tools)} tools from HTTP server {self.server_name}")
                # Tool descriptions commented out to reduce output
                # for name, info in server_tools.items():
                #     logger.info(f"  - {name}: {info['description']}")
                
                self.discovered_tools = server_tools
                return server_tools
                
        except Exception as e:
            logger.log(TOOL_CALL_ERROR, f"ERROR in discovering tools from HTTP server {self.server_name}: {e}")
            import traceback
            logger.log(TOOL_CALL_ERROR, f"Full traceback: {traceback.format_exc()}")
            raise

    async def stop_http_server(self):
        """Stops the HTTP MCP server process and ensures port is released."""
        if self.server_process:
            try:
                process_pid = self.server_process.pid
                logger.info(f"Stopping HTTP server for {self.server_name} (PID: {process_pid}, Port: {self.port})")
                
                # First try graceful termination
                self.server_process.terminate()
                await asyncio.sleep(3)  # Give more time for graceful shutdown
                
                # Check if process is still running
                if self.server_process.poll() is None:
                    logger.warning(f"Process {process_pid} didn't terminate gracefully, using KILL")
                    self.server_process.kill()
                    await asyncio.sleep(1)  # Brief wait after kill
                
                # Wait for process to fully exit
                try:
                    self.server_process.wait(timeout=config_loader.config.get('mcp.connection.process_wait_timeout', 5))
                    logger.info(f"HTTP server process {process_pid} for {self.server_name} has exited")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {process_pid} still running after kill signal")
                
                # Verify port is released by trying to bind to it
                await asyncio.sleep(1)  # Additional wait for port release
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                        test_sock.bind(('localhost', self.port))
                        logger.info(f"Port {self.port} successfully released for {self.server_name}")
                except OSError:
                    logger.warning(f"Port {self.port} may still be in use after stopping {self.server_name}")
                    
            except Exception as e:
                logger.error(f"ERROR in stopping HTTP server for {self.server_name}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
            finally:
                self.server_process = None

    @staticmethod
    def format_tools_for_prompt(tools: Dict[str, Any]) -> str:
        """Formats tool information for inclusion in an LLM prompt."""
        formatted = ""
        for name, info in tools.items():
            formatted += f"\nTool: `{name}` (Server: {info.get('server', 'unknown')})\n"
            formatted += f"  Description: {info['description']}\n"
            if info.get('input_schema'):
                schema_str = json.dumps(info['input_schema'], indent=2)
                formatted += f"  Input Schema:\n```json\n{schema_str}\n```\n"
        return formatted
    
    @staticmethod
    def estimate_tools_token_count(tools: Dict[str, Any]) -> Dict[str, int]:
        """
        Estimate token count for tool descriptions and input schemas
        
        Args:
            tools: Dictionary of tools
            
        Returns:
            Dictionary containing detailed statistics
        """
        stats = {
            'total_tokens': 0,
            'description_tokens': 0,
            'schema_tokens': 0,
            'tool_count': len(tools),
            'per_tool_tokens': {}
        }
        
        for name, info in tools.items():
            tool_tokens = 0
            description_tokens = 0
            schema_tokens = 0
            
            # Count tokens in description
            description = info.get('description', '')
            if description:
                description_tokens = len(description) // 4  # Rough estimate: 4 chars ≈ 1 token
                tool_tokens += description_tokens
            
            # Count tokens in input schema
            if info.get('input_schema'):
                schema_str = json.dumps(info['input_schema'], indent=2)
                schema_tokens = len(schema_str) // 4
                tool_tokens += schema_tokens
            
            # Count tokens for tool name and formatting markers
            tool_header = f"Tool: `{name}` (Server: {info.get('server', 'unknown')})"
            header_tokens = len(tool_header) // 4
            tool_tokens += header_tokens
            
            stats['per_tool_tokens'][name] = {
                'total': tool_tokens,
                'description': description_tokens,
                'schema': schema_tokens,
                'header': header_tokens
            }
            
            stats['total_tokens'] += tool_tokens
            stats['description_tokens'] += description_tokens
            stats['schema_tokens'] += schema_tokens
        
        return stats