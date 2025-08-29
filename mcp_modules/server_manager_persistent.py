"""MCP Server Manager Module with Persistent Sessions.

This module manages persistent connections to multiple MCP servers throughout
task execution to preserve state and enable efficient tool calling.

Classes:
    PersistentMultiServerManager: Manages persistent connections to multiple MCP servers
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from contextlib import AsyncExitStack

import aiohttp
from mcp import ClientSession
from mcp.client.stdio import stdio_client

import config.config_loader as config_loader
from mcp_modules.connector import MCPConnector
from mcp_modules.tool_cache import get_cache

logger = logging.getLogger(__name__)

TOOL_CALL_ERROR = 35
logging.addLevelName(TOOL_CALL_ERROR, 'TOOL CALL ERROR')


class PersistentMultiServerManager:
    """Manages multiple MCP server connections with persistent sessions.
    
    This class maintains persistent connections to multiple MCP servers,
    enabling efficient tool discovery and execution while preserving
    server state across multiple tool calls.
    
    Attributes:
        server_configs: List of server configuration dictionaries
        filter_problematic_tools: Whether to filter known problematic tools
        connectors: Dictionary mapping server names to MCPConnector instances
        sessions: Dictionary of active ClientSession instances
        exit_stack: AsyncExitStack for managing async contexts
        all_tools: Dictionary of all discovered tools
        
    Example:
        >>> configs = [{'name': 'server1', 'command': ['python', 'server.py']}]
        >>> manager = PersistentMultiServerManager(configs)
        >>> tools = await manager.connect_all_servers()
        >>> result = await manager.call_tool('server1:tool_name', {'param': 'value'})
    """
    
    def __init__(
        self, 
        server_configs: List[Dict[str, Any]], 
        filter_problematic_tools: bool = False
    ) -> None:
        self.server_configs = server_configs
        self.filter_problematic_tools = filter_problematic_tools
        self.connectors: Dict[str, MCPConnector] = {}
        
        # Store persistent sessions and their context managers
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack: AsyncExitStack = None  # Use AsyncExitStack to manage contexts properly
        
        self.all_tools: Dict[str, Any] = {}
        self._connection_tasks: Dict[str, Any] = {}  # Store connection tasks for cleanup
        
        logger.info(f"PersistentMultiServerManager initialized with {len(server_configs)} server configurations")
        
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
        """Connect to all configured servers and discover their tools.
        
        Establishes persistent connections to all configured MCP servers
        sequentially to avoid cancel scope issues. Discovers and collects
        all available tools from connected servers.
        
        Returns:
            Dictionary mapping tool names to tool information including
            server name, description, and input schema
            
        Raises:
            ConnectionError: If unable to connect to required servers
        """
        logger.info(f"Establishing persistent connections to {len(self.server_configs)} MCP servers (sequential mode)...")
        
        # Initialize AsyncExitStack to manage all contexts
        self.exit_stack = AsyncExitStack()
        
        successful_connections = 0
        for config in self.server_configs:
            server_name = config["name"]
            try:
                result = await self._connect_single_server(server_name)
                self.all_tools.update(result)
                successful_connections += 1
            except Exception as e:
                logger.error(f"ERROR in connecting to {server_name}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        logger.info(f"Successfully connected to {successful_connections}/{len(self.server_configs)} servers with persistent sessions")
        logger.info(f"Total tools discovered: {len(self.all_tools)}")
        
        # Filter problematic tools if enabled
        if self.filter_problematic_tools:
            # Load problematic tools from config
            from config.config_loader import get_problematic_tools
            problematic_tools = get_problematic_tools()
            
            filtered_tools = {}
            removed_count = 0
            for tool_name, tool_info in self.all_tools.items():
                if tool_name not in problematic_tools:
                    filtered_tools[tool_name] = tool_info
                else:
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Filtered out {removed_count} problematic tools")
                self.all_tools = filtered_tools
        
        return self.all_tools

    async def _connect_single_server(self, server_name: str) -> Dict[str, Any]:
        """Connects to a single server and maintains the session."""
        connector = self.connectors[server_name]
        
        if connector.transport_type == "http":
            return await self._connect_http_server(server_name)
        else:
            return await self._connect_stdio_server_persistent(server_name)
    
    async def _connect_stdio_server_persistent(self, server_name: str) -> Dict[str, Any]:
        """Creates and maintains a persistent STDIO connection using AsyncExitStack."""
        connector = self.connectors[server_name]
        
        logger.info(f"Creating persistent connection to {server_name}...")
        try:
            # Enter stdio context using AsyncExitStack
            stdio_ctx = stdio_client(connector.server_params)
            read, write = await self.exit_stack.enter_async_context(stdio_ctx)
            
            # Create and enter session context  
            session = ClientSession(read, write)
            await self.exit_stack.enter_async_context(session)
            await session.initialize()
            
            # Store session reference
            self.sessions[server_name] = session
            
            # Discover tools
            tools = await connector.discover_tools(session)
            
            logger.info(f"Persistent session established for {server_name} with {len(tools)} tools")
            return tools
            
        except Exception as e:
            logger.error(f"ERROR in connecting to STDIO server {server_name}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
        """Call a tool using the persistent session.
        
        Args:
            tool_name: Full tool name in format 'server:tool_name'
            parameters: Dictionary of parameters to pass to the tool
            use_cache: Whether to use cache for this call
            
        Returns:
            Tool execution result from the server
            
        Raises:
            ValueError: If the tool is not found
            Exception: If tool execution fails
        """
        if tool_name not in self.all_tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self.all_tools[tool_name]
        server_name = tool_info["server"]
        original_tool_name = tool_info["original_name"]
        
        # Log tool call with parameters
        logger.info(f"Calling tool '{original_tool_name}' on server '{server_name}'")
        logger.info(f"Tool parameters: {json.dumps(parameters, indent=2)}")
        
        # Check cache first if enabled
        cache = get_cache()
        if use_cache and cache.enabled:
            cached_result = cache.get(server_name, original_tool_name, parameters)
            if cached_result is not None:
                logger.info(f"Using cached result for {server_name}:{original_tool_name}")
                return cached_result
            else:
                logger.info(f"Cache MISS for {server_name}:{original_tool_name} - executing tool")
        
        connector = self.connectors[server_name]
        
        if connector.transport_type == "http":
            result = await self._call_tool_http(connector, original_tool_name, parameters)
        else:
            # Use persistent session
            session = self.sessions.get(server_name)
            
            if session is None:
                raise Exception(f"No persistent session found for {server_name}. Call connect_all_servers() first.")
            
            try:
                result = await session.call_tool(original_tool_name, parameters)
                logger.debug(f"Tool call successful on persistent session")
            except Exception as e:
                logger.log(TOOL_CALL_ERROR, f"ERROR in calling tool '{original_tool_name}' on persistent session: {e}")
                import traceback
                logger.log(TOOL_CALL_ERROR, f"Full traceback: {traceback.format_exc()}")
                raise
        
        # Store in cache if successful and enabled
        # Additional validation before caching
        if use_cache and cache.enabled:
            # Only cache if result is valid and not empty
            if result and result != {} and result != []:
                cache_success = cache.set(server_name, original_tool_name, parameters, result)
                if cache_success:
                    result_size = len(str(result))
                    logger.info(f"Result cached for {server_name}:{original_tool_name} (size: {result_size} bytes)")
                else:
                    logger.info(f"Result NOT cached for {server_name}:{original_tool_name} (failed validation or not in whitelist)")
            else:
                logger.info(f"Result NOT cached for {server_name}:{original_tool_name} (empty/invalid result)")
        
        return result
    
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
                # Prepare headers with session ID if available
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream'
                }
                if hasattr(connector, 'session_id') and connector.session_id:
                    headers['mcp-session-id'] = connector.session_id
                
                async with session.post(
                    base_url,
                    json=tool_request,
                    headers=headers,
                    timeout=config_loader.get_mcp_timeout()
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    # Handle both JSON and Server-Sent Events responses
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
                            # If no valid JSON found in SSE stream
                            result = {"result": response_text}
                    else:
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

    async def _cleanup_server_connection(self, server_name: str):
        """Clean up a single server connection - now handled by AsyncExitStack."""
        # Just remove the session reference
        if server_name in self.sessions:
            del self.sessions[server_name]
        logger.debug(f"Server {server_name} cleanup completed")

    async def close_all_connections(self) -> None:
        """Close all persistent server connections.
        
        Safely closes all active server connections using AsyncExitStack,
        handling any errors that occur during cleanup without raising them.
        Also stops any HTTP servers that were started.
        """
        logger.info(f"Closing {len(self.sessions)} persistent STDIO sessions...")
        
        # Close all contexts using AsyncExitStack
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.debug(f"Error closing exit stack: {e}")
            finally:
                self.exit_stack = None
        
        # Stop all HTTP servers
        http_cleanup_tasks = []
        for server_name, connector in self.connectors.items():
            if connector.transport_type == "http":
                logger.info(f"Stopping HTTP server {server_name}")
                http_cleanup_tasks.append(connector.stop_http_server())
        
        if http_cleanup_tasks:
            await asyncio.gather(*http_cleanup_tasks, return_exceptions=True)
        
        # Final cleanup of any remaining references
        self.sessions.clear()
        
        logger.info("All persistent connections closed")


# Backward compatibility
MultiServerManager = PersistentMultiServerManager