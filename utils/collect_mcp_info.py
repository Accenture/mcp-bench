#!/usr/bin/env python3
"""MCP Server Information Collection Script.

This module connects to all MCP servers sequentially, collects descriptions
and input schema information, and saves the results to file.

Classes:
    MCPServerInfoCollector: Collects information from MCP servers
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Use the same imports and classes as multiturn_mcp_agent.py
from mcp_modules.server_manager import MultiServerManager
from utils.local_server_config import LocalServerConfigLoader
import config.config_loader as config_loader

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_info_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MCPServerInfoCollector:
    """MCP Server Information Collector.
    
    This class connects to MCP servers and collects their tool descriptions,
    input schemas, and other metadata for documentation and analysis.
    
    Attributes:
        collected_info: Dictionary storing collected server information
        local_config_loader: Configuration loader for local servers
        connection_mode: Connection mode ('individual' or 'batch')
        
    Example:
        >>> collector = MCPServerInfoCollector("individual")
        >>> await collector.collect_all_servers_info()
    """
    
    def __init__(self, connection_mode: str = "individual") -> None:
        """Initialize collector.
        
        Args:
            connection_mode: Connection mode, "individual" for sequential connection,
                           "batch" for batch connection
                           
        Raises:
            ValueError: If connection_mode is not 'individual' or 'batch'
        """
        self.collected_info: Dict[str, Any] = {}
        self.local_config_loader: LocalServerConfigLoader = LocalServerConfigLoader()
        self.connection_mode: str = connection_mode
        
        if connection_mode not in ["individual", "batch"]:
            raise ValueError("connection_mode must be 'individual' or 'batch'")
    
    def extract_package_name(self, command: List[str]) -> str:
        """Extract the actual package name from the command array.
        
        Args:
            command: List of command parts
            
        Returns:
            Extracted package name or 'unknown-package' if not found
        """
        # Look for "run" and get the next parameter
        if "run" in command:
            idx = command.index("run")
            if idx + 1 < len(command):
                return command[idx + 1]
        
        # Look for @ prefixed packages (skip @smithery/cli)
        for arg in command:
            if arg.startswith("@") and "smithery/cli" not in arg:
                return arg
        
        # Look for non-option arguments
        for arg in command:
            if not arg.startswith("-") and "/" not in arg and arg != "npx" and not arg.endswith("npx"):
                return arg
        
        # Fallback - should not happen
        return "unknown-package"
        
    def load_server_configs(self) -> List[Dict[str, Any]]:
        """Load local server configurations from commands.json.
        
        Returns:
            List of server configuration dictionaries
        """
        logger.info("Loading local server configurations...")
        
        all_server_configs = []
        
        # Directory mapping for servers where name != directory
        dir_mapping = {
            "Bibliomantic": "bibliomantic-mcp-server",
            "BioMCP": "biomcp",
            "Call for Papers": "call-for-papers-mcp/call-for-papers-mcp-main",
            "Car Price Evaluator": "car-price-mcp-main",
            "Context7": "context7-mcp",
            "DEX Paprika": "dexpaprika-mcp",
            "FruityVice": "fruityvice-mcp",
            "Game Trends": "game-trends-mcp",
            "Huge Icons": "hugeicons-mcp-server",
            "Hugging Face": "huggingface-mcp-server",
            "Hotel MCP": "jinko-mcp",
            "Math MCP": "math-mcp",
            "NixOS": "mcp-nixos",
            "OSINT Intelligence": "mcp-osint-server",
            "Reddit": "mcp-reddit",
            "National Parks": "mcp-server-nationalparks",
            "Unit Converter": "unit-converter-mcp",
            "Medical Calculator": "medcalc",
            "Metropolitan Museum": "metmuseum-mcp",
            "Movie Recommender": "movie-recommender-mcp/movie-reccomender-mcp",
            "NASA Data": "nasa-mcp",
            "OKX Exchange": "okx-mcp",
            "Paper Search": "paper-search-mcp",
            "Scientific Computing": "scientific_computation_mcp",
            "Weather Data": "weather_mcp",
            "Wikipedia": "wikipedia-mcp",
            "Google Maps": "mcp-google-map",
            "Yahoo Finance": "yahoo-finance-mcp",
            "Amazon Shopping": "amazon-mcp-server",
            "OpenAPI Explorer": "openapi-mcp-server",
            "Time MCP": "time-mcp"
        }
        
        # Load local commands and create server configs
        for server_name, config in self.local_config_loader.local_commands.items():
            cmd_parts = config.get('cmd', '').split()
            if not cmd_parts:
                continue
                
            actual_dir = dir_mapping.get(server_name, server_name.lower().replace(' ', '-'))
            
            # Build environment variables
            env = {}
            for env_var in config.get('env', []):
                if env_var in self.local_config_loader.api_keys:
                    env[env_var] = self.local_config_loader.api_keys[env_var]
            
            # Build server config with optional HTTP transport settings
            server_config = {
                "name": server_name,
                "command": cmd_parts,
                "env": env,
                "cwd": f"mcp_servers/{actual_dir}",
                "description": ""
            }
            
            # Add HTTP transport configuration if present
            if config.get("transport") == "http":
                server_config["transport"] = "http"
                server_config["port"] = config.get("port", config_loader.get_default_http_port())
                server_config["endpoint"] = config.get("endpoint", "/mcp")
            
            all_server_configs.append(server_config)
        
        logger.info(f"Loaded {len(all_server_configs)} server configurations")
        return all_server_configs
    
    async def test_individual_server(self, config: Dict[str, Any], max_retries: int = None) -> Dict[str, Any]:
        """Test individual server connection with retry mechanism"""
        server_name = config["name"]
        logger.info(f"Testing individual server: {server_name}")
        
        if max_retries is None:
            max_retries = config_loader.get_data_collection_max_retries()
        
        last_error = None
        
        # Retry loop
        for attempt in range(max_retries):
            if attempt > 0:
                retry_delay = config_loader.get_retry_delay_base() + (attempt * config_loader.get_retry_delay_multiplier())  # Configurable retry delay
                logger.info(f"Retrying {server_name} (attempt {attempt + 1}/{max_retries}) after {retry_delay}s delay...")
                await asyncio.sleep(retry_delay)
            
            # Use single-server MultiServerManager to connect, with timeout control
            single_server_manager = None
            try:
                single_server_manager = MultiServerManager([config])
                # Set 30 second timeout to avoid infinite waiting
                available_tools = await asyncio.wait_for(
                    single_server_manager.connect_all_servers(), 
                    timeout=config_loader.get_individual_timeout()
                )
                
                # Organize tool information for this server
                tools_info = {}
                for tool_info in available_tools.values():
                    if tool_info.get("server") == server_name:
                        tools_info[tool_info["name"]] = {
                            "name": tool_info["name"],
                            "description": tool_info["description"] or "",
                            "input_schema": tool_info["input_schema"] or {}
                        }
                
                server_info = {
                    "name": server_name,  # Use package name directly, no ID needed
                    "icon": config.get("icon", ""),
                    "description": config.get("description", ""),
                    "command": config["command"],
                    "connection_status": "success" if tools_info else "success_no_tools",
                    "tools": tools_info,
                    "attempts": attempt + 1
                }
                
                if attempt > 0:
                    logger.info(f"{server_name}: Connection succeeded on attempt {attempt + 1}, {len(tools_info)} tools discovered")
                else:
                    logger.info(f"{server_name}: {len(tools_info)} tools discovered")
                return server_info
                
            except asyncio.TimeoutError:
                last_error = Exception(f"Connection timeout after {config_loader.get_individual_timeout()} seconds")
                logger.warning(f"{server_name}: Attempt {attempt + 1} timed out ({config_loader.get_individual_timeout()}s)")
                
                if attempt == max_retries - 1:
                    logger.error(f"{server_name}: All {max_retries} attempts timed out")
                    print(f"Server connection failed: {server_name} - Connection timeout (retried {max_retries} times)")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                # Simplify 502 error messages
                if "502" in error_msg or "Bad Gateway" in error_msg:
                    error_msg = "Smithery server returned 502 Bad Gateway"
                    
                logger.warning(f"{server_name}: Attempt {attempt + 1} failed - {error_msg}")
                
                # If not the last attempt, don't print error
                if attempt == max_retries - 1:
                    logger.error(f"{server_name}: All {max_retries} attempts failed")
                    print(f"Server connection failed: {server_name} - {error_msg} (retried {max_retries} times)")
                
            finally:
                # Clean up connections
                try:
                    if single_server_manager:
                        await single_server_manager.close_all_connections()
                except:
                    pass
        
        # All retries failed, return failure information
        return {
            "name": server_name,
            "icon": config.get("icon", ""),
            "description": config.get("description", ""),
            "command": config["command"],
            "connection_status": "failed",
            "error": str(last_error),
            "attempts": max_retries,
            "tools": {}
        }

    async def collect_batch_info_parallel(self, batch_configs: List[Dict[str, Any]], batch_num: int, max_retries: int = None) -> Dict[str, Any]:
        """Collect MCP server information in parallel batches (with retry mechanism)"""
        logger.info(f"Processing batch {batch_num} with {len(batch_configs)} servers in PARALLEL mode...")
        
        # Print server names in this batch
        server_names = [config["name"] for config in batch_configs]
        logger.info(f"   Servers in this batch: {', '.join(server_names)}")
        
        if max_retries is None:
            max_retries = config_loader.get_data_collection_max_retries()
        
        last_error = None
        
        # Retry loop
        for attempt in range(max_retries):
            if attempt > 0:
                retry_delay = config_loader.get_batch_retry_delay_base() + (attempt * config_loader.get_batch_retry_delay_multiplier())  # Configurable batch retry delay
                logger.info(f"Retrying batch {batch_num} (attempt {attempt + 1}/{max_retries}) after {retry_delay}s delay...")
                print(f"Retrying batch {batch_num} (attempt {attempt + 1}/{max_retries} attempts) - waiting {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            
            # Use MultiServerManager for batch connection
            server_manager = None
            try:
                server_manager = MultiServerManager(batch_configs)
                # Set timeout for batch connection
                available_tools = await asyncio.wait_for(
                    server_manager.connect_all_servers(),
                    timeout=config_loader.get_batch_timeout()  # Longer timeout for batch connections
                )
                
                # Organize server information
                batch_server_info = {}
                
                # Create info entry for each server
                for config in batch_configs:
                    server_name = config["name"]
                    server_tools = {}
                    
                    # Find tools belonging to this server
                    for tool_info in available_tools.values():
                        if tool_info.get("server") == server_name:
                            server_tools[tool_info["name"]] = {
                                "name": tool_info["name"],
                                "description": tool_info["description"] or "",
                                "input_schema": tool_info["input_schema"] or {}
                            }
                    
                    server_info = {
                        "name": server_name,
                        "icon": config.get("icon", ""),
                        "description": config.get("description", ""),
                        "command": config["command"],
                        "connection_status": "success" if server_tools else "success_no_tools",
                        "tools": server_tools,
                        "attempts": attempt + 1
                    }
                    
                    batch_server_info[server_name] = server_info
                    logger.info(f"{server_name}: {len(server_tools)} tools discovered")
                
                if attempt > 0:
                    logger.info(f"Batch {batch_num}: Connection succeeded on attempt {attempt + 1}")
                    print(f"Batch {batch_num}: Connection succeeded on attempt {attempt + 1}")
                
                return batch_server_info
                
            except asyncio.TimeoutError:
                last_error = Exception("Batch connection timeout after 60 seconds")
                logger.warning(f"Batch {batch_num}: Attempt {attempt + 1} timed out (60s)")
                
                if attempt == max_retries - 1:
                    logger.error(f"Batch {batch_num}: All {max_retries} attempts timed out")
                    print(f"Batch {batch_num} connection timeout (retried {max_retries} times)")
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if "502" in error_msg or "Bad Gateway" in error_msg:
                    error_msg = "Smithery server returned 502 Bad Gateway"
                
                logger.warning(f"Batch {batch_num}: Attempt {attempt + 1} failed - {error_msg}")
                
                if attempt == max_retries - 1:
                    logger.error(f"Batch {batch_num}: All {max_retries} attempts failed")
                    print(f"Batch {batch_num} connection failed: {error_msg} (retried {max_retries} times)")
                
            finally:
                # Clean up connections
                if server_manager:
                    await server_manager.close_all_connections()
                    logger.info(f"Batch {batch_num} connections closed")
        
        # All retries failed, return failure status
        failed_batch_info = {}
        for config in batch_configs:
            server_name = config["name"]
            failed_batch_info[server_name] = {
                "name": server_name,
                "icon": config.get("icon", ""),
                "description": config.get("description", ""),
                "command": config["command"],
                "connection_status": "failed",
                "error": str(last_error) if last_error else "Batch connection failed",
                "attempts": max_retries,
                "tools": {}
            }
        return failed_batch_info

    async def collect_batch_info(self, batch_configs: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """Collect batch of MCP server info (individual or batch mode)"""
        if self.connection_mode == "batch":
            return await self.collect_batch_info_parallel(batch_configs, batch_num)
        else:
            return await self.collect_batch_info_individual(batch_configs, batch_num)
    
    async def collect_batch_info_individual(self, batch_configs: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """Collect MCP server information individually"""
        logger.info(f"Processing batch {batch_num} with {len(batch_configs)} servers in INDIVIDUAL mode...")
        
        # Print server names in this batch
        server_names = [config["name"] for config in batch_configs]
        logger.info(f"   Servers in this batch: {', '.join(server_names)}")
        
        # Test servers individually
        batch_server_info = {}
        
        for i, config in enumerate(batch_configs):
            server_info = await self.test_individual_server(config)
            batch_server_info[server_info["name"]] = server_info
            
            # Add delay after each server test to avoid stressing Smithery servers
            if i < len(batch_configs) - 1:  # Not the last server in batch
                delay = 2.0  # 2 second delay between servers
                logger.info(f"Waiting {delay}s before testing next server...")
                await asyncio.sleep(delay)
        
        return batch_server_info

    async def collect_all_info(self) -> Dict[str, Any]:
        """Collect all MCP server information, process in batches"""
        logger.info(f"Starting MCP server information collection in {self.connection_mode.upper()} mode...")
        
        # Set correct PATH environment variable
        node_path = "/Users/zhenting.wang/.nvm/versions/node/v22.16.0/bin"
        current_path = os.environ.get("PATH", "")
        if node_path not in current_path:
            os.environ["PATH"] = f"{node_path}:{current_path}"
            logger.info(f"Added Node.js path to environment: {node_path}")
        
        # Load server configurations
        all_server_configs = self.load_server_configs()
        
        # Process configurations in batches
        batch_size = 5
        all_server_info = {}
        total_tools = 0
        successful_connections = 0
        
        # Process servers in batches
        for i in range(0, len(all_server_configs), batch_size):
            batch_configs = all_server_configs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Starting batch {batch_num}/{(len(all_server_configs) + batch_size - 1) // batch_size}")
            
            # Collect information for this batch
            batch_info = await self.collect_batch_info(batch_configs, batch_num)
            
            # Merge into total results
            all_server_info.update(batch_info)
            
            # Count results for this batch
            batch_tools = sum(len(server["tools"]) for server in batch_info.values())
            batch_success = len([s for s in batch_info.values() if s["connection_status"].startswith("success")])
            
            total_tools += batch_tools
            successful_connections += batch_success
            
            logger.info(f"Batch {batch_num} complete: {batch_success}/{len(batch_configs)} servers, {batch_tools} tools")
            
            # Longer rest between batches to let Smithery servers recover
            if i + batch_size < len(all_server_configs):
                batch_delay = 5.0  # 5 second delay between batches
                logger.info(f"Waiting {batch_delay}s before next batch...")
                await asyncio.sleep(batch_delay)
        
        # Calculate detailed statistics
        failed_servers = []
        servers_needed_retry = []
        retry_stats = {"servers_needed_retry": 0, "total_retry_attempts": 0}
        
        for server_info in all_server_info.values():
            if server_info["connection_status"] == "failed":
                failed_servers.append({
                    "name": server_info["name"],
                    "error": server_info.get("error", "Unknown error"),
                    "attempts": server_info.get("attempts", 1)
                })
            
            # Count retry attempts
            attempts = server_info.get("attempts", 1)
            if attempts > 1:
                retry_stats["servers_needed_retry"] += 1
                retry_stats["total_retry_attempts"] += attempts - 1
                servers_needed_retry.append({
                    "name": server_info["name"],
                    "attempts": attempts,
                    "status": server_info["connection_status"],
                    "tools_count": len(server_info.get("tools", {}))
                })
        
        # Add summary information
        summary = {
            "collection_timestamp": datetime.now().isoformat(),
            "total_servers": len(all_server_configs),
            "successful_connections": successful_connections,
            "failed_connections": len(all_server_configs) - successful_connections,
            "total_tools_discovered": total_tools,
            "batch_size": batch_size,
            "total_batches": (len(all_server_configs) + batch_size - 1) // batch_size,
            "connection_mode": self.connection_mode,
            "retry_statistics": retry_stats,
            "servers_needed_retry": servers_needed_retry,
            "failed_servers": failed_servers
        }
        
        result = {
            "summary": summary,
            "servers": all_server_info
        }
        
        logger.info(f"Collection complete: {successful_connections}/{len(all_server_configs)} servers connected, {total_tools} tools discovered")
        return result
    
    def save_to_json(self, data: Dict[str, Any], filename: str = "mcp_servers_info.json"):
        """Save data to JSON file"""
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filepath.absolute()}")
    
    def save_to_markdown(self, data: Dict[str, Any], filename: str = "mcp_servers_info.md"):
        """Save data to Markdown file"""
        filepath = Path(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# MCP Server Information Summary\n\n")
            
            # Write summary information
            summary = data["summary"]
            f.write("## Summary Information\n\n")
            f.write(f"- **Collection Time**: {summary['collection_timestamp']}\n")
            f.write(f"- **Connection Mode**: {summary.get('connection_mode', 'unknown').upper()}\n")
            f.write(f"- **Total Servers**: {summary['total_servers']}\n")
            f.write(f"- **Successful Connections**: {summary['successful_connections']}\n")
            f.write(f"- **Failed Connections**: {summary['failed_connections']}\n")
            f.write(f"- **Total Tools Discovered**: {summary['total_tools_discovered']}\n")
            
            if summary['retry_statistics']['servers_needed_retry'] > 0:
                f.write(f"- **Servers That Needed Retry**: {summary['retry_statistics']['servers_needed_retry']}\n")
                f.write(f"- **Total Retry Attempts**: {summary['retry_statistics']['total_retry_attempts']}\n")
            
            f.write("\n")
            
            # Write servers that needed retry list
            if summary.get('servers_needed_retry'):
                f.write("## Servers That Needed Retry\n\n")
                for server in summary['servers_needed_retry']:
                    status = "success" if server['status'] == "success" else "failed"
                    f.write(f"- **{server['name']}**: {server['attempts']} attempts, {server['tools_count']} tools, final status: {status}\n")
                f.write("\n")
            
            # Write failed servers list
            if summary.get('failed_servers'):
                f.write("## Failed Servers\n\n")
                for failed in summary['failed_servers']:
                    f.write(f"- **{failed['name']}**: {failed['error']} (attempted {failed['attempts']} times)\n")
                f.write("\n")
            
            # Write detailed information for each server
            f.write("## Server Details\n\n")
            
            for server_name, server_info in data["servers"].items():
                f.write(f"### {server_info.get('icon', '')} {server_info['name']}\n\n")
                f.write(f"**Description**: {server_info['description']}\n\n")
                f.write(f"**Connection Status**: {server_info['connection_status']}\n\n")
                
                if server_info.get("error"):
                    f.write(f"**Error Message**: {server_info['error']}\n\n")
                
                if server_info["tools"]:
                    f.write(f"**Available Tools** ({len(server_info['tools'])} ):\n\n")
                    
                    for tool_name, tool_info in server_info["tools"].items():
                        f.write(f"#### {tool_name}\n\n")
                        f.write(f"**Description**: {tool_info['description']}\n\n")
                        f.write("**Input Parameters**:\n")
                        f.write("```json\n")
                        f.write(json.dumps(tool_info['input_schema'], indent=2, ensure_ascii=False))
                        f.write("\n```\n\n")
                else:
                    f.write("**Available Tools**: None\n\n")
                
                f.write("---\n\n")
        
        logger.info(f"Markdown documentation saved to {filepath.absolute()}")

async def main():
    """Main function"""
    import argparse
    
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='MCP Server Information Collection Tool')
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['individual', 'batch'], 
        default='individual',
        help='Connection mode: individual (sequential, default) or batch (parallel)'
    )
    
    args = parser.parse_args()
    
    # Create collector instance
    collector = MCPServerInfoCollector(connection_mode=args.mode)
    
    print(f"\nUsing {args.mode.upper()} mode to collect MCP server information")
    if args.mode == "individual":
        print("   - Connect servers individually, more stable but slower")
        print("   - Connection failures automatically retry 3 times")
    else:
        print("   - Batch parallel connection, faster but potentially unstable")
        print("   - When batch fails, all servers marked as failed")
    print()
    
    try:
        # Collect all server information
        all_info = await collector.collect_all_info()
        
        # Save to files
        collector.save_to_json(all_info)
        collector.save_to_markdown(all_info)
        
        summary = all_info['summary']
        print(f"\nInformation collection completed!")
        print(f"Summary: {summary['successful_connections']}/{summary['total_servers']} servers connected")
        print(f"Total tools discovered: {summary['total_tools_discovered']}")
        print(f"Connection mode: {summary['connection_mode'].upper()}")
        
        if summary['retry_statistics']['servers_needed_retry'] > 0:
            print(f"\nRetry statistics: {summary['retry_statistics']['servers_needed_retry']} servers needed retry, {summary['retry_statistics']['total_retry_attempts']} total retry attempts")
            
            # Show servers that needed retry details
            if summary['servers_needed_retry']:
                print(f"\nServers that needed retry ({len(summary['servers_needed_retry'])}):")
                for server in summary['servers_needed_retry']:
                    status_symbol = "[SUCCESS]" if server['status'] == "success" else "[FAILED]"
                    print(f"   {status_symbol} {server['name']}: {server['attempts']} attempts, {server['tools_count']} tools found, final status: {server['status']}")
        
        if summary['failed_servers']:
            print(f"\nFailed servers ({len(summary['failed_servers'])}):")
            for failed in summary['failed_servers']:
                print(f"   - {failed['name']}: {failed['error'][:80]}{'...' if len(failed['error']) > 80 else ''} (attempted {failed['attempts']} times)")
        
        print(f"\nFiles saved: mcp_servers_info.json, mcp_servers_info.md")
        
        # Print servers with 0 tools discovered
        servers_with_no_tools = []
        for server_name, server_info in all_info['servers'].items():
            if server_info['connection_status'] in ['success_no_tools'] and len(server_info.get('tools', {})) == 0:
                servers_with_no_tools.append(server_name)
        
        if servers_with_no_tools:
            print(f"\nServers with 0 tools discovered ({len(servers_with_no_tools)}):")
            for server_name in servers_with_no_tools:
                print(f"   - {server_name}")
        else:
            print(f"\nAll successfully connected servers returned tools!")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())