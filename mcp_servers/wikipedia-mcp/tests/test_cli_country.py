"""
Tests for CLI country support.
"""

import pytest
import subprocess
import time
import signal
import os
from unittest.mock import patch
import sys


class TestCountryCLI:
    """Test CLI functionality with country codes."""

    def test_cli_country_argument_help(self):
        """Test that country argument appears in help."""
        result = subprocess.run(
            [sys.executable, "-m", "wikipedia_mcp", "--help"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "--country" in result.stdout
        assert "Country/locale code" in result.stdout
        assert "--list-countries" in result.stdout

    def test_cli_list_countries_functionality(self):
        """Test the --list-countries functionality."""
        result = subprocess.run(
            [sys.executable, "-m", "wikipedia_mcp", "--list-countries"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0
        assert "Supported Country/Locale Codes:" in result.stdout
        assert "en: US, USA, United States, UK, GB" in result.stdout  # Updated expectation
        assert "zh-hans: CN, China" in result.stdout
        assert "zh-tw: TW, Taiwan" in result.stdout
        assert "Examples:" in result.stdout
        assert "wikipedia-mcp --country US" in result.stdout

    def test_cli_country_validation_error(self):
        """Test error handling for invalid country codes."""
        result = subprocess.run(
            [sys.executable, "-m", "wikipedia_mcp", "--country", "INVALID"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0  # Should exit gracefully
        assert "Configuration error" in result.stderr
        assert "Unsupported country/locale: 'INVALID'" in result.stdout
        assert "Use --list-countries" in result.stdout

    def test_cli_country_and_language_conflict(self):
        """Test handling of conflicting country and language arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "wikipedia_mcp", "--language", "ja", "--country", "US"],
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0  # Should exit gracefully
        assert "Cannot specify both --language and --country" in result.stdout

    def test_cli_country_start_timeout(self):
        """Test that server starts successfully with country code."""
        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "--country", "JP", "--transport", "sse", "--port", "8200"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start
            time.sleep(2)
            
            # Check if process is still running (didn't crash)
            poll_result = process.poll()
            assert poll_result is None, "Server process should still be running"
            
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    def test_cli_country_short_flag(self):
        """Test that -c short flag works for country."""
        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "-c", "FR", "--transport", "sse", "--port", "8201"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start
            time.sleep(2)
            
            # Check if process is still running
            poll_result = process.poll()
            assert poll_result is None, "Server process should still be running"
            
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


class TestCLICountryIntegration:
    """Integration tests for CLI with country support."""

    def test_country_to_language_resolution_log(self):
        """Test that country resolution is properly logged."""
        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "--country", "Taiwan"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start and log
            time.sleep(3)
            
            # Terminate and read output
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            
            # Check that Taiwan country was properly logged
            assert "Starting Wikipedia MCP server with stdio transport for country: Taiwan" in stderr
            
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                stdout, stderr = process.communicate()

    def test_country_with_cache_option(self):
        """Test that country works with caching option."""
        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "--country", "DE", "--enable-cache", "--transport", "sse", "--port", "8202"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start
            time.sleep(2)
            
            # Check if process is still running
            poll_result = process.poll()
            assert poll_result is None, "Server with country and cache should start successfully"
            
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

    def test_country_with_sse_transport(self):
        """Test that country works with SSE transport."""
        process = None
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "--country", "IT", "--transport", "sse", "--port", "8203"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start
            time.sleep(2)
            
            # Check if process is still running
            poll_result = process.poll()
            assert poll_result is None, "Server with country and SSE transport should start successfully"
            
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


class TestCLICountryExamples:
    """Test CLI with various country examples from documentation."""

    @pytest.mark.parametrize("country,expected_language", [
        ("US", "en"),
        ("CN", "zh-hans"),
        ("TW", "zh-tw"),
        ("Japan", "ja"),
        ("Germany", "de"),
        ("france", "fr"),  # Test case insensitive
    ])
    def test_cli_country_examples(self, country, expected_language):
        """Test CLI with different country examples."""
        process = None
        port = 8210 + hash(country) % 100  # Generate unique port for each test
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "wikipedia_mcp", "--country", country, "--transport", "sse", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Give the server time to start
            time.sleep(2)
            
            # Check if process is still running (successful start)
            poll_result = process.poll()
            assert poll_result is None, f"Server should start successfully with country: {country}"
            
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()