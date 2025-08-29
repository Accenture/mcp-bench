#!/usr/bin/env python3
"""Benchmark Runner for MCP-Bench.

This module provides the core functionality for running benchmarks across multiple
LLM models and MCP servers. It handles task execution, result collection, and 
performance evaluation.

Classes:
    ConnectionManager: Manages MCP server connections with proper async lifecycle
    BenchmarkRunner: Main benchmark orchestrator for multi-model testing
    
Functions:
    parse_arguments: Parse command-line arguments
    main: Entry point for the benchmark runner
"""

import asyncio
import json
import logging
import os
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to Python path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncAzureOpenAI

from agent.executor import TaskExecutor
from mcp_modules.server_manager_persistent import PersistentMultiServerManager
from llm.provider import LLMProvider
from llm.factory import LLMFactory
from benchmark.evaluator import TaskEvaluator
from benchmark.results_aggregator import ResultsAggregator
from benchmark.results_formatter import ResultsFormatter, execution_results_to_text
from utils.local_server_config import LocalServerConfigLoader
import config.config_loader as config_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages MCP server connections with proper async context management.
    
    This class ensures that all MCP server connections are properly established
    and cleaned up using Python's async context manager protocol. It handles
    connection lifecycle management and error recovery during cleanup.
    
    Attributes:
        server_configs: List of server configuration dictionaries
        filter_problematic_tools: Whether to filter out known problematic tools
        server_manager: Instance of PersistentMultiServerManager
        all_tools: Dictionary of all available tools from connected servers
        
    Example:
        >>> configs = [{'name': 'server1', 'command': ['python', 'server.py']}]
        >>> async with ConnectionManager(configs) as conn_mgr:
        ...     tools = conn_mgr.all_tools
        ...     # Use tools here
    """
    
    def __init__(
        self, 
        server_configs: List[Dict[str, Any]], 
        filter_problematic_tools: bool = False,
        server_manager: Optional[PersistentMultiServerManager] = None
    ) -> None:
        """Initialize the ConnectionManager.
        
        Args:
            server_configs: List of server configuration dictionaries containing
                name, command, env, cwd, and other server parameters
            filter_problematic_tools: If True, filters out known problematic tools
                that may cause execution issues
            server_manager: Optional pre-configured server manager instance
                (if not provided, will create one)
        """
        self.server_configs: List[Dict[str, Any]] = server_configs
        self.filter_problematic_tools: bool = filter_problematic_tools
        self._injected_server_manager: Optional[PersistentMultiServerManager] = server_manager
        self.server_manager: Optional[PersistentMultiServerManager] = None
        self.all_tools: Optional[Dict[str, Any]] = None
        
    async def __aenter__(self) -> 'ConnectionManager':
        """Enter the async context and establish all server connections.
        
        Creates a PersistentMultiServerManager instance and connects to all
        configured servers, discovering their available tools.
        
        Returns:
            Self reference for use in async with statement
            
        Raises:
            ConnectionError: If unable to connect to required servers
        """
        # Use injected server manager or create new one
        self.server_manager = self._injected_server_manager or PersistentMultiServerManager(
            self.server_configs, 
            self.filter_problematic_tools
        )
        self.all_tools = await self.server_manager.connect_all_servers()
        return self
        
    async def __aexit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[Exception], 
        exc_tb: Optional[Any]
    ) -> bool:
        """Exit the async context and clean up all connections.
        
        Ensures all server connections are properly closed, even if errors occur
        during cleanup. Handles CancelledError gracefully as it's expected during
        asyncio shutdown.
        
        Args:
            exc_type: Type of exception that occurred, if any
            exc_val: Exception instance that occurred, if any
            exc_tb: Exception traceback, if any
            
        Returns:
            False to propagate any exceptions that occurred in the context
        """
        if self.server_manager:
            try:
                await self.server_manager.close_all_connections()
            except asyncio.CancelledError:
                # Ignore cancel error, this is normal behavior during asyncio cleanup
                logger.debug("Ignoring CancelledError during connection cleanup")
            except Exception as e:
                # Other errors only logged, not raised
                logger.error(f"ERROR in connection cleanup: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
            finally:
                self.server_manager = None
                self.all_tools = None
        return False  # Do not suppress exceptions


class BenchmarkRunner:
    """Main benchmark runner for testing multiple LLM models.
    
    This class orchestrates the execution of benchmark tasks across multiple
    LLM models and MCP servers. It handles task loading, server configuration,
    model execution, result collection, and performance evaluation.
    
    Attributes:
        tasks_file: Path to the main tasks JSON file
        local_config_loader: Loader for local server configurations
        model_configs: Dictionary of available model configurations
        enable_distraction_servers: Whether to include distraction servers
        distraction_count: Number of distraction servers to include
        enable_judge_stability: Whether to enable judge stability checks
        filter_problematic_tools: Whether to filter known problematic tools
        concurrent_summarization: Whether to summarize results concurrently
        use_fuzzy_descriptions: Whether to use fuzzy task descriptions
        aggregator: Results aggregator instance
        formatter: Results formatter instance
    """
    
    def __init__(
        self, 
        tasks_file: Optional[str] = None, 
 
        enable_distraction_servers: Optional[bool] = None, 
        distraction_count: Optional[int] = None, 
        enable_judge_stability: Optional[bool] = None, 
        filter_problematic_tools: Optional[bool] = None, 
        concurrent_summarization: Optional[bool] = None, 
        use_fuzzy_descriptions: Optional[bool] = None,
        # Dependency injection parameters
        local_config_loader: Optional[LocalServerConfigLoader] = None,
        aggregator: Optional[ResultsAggregator] = None,
        formatter: Optional[ResultsFormatter] = None,
        judge_provider: Optional[Any] = None
    ) -> None:
        # Use config file defaults if not explicitly provided
        self.tasks_file = tasks_file or config_loader.get_tasks_file()
        
        # Use injected dependencies or create defaults
        self.local_config_loader = local_config_loader or LocalServerConfigLoader()
        self.model_configs = LLMFactory.get_model_configs()
        self._judge_provider = judge_provider  # Store injected judge provider
        
        # Use config file defaults for feature flags
        self.enable_distraction_servers = enable_distraction_servers if enable_distraction_servers is not None else True
        self.distraction_count = distraction_count if distraction_count is not None else config_loader.get_distraction_servers_count()
        self.enable_judge_stability = enable_judge_stability if enable_judge_stability is not None else config_loader.is_judge_stability_enabled()
        self.filter_problematic_tools = filter_problematic_tools if filter_problematic_tools is not None else config_loader.is_problematic_tools_filter_enabled()
        self.concurrent_summarization = concurrent_summarization if concurrent_summarization is not None else config_loader.is_concurrent_summarization_enabled()
        self.use_fuzzy_descriptions = use_fuzzy_descriptions if use_fuzzy_descriptions is not None else config_loader.use_fuzzy_descriptions()
        self.enable_concrete_description_ref = config_loader.is_concrete_description_ref_enabled()
        self.commands_config = None
        
        # Track current cumulative metrics for error handling
        self.last_cumulative_metrics = {}
        
        # Initialize results handling components (use injected or create defaults)
        self.aggregator = aggregator or ResultsAggregator()
        self.formatter = formatter or ResultsFormatter()
        
    async def load_tasks(self) -> List[Dict[str, Any]]:
        """Load benchmark tasks from JSON file.
        
        Loads and flattens tasks from various JSON formats including
        server_tasks, multi-server tasks, and combination-based tasks.
        
        Returns:
            List of task dictionaries containing task information
            
        Raises:
            FileNotFoundError: If the tasks file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        logger.info(f"Loading tasks from {self.tasks_file}")
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'server_tasks' in data:
                # Flatten nested task structure
                flattened_tasks = []
                for server_group in data['server_tasks']:
                    server_name = server_group.get('server_name', '')
                    # Handle both 'task' (single) and 'tasks' (array) formats
                    if 'task' in server_group:
                        # Single task format
                        flattened_tasks.append({
                            'server_name': server_name,
                            'task': server_group['task']
                        })
                    elif 'tasks' in server_group:
                        # Multiple tasks format
                        for task in server_group.get('tasks', []):
                            flattened_tasks.append({
                                'server_name': server_name,
                                'task': task
                            })
                tasks = flattened_tasks
            elif 'tasks' in data:
                # Multi-server task format (converted from multiserver generation)
                tasks = data['tasks']
            elif 'combinations' in data:
                # Handle combination-based task format
                flattened_tasks = []
                for combination in data['combinations']:
                    combination_name = combination.get('combination_name', 'Unknown')
                    servers = combination.get('servers', [])
                    server_name = '+'.join(servers) if servers else combination_name
                    
                    for task in combination.get('generated_tasks', []):
                        flattened_tasks.append({
                            'server_name': server_name,
                            'task': task
                        })
                tasks = flattened_tasks
            else:
                tasks = data
                
            logger.info(f"Loaded {len(tasks)} tasks from file")
            return tasks
            
        except Exception as e:
            logger.error(f"ERROR in loading tasks: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def load_server_configs(self) -> Dict[str, Any]:
        """Load local MCP server configurations."""
        logger.info(f"Loading local server configurations")
        
        try:
            # Return local_commands directly as it's already in the right format
            servers = self.local_config_loader.local_commands
            logger.info(f"Loaded configurations for {len(servers)} local servers")
            return servers
            
        except Exception as e:
            logger.error(f"ERROR in loading server configurations: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def map_server_name_to_config(self, server_name: str, servers_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map single server name to actual server configuration.
        
        Server name should be the local server name (e.g., "National Parks", "DEX Paprika")
        Multi-server combinations should be handled by the caller.
        """
        
        # Direct lookup for local servers
        if server_name in servers_info:
            server_config = servers_info[server_name]
            cmd_parts = server_config.get('cmd', '').split()
            
            if not cmd_parts:
                logger.warning(f"Empty command for server: {server_name}")
                return None
            
            # Use cwd path directly from commands.json
            cwd_path = server_config.get('cwd', '')
            if cwd_path.startswith('../'):
                # Handle relative path, convert to absolute path
                actual_cwd = f"mcp_servers/{cwd_path[3:]}"
            else:
                actual_cwd = cwd_path
            
            # Build environment variables
            env = {}
            for env_var in server_config.get('env', []):
                if env_var in self.local_config_loader.api_keys:
                    env[env_var] = self.local_config_loader.api_keys[env_var]
            
            # Build base configuration
            config = {
                'name': server_name,
                'command': cmd_parts,
                'env': env,
                'cwd': actual_cwd
            }
            
            # Add HTTP configuration if this is an HTTP server
            if server_config.get('transport') == 'http':
                config['transport'] = 'http'
                config['port'] = server_config.get('port', config_loader.get_default_port())
                config['endpoint'] = server_config.get('endpoint', '/mcp')
            
            return config
        
        # Log available servers for debugging
        logger.warning(f"No configuration found for server: {server_name}")
        logger.debug(f"Available servers: {list(servers_info.keys())}")
        return None
    
    async def load_commands_config(self) -> Dict[str, Any]:
        """Load MCP server commands configuration from commands.json."""
        commands_file = "mcp_servers/commands.json"
        logger.info(f"Loading commands configuration from {commands_file}")
        
        try:
            with open(commands_file, 'r', encoding='utf-8') as f:
                commands_config = json.load(f)
            
            logger.info(f"Loaded commands for {len(commands_config)} servers")
            return commands_config
            
        except Exception as e:
            logger.error(f"ERROR in loading commands configuration: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {}
    
    def select_random_distraction_servers(self, excluded_server_names: List[str], commands_config: Dict[str, Any], count: int = None) -> List[Dict[str, Any]]:
        """Select random distraction servers excluding the specified servers."""
        import random
        
        if count is None:
            count = config_loader.get_distraction_servers_count()
        
        if not commands_config:
            return []
        
        # Get all available server names excluding the already included servers
        available_servers = [name for name in commands_config.keys() if name not in excluded_server_names]
        
        # Randomly select up to 'count' servers
        selected_count = min(count, len(available_servers))
        selected_servers = random.sample(available_servers, selected_count)
        
        # Convert to server config format using the same method as target servers
        distraction_configs = []
        for server_name in selected_servers:
            # Use the existing mapping method to ensure consistent format
            # Create a temporary servers_info dict with the single server
            temp_servers_info = {server_name: commands_config[server_name]}
            distraction_config = self.map_server_name_to_config(server_name, temp_servers_info)
            if distraction_config:
                distraction_configs.append(distraction_config)
            else:
                logger.warning(f"Failed to create config for distraction server: {server_name}")
        
        logger.info(f"Selected {len(distraction_configs)} distraction servers: {[s['name'] for s in distraction_configs]}")
        return distraction_configs

    
    async def execute_single_task_with_model(
        self, 
        task_info: Dict[str, Any], 
        servers_info: Dict[str, Any], 
        model_name: str, 
        llm_provider: LLMProvider, 
        max_retries: Optional[int] = None, 
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a single task with a specific model with retry mechanism.
        
        Handles the complete execution lifecycle of a single task including
        server connection, task execution, result evaluation, and error recovery.
        
        Args:
            task_info: Dictionary containing task details (id, description, etc.)
            servers_info: Dictionary of available server configurations
            model_name: Name of the LLM model to use for execution
            llm_provider: LLM provider instance for model interaction
            max_retries: Maximum retry attempts (uses config default if None)
            timeout_seconds: Execution timeout (uses config default if None)
            
        Returns:
            Dictionary with execution results including status, result/error,
            execution time, and optional judge score
        """
        
        # Set default values from config
        if max_retries is None:
            max_retries = config_loader.get_max_retries()
        if timeout_seconds is None:
            timeout_seconds = config_loader.get_task_timeout()
        
        # Initialize judge provider once for this task execution
        if not hasattr(self, '_judge_provider') or self._judge_provider is None:
            azure_client = AsyncAzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=config_loader.get_azure_api_version()
            )
            self._judge_provider = LLMProvider(azure_client, "o4-mini", "azure")
        
        # Step 1: Prepare task execution information
        task_execution_info = await self._prepare_task_execution(task_info)
        logger.info(f"Executing task {task_execution_info['task_id']} with model {model_name} using {task_execution_info['description_type']} description{task_execution_info['ref_info']}")
        
        # Step 2: Prepare server configurations
        server_config_result = await self._prepare_server_configs(task_execution_info['server_name'], servers_info, task_execution_info['task_data'])
        if server_config_result['status'] == 'failed':
            return {
                'task_id': task_execution_info['task_id'],
                'server_name': task_execution_info['server_name'],
                'model_name': model_name,
                'status': 'failed',
                'error': server_config_result['error'],
                'execution_time': 0
            }
        
        all_server_configs = server_config_result['all_server_configs']
        
        # Step 3: Execute task with retry mechanism
        task_id = task_execution_info['task_id']
        task_description = task_execution_info['task_description']
        
        # Retry logic with complete reconnection
        execution_result = None
        for attempt in range(max_retries):
            start_time = time.time()
            
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} for task {task_id}")
                if attempt > 0:
                    logger.info(f"Creating fresh connection for retry...")
                
                # Use ConnectionManager to manage connection lifecycle
                async with ConnectionManager(all_server_configs, self.filter_problematic_tools) as conn_mgr:
                    if not conn_mgr.all_tools:
                        logger.error("No tools discovered from any server. Cannot execute task.")
                        if attempt < max_retries - 1:
                            logger.info(f"Will retry task {task_id} with fresh connection...")
                            await asyncio.sleep(config_loader.get_retry_delay())
                            continue
                        else:
                            return {
                                'task_id': task_id,
                                'server_name': task_execution_info['server_name'],
                                'model_name': model_name,
                                'status': 'failed',
                                'error': 'No tools discovered from any server',
                                'execution_time': time.time() - start_time
                            }
                    
                    # Create executor and execute task
                    executor = TaskExecutor(
                        llm_provider, 
                        conn_mgr.server_manager, 
                        self.concurrent_summarization
                    )
                    
                    
                    task_execution_start_time = time.time()
                    execution_start_time = time.time()
                    
                    try:
                        logger.info(f"Running full execution mode for task {task_id}")
                        result = await asyncio.wait_for(
                            executor.execute(task_description),
                            timeout=timeout_seconds
                        )
                        execution_time = time.time() - execution_start_time
                        logger.info(f"Task execution completed in {execution_time:.2f}s")
                        
                        if not isinstance(result, dict):
                            logger.error(f"execute returned {type(result)} instead of dict: {result}")
                            raise TypeError(f"execute returned {type(result)}, expected dict")
                        
                        # Add available tools to result
                        result['available_tools'] = conn_mgr.all_tools
                        
                        # Successful execution, prepare return result
                        execution_result = {
                            'status': 'success',
                            'result': result,
                            'execution_time': time.time() - start_time,
                            'agent_execution_time': time.time() - execution_start_time,
                            'task_execution_start_time': task_execution_start_time
                        }
                        
                        # Break out of retry loop
                        break
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Task {task_id} timed out after {timeout_seconds} seconds on attempt {attempt + 1}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"Will retry task {task_id} with fresh connection...")
                            await asyncio.sleep(config_loader.get_retry_delay())
                            continue
                        else:
                            return {
                                'task_id': task_id,
                                'server_name': task_execution_info['server_name'],
                                'model_name': model_name,
                                'status': 'failed',
                                'error': f'Task timed out after {max_retries} attempts',
                                'execution_time': timeout_seconds * max_retries
                            }
                    except asyncio.CancelledError:
                        logger.warning(f"Task {task_id} was cancelled (likely due to server crash) on attempt {attempt + 1}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"Will retry task {task_id} with fresh connection after cancellation...")
                            await asyncio.sleep(config_loader.get_retry_delay())
                            continue
                        else:
                            return {
                                'task_id': task_id,
                                'server_name': task_execution_info['server_name'],
                                'model_name': model_name,
                                'status': 'failed',
                                'error': 'Task cancelled due to server crash or connection loss',
                                'execution_time': time.time() - start_time
                            }
                
                # ConnectionManager will automatically clean up connections when exiting the with block
                
            except asyncio.CancelledError as e:
                logger.warning(f"Task {task_id} execution was cancelled (server crash or connection lost) on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    logger.info(f"Will retry task {task_id} with fresh connection after cancellation...")
                    await asyncio.sleep(config_loader.get_retry_delay())
                    continue
                else:
                    return {
                        'task_id': task_id,
                        'server_name': task_execution_info['server_name'],
                        'model_name': model_name,
                        'status': 'failed',
                        'error': 'Task cancelled due to server crash or connection loss',
                        'execution_time': time.time() - start_time
                    }
            except Exception as e:
                logger.error(f"Error executing task {task_id} with model {model_name} on attempt {attempt + 1}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Will retry task {task_id} with fresh connection due to error...")
                    await asyncio.sleep(config_loader.get_retry_delay())
                    continue
                else:
                    return {
                        'task_id': task_id,
                        'server_name': task_execution_info['server_name'],
                        'model_name': model_name,
                        'status': 'failed',
                        'error': str(e),
                        'execution_time': time.time() - start_time
                    }
        
        if execution_result is None:
            raise RuntimeError(f"Task {task_id} execution completed retry loop without returning - this is a bug")
        
        # Step 4: Evaluate task result and format output
        final_result = await self._evaluate_task_result(
            task_execution_info, execution_result, model_name, task_execution_info['server_name'])
        
        return final_result
    
    async def _run_single_file_benchmark_core(self, selected_models: List[str] = None, 
                                             task_limit: int = None) -> Dict[str, Any]:
        """Run benchmark across multiple models for current task file"""
        logger.info("Starting multi-model benchmark execution")
        
        # Step 1: Initialize benchmark
        init_result = await self._initialize_benchmark(selected_models, task_limit)
        if init_result['status'] == 'failed':
            # Return empty metrics on initialization failure
            return {}
        
        tasks = init_result['tasks']
        servers_info = init_result['servers_info']
        available_models = init_result['available_models']
        
        # Calculate total tasks across all models for overall progress
        total_tasks_all_models = len(available_models) * len(tasks)
        completed_tasks_all_models = 0
        
        # Step 2: Test each model
        for model_idx, (model_name, model_config) in enumerate(available_models.items(), 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing model: {model_name}")
            logger.info(f"{'='*60}")
            
            try:
                # Create LLM provider for this model
                llm_provider = await LLMFactory.create_llm_provider(model_config)
                
                model_results = []
                completed_tasks = 0
                failed_tasks = 0
                
                # Execute each task with this model
                for i, task_info in enumerate(tasks, 1):
                    # Calculate overall progress
                    overall_progress_pct = (completed_tasks_all_models / total_tasks_all_models) * 100 if total_tasks_all_models > 0 else 0
                    
                    logger.info(f"\n[Overall Progress: {completed_tasks_all_models}/{total_tasks_all_models} ({overall_progress_pct:.1f}%)]")
                    logger.info(f"Model {model_name} ({model_idx}/{len(available_models)}): Processing task {i}/{len(tasks)}")
                    
                    result = await self.execute_single_task_with_model(
                        task_info, servers_info, model_name, llm_provider)
                    
                    # execute_single_task_with_model should never return None
                    if result is None:
                        raise RuntimeError(f"execute_single_task_with_model returned None for task {i} - this is a bug")
                    
                    model_results.append(result)
                    
                    if result['status'] == 'completed':
                        completed_tasks += 1
                    else:
                        failed_tasks += 1
                    
                    # Update overall progress
                    completed_tasks_all_models += 1
                    
                    # Log task completion status
                    status_text = "SUCCESS" if result['status'] == 'completed' else "FAILED"
                    logger.info(f"[{status_text}] Task {result['task_id']} completed with status: {result['status']}")
                    
                    # Display current metrics after each task
                    if completed_tasks > 0:
                        try:
                            current_metrics = self.aggregator.aggregate_current_metrics(model_results)
                            self.formatter.format_current_metrics(model_name, completed_tasks, len(tasks), current_metrics, self.tasks_file)
                            # Update tracked cumulative metrics
                            self.last_cumulative_metrics = current_metrics.copy()
                        except Exception as e:
                            logger.error(f"Error calculating metrics for task {i}: {e}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            logger.info(f"Continuing to next task despite metrics calculation error...")
                        
                    # Small delay between tasks
                    await asyncio.sleep(config_loader.get_task_delay())
                
                logger.info(f"Model {model_name} completed: {completed_tasks}/{len(tasks)} tasks successful")
                
            except Exception as e:
                logger.error(f"Error testing model {model_name}: {e}")
                import traceback
                logger.error(f"Full traceback for model {model_name}: {traceback.format_exc()}")
        
        # Step 3: Return final cumulative metrics
        logger.info(f"MCP-Bench benchmark completed: {len(available_models)} models tested")
        # Return the final cumulative metrics directly
        return self.last_cumulative_metrics.copy()
    
    async def run_benchmark(self, selected_models: List[str] = None, task_limit: int = None) -> Dict[str, Any]:
        """Run benchmark - either single file or all files based on configuration"""
        # Determine which task files to run
        if hasattr(self, '_force_single_file') and self._force_single_file:
            # This is called from run_single_file_benchmark, use current task file
            return await self._run_single_file_benchmark_core(selected_models, task_limit)
        
        # Check if user specified specific task file(s)
        all_task_files = config_loader.get_all_task_files()
        
        # Check if user specified comma-separated task files
        if self.tasks_file and ',' in self.tasks_file:
            # User specified multiple task files via comma separation
            user_task_files = [f.strip() for f in self.tasks_file.split(',')]
            logger.info(f"Running benchmark for user-specified task files: {user_task_files}")
            all_task_files = user_task_files
        elif self.tasks_file:
            # User specified a custom single task file, run only that file
            logger.info(f"Running benchmark for specified task file: {self.tasks_file}")
            return await self._run_single_file_benchmark_core(selected_models, task_limit)
        
        # Default behavior: run all task files
        logger.info("Running comprehensive benchmark across all task files")
        
        # Store results for all files
        all_files_metrics = {}
        
        for task_file in all_task_files:
            logger.info(f"\n{'='*100}")
            logger.info(f"Starting benchmark for: {os.path.basename(task_file)}")
            logger.info(f"{'='*100}")
            
            try:
                # Temporarily set the task file
                original_task_file = self.tasks_file
                self.tasks_file = task_file
                self._force_single_file = True
                
                # Run benchmark for this file
                file_metrics = await self._run_single_file_benchmark_core(selected_models, task_limit)
                
                # Store the metrics for this file
                all_files_metrics[task_file] = file_metrics
                
            except Exception as e:
                logger.error(f"Error running benchmark for {task_file}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                # Save last cumulative metrics even on failure
                all_files_metrics[task_file] = self.last_cumulative_metrics.copy()
                
            finally:
                # Restore original settings
                self.tasks_file = original_task_file
                if hasattr(self, '_force_single_file'):
                    delattr(self, '_force_single_file')
        
        # Return metrics for all files
        return all_files_metrics
    
    async def run_single_file_benchmark(self, task_file: str, selected_models: List[str], task_limit: int = None) -> Dict[str, Any]:
        """Run benchmark for a single task file and return final metrics"""
        logger.info(f"\n{'='*100}")
        logger.info(f"Starting benchmark for task file: {os.path.basename(task_file)}")
        logger.info(f"{'='*100}")
        
        # Temporarily set the task file
        original_task_file = self.tasks_file
        self.tasks_file = task_file
        
        try:
            # Run the standard benchmark for this file
            await self._run_single_file_benchmark_core(selected_models, task_limit)
            # Directly return the final cumulative metrics
            return self.last_cumulative_metrics.copy()
            
        except Exception as e:
            logger.error(f"Error running benchmark for {task_file}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Return current cumulative metrics even on failure
            return self.last_cumulative_metrics.copy()
        finally:
            # Restore original task file
            self.tasks_file = original_task_file
    
    async def save_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Save benchmark results to JSON file"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'mcpbench_results_{timestamp}.json'
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"ERROR in saving results: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _prepare_task_execution(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare basic task execution information"""
        task_data = task_info.get('task', {})
        server_name = task_info.get('server_name', '')
        
        if self.use_fuzzy_descriptions:
            task_description = task_data.get('fuzzy_description', task_data.get('task_description', ''))
        else:
            task_description = task_data.get('task_description', '')
        
        # Prepare concrete task description for evaluation reference
        concrete_task_description = None
        if self.enable_concrete_description_ref and self.use_fuzzy_descriptions:
            concrete_task_description = task_data.get('task_description', '')
        
        task_id = task_data.get('task_id', 'unknown')
        
        description_type = "fuzzy" if self.use_fuzzy_descriptions else "detailed"
        ref_info = " (with concrete reference)" if concrete_task_description else ""
        
        return {
            'task_data': task_data,
            'server_name': server_name,
            'task_description': task_description,
            'concrete_task_description': concrete_task_description,
            'task_id': task_id,
            'description_type': description_type,
            'ref_info': ref_info
        }
    
    async def _prepare_server_configs(self, server_name: str, servers_info: Dict[str, Any], task_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare server configurations including required, resident, and distraction servers"""
        # Parse server_name to handle multi-server combinations
        if '+' in server_name:
            required_server_names = [s.strip() for s in server_name.split('+')]
            logger.info(f"Multi-server combination detected: {server_name} -> {required_server_names}")
            
            server_configs = []
            for srv_name in required_server_names:
                srv_config = self.map_server_name_to_config(srv_name, servers_info)
                if srv_config:
                    server_configs.append(srv_config)
                else:
                    return {
                        'status': 'failed',
                        'error': f'Required server configuration not found for {srv_name}'
                    }
            logger.info(f"Multi-server task requires {len(server_configs)} servers: {required_server_names}")
        else:
            server_config = self.map_server_name_to_config(server_name, servers_info)
            if not server_config:
                return {
                    'status': 'failed',
                    'error': f'Server configuration not found for {server_name}'
                }
            server_configs = [server_config]
            required_server_names = [server_name]
        
        # Prepare all server configurations
        all_server_configs = server_configs.copy()
        
        # Add resident servers
        resident_server_names = ["Time MCP"]
        existing_server_names = [cfg['name'] for cfg in server_configs]
        
        for resident_name in resident_server_names:
            if resident_name not in existing_server_names and resident_name in self.commands_config:
                resident_config = self.map_server_name_to_config(resident_name, self.commands_config)
                if resident_config:
                    all_server_configs.append(resident_config)
                    existing_server_names.append(resident_name)
                    logger.info(f"Added resident server: {resident_name}")
        
        # Add distraction servers if enabled
        if self.enable_distraction_servers and self.commands_config:
            # Process distraction servers logic...
            distraction_configs = self._prepare_distraction_servers(existing_server_names, task_data)
            all_server_configs.extend(distraction_configs)
            
            logger.info(f"Connecting to {len(all_server_configs)} servers: required={required_server_names}, resident={len([name for name in resident_server_names if name in existing_server_names])}, distractions={len(distraction_configs)}")
        else:
            resident_count = len([name for name in resident_server_names if name in existing_server_names])
            logger.info(f"Connecting to {len(all_server_configs)} server(s): required={required_server_names}, resident={resident_count} (distraction disabled)")
        
        return {
            'status': 'success',
            'all_server_configs': all_server_configs,
            'required_server_names': required_server_names
        }
    
    def _prepare_distraction_servers(self, existing_server_names: List[str], task_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Prepare distraction server configurations"""
        # Check if task has predefined distraction servers
        predefined_distraction_servers = task_data.get('distraction_servers', []) if task_data else []
        
        if predefined_distraction_servers:
            # Use predefined distraction servers from task
            logger.info(f"Using {len(predefined_distraction_servers)} predefined distraction servers from task")
            distraction_configs = []
            for server_name in predefined_distraction_servers:
                if server_name not in existing_server_names and server_name in self.commands_config:
                    # Create a temporary servers_info dict with the single server
                    temp_servers_info = {server_name: self.commands_config[server_name]}
                    distraction_config = self.map_server_name_to_config(server_name, temp_servers_info)
                    if distraction_config:
                        distraction_configs.append(distraction_config)
                    else:
                        logger.warning(f"Failed to create config for predefined distraction server: {server_name}")
                elif server_name in existing_server_names:
                    logger.debug(f"Skipping predefined distraction server {server_name} (already connected)")
                else:
                    logger.warning(f"Predefined distraction server {server_name} not found in commands config")
        else:
            # Fall back to random selection if no predefined servers
            logger.info(f"No predefined distraction servers found, using random selection")
            distraction_configs = self.select_random_distraction_servers(
                existing_server_names, self.commands_config, self.distraction_count
            )
        
        return distraction_configs
    
    async def _initialize_benchmark(self, selected_models: List[str] = None, task_limit: int = None) -> Dict[str, Any]:
        """Initialize benchmark by loading data and filtering models"""
        # Load data
        tasks = await self.load_tasks()
        servers_info = await self.load_server_configs()
        
        # Load commands configuration for distraction servers
        if self.enable_distraction_servers:
            self.commands_config = await self.load_commands_config()
            logger.info(f"Distraction servers enabled: will connect {self.distraction_count} additional servers")
        else:
            logger.info("Distraction servers disabled")
        
        if task_limit:
            tasks = tasks[:task_limit]
            logger.info(f"Limited to {task_limit} tasks")
        
        # Filter models if specified
        if selected_models:
            available_models = {name: config for name, config in self.model_configs.items() 
                             if name in selected_models}
        else:
            available_models = self.model_configs
            
        if not available_models:
            logger.error("No models available for testing")
            return {'status': 'failed', 'error': 'No models available'}
        
        logger.info(f"Testing {len(available_models)} models: {list(available_models.keys())}")
        logger.info(f"Running {len(tasks)} tasks per model")
        
        return {
            'status': 'success',
            'tasks': tasks,
            'servers_info': servers_info,
            'available_models': available_models
        }
    
    
    
    async def _evaluate_task_result(self, task_execution_info: Dict[str, Any], execution_result: Dict[str, Any], 
                                  model_name: str, server_name: str) -> Dict[str, Any]:
        """Evaluate task execution result and format output"""
        task_id = task_execution_info['task_id']
        task_description = task_execution_info['task_description']
        concrete_task_description = task_execution_info['concrete_task_description']
        dependency_analysis = task_execution_info.get('dependency_analysis', '')
        
        result = execution_result['result']
        task_execution_start_time = execution_result['task_execution_start_time']
        
        # Evaluate the results using cached judge provider
        evaluation_start_time = time.time()
        evaluator = TaskEvaluator(self._judge_provider, enable_judge_stability=self.enable_judge_stability)
        
        if not isinstance(result, dict):
            logger.error(f"Result is {type(result)} instead of dict before evaluation: {result}")
            raise TypeError(f"Result is {type(result)}, expected dict")
        
        logger.info(f"Starting evaluation for task {task_id}...")
        evaluation = await evaluator.evaluate(
            task=task_description,
            execution_results=result.get('execution_results', []),
            final_solution=result.get('solution', ''),
            total_rounds=result.get('total_rounds', 0),
            available_tools=result.get('available_tools', {}),
            planning_json_compliance=result.get('planning_json_compliance', 1.0),
            # Use uncompressed version for judge evaluation if available
            accumulated_information=result.get('accumulated_information_uncompressed') or result.get('accumulated_information', ''),
            concrete_task_description=concrete_task_description,
            dependency_analysis=dependency_analysis if config_loader.get_config('benchmark.enable_dependency_analysis_ref_for_eval', True) else None
        )
        evaluation_time = time.time() - evaluation_start_time
        
        logger.info(f"Evaluation completed in {evaluation_time:.2f}s")
        logger.info(f"Total task time: {time.time() - task_execution_start_time:.2f}s")
        
        # Print execution comparison
        logger.info("\n" + "="*80)
        logger.info(f"Task {task_id} Completed - Execution Comparison")
        logger.info("="*80)
        
        logger.info("\n EXECUTION RESULTS:")
        logger.info(execution_results_to_text(result.get('execution_results', [])))
        
        # Print final solution
        final_solution = result.get('solution', '')
        if final_solution:
            logger.info("\n FINAL SOLUTION:")
            logger.info(final_solution)
        else:
            logger.info("\n FINAL SOLUTION:")
            logger.info("No final solution provided")
        
        # Print accumulated information used for judge evaluation
        accumulated_info = result.get('accumulated_information_uncompressed') or result.get('accumulated_information', '')
        if accumulated_info:
            logger.info("\n ACCUMULATED INFORMATION (used for judge evaluation):")
            logger.info(accumulated_info)
            logger.info(f"\n[Total accumulated information length: {len(accumulated_info)} chars]")
        else:
            logger.info("\n ACCUMULATED INFORMATION:")
            logger.info("No accumulated information available")
        
        # Print individual task metrics
        if evaluation:
            logger.info("\n TASK METRICS:")
            self.formatter.format_single_task_report(task_id, evaluation, [])
        
        logger.info("="*80 + "\n")
        
        return {
            'task_id': task_id,
            'server_name': server_name,
            'model_name': model_name,
            'task_description': task_description,
            'status': 'completed',
            'execution_time': execution_result['execution_time'],
            'agent_execution_time': execution_result['agent_execution_time'],
            'evaluation_time': evaluation_time,
            'execution_results': result.get('execution_results', []),
            'final_solution': result.get('solution', ''),
            'total_rounds': result.get('total_rounds', 0),
            'evaluation': evaluation,
            # Token usage statistics
            'total_output_tokens': result.get('total_output_tokens', 0),
            'total_prompt_tokens': result.get('total_prompt_tokens', 0),
            'total_tokens': result.get('total_tokens', 0)
        }


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Multi-Model MCP Benchmark Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                                    # Run with default settings (o4-mini, all tasks)
  %(prog)s --models o4-mini                   # Test only o4-mini
  %(prog)s --models all                       # Test all available models
  %(prog)s --list-models                      # List all available models
        '''
    )
    
    parser.add_argument(
        '--models', 
        nargs='*',
        metavar='MODEL',
        help='Models to test. Use "all" for all models, or specify model names. Default: o4-mini'
    )
    
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all available models and exit'
    )
    
    parser.add_argument(
        '--output',
        metavar='FILE',
        help='Output file for results (default: auto-generated timestamp name)'
    )
    
    parser.add_argument(
        '--tasks-file',
        metavar='FILE',
        default=None,
        help='Path to tasks JSON file(s), comma-separated for multiple (default: run all task files)'
    )
    
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--distraction-count',
        type=int,
        default=config_loader.get_distraction_servers_count(),
        help='Number of distraction servers to connect (default: 10, set to 0 to disable)'
    )
    
    default_judge_stability = config_loader.is_judge_stability_enabled()
    parser.add_argument(
        '--disable-judge-stability',
        action='store_true',
        help=f'Disable LLM Judge stability testing (default: {"enabled" if default_judge_stability else "disabled"})'
    )
    
    
    default_filter_tools = config_loader.is_problematic_tools_filter_enabled()
    parser.add_argument(
        '--disable-filter-problematic-tools',
        action='store_true',
        help=f'Disable filtering of known problematic tools (default: {"enabled" if default_filter_tools else "disabled"})'
    )
    
    default_concurrent_summarization = config_loader.is_concurrent_summarization_enabled()
    parser.add_argument(
        '--disable-concurrent-summarization',
        action='store_true',
        help=f'Disable concurrent content summarization (default: {"enabled" if default_concurrent_summarization else "disabled"})'
    )
    
    default_use_fuzzy = config_loader.use_fuzzy_descriptions()
    parser.add_argument(
        '--disable-fuzzy',
        action='store_true',
        help=f'Use detailed task descriptions instead of fuzzy descriptions (default: {"fuzzy" if default_use_fuzzy else "detailed"})'
    )
    
    parser.add_argument(
        '--enable-cache',
        action='store_true',
        default=config_loader.is_cache_enabled(),
        help=f'Enable tool call caching to reduce API rate limiting (default: {config_loader.is_cache_enabled()})'
    )
    
    parser.add_argument(
        '--cache-ttl',
        type=int,
        default=config_loader.get_cache_ttl(),
        help=f'Cache TTL in hours (default: {config_loader.get_cache_ttl()}, 0 = permanent cache)'
    )
    
    parser.add_argument(
        '--cache-dir',
        default=config_loader.get_cache_dir(),
        help=f'Directory for cache storage (default: {config_loader.get_cache_dir()})'
    )
    
    return parser.parse_args()

def _parse_and_validate_args():
    """Parse and validate command line arguments"""
    args = parse_arguments()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Use provided file paths
    tasks_file = args.tasks_file
    
    # Check if files exist (handle comma-separated files)
    if tasks_file:
        if ',' in tasks_file:
            # Multiple files specified
            task_files = [f.strip() for f in tasks_file.split(',')]
            for task_file in task_files:
                if not os.path.exists(task_file):
                    logger.error(f"Tasks file not found: {task_file}")
                    sys.exit(1)
        else:
            # Single file specified
            if not os.path.exists(tasks_file):
                logger.error(f"Tasks file not found: {tasks_file}")
                sys.exit(1)
    
    # Determine if distraction is enabled based on count
    enable_distraction = args.distraction_count > 0
    
    return args, tasks_file, enable_distraction

def _create_runner_and_get_models(args, tasks_file, enable_distraction):
    """Create benchmark runner and get available models"""
    runner = BenchmarkRunner(
        tasks_file=tasks_file,
        enable_distraction_servers=enable_distraction,
        distraction_count=args.distraction_count,
        enable_judge_stability=not args.disable_judge_stability,
        filter_problematic_tools=not args.disable_filter_problematic_tools,
        concurrent_summarization=not args.disable_concurrent_summarization,
        use_fuzzy_descriptions=not args.disable_fuzzy
    )
    available_models = list(runner.model_configs.keys())
    
    return runner, available_models

def _determine_selected_models(args, available_models):
    """Determine which models to test based on arguments"""
    if args.models is None:
        # Default to o4-mini if available, otherwise first available model
        if 'o4-mini' in available_models:
            selected_models = ['o4-mini']
        elif available_models:
            selected_models = [available_models[0]]
        else:
            logger.error("No models available for testing")
            sys.exit(1)
    elif args.models == ['all']:
        selected_models = available_models
    else:
        # Validate specified models
        selected_models = []
        for model in args.models:
            if model in available_models:
                selected_models.append(model)
            else:
                logger.error(f"Model '{model}' not available. Use --list-models to see available models.")
                sys.exit(1)
    
    if not selected_models:
        logger.error("No valid models selected for testing")
        sys.exit(1)
    
    return selected_models

def _print_configuration(selected_models, available_models, runner, args):
    """Print benchmark configuration"""
    print(f"Benchmark Configuration:")
    print(f"   Selected models: {selected_models}")
    print(f"   Tasks per model: all")
    print(f"   Total available models: {len(available_models)}")
    
    # Show task file configuration
    all_task_files = config_loader.get_all_task_files()
    if runner.tasks_file and runner.tasks_file not in all_task_files:
        print(f"   Task mode: Single file specified")
        print(f"   Tasks file: {runner.tasks_file}")
    else:
        print(f"   Task mode: All files (comprehensive benchmark)")
        print(f"   Task files to run:")
        for i, task_file in enumerate(all_task_files, 1):
            print(f"     {i}. {os.path.basename(task_file)}")
    
    print(f"   Distraction servers: {runner.distraction_count} ({'enabled' if runner.enable_distraction_servers else 'disabled'})")
    print(f"   Judge stability: {'enabled' if runner.enable_judge_stability else 'disabled'}")
    print(f"   Filter problematic tools: {'enabled' if runner.filter_problematic_tools else 'disabled'}")
    print(f"   Concurrent summarization: {'enabled' if runner.concurrent_summarization else 'disabled'}")
    description_mode = 'fuzzy' if runner.use_fuzzy_descriptions else 'detailed'
    ref_mode = ' (with concrete ref)' if runner.enable_concrete_description_ref and runner.use_fuzzy_descriptions else ''
    print(f"   Task descriptions: {description_mode}{ref_mode}")
    
    # Print cache configuration
    if args.enable_cache:
        cache_ttl_desc = 'permanent' if args.cache_ttl == 0 else f'{args.cache_ttl} hours'
        print(f"   Tool cache: enabled (TTL: {cache_ttl_desc}, dir: {args.cache_dir})")
    else:
        print(f"   Tool cache: disabled")
    
    if args.output:
        print(f"   Output file: {args.output}")

async def main():
    """Main entry point for multi-model benchmark runner"""
    # Step 1: Parse and validate arguments
    args, tasks_file, enable_distraction = _parse_and_validate_args()
    
    # Step 1.5: Initialize cache if enabled
    if args.enable_cache:
        from mcp_modules.tool_cache import ToolCache, set_cache_instance
        server_whitelist = config_loader.get_cache_server_whitelist()
        cache = ToolCache(
            cache_dir=args.cache_dir,
            ttl_hours=args.cache_ttl,
            enabled=True,
            server_whitelist=server_whitelist
        )
        set_cache_instance(cache)
        
        whitelist_msg = f", whitelist: {server_whitelist}" if server_whitelist else ""
        logger.info(f"Tool cache enabled: dir={args.cache_dir}, TTL={'permanent' if args.cache_ttl == 0 else f'{args.cache_ttl} hours'}{whitelist_msg}")
        
        # Show cache stats if cache already exists
        stats = cache.get_stats()
        if stats.get('total_entries', 0) > 0:
            logger.info(f"Existing cache: {stats['total_entries']} entries, {stats['total_accesses']} total accesses")
    
    # Step 2: Create runner and get available models
    runner, available_models = _create_runner_and_get_models(args, tasks_file, enable_distraction)
    
    # Handle --list-models option
    if args.list_models:
        print("Available models:")
        for i, model in enumerate(available_models, 1):
            print(f"  {i:2d}. {model}")
        print(f"\nTotal: {len(available_models)} models")
        print("\nUsage examples:")
        print(f"  python {sys.argv[0]} --models {available_models[0] if available_models else 'MODEL_NAME'}")
        return
    
    # Step 3: Determine which models to test
    selected_models = _determine_selected_models(args, available_models)
    
    # Step 4: Print configuration
    _print_configuration(selected_models, available_models, runner, args)
    
    # Step 5: Run benchmark
    task_limit = None
    try:
        logger.info("Starting multi-model benchmark execution...")
        results = await runner.run_benchmark(
            selected_models=selected_models, 
            task_limit=task_limit
        )
        
        # Save results to JSON file
        if results:
            output_file = args.output if args.output else f'benchmark_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                logger.info(f"Results saved to {output_file}")
            except Exception as save_error:
                logger.error(f"Failed to save results to {output_file}: {save_error}")
  
    except Exception as e:
        logger.error(f"ERROR in multi-model benchmark execution: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())