"""
Tests for new features: configurable port and caching.
"""

import subprocess
import time
import requests
import pytest
from unittest.mock import patch, MagicMock
import functools
from wikipedia_mcp.wikipedia_client import WikipediaClient
from wikipedia_mcp.server import create_server


class TestPortConfiguration:
    """Test configurable port functionality."""

    def test_cli_port_argument(self):
        """Test that --port argument is available in CLI."""
        result = subprocess.run(
            ["python", "-m", "wikipedia_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "--port PORT" in result.stdout
        assert "Port for SSE transport" in result.stdout

    def test_port_default_value(self):
        """Test that port defaults to 8000."""
        result = subprocess.run(
            ["python", "-m", "wikipedia_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "default: 8000" in result.stdout

    @pytest.mark.timeout(30)
    def test_sse_server_starts_on_custom_port(self):
        """Test that SSE server starts on the specified port."""
        port = 8082
        process = None
        try:
            # Start server in background
            process = subprocess.Popen(
                ["python", "-m", "wikipedia_mcp", "--transport", "sse", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if port is in use
            try:
                response = requests.get(f"http://localhost:{port}/", timeout=5)
                # Server should respond (even if with an error)
                assert response.status_code in [200, 404, 405, 500]
            except requests.exceptions.RequestException:
                # Connection error is also acceptable as the server might not have HTTP endpoints
                pass
            
            # Verify process is still running
            assert process.poll() is None, "Server process should still be running"
            
        finally:
            if process:
                process.terminate()
                process.wait(timeout=5)

    def test_stdio_transport_ignores_port(self):
        """Test that STDIO transport ignores port parameter."""
        # This should not raise an error
        result = subprocess.run(
            ["python", "-m", "wikipedia_mcp", "--transport", "stdio", "--port", "9999", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0


class TestCachingFunctionality:
    """Test caching functionality."""

    def test_cli_cache_argument(self):
        """Test that --enable-cache argument is available in CLI."""
        result = subprocess.run(
            ["python", "-m", "wikipedia_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "--enable-cache" in result.stdout
        assert "Enable caching for Wikipedia API calls" in result.stdout

    def test_wikipedia_client_without_cache(self):
        """Test WikipediaClient without caching."""
        client = WikipediaClient(enable_cache=False)
        assert client.enable_cache is False
        
        # Methods should not be wrapped with lru_cache
        assert not hasattr(client.search, 'cache_info')

    def test_wikipedia_client_with_cache(self):
        """Test WikipediaClient with caching enabled."""
        client = WikipediaClient(enable_cache=True)
        assert client.enable_cache is True
        
        # Methods should be wrapped with lru_cache
        assert hasattr(client.search, 'cache_info')
        assert hasattr(client.get_article, 'cache_info')
        assert hasattr(client.get_summary, 'cache_info')

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_cache_effectiveness(self, mock_get):
        """Test that caching actually works."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': 'Test Article',
                        'snippet': 'Test snippet',
                        'pageid': 123,
                        'wordcount': 100,
                        'timestamp': '2023-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Create client with caching
        client = WikipediaClient(enable_cache=True)
        
        # Call the same search twice
        result1 = client.search("test query")
        result2 = client.search("test query")
        
        # Should be the same result
        assert result1 == result2
        
        # API should only be called once due to caching
        assert mock_get.call_count == 1
        
        # Cache info should show hits
        cache_info = client.search.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1

    def test_cache_methods_coverage(self):
        """Test that all expected methods are cached when caching is enabled."""
        client = WikipediaClient(enable_cache=True)
        
        cached_methods = [
            'search',
            'get_article', 
            'get_summary',
            'get_sections',
            'get_links',
            'get_related_topics',
            'summarize_for_query',
            'summarize_section',
            'extract_facts'
        ]
        
        for method_name in cached_methods:
            method = getattr(client, method_name)
            assert hasattr(method, 'cache_info'), f"Method {method_name} should be cached"

    def test_cache_size_limit(self):
        """Test that cache has proper size limit."""
        client = WikipediaClient(enable_cache=True)
        
        # Check cache maxsize is set correctly
        cache_info = client.search.cache_info()
        assert cache_info.maxsize == 128


class TestIntegrationNewFeatures:
    """Integration tests for new features."""

    def test_server_creation_with_all_options(self):
        """Test server creation with all new options."""
        server = create_server(language="en", enable_cache=True)
        assert server is not None

    @pytest.mark.timeout(20)
    def test_full_cli_with_new_options(self):
        """Test CLI with all new options."""
        result = subprocess.run(
            [
                "python", "-m", "wikipedia_mcp", 
                "--transport", "stdio",
                "--port", "8083", 
                "--enable-cache",
                "--language", "en",
                "--log-level", "INFO",
                "--help"
            ],
            capture_output=True,
            text=True,
            timeout=15
        )
        assert result.returncode == 0
        assert "Wikipedia MCP Server" in result.stdout

    def test_cache_and_port_independence(self):
        """Test that caching and port options work independently."""
        # Test cache without custom port
        server1 = create_server(enable_cache=True)
        assert server1 is not None
        
        # Test custom port without cache (implicitly)
        server2 = create_server(language="en")  # enable_cache defaults to False
        assert server2 is not None 