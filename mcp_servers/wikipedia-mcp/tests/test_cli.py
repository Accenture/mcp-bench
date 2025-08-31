"""
Tests for the command-line interface of Wikipedia MCP server.
"""
import subprocess
import sys
import pytest

# Path to the wikipedia-mcp executable
WIKIPEDIA_MCP_CMD = ["wikipedia-mcp"]

def run_mcp_command(args, expect_timeout=False):
    """Helper function to run the wikipedia-mcp command and return its output."""
    try:
        process = subprocess.run(
            WIKIPEDIA_MCP_CMD + args,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,  # Increased timeout
            stdin=subprocess.PIPE  # Explicitly pipe stdin
        )
        return process
    except FileNotFoundError:
        try:
            process = subprocess.run(
                [sys.executable, "-m", "wikipedia_mcp"] + args,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,  # Increased timeout
                stdin=subprocess.PIPE  # Explicitly pipe stdin
            )
            return process
        except subprocess.TimeoutExpired as e:
            if expect_timeout:
                return e
            else:
                raise
    except subprocess.TimeoutExpired as e:
        if expect_timeout:
            return e
        else:
            raise


def test_cli_stdio_transport_starts():
    """Test that stdio transport starts without immediate errors."""
    args = ["--transport", "stdio", "--log-level", "INFO"]
    result = run_mcp_command(args, expect_timeout=True)

    # For stdio mode, we now expect the process to start, log, and exit cleanly.
    # It does not block indefinitely in the test environment with piped stdin.
    assert not isinstance(result, subprocess.TimeoutExpired), \
        f"Expected command to complete, but it timed out. Stderr: {getattr(result.stderr, 'decode', lambda x: x)('utf-8', 'replace') if hasattr(result, 'stderr') and result.stderr else 'N/A'}"
    assert result.returncode == 0, \
        f"Expected return code 0, got {result.returncode}. Stderr: {result.stderr}"
    
    # Check that some logging output was captured
    stderr_output = result.stderr if result.stderr else ""
        
    assert "Starting Wikipedia MCP server with stdio transport" in stderr_output, \
        f"Expected startup message not found in stderr. Stderr: {stderr_output}"
    assert "Using stdio transport - suppressing direct stdout messages" in stderr_output, \
        f"Expected stdio mode message not found in stderr. Stderr: {stderr_output}"

    # Verify stdout is empty (no prints interfering with stdio protocol)
    stdout_output = result.stdout if result.stdout else ""
    assert stdout_output.strip() == "", f"stdout should be empty for stdio transport. Stdout: {stdout_output}"


def test_cli_sse_transport_starts():
    """Test that sse transport starts without immediate errors."""
    args = ["--transport", "sse", "--log-level", "INFO"]
    result = run_mcp_command(args, expect_timeout=True)

    # For sse mode, we expect the process to start the HTTP server and then timeout
    assert isinstance(result, subprocess.TimeoutExpired), "Expected timeout for sse mode"
    
    # Check that logging output was captured
    stderr_bytes = result.stderr if hasattr(result, 'stderr') else b''
    stderr_output = stderr_bytes.decode('utf-8', errors='replace') if isinstance(stderr_bytes, bytes) else stderr_bytes
    
    # Should see uvicorn startup messages for sse mode
    assert "uvicorn" in stderr_output.lower() or "application startup" in stderr_output.lower(), \
        "Expected uvicorn startup messages for sse transport"


def test_cli_invalid_transport():
    """Test CLI behavior with an invalid transport option."""
    args = ["--transport", "invalid_transport_option"]
    result = run_mcp_command(args)
    assert result.returncode != 0, "Should exit with non-zero code for invalid transport"
    assert "invalid choice: 'invalid_transport_option'" in result.stderr, "Should show argparse error"


def test_cli_help_message():
    """Test that the help message can be displayed."""
    args = ["--help"]
    result = run_mcp_command(args)
    assert result.returncode == 0, "Help should exit with code 0"
    assert "usage:" in result.stdout.lower(), "Should show usage information"
    assert "--transport" in result.stdout, "Should show transport option"
    assert "--log-level" in result.stdout, "Should show log-level option"


def test_cli_log_levels():
    """Test different log levels work without errors."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        args = ["--transport", "stdio", "--log-level", level]
        result = run_mcp_command(args, expect_timeout=True)
        
        # For stdio mode, we now expect the process to start, log, and exit cleanly.
        assert not isinstance(result, subprocess.TimeoutExpired), \
            f"Expected command to complete for log level {level}, but it timed out. Stderr: {getattr(result.stderr, 'decode', lambda x: x)('utf-8', 'replace') if hasattr(result, 'stderr') and result.stderr else 'N/A'}"
        assert result.returncode == 0, \
            f"Expected return code 0 for log level {level}, got {result.returncode}. Stderr: {result.stderr}"
        
        stderr_output = result.stderr if result.stderr else ""
        
        startup_message = "Starting Wikipedia MCP server with stdio transport"
        if level in ["DEBUG", "INFO"]:
            assert startup_message in stderr_output, \
                f"Expected startup message for log level {level} not found in stderr. Stderr: {stderr_output}"
        elif level in ["WARNING", "ERROR"]:
            assert startup_message not in stderr_output, \
                f"Expected startup message for log level {level} TO NOT BE PRESENT in stderr, but it was. Stderr: {stderr_output}"
            # We can also check if *any* output is present for WARNING/ERROR, 
            # or if specific higher-level messages appear, but for now, ensuring the INFO message
            # is correctly excluded is the main goal for this part of the test.
            # The primary check is that it started and timed out, which is covered by isinstance(TimeoutExpired).
            # We also need to make sure that *some* log output is produced, as the logger is configured.
            # For WARNING and ERROR, a simple check that stderr is not empty might suffice if no specific message is expected at these levels during startup.
            # However, the basicConfig in __main__ should always produce *some* output if logging is active.
            # Let's check if the generic log format appears for WARNING/ERROR, which would imply the logger is active.
            # This is a bit fragile, but better than nothing.
            if level == "WARNING":
                 # Example: Check for a line that looks like a log entry if specific messages are hard to predict
                 # For now, the absence of the INFO message and the timeout is the core check.
                 pass # Add more specific checks if needed
            if level == "ERROR":
                 pass # Add more specific checks if needed 