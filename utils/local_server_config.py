#!/usr/bin/env python3
"""Local Server Configuration Loader.

This module handles loading local MCP server configurations and mapping
from Smithery names, providing utilities for managing server commands,
API keys, and environment variables.

Classes:
    LocalServerConfigLoader: Manages local MCP server configurations
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class LocalServerConfigLoader:
    """Loads and manages local MCP server configurations.
    
    This class handles loading server commands from JSON files, managing
    API keys, and providing configuration data for local MCP servers.
    
    Attributes:
        commands_json_path: Path to commands.json file
        api_key_path: Path to API key file
        local_commands: Dictionary of server commands
        api_keys: Dictionary of API keys
        
    Example:
        >>> loader = LocalServerConfigLoader()
        >>> config = loader.get_local_command("server-name")
    """
    
    def __init__(
        self,
        commands_json_path: str = "mcp_servers/commands.json",
        api_key_path: str = "mcp_servers/api_key"
    ) -> None:
        """Initialize the config loader.
        
        Args:
            commands_json_path: Path to commands.json file
            api_key_path: Path to API key file
        """
        self.commands_json_path = Path(commands_json_path)
        self.api_key_path = Path(api_key_path)
        
        self.local_commands: Dict[str, Any] = {}
        self.api_keys: Dict[str, str] = {}
        
        self._load_commands_json()
        self._load_api_keys()
    
    def _load_commands_json(self) -> None:
        """Load local server commands from commands.json.
        
        Raises:
            Exception: If commands.json cannot be loaded
        """
        try:
            with open(self.commands_json_path, 'r') as f:
                self.local_commands = json.load(f)
            logger.info(f"Loaded {len(self.local_commands)} local server configurations")
        except Exception as e:
            logger.error(f"Failed to load commands.json: {e}")
            raise
    
    
    def _load_api_keys(self) -> None:
        """Load API keys from api_key file.
        
        Reads key=value pairs from the API key file, ignoring comments
        and empty lines.
        """
        if not self.api_key_path.exists():
            logger.warning(f"API key file not found at {self.api_key_path}")
            return
        
        try:
            with open(self.api_key_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        self.api_keys[key.strip()] = value.strip()
            logger.info(f"Loaded {len(self.api_keys)} API keys")
        except Exception as e:
            logger.warning(f"Error loading API keys: {e}")
    
    
    def get_local_command(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get local command configuration for a server.
        
        Args:
            server_name: Name of the server to get configuration for
            
        Returns:
            Dictionary containing server configuration, or None if not found
        """
        return self.local_commands.get(server_name)
    
    
    def _parse_command_string(self, cmd_str: str) -> List[str]:
        """Parse command string into array format.
        
        Handles quoted strings and splits command by spaces.
        
        Args:
            cmd_str: Command string to parse
            
        Returns:
            List of command parts
        """
        # Simple parsing - split by spaces but handle quoted strings
        parts = []
        current = []
        in_quotes = False
        
        for char in cmd_str:
            if char == '"' and not in_quotes:
                in_quotes = True
            elif char == '"' and in_quotes:
                in_quotes = False
            elif char == ' ' and not in_quotes:
                if current:
                    parts.append(''.join(current))
                    current = []
            else:
                current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _get_working_directory(self, cmd_str: str, server_name: str) -> Optional[str]:
        """Determine the working directory for special cases.
        
        Handles relative paths and special server configurations that
        require specific working directories.
        
        Args:
            cmd_str: Command string to analyze
            server_name: Name of the server
            
        Returns:
            Absolute path to working directory, or None to use current directory
        """
        # Handle relative paths (e.g., ../mcp_servers/server-name/...)
        if "../mcp_servers/" in cmd_str:
            # Extract the server directory from the relative path
            import re
            match = re.search(r'\.\./mcp_servers/([^/]+)/', cmd_str)
            if match:
                server_dir = match.group(1)
                return str(Path(f"mcp_servers/{server_dir}").resolve())
        
        # Handle special cases that need specific working directories
        if "python -m biomcp" in cmd_str:
            return str(Path("mcp_servers/biomcp/src").resolve())
        elif "python -m mcp_server_github_trending" in cmd_str:
            return str(Path("mcp_servers/mcp-github-trending/src").resolve())
        elif "python -m mlb_stats_mcp" in cmd_str:
            return str(Path("mcp_servers/mlb-mcp").resolve())
        elif "python -m paper_search_mcp" in cmd_str:
            return str(Path("mcp_servers/paper-search-mcp").resolve())
        elif "python -m wikipedia_mcp" in cmd_str:
            return str(Path("mcp_servers/wikipedia-mcp").resolve())
        elif "python -m mcp_reddit" in cmd_str:
            return str(Path("mcp_servers/mcp-reddit/src").resolve())
        elif "npx tsx src/index.ts" in cmd_str and "finance" in server_name.lower():
            return str(Path("mcp_servers/finance-calculator").resolve())
        elif "npx tsx src/index.ts" in cmd_str and "erickwendel" in server_name.lower():
            return str(Path("mcp_servers/erickwendel-contributions-mcp").resolve())
        
        # Default to MCP-Benchmark root
        return str(Path(".").resolve())
    
    def _get_environment_variables(self, required_vars: List[str]) -> Dict[str, str]:
        """Get environment variables for server.
        
        Retrieves required environment variables from API keys or system
        environment.
        
        Args:
            required_vars: List of required environment variable names
            
        Returns:
            Dictionary of environment variable name to value mappings
        """
        env = {}
        
        # Add required environment variables from api_keys
        for var in required_vars:
            if var in self.api_keys:
                env[var] = self.api_keys[var]
            elif var in os.environ:
                env[var] = os.environ[var]
            else:
                logger.warning(f"Required environment variable not found: {var}")
        
        return env
    
    def get_all_available_local_servers(self) -> List[Dict[str, Any]]:
        """Get all available local server configurations.
        
        Returns:
            List of server configuration dictionaries
        """
        available = []
        
        for smithery_name, local_name in self.smithery_mapping.items():
            if local_name:  # Skip null mappings
                config = self.get_server_config_from_smithery(smithery_name)
                if config:
                    available.append(config)
        
        logger.info(f"Found {len(available)} available local servers")
        return available
    
    def list_unmapped_servers(self) -> List[str]:
        """List Smithery servers without local mappings.
        
        Returns:
            List of Smithery server names that have no local implementation
        """
        unmapped = []
        for smithery_name, local_name in self.smithery_mapping.items():
            if not local_name:
                unmapped.append(smithery_name)
        return unmapped


# Test the loader if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    loader = LocalServerConfigLoader()
    
    # Test getting a server config
    test_server = "@geobio/mcp-server-nationalparks"
    config = loader.get_server_config_from_smithery(test_server)
    if config:
        print(f"\nConfig for {test_server}:")
        print(json.dumps(config, indent=2))
    
    # List unmapped servers
    unmapped = loader.list_unmapped_servers()
    if unmapped:
        print(f"\nUnmapped servers ({len(unmapped)}):")
        for server in unmapped:
            print(f"  - {server}")
    
    # List all available servers
    available = loader.get_all_available_local_servers()
    print(f"\nTotal available local servers: {len(available)}")