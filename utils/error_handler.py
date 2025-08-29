#!/usr/bin/env python3
"""Unified Error Handling Utilities.

This module provides decorators and utilities to standardize error handling
across the project according to CLAUDE.md specifications.

Classes:
    ErrorContext: Context manager for standardized error handling
    MCPConnectionError: MCP server connection failures
    TaskExecutionError: Task execution failures
    LLMProviderError: LLM provider errors
    ConfigurationError: Configuration errors

Functions:
    handle_errors: Decorator for standardized error handling
    log_exception: Log exceptions with full traceback
    retry_with_logging: Retry operations with proper logging
"""

import functools
import logging
import traceback
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


def handle_errors(
    operation_name: str,
    log_level: int = logging.ERROR,
    reraise: bool = True
) -> Callable:
    """Decorator to standardize error handling according to CLAUDE.md specifications.
    
    Args:
        operation_name: Description of the operation for logging
        log_level: Logging level for errors (default: ERROR)
        reraise: Whether to reraise the exception after logging
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"ERROR in {operation_name}: {e}")
                logger.log(log_level, f"Full traceback: {traceback.format_exc()}")
                if reraise:
                    raise
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"ERROR in {operation_name}: {e}")
                logger.log(log_level, f"Full traceback: {traceback.format_exc()}")
                if reraise:
                    raise
                return None
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_exception(
    operation_name: str,
    exception: Exception,
    log_level: int = logging.ERROR
) -> None:
    """Utility function to log exceptions according to CLAUDE.md standards.
    
    Args:
        operation_name: Description of the operation that failed
        exception: The caught exception
        log_level: Logging level for the error
    """
    logger.log(log_level, f"ERROR in {operation_name}: {exception}")
    logger.log(log_level, f"Full traceback: {traceback.format_exc()}")


class ErrorContext:
    """Context manager for standardized error handling.
    
    Provides a context manager that automatically logs exceptions
    with full traceback according to CLAUDE.md standards.
    
    Attributes:
        operation_name: Description of the operation
        log_level: Logging level for errors
        reraise: Whether to reraise exceptions
        
    Example:
        >>> with ErrorContext("database operation"):
        ...     perform_database_operation()
    """
    
    def __init__(
        self,
        operation_name: str,
        log_level: int = logging.ERROR,
        reraise: bool = True
    ) -> None:
        """Initialize the error context.
        
        Args:
            operation_name: Description of the operation
            log_level: Logging level for errors
            reraise: Whether to reraise exceptions
        """
        self.operation_name = operation_name
        self.log_level = log_level
        self.reraise = reraise
    
    def __enter__(self) -> 'ErrorContext':
        """Enter the context.
        
        Returns:
            The ErrorContext instance
        """
        return self
    
    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any]
    ) -> bool:
        """Exit the context and handle any exceptions.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
            
        Returns:
            True to suppress the exception, False to reraise
        """
        if exc_type is not None:
            log_exception(self.operation_name, exc_val, self.log_level)
            return not self.reraise  # Return True to suppress exception if not reraising
        return False


class MCPConnectionError(Exception):
    """Raised when MCP server connection fails.
    
    This exception indicates failures in establishing or maintaining
    connections to MCP servers.
    """
    pass


class TaskExecutionError(Exception):
    """Raised when task execution fails.
    
    This exception indicates failures during the execution of
    benchmark tasks.
    """
    pass


class LLMProviderError(Exception):
    """Raised when LLM provider encounters an error.
    
    This exception indicates failures in LLM API calls or
    response processing.
    """
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing.
    
    This exception indicates problems with configuration files
    or required environment variables.
    """
    pass


async def retry_with_logging(
    operation: Callable,
    operation_name: str,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry an operation with proper error logging.
    
    Implements exponential backoff and logs errors according to
    CLAUDE.md specifications.
    
    Args:
        operation: The async operation to retry
        operation_name: Description for logging
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry on
    
    Returns:
        Result of the operation
        
    Raises:
        The last exception if all retries fail
        
    Example:
        >>> result = await retry_with_logging(
        ...     lambda: fetch_data(),
        ...     "data fetch",
        ...     max_retries=3
        ... )
    """
    import asyncio
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(f"Retrying {operation_name}, attempt {attempt + 1}/{max_retries + 1}")
                await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
            
            return await operation()
            
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"ERROR in {operation_name} (attempt {attempt + 1}): {e}")
                logger.warning(f"Will retry in {retry_delay * (attempt + 1)} seconds...")
            else:
                logger.error(f"ERROR in {operation_name} (final attempt): {e}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # All retries failed
    raise last_exception


def retry_on_error(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    operation_name: Optional[str] = None
) -> Callable:
    """Decorator that adds retry logic to functions with proper error logging.
    
    This decorator wraps functions to automatically retry them on failure,
    with exponential backoff and proper error logging.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry on
        operation_name: Custom operation name for logging (uses function name if None)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        >>> @retry_on_error(max_retries=3, exceptions=(ConnectionError, TimeoutError))
        ... async def connect_to_server():
        ...     # Connection logic here
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        actual_operation_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            async def operation():
                return await func(*args, **kwargs)
            
            return await retry_with_logging(
                operation=operation,
                operation_name=actual_operation_name,
                max_retries=max_retries,
                retry_delay=retry_delay,
                exceptions=exceptions
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            import asyncio
            
            async def operation():
                return func(*args, **kwargs)
            
            # For sync functions, we need to handle the retry differently
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"Retrying {actual_operation_name}, attempt {attempt + 1}/{max_retries + 1}")
                        import time
                        time.sleep(retry_delay * attempt)
                    
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"ERROR in {actual_operation_name} (attempt {attempt + 1}): {e}")
                        logger.warning(f"Will retry in {retry_delay * (attempt + 1)} seconds...")
                    else:
                        logger.error(f"ERROR in {actual_operation_name} (final attempt): {e}")
                        logger.error(f"Full traceback: {traceback.format_exc()}")
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ErrorStats:
    """Simple error statistics collector.
    
    Tracks error counts and types for monitoring purposes.
    """
    
    def __init__(self) -> None:
        """Initialize error statistics."""
        self.error_counts = {}
        self.total_errors = 0
    
    def record_error(self, operation_name: str, exception: Exception) -> None:
        """Record an error occurrence.
        
        Args:
            operation_name: Name of the operation that failed
            exception: The exception that occurred
        """
        error_type = type(exception).__name__
        key = f"{operation_name}:{error_type}"
        
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        self.total_errors += 1
    
    def get_stats(self) -> dict:
        """Get current error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': self.total_errors,
            'error_breakdown': self.error_counts.copy(),
            'top_errors': sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def reset(self) -> None:
        """Reset error statistics."""
        self.error_counts.clear()
        self.total_errors = 0


# Global error statistics instance
error_stats = ErrorStats()


def handle_errors_with_stats(
    operation_name: str,
    log_level: int = logging.ERROR,
    reraise: bool = True,
    record_stats: bool = True
) -> Callable:
    """Enhanced error handling decorator with statistics tracking.
    
    Like handle_errors but also records error statistics for monitoring.
    
    Args:
        operation_name: Description of the operation for logging
        log_level: Logging level for errors
        reraise: Whether to reraise the exception after logging
        record_stats: Whether to record error statistics
        
    Returns:
        Decorated function with error handling and stats
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"ERROR in {operation_name}: {e}")
                logger.log(log_level, f"Full traceback: {traceback.format_exc()}")
                
                if record_stats:
                    error_stats.record_error(operation_name, e)
                
                if reraise:
                    raise
                return None
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"ERROR in {operation_name}: {e}")
                logger.log(log_level, f"Full traceback: {traceback.format_exc()}")
                
                if record_stats:
                    error_stats.record_error(operation_name, e)
                
                if reraise:
                    raise
                return None
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator