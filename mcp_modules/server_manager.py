"""
MCP Manager Module

Manages multiple MCP server connections and coordinates tool discovery and execution.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any

import aiohttp
from mcp import ClientSession
from mcp.client.stdio import stdio_client

import config.config_loader as config_loader

from mcp_modules.connector import MCPConnector
from mcp_modules.tool_cache import get_cache

logger = logging.getLogger(__name__)

TOOL_CALL_ERROR = 35
logging.addLevelName(TOOL_CALL_ERROR, 'TOOL CALL ERROR')


class MultiServerManager:
    """Manages multiple MCP server connections and coordinates tool discovery."""
    
    def __init__(self, server_configs: List[Dict[str, Any]]):
        self.server_configs = server_configs
        self.connectors: Dict[str, MCPConnector] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.clients: Dict[str, Any] = {}
        self.all_tools: Dict[str, Any] = {}
        
        logger.info(f"MultiServerManager initialized with {len(server_configs)} server configurations")
        
        for config in server_configs:
            server_name = config["name"]
            transport_type = config.get("transport", "stdio")
            
            self.connectors[server_name] = MCPConnector(
                server_name, 
                config["command"], 
                config.get("env"),
                config.get("cwd"),
                transport_type=transport_type,
                port=config.get("port"),
                endpoint=config.get("endpoint", "/mcp")
            )

    async def connect_all_servers(self) -> Dict[str, Any]:
        """Connects to all configured servers and discovers their tools."""
        logger.info(f"Connecting to {len(self.server_configs)} MCP servers...")
        
        connection_tasks = []
        for config in self.server_configs:
            server_name = config["name"]
            connection_tasks.append(self._connect_single_server(server_name))
        
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        successful_connections = 0
        for i, result in enumerate(results):
            server_name = self.server_configs[i]["name"]
            if isinstance(result, Exception):
                logger.error(f"Failed to connect to {server_name}: {result}")
            else:
                successful_connections += 1
                self.all_tools.update(result)
        
        logger.info(f"Successfully connected to {successful_connections}/{len(self.server_configs)} servers")
        logger.info(f"Total tools discovered: {len(self.all_tools)}")
        
        return self.all_tools

    async def _connect_single_server(self, server_name: str) -> Dict[str, Any]:
        """Connects to a single server and discovers its tools."""
        connector = self.connectors[server_name]
        
        if connector.transport_type == "http":
            return await self._connect_http_server(server_name)
        else:
            return await self._connect_stdio_server(server_name)
    
    async def _connect_stdio_server(self, server_name: str) -> Dict[str, Any]:
        """Connects to a STDIO MCP server."""
        connector = self.connectors[server_name]
        
        print(f"Connecting to {server_name} with STDIO params: {connector.server_params}")
        try:
            async with stdio_client(connector.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    tools = await connector.discover_tools(session)
                    logger.debug("tools: %s", tools)
                    
                    self.sessions[server_name] = None
                    
                    return tools
            
        except Exception as e:
            # Special handling for TaskGroup errors to get more details
            if "TaskGroup" in str(e):
                import traceback
                logger.error(f"Error connecting to STDIO server {server_name}: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                # Try to extract the actual sub-exception
                if hasattr(e, '__cause__'):
                    logger.error(f"Cause: {e.__cause__}")
                if hasattr(e, '__context__'):
                    logger.error(f"Context: {e.__context__}")
                if hasattr(e, 'exceptions'):
                    for i, sub_exc in enumerate(e.exceptions):
                        logger.error(f"Sub-exception {i+1}: {sub_exc}")
            else:
                logger.error(f"Error connecting to STDIO server {server_name}: {e}")
            raise

    async def _connect_http_server(self, server_name: str) -> Dict[str, Any]:
        """Connects to an HTTP MCP server."""
        connector = self.connectors[server_name]
        
        logger.info(f"Connecting to {server_name} with HTTP transport on port {connector.port}")
        try:
            if not await connector.start_http_server():
                raise Exception(f"Failed to start HTTP server for {server_name}")
            
            tools = await connector.discover_tools_http()
            logger.debug("tools: %s", tools)
            
            return tools
            
        except Exception as e:
            logger.error(f"ERROR in connecting to HTTP server {server_name}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            await connector.stop_http_server()
            raise

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], use_cache: bool = True) -> Any:
        """Calls a tool on the appropriate server by creating a new connection."""
        if tool_name not in self.all_tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self.all_tools[tool_name]
        server_name = tool_info["server"]
        original_tool_name = tool_info["original_name"]
        
        # Check cache first if enabled
        cache = get_cache()
        if use_cache and cache.enabled:
            cached_result = cache.get(server_name, original_tool_name, parameters)
            if cached_result is not None:
                return cached_result
        
        connector = self.connectors[server_name]
        
        logger.info(f"Calling tool '{original_tool_name}' on server '{server_name}' with params: {json.dumps(parameters)}")
        
        if connector.transport_type == "http":
            result = await self._call_tool_http(connector, original_tool_name, parameters)
        else:
            result = await self._call_tool_stdio(connector, original_tool_name, parameters)
        
        # Store in cache if successful and enabled
        # Additional validation before caching
        if use_cache and cache.enabled:
            # Only cache if result is valid and not empty
            if result and result != {} and result != []:
                cache.set(server_name, original_tool_name, parameters, result)
            else:
                logger.debug(f"Skipping cache for empty/invalid result from {server_name}:{original_tool_name}")
        
        return result
    
    async def _call_tool_stdio(self, connector: MCPConnector, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call tool using STDIO transport."""
        try:
            async with stdio_client(connector.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool_name, parameters)
        except Exception as e:
            logger.log(TOOL_CALL_ERROR, f"ERROR in calling STDIO tool '{tool_name}': {e}")
            import traceback
            logger.log(TOOL_CALL_ERROR, f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def _call_tool_http(self, connector: MCPConnector, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call tool using HTTP transport."""
        base_url = f"http://localhost:{connector.port}{connector.endpoint}"
        
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    base_url,
                    json=tool_request,
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=config_loader.get_mcp_timeout()
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "error" in result:
                        raise Exception(f"MCP Error: {result['error']}")
                    
                    # Check if we got a valid result
                    tool_result = result.get("result")
                    if tool_result is None:
                        # If no result field, check if the entire response is the result
                        if result and result != {}:
                            return result
                        else:
                            raise Exception(f"No valid result returned from tool '{tool_name}'")
                    
                    return tool_result
                    
        except Exception as e:
            logger.log(TOOL_CALL_ERROR, f"ERROR in calling HTTP tool '{tool_name}': {e}")
            import traceback
            logger.log(TOOL_CALL_ERROR, f"Full traceback: {traceback.format_exc()}")
            raise

    async def close_all_connections(self):
        """Closes all server connections."""
        logger.info(f"Closing connections to {len(self.connectors)} MCP servers...")
        
        # Stop all HTTP servers concurrently for faster cleanup
        http_cleanup_tasks = []
        for server_name, connector in self.connectors.items():
            if connector.transport_type == "http":
                logger.info(f"Scheduling cleanup for HTTP server {server_name}")
                http_cleanup_tasks.append(self._cleanup_http_server(server_name, connector))
        
        # Wait for all HTTP servers to be cleaned up
        if http_cleanup_tasks:
            logger.info(f"Waiting for {len(http_cleanup_tasks)} HTTP servers to shutdown...")
            results = await asyncio.gather(*http_cleanup_tasks, return_exceptions=True)
            
            # Log any cleanup failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    server_name = list(self.connectors.keys())[i]
                    logger.error(f"Failed to cleanup HTTP server {server_name}: {result}")
        
        # Clear references
        self.sessions.clear()
        self.clients.clear()
        logger.info("All MCP server connections closed")
    
    async def _cleanup_http_server(self, server_name: str, connector):
        """Helper method to cleanup individual HTTP server with error handling."""
        try:
            await connector.stop_http_server()
        except Exception as e:
            logger.error(f"ERROR in cleaning up HTTP server {server_name}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise