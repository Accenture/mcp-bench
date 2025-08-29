"""Configuration Loader Module.

This module provides unified management of all MCP-Bench configurations,
supporting YAML file configuration with environment variable overrides.

Classes:
    BenchmarkConfig: Singleton configuration manager for benchmark settings
"""

import yaml
import os
from typing import Dict, Any, Union, Optional, List
from pathlib import Path


class BenchmarkConfig:
    """Singleton configuration manager for benchmark settings.
    
    This class manages all benchmark configurations using a singleton pattern,
    loading settings from YAML files and allowing environment variable overrides.
    Configuration priority: environment variables > YAML file > default values.
    
    Attributes:
        _instance: Singleton instance
        _config: Loaded configuration dictionary
        
    Example:
        >>> config = BenchmarkConfig()
        >>> timeout = config.get_value('mcp.connection.http_timeout')
    """
    
    _instance: Optional['BenchmarkConfig'] = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls) -> 'BenchmarkConfig':
        """Create or return the singleton instance.
        
        Returns:
            The singleton BenchmarkConfig instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the configuration if not already loaded."""
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file with environment overrides.
        
        Loads configuration in priority order:
        1. Environment variables (highest priority)
        2. YAML configuration file
        3. Default values (lowest priority)
        """
        config_path = Path(__file__).parent / 'benchmark_config.yaml'
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file {config_path}: {e}")
                self._config = self._get_default_config()
        else:
            print(f"Config file {config_path} not found, using default configuration")
            self._config = self._get_default_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration (current hardcoded values).
        
        Returns:
            Dictionary containing all default configuration values
        """
        return {
            'mcp': {
                'connection': {
                    'http_timeout': 60,
                    'tool_discovery_timeout': 10,
                    'server_startup_timeout': 30,
                    'health_check_timeout': 2,
                    'process_wait_timeout': 5,
                    'batch_timeout': 60
                },
                'ports': {
                    'default_port': 3001,
                    'port_search_attempts': 100,
                    'random_port_min': 10000,
                    'random_port_max': 50000
                }
            },
            'execution': {
                'task_timeout': 1500,
                'task_retry_max': 3,
                'retry_delay': 5,
                'compression_retries': 2
            },
            'benchmark': {
                'distraction_servers_default': 10,
                'resident_servers': ["Time MCP"],
                'task_delay': 1
            },
            'evaluation': {
                'judge_stability_runs': 5,
                'consensus_threshold': 2
            },
            'llm': {
                'json_retry_groups': 20,
                'token_reduction_factors': [0.9, 0.8, 0.7],
                'min_tokens': 1000,
                'token_increment': 1000,
                'evaluation_max_tokens': 15000
            },
            'azure': {
                'api_version': '2024-12-01-preview'
            },
            'data_collection': {
                'individual_timeout': 30,
                'max_retries': 5,
                'retry_delay_base': 3,
                'retry_delay_multiplier': 2
            }
        }
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable configuration overrides.
        
        Scans environment variables starting with 'BENCHMARK_' and applies
        them to the configuration. Supports automatic type conversion.
        """
        # Supported format: BENCHMARK_MCP_CONNECTION_HTTP_TIMEOUT=120
        # Mapping table: environment variable suffix -> actual configuration path
        env_mapping = {
            'EXECUTION_TASK_TIMEOUT': 'execution.task_timeout',
            'MCP_CONNECTION_HTTP_TIMEOUT': 'mcp.connection.http_timeout',
            'EXECUTION_MAX_EXECUTION_ROUNDS': 'execution.max_execution_rounds',
            'EXECUTION_COMPRESSION_RETRIES': 'execution.compression_retries',
            # Add more mappings...
        }
        
        for key, value in os.environ.items():
            if key.startswith('BENCHMARK_'):
                env_suffix = key[10:]  # Remove BENCHMARK_ prefix
                
                # Try direct mapping first
                if env_suffix in env_mapping:
                    config_path = env_mapping[env_suffix]
                else:
                    # Fallback to automatic conversion (convert underscores to dots)
                    config_path = env_suffix.lower().replace('_', '.')
                
                try:
                    # Try to convert to numbers or boolean values
                    converted_value = self._convert_env_value(value)
                    self._set_nested_value(self._config, config_path, converted_value)
                except Exception as e:
                    print(f"Warning: Failed to apply environment override {key}={value}: {e}")
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable values to appropriate types.
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value as int, float, bool, or original string
        """
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _set_nested_value(
        self,
        config: Dict[str, Any],
        path: str,
        value: Any
    ) -> None:
        """Set value in nested dictionary using dot-separated path.
        
        Args:
            config: Dictionary to modify
            path: Dot-separated path (e.g., 'mcp.connection.timeout')
            value: Value to set at the path
        """
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value through dot-separated path.
        
        Args:
            key_path: Dot-separated configuration path, e.g. 'mcp.connection.http_timeout'
            default: Default value if path not found
            
        Returns:
            Configuration value or default value
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.
        
        Args:
            section: Section name to retrieve
            
        Returns:
            Dictionary containing the section's configuration
        """
        return self.get(section, {})
    
    def reload(self) -> None:
        """Reload configuration from file and environment."""
        self._config = None
        self._load_config()

# Create global configuration instance
config = BenchmarkConfig()

# Convenience functions
def get_config(key_path: str, default: Any = None) -> Any:
    """Convenience function to get configuration value.
    
    Args:
        key_path: Dot-separated configuration path
        default: Default value if path not found
        
    Returns:
        Configuration value or default
    """
    return config.get(key_path, default)

def get_mcp_timeout() -> int:
    """Get MCP HTTP timeout.
    
    Returns:
        HTTP timeout in seconds
    """
    return config.get('mcp.connection.http_timeout', 60)

def get_task_timeout() -> int:
    """Get task execution timeout.
    
    Returns:
        Task timeout in seconds
    """
    return config.get('execution.task_timeout', 1500)

def get_max_retries() -> int:
    """Get maximum retry count.
    
    Returns:
        Maximum number of retries
    """
    return config.get('execution.task_retry_max', 3)

def get_default_port() -> int:
    """Get default MCP port.
    
    Returns:
        Default port number
    """
    return config.get('mcp.ports.default_port', 3001)

def get_distraction_servers_count() -> int:
    """Get default distraction server count.
    
    Returns:
        Number of distraction servers
    """
    return config.get('benchmark.distraction_servers_default', 10)

def get_retry_delay() -> int:
    """Get retry delay time.
    
    Returns:
        Retry delay in seconds
    """
    return config.get('execution.retry_delay', 5)

def get_task_delay() -> int:
    """Get inter-task delay time.
    
    Returns:
        Task delay in seconds
    """
    return config.get('benchmark.task_delay', 1)

def get_max_execution_rounds() -> int:
    """Get maximum execution rounds.
    
    Returns:
        Maximum number of execution rounds
    """
    return config.get('execution.max_execution_rounds', 10)

def get_compression_retries() -> int:
    """Get information compression retry count.
    
    Returns:
        Number of compression retries
    """
    return config.get('execution.compression_retries', 2)

def get_server_semaphore_limit() -> int:
    """Get server concurrency semaphore limit.
    
    Returns:
        Maximum concurrent server connections
    """
    return config.get('execution.server_semaphore_limit', 15)

def get_content_summary_threshold() -> int:
    """Get content summary token threshold.
    
    Returns:
        Token threshold for content summarization
    """
    return config.get('execution.content_summary_threshold', 1000)

def get_content_truncate_length() -> int:
    """Get content truncation length.
    
    Returns:
        Maximum content length before truncation
    """
    return config.get('execution.content_truncate_length', 4000)

def get_error_truncate_length() -> int:
    """Get error message truncation length.
    
    Returns:
        Maximum error message length
    """
    return config.get('execution.error_truncate_length', 1000)

def get_error_display_prefix() -> int:
    """Get error display prefix length.
    
    Returns:
        Length of error message prefix to display
    """
    return config.get('execution.error_display_prefix', 200)


def get_format_conversion_tokens() -> int:
    """Get format conversion token limit.
    
    Returns:
        Maximum tokens for format conversion
    """
    return config.get('llm.format_conversion_tokens', 8000)

def get_planning_tokens() -> int:
    """Get planning token limit.
    
    Returns:
        Maximum tokens for planning phase
    """
    return config.get('llm.planning_tokens', 12000)

def get_summarization_max_tokens() -> int:
    """Get summarization maximum tokens.
    
    Returns:
        Maximum tokens for summarization
    """
    return config.get('llm.summarization_max_tokens', 10000)

def get_user_prompt_max_length() -> int:
    """Get user prompt maximum length.
    
    Returns:
        Maximum user prompt length in characters
    """
    return config.get('llm.user_prompt_max_length', 30000)

def get_individual_timeout() -> float:
    """Get individual server test timeout.
    
    Returns:
        Timeout for individual server tests in seconds
    """
    return config.get('data_collection.individual_timeout', 30.0)

def get_batch_timeout() -> float:
    """Get batch connection timeout.
    
    Returns:
        Timeout for batch connections in seconds
    """
    return config.get('data_collection.batch_timeout', 60.0)

def get_data_collection_max_retries() -> int:
    """Get data collection maximum retry count.
    
    Returns:
        Maximum retries for data collection
    """
    return config.get('data_collection.max_retries', 5)

def get_retry_delay_base() -> int:
    """Get base retry delay.
    
    Returns:
        Base delay for retries in seconds
    """
    return config.get('data_collection.retry_delay_base', 3)

def get_retry_delay_multiplier() -> int:
    """Get retry delay multiplier.
    
    Returns:
        Multiplier for exponential backoff
    """
    return config.get('data_collection.retry_delay_multiplier', 2)

def get_batch_retry_delay_base() -> int:
    """Get batch retry base delay.
    
    Returns:
        Base delay for batch retries in seconds
    """
    return config.get('data_collection.batch_retry_delay_base', 5)

def get_batch_retry_delay_multiplier() -> int:
    """Get batch retry delay multiplier.
    
    Returns:
        Multiplier for batch retry exponential backoff
    """
    return config.get('data_collection.batch_retry_delay_multiplier', 3)

def get_default_http_port() -> int:
    """Get default HTTP port.
    
    Returns:
        Default HTTP port number
    """
    return config.get('data_collection.default_http_port', 3000)

def get_tool_description_truncate() -> int:
    """Get tool description truncation length.
    
    Returns:
        Maximum tool description length
    """
    return config.get('data_collection.tool_description_truncate', 150)

def get_selection_tokens() -> int:
    """Get server selection token limit.
    
    Returns:
        Maximum tokens for server selection
    """
    return config.get('server_selection.selection_tokens', 8000)

def get_tool_sample_count() -> int:
    """Get tool sample count.
    
    Returns:
        Number of tool samples to collect
    """
    return config.get('server_selection.tool_sample_count', 3)

def get_token_reduction_factors() -> List[float]:
    """Get token reduction factor sequence.
    
    Returns:
        List of token reduction factors for retry attempts
    """
    return config.get('llm.token_reduction_factors', [0.9, 0.8, 0.7])

# Benchmark runner configuration functions
def get_tasks_file() -> str:
    """Get default tasks file path.
    
    Returns:
        Path to the default tasks file
    """
    return config.get('benchmark.tasks_file', 'benchmark_tasks.json')


def is_judge_stability_enabled() -> bool:
    """Check if LLM judge stability testing is enabled.
    
    Returns:
        True if judge stability testing is enabled
    """
    return config.get('benchmark.enable_judge_stability', True)


def is_problematic_tools_filter_enabled() -> bool:
    """Check if problematic tools filtering is enabled.
    
    Returns:
        True if problematic tools filtering is enabled
    """
    return config.get('benchmark.filter_problematic_tools', True)

def is_concurrent_summarization_enabled() -> bool:
    """Check if concurrent content summarization is enabled.
    
    Returns:
        True if concurrent summarization is enabled
    """
    return config.get('benchmark.concurrent_summarization', True)

def use_fuzzy_descriptions() -> bool:
    """Check if fuzzy task descriptions should be used.
    
    Returns:
        True if fuzzy descriptions should be used
    """
    return config.get('benchmark.use_fuzzy_descriptions', True)

def is_concrete_description_ref_enabled() -> bool:
    """Check if concrete description reference for evaluation is enabled.
    
    Returns:
        True if concrete description reference is enabled
    """
    return config.get('benchmark.enable_concrete_description_ref_for_eval', True)

def get_all_task_files() -> List[str]:
    """Get all task files for comprehensive benchmark.
    
    Returns:
        List of paths to all task files
    """
    return config.get('benchmark.all_task_files', [
        "./tasks/mcpbench_tasks_single_runner_format.json",
        "./tasks/mcpbench_tasks_multi_2server_runner_format.json",
        "./tasks/mcpbench_tasks_multi_3server_runner_format.json",
        "./tasks/mcpbench_tasks_multi_4plus_server_runner_format.json"
    ])

def get_sequential_only_tools() -> List[str]:
    """Get list of tools that must be executed sequentially (not concurrently).
    
    Returns:
        List of tool names that require sequential execution
    """
    return config.get('execution.sequential_only_tools', [])

def get_evaluation_max_tokens() -> int:
    """Get maximum tokens for LLM evaluation.
    
    Returns:
        Maximum tokens for evaluation prompts
    """
    return config.get('llm.evaluation_max_tokens', 15000)

def get_azure_api_version() -> str:
    """Get Azure OpenAI API version.
    
    Returns:
        Azure OpenAI API version string
    """
    return config.get('azure.api_version', '2024-12-01-preview')

# Cache configuration functions
def is_cache_enabled() -> bool:
    """Check if tool cache is enabled.
    
    Returns:
        True if cache is enabled
    """
    return config.get('cache.enabled', False)

def get_cache_dir() -> str:
    """Get cache directory path.
    
    Returns:
        Path to cache directory
    """
    return config.get('cache.cache_dir', '.cache/tools')

def get_cache_ttl() -> int:
    """Get cache TTL in hours.
    
    Returns:
        Cache TTL in hours (0 for permanent)
    """
    return config.get('cache.ttl_hours', 24)

def get_cache_max_size_mb() -> int:
    """Get maximum cache size in MB.
    
    Returns:
        Maximum cache size in MB (0 for unlimited)
    """
    return config.get('cache.max_size_mb', 1000)

def get_cache_key_strategy() -> str:
    """Get cache key generation strategy.
    
    Returns:
        Cache key strategy ('hash' or 'structured')
    """
    return config.get('cache.key_strategy', 'hash')

def is_cache_log_stats_enabled() -> bool:
    """Check if cache statistics logging is enabled.
    
    Returns:
        True if cache stats logging is enabled
    """
    return config.get('cache.log_stats', True)

def get_cache_cleanup_interval() -> int:
    """Get cache cleanup interval in hours.
    
    Returns:
        Cleanup interval in hours (0 for no automatic cleanup)
    """
    return config.get('cache.cleanup_interval', 168)

def is_cache_persistent() -> bool:
    """Check if cache should be persistent between runs.
    
    Returns:
        True if cache should be persistent
    """
    return config.get('cache.persistent', True)

def get_cache_server_whitelist() -> List[str]:
    """Get list of servers whose tools should be cached.
    
    Returns:
        List of server names to cache (empty list means cache all)
    """
    return config.get('cache.server_whitelist', [])

def get_problematic_tools() -> List[str]:
    """Get list of problematic tools that should be filtered out.
    
    Returns:
        List of tool names that should be filtered due to issues (rate limits, bugs, etc)
    """
    return config.get('execution.problematic_tools', [])