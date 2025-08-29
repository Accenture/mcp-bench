#!/usr/bin/env python3
"""
Unified Benchmark Task Generator
Handles both single-server and multi-server task generation
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from synthesis.task_synthesis import TaskSynthesizer
from utils.collect_mcp_info import MCPServerInfoCollector
from utils.local_server_config import LocalServerConfigLoader
from mcp_modules.server_manager import MultiServerManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkTaskGenerator:
    """Unified benchmark task generator for single and multi-server configurations"""
    
    def __init__(
        self, 
        filter_problematic: bool = False,
        tasks_per_server: int = 1,
        max_retries: int = 3
    ):
        """
        Initialize the benchmark generator
        
        Args:
            filter_problematic: Whether to filter out problematic servers/tools
            tasks_per_server: Number of tasks to generate per server
            max_retries: Maximum retry attempts for failed servers
        """
        self.filter_problematic = filter_problematic
        self.tasks_per_server = tasks_per_server  # Keep this for compatibility
        self.max_retries = max_retries
        
        # Load available servers for distraction selection
        self.all_server_names = self._load_available_servers()
        
        # Initialize components
        self.local_config_loader = LocalServerConfigLoader()
        self.info_collector = MCPServerInfoCollector()
        
        # Initialize LLM provider for TaskSynthesizer
        from openai import AsyncAzureOpenAI
        from llm.provider import LLMProvider
        import os
        
        azure_client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-12-01-preview"
        )
        llm_provider = LLMProvider(azure_client, "o4-mini", "azure")
        
        # TaskSynthesizer only takes llm_provider
        self.synthesizer = TaskSynthesizer(llm_provider)
        
        # Store tasks_per_server for later use
        self.tasks_per_server_config = tasks_per_server
        
        # Load server configurations
        self.server_configs = self._load_server_configs()
        
    def _load_server_configs(self) -> List[Dict[str, Any]]:
        """Load all server configurations"""
        all_configs = []
        
        # Load from local configurations
        for server_name, config in self.local_config_loader.local_commands.items():
            if config.get("command"):
                all_configs.append({
                    "name": server_name,
                    "command": config["command"],
                    "args": config.get("args", []),
                    "env": config.get("env", {}),
                    "description": config.get("description", "")
                })
        
        # Load from MCP info collector
        collected_configs = self.info_collector.load_server_configs()
        for config in collected_configs:
            # Check if not already in local configs
            if not any(c["name"] == config["name"] for c in all_configs):
                all_configs.append(config)
        
        logger.info(f"Loaded {len(all_configs)} server configurations")
        return all_configs
    
    # ========== Helper Methods ==========
    
    def _format_task(self, task: Dict[str, Any], required_servers: List[str] = None) -> Dict[str, Any]:
        """Format a generated task into standard structure"""
        # Get base task description
        task_desc = task.get("final_task", task.get("task_description", ""))
        
        # Get fuzzy description - try multiple possible field names
        fuzzy_desc = task.get("final_fuzzy", task.get("fuzzy_description", ""))
        # Note: If fuzzy_desc is empty, it means FuzzyTaskGenerator failed
        # We keep it empty to expose the issue rather than hiding it with a fallback
        
        # Get dependency analysis if present
        dependency_analysis = task.get("dependency_analysis", "")
        
        # Get dependency structures and remove parallel_groups from each structure
        dep_structures = task.get("generation_metadata", {}).get("dependency_structures", task.get("dependency_structures", []))
        cleaned_structures = []
        for struct in dep_structures:
            # Create a copy of the structure without parallel_groups
            cleaned_struct = {k: v for k, v in struct.items() if k != "parallel_groups"}
            cleaned_structures.append(cleaned_struct)
        
        # Extract required tools to determine servers used in task
        required_tools = task.get("required_tools", [])
        if not required_servers:
            # Extract server names from required tools (format: "Server Name:tool_name")
            required_servers = []
            for tool in required_tools:
                if ":" in tool:
                    server_name = tool.split(":")[0]
                    if server_name not in required_servers:
                        required_servers.append(server_name)
        
        # Select fixed distraction servers for this task
        distraction_servers = self._select_distraction_servers(required_servers)
        
        return {
            "task_id": task.get("task_id", ""),
            "task_description": task_desc,
            "fuzzy_description": fuzzy_desc,
            "dependency_analysis": dependency_analysis,
            "distraction_servers": distraction_servers
        }
    
    
    def _filter_configs(
        self,
        configs: List[Dict[str, Any]],
        servers: Optional[List[str]] = None,
        skip: int = 0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Filter server configurations based on criteria"""
        filtered = configs
        
        # Filter by specified servers
        if servers:
            filtered = [c for c in filtered if c["name"] in servers]
        
        # Apply skip and limit
        if skip > 0:
            filtered = filtered[skip:]
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def _build_task_result(
        self,
        server_name: str,
        success: bool,
        tasks: List[Dict] = None,
        error: str = None,
        attempts: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """Build standardized task result"""
        result = {
            "server_name": server_name,
            "server_description": kwargs.get("description", ""),
            "generation_status": "success" if success else "failed",
            "connection_attempts": attempts
        }
        
        if success:
            result["tasks"] = tasks or []
        else:
            result["tasks"] = []
            result["error_message"] = error or "Unknown error"
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in ["description"]:
                result[key] = value
        
        return result
    
    async def _generate_with_retry(
        self,
        configs: List[Dict[str, Any]],
        name: str,
        progress: str = "",
        return_raw: bool = False
    ) -> Dict[str, Any]:
        """Generate tasks with retry logic
        
        Args:
            configs: Server configurations
            name: Name for logging
            progress: Progress string for logging
            return_raw: If True, return raw tasks without formatting
        
        Returns:
            Dict with status, tasks (formatted or raw), and attempts
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            server_manager = None
            try:
                logger.info(f"{progress} Attempting to generate task for {name} (attempt {attempt})")
                
                # Connect to server to get tools
                server_manager = MultiServerManager(configs)
                tools = await asyncio.wait_for(
                    server_manager.connect_all_servers(),
                    timeout=60.0
                )
                
                if not tools:
                    last_error = f"No tools found for server {name}"
                    logger.warning(f"{progress} {last_error}")
                    await server_manager.close_all_connections()
                    continue
                
                # Filter problematic tools if enabled
                if self.filter_problematic:
                    # Load problematic tools from config
                    from config.config_loader import get_problematic_tools
                    problematic_tools = get_problematic_tools()
                    filtered_tools = {}
                    for tool_name, tool_info in tools.items():
                        if tool_name not in problematic_tools:
                            filtered_tools[tool_name] = tool_info
                    
                    removed_count = len(tools) - len(filtered_tools)
                    if removed_count > 0:
                        logger.info(f"{progress} Filtered out {removed_count} problematic tools")
                    tools = filtered_tools
                
                logger.info(f"{progress} Connected to {name}: {len(tools)} tools discovered")
                
                # Use TaskSynthesizer to generate tasks
                # For multi-server, combine server names with '+'
                if len(configs) > 1:
                    server_names = [c.get('name', '') for c in configs]
                    server_name = '+'.join(server_names) if server_names else name
                else:
                    server_name = configs[0].get('name', name) if configs else name
                generated_tasks = await asyncio.wait_for(
                    self.synthesizer.generate_tasks(tools, server_name, self.tasks_per_server),
                    timeout=1000.0
                )
                
                # Disconnect from server
                await server_manager.close_all_connections()
                
                # Process generated tasks
                tasks = []
                raw_tasks = generated_tasks if generated_tasks else []
                if not return_raw and generated_tasks:
                    for task in generated_tasks:
                        tasks.append(self._format_task(task))
                
                if raw_tasks:
                    return {
                        "status": "success",
                        "tasks": raw_tasks if return_raw else tasks,
                        "raw_tasks": raw_tasks,
                        "attempts": attempt
                    }
                else:
                    last_error = "No tasks generated"
                    
            except asyncio.TimeoutError:
                last_error = f"Timeout after 1000 seconds (attempt {attempt})"
                logger.warning(f"{progress} {last_error}")
                if server_manager:
                    try:
                        await server_manager.close_all_connections()
                    except Exception as e:
                        logger.warning(f"Error closing connections: {e}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"{progress} Error: {last_error}")
                if server_manager:
                    try:
                        await server_manager.close_all_connections()
                    except Exception as e:
                        logger.warning(f"Error closing connections: {e}")
            
            # Retry delay
            if attempt < self.max_retries:
                delay = 5 * attempt
                logger.info(f"{progress} Retrying {name} after {delay}s...")
                await asyncio.sleep(delay)
        
        # All attempts failed
        return {
            "status": "failed",
            "error": f"Failed after {self.max_retries} attempts. Last error: {last_error}",
            "attempts": self.max_retries
        }
    
    def _save_json(self, data: Dict[str, Any], output_file: str, log_message: str = None) -> None:
        """Save data to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if log_message:
            logger.info(log_message)
    
    # ========== Single Server Generation ==========
    
    async def generate_single_server_tasks(
        self,
        servers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        skip: int = 0,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate tasks for individual servers with incremental saving"""
        logger.info("Starting single-server task generation")
        start_time = datetime.now()
        
        # Filter configurations
        configs_to_process = self._filter_configs(
            self.server_configs, servers, skip, limit
        )
        logger.info(f"Processing {len(configs_to_process)} servers")
        
        # Process each server
        successful_servers = []
        failed_servers = []
        all_tasks = []
        
        for idx, config in enumerate(configs_to_process, 1):
            server_name = config["name"]
            progress = f"[{idx}/{len(configs_to_process)}]"
            
            logger.info(f"{progress} Processing server: {server_name}")
            
            # Generate with retry - use return_raw=True to preserve all task data
            result = await self._generate_with_retry(
                [config], server_name, progress, return_raw=True
            )
            
            # Build task result - use raw_tasks to preserve complete data
            raw_tasks = result.get("raw_tasks", result.get("tasks", []))
            task_result = self._build_task_result(
                server_name=server_name,
                success=(result["status"] == "success"),
                tasks=raw_tasks,
                error=result.get("error"),  # This can be None for success
                attempts=result["attempts"],
                description=config.get("description", "")
            )
            all_tasks.append(task_result)
            
            # Track success/failure
            if result["status"] == "success":
                successful_servers.append(server_name)
            else:
                failed_servers.append({
                    "server_name": server_name,
                    "error": result["error"],
                    "attempts": result["attempts"]
                })
            
            # Incremental save after each server
            if output_file:
                current_results = {
                    "generation_info": {
                        "timestamp": datetime.now().isoformat(),
                        "total_servers": len(configs_to_process),
                        "processed_servers": idx,
                        "successful_servers": len(successful_servers),
                        "failed_servers": len(failed_servers),
                        "generation_model": "o4-mini",
                        "tasks_per_server": self.tasks_per_server,
                        "duration": str(datetime.now() - start_time),
                        "status": "in_progress" if idx < len(configs_to_process) else "completed"
                    },
                    "server_tasks": all_tasks,
                    "failed_servers": failed_servers
                }
                self._save_json(current_results, output_file)
                logger.info(f"{progress} Progress saved to {output_file}")
            
            # Small delay between servers
            await asyncio.sleep(1)
        
        # Build final results
        final_results = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "total_servers": len(configs_to_process),
                "processed_servers": len(configs_to_process),
                "successful_servers": len(successful_servers),
                "failed_servers": len(failed_servers),
                "generation_model": "o4-mini",
                "tasks_per_server": self.tasks_per_server,
                "duration": str(datetime.now() - start_time),
                "status": "completed"
            },
            "server_tasks": all_tasks,
            "failed_servers": failed_servers
        }
        
        # Final save
        if output_file:
            self._save_json(final_results, output_file)
            logger.info(f"Final results saved to {output_file}")
        
        return final_results
    
    # ========== Multi Server Generation ==========
    
    async def generate_multi_server_tasks(
        self,
        combinations_file: str = "mcp_server_combinations.json",
        start_from: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate tasks for multi-server combinations with incremental saving"""
        logger.info("Starting multi-server task generation")
        start_time = datetime.now()
        
        # Load and prepare combinations
        all_combinations = self._prepare_combinations(combinations_file, start_from)
        logger.info(f"Processing {len(all_combinations)} combinations")
        
        # Process each combination
        results = []
        for idx, combination in enumerate(all_combinations, 1):
            result = await self._process_combination(combination, idx, len(all_combinations))
            results.append(result)
            
            # Incremental save after each combination
            if output_file:
                successful = sum(1 for r in results if r["generation_success"])
                total_tasks = sum(r.get("task_count", 0) for r in results)
                
                current_results = {
                    "generation_info": {
                        "total_combinations": len(all_combinations),
                        "processed_combinations": idx,
                        "successful_combinations": successful,
                        "failed_combinations": len(results) - successful,
                        "total_tasks": total_tasks,
                        "generation_timestamp": datetime.now().isoformat(),
                        "generation_duration": str(datetime.now() - start_time),
                        "status": "in_progress" if idx < len(all_combinations) else "completed"
                    },
                    "combinations": results
                }
                self._save_json(current_results, output_file)
                logger.info(f"[{idx}/{len(all_combinations)}] Progress saved to {output_file}")
            
            # Small delay between combinations
            await asyncio.sleep(2)
        
        # Calculate final statistics
        successful = sum(1 for r in results if r["generation_success"])
        total_tasks = sum(r.get("task_count", 0) for r in results)
        
        final_results = {
            "generation_info": {
                "total_combinations": len(all_combinations),
                "processed_combinations": len(all_combinations),
                "successful_combinations": successful,
                "failed_combinations": len(results) - successful,
                "total_tasks": total_tasks,
                "generation_timestamp": datetime.now().isoformat(),
                "generation_duration": str(datetime.now() - start_time),
                "status": "completed"
            },
            "combinations": results
        }
        
        # Final save
        if output_file:
            self._save_json(final_results, output_file)
            logger.info(f"Final results saved to {output_file}")
        
        return final_results
    
    def _prepare_combinations(
        self,
        combinations_file: str,
        start_from: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Load and prepare combinations for processing"""
        # Load combinations file
        combinations_path = Path(combinations_file)
        if not combinations_path.exists():
            combinations_path = Path(__file__).parent / combinations_file
            if not combinations_path.exists():
                raise FileNotFoundError(f"Combinations file not found: {combinations_file}")
        
        with open(combinations_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        combinations = data.get("mcp_server_combinations", {})
        
        # Flatten all combinations
        all_combinations = []
        for combo_type, combos in combinations.items():
            if isinstance(combos, list):
                for combo in combos:
                    combo["combination_type"] = combo_type
                    all_combinations.append(combo)
        
        # Start from specific combination if requested
        if start_from:
            start_idx = next(
                (i for i, c in enumerate(all_combinations) if c.get("name") == start_from),
                0
            )
            all_combinations = all_combinations[start_idx:]
            logger.info(f"Starting from combination: {start_from}")
        
        logger.info(f"Loaded {len(all_combinations)} combinations")
        return all_combinations
    
    async def _process_combination(
        self,
        combination: Dict[str, Any],
        idx: int,
        total: int
    ) -> Dict[str, Any]:
        """Process a single combination"""
        combination_name = combination.get("name")
        server_names = combination.get("servers", [])
        description = combination.get("description", "")
        combination_type = combination.get("combination_type", "")
        
        progress = f"[{idx}/{total}]"
        
        # Build base result
        base_result = {
            "combination_name": combination_name,
            "combination_type": combination_type,
            "servers": server_names,
            "description": description
        }
        
        logger.info(f"{progress} Processing combination: {combination_name}")
        
        # Get server configurations
        server_configs = []
        for server_name in server_names:
            config = next((c for c in self.server_configs if c["name"] == server_name), None)
            if config is None:
                logger.error(f"Server configuration not found: {server_name}")
                return {
                    **base_result,
                    "generated_tasks": [],
                    "task_count": 0,
                    "generation_success": False,
                    "error_message": f"Server configuration not found: {server_name}"
                }
            server_configs.append(config)
        
        # Generate tasks
        try:
            result = await self._generate_with_retry(
                server_configs, combination_name, progress, return_raw=True
            )
            
            if result["status"] == "success":
                # Use raw tasks from the result
                raw_tasks = result.get("raw_tasks", result.get("tasks", []))
                return {
                    **base_result,
                    "generated_tasks": raw_tasks,
                    "task_count": len(raw_tasks),
                    "generation_success": True
                }
            else:
                return {
                    **base_result,
                    "generated_tasks": [],
                    "task_count": 0,
                    "generation_success": False,
                    "error_message": result["error"]
                }
                
        except Exception as e:
            logger.error(f"Error processing combination {combination_name}: {e}")
            return {
                **base_result,
                "generated_tasks": [],
                "task_count": 0,
                "generation_success": False,
                "error_message": str(e)
            }
    # ========== Output Methods ==========
    
    def save_results(self, results: Dict[str, Any], output_file: str) -> None:
        """Save results to JSON file"""
        self._save_json(results, output_file, f"Results saved successfully: {output_file}")
    
    def convert_multi_to_runner_format(self, results: Dict[str, Any], output_file: str) -> None:
        """Convert multi-server results to runner-compatible format"""
        logger.info(f"Converting to runner format: {output_file}")
        
        converted_tasks = []
        
        # Extract tasks from combinations
        for combination in results.get('combinations', []):
            if combination.get('generation_success', False):
                for task in combination.get('generated_tasks', []):
                    servers = combination.get('servers', [])
                    server_name = '+'.join(servers) if len(servers) > 1 else (servers[0] if servers else 'Unknown')
                    
                    converted_task = {
                        'server_name': server_name,
                        'tasks': [self._format_task(task, servers)],
                        'servers': servers,
                        'combination_name': combination.get('combination_name', ''),
                        'combination_type': combination.get('combination_type', '')
                    }
                    converted_tasks.append(converted_task)
        
        # Prepare generation_info without the first two fields
        original_generation_info = results.get('generation_info', {})
        filtered_generation_info = {}
        
        # Skip the first two fields: total_combinations and processed_combinations
        skip_fields = {'total_combinations', 'processed_combinations'}
        for key, value in original_generation_info.items():
            if key not in skip_fields:
                filtered_generation_info[key] = value
        
        output_data = {
            'generation_info': filtered_generation_info,
            'server_tasks': converted_tasks,
            'total_tasks': len(converted_tasks)
        }
        
        self._save_json(
            output_data, output_file,
            f"Runner format saved: {output_file} ({len(converted_tasks)} tasks)"
        )
    
    def convert_single_to_runner_format(self, results: Dict[str, Any], output_file: str) -> None:
        """Convert single-server results to runner-compatible format"""
        logger.info(f"Converting single-server to runner format: {output_file}")
        
        converted_tasks = []
        
        # Extract tasks from server_tasks
        for server_result in results.get('server_tasks', []):
            if server_result.get('generation_status') == 'success':
                server_name = server_result.get('server_name', 'Unknown')
                tasks = server_result.get('tasks', [])
                
                # Format raw tasks using the same logic as multi-server
                formatted_tasks = []
                for task in tasks:
                    # Tasks in single-server format are raw tasks, need formatting
                    formatted_tasks.append(self._format_task(task, [server_name]))
                
                if formatted_tasks:
                    converted_task = {
                        'server_name': server_name,
                        'tasks': formatted_tasks,
                        'servers': [server_name],  # Single server
                        'combination_name': f"Single Server: {server_name}",
                        'combination_type': 'single_server'
                    }
                    converted_tasks.append(converted_task)
        
        # Prepare generation_info without the first two fields
        original_generation_info = results.get('generation_info', {})
        filtered_generation_info = {}
        
        # Skip the first two fields: total_servers and processed_servers
        skip_fields = {'total_servers', 'processed_servers'}
        for key, value in original_generation_info.items():
            if key not in skip_fields:
                filtered_generation_info[key] = value
        
        output_data = {
            'generation_info': filtered_generation_info,
            'server_tasks': converted_tasks,
            'total_tasks': len(converted_tasks)
        }
        
        self._save_json(
            output_data, output_file,
            f"Single-server runner format saved: {output_file} ({len(converted_tasks)} tasks)"
        )
    
    def _load_available_servers(self) -> List[str]:
        """Load all available server names from commands.json"""
        try:
            commands_file = Path(__file__).parent.parent / "mcp_servers" / "commands.json"
            if commands_file.exists():
                with open(commands_file, 'r', encoding='utf-8') as f:
                    commands_data = json.load(f)
                    return list(commands_data.keys())
            else:
                logger.warning(f"Commands file not found: {commands_file}")
                return []
        except Exception as e:
            logger.error(f"Failed to load available servers: {e}")
            return []
    
    def _select_distraction_servers(self, required_servers: List[str], count: int = 10) -> List[str]:
        """
        Select random distraction servers for a task to increase diversity
        
        Args:
            required_servers: Servers already used in the task
            count: Number of distraction servers to select
            
        Returns:
            List of distraction server names
        """
        import random
        
        # Resident servers that are always available
        resident_servers = {"Time MCP"}
        
        # Create exclusion list: only required servers and resident servers
        # No need to exclude other servers - problematic tools will be filtered at runtime
        exclude_list = set(required_servers) | resident_servers
        
        # Get available distraction candidates
        available_servers = [server for server in self.all_server_names 
                           if server not in exclude_list]
        
        # Randomly select servers for diversity across different tasks
        selected_count = min(count, len(available_servers))
        selected_servers = random.sample(available_servers, selected_count)
        
        # Sort the selected servers for consistent output format
        selected_servers.sort()
        
        logger.info(f"Randomly selected {len(selected_servers)} distraction servers from {len(available_servers)} available")
        return selected_servers