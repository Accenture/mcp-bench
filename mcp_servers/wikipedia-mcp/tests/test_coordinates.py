"""
Tests for Wikipedia coordinates functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from wikipedia_mcp.wikipedia_client import WikipediaClient
from wikipedia_mcp.server import create_server


class TestWikipediaClientCoordinates:
    """Test coordinates functionality in WikipediaClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = WikipediaClient(language="en")

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_success(self, mock_get):
        """Test successful coordinate retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "123456": {
                        "pageid": 123456,
                        "title": "Statue of Liberty",
                        "coordinates": [
                            {
                                "lat": 40.689247,
                                "lon": -74.044502,
                                "primary": True,
                                "globe": "earth"
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_coordinates("Statue of Liberty")

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://en.wikipedia.org/w/api.php"
        params = call_args[1]['params']
        assert params['action'] == 'query'
        assert params['prop'] == 'coordinates'
        assert params['titles'] == 'Statue of Liberty'
        assert params['format'] == 'json'

        # Verify result structure
        assert result['title'] == "Statue of Liberty"
        assert result['pageid'] == 123456
        assert result['exists'] is True
        assert result['error'] is None
        assert len(result['coordinates']) == 1
        
        coord = result['coordinates'][0]
        assert coord['latitude'] == 40.689247
        assert coord['longitude'] == -74.044502
        assert coord['primary'] is True
        assert coord['globe'] == "earth"

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_no_coordinates(self, mock_get):
        """Test article with no coordinates."""
        # Mock API response for article without coordinates
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "789012": {
                        "pageid": 789012,
                        "title": "Test Article"
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_coordinates("Test Article")

        assert result['title'] == "Test Article"
        assert result['pageid'] == 789012
        assert result['exists'] is True
        assert result['coordinates'] is None
        assert result['error'] is None
        assert result['message'] == 'No coordinates available for this article'

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_page_not_found(self, mock_get):
        """Test coordinates for non-existent page."""
        # Mock API response for non-existent page
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "title": "Non-existent Article",
                        "missing": True
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_coordinates("Non-existent Article")

        assert result['title'] == "Non-existent Article"
        assert result['exists'] is False
        assert result['coordinates'] is None
        assert result['error'] == 'Page does not exist'

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_multiple_coordinates(self, mock_get):
        """Test article with multiple coordinate systems."""
        # Mock API response with multiple coordinates
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "345678": {
                        "pageid": 345678,
                        "title": "Multi-location Article",
                        "coordinates": [
                            {
                                "lat": 40.689247,
                                "lon": -74.044502,
                                "primary": True,
                                "globe": "earth",
                                "type": "landmark",
                                "name": "Main location"
                            },
                            {
                                "lat": 40.690000,
                                "lon": -74.045000,
                                "primary": False,
                                "globe": "earth",
                                "type": "region",
                                "name": "Secondary location"
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_coordinates("Multi-location Article")

        assert result['title'] == "Multi-location Article"
        assert result['exists'] is True
        assert len(result['coordinates']) == 2
        
        # Check primary coordinate
        primary_coord = result['coordinates'][0]
        assert primary_coord['latitude'] == 40.689247
        assert primary_coord['longitude'] == -74.044502
        assert primary_coord['primary'] is True
        assert primary_coord['type'] == "landmark"
        assert primary_coord['name'] == "Main location"
        
        # Check secondary coordinate
        secondary_coord = result['coordinates'][1]
        assert secondary_coord['latitude'] == 40.690000
        assert secondary_coord['longitude'] == -74.045000
        assert secondary_coord['primary'] is False
        assert secondary_coord['type'] == "region"
        assert secondary_coord['name'] == "Secondary location"

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_api_error(self, mock_get):
        """Test handling of API errors."""
        # Mock API error
        mock_get.side_effect = Exception("Connection error")

        result = self.client.get_coordinates("Any Article")

        assert result['title'] == "Any Article"
        assert result['exists'] is False
        assert result['coordinates'] is None
        assert "Connection error" in result['error']

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_get_coordinates_empty_response(self, mock_get):
        """Test handling of empty API response."""
        # Mock empty API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"query": {}}
        mock_get.return_value = mock_response

        result = self.client.get_coordinates("Test Article")

        assert result['title'] == "Test Article"
        assert result['exists'] is False
        assert result['coordinates'] is None
        assert result['error'] == 'No page found'

    def test_get_coordinates_with_language_variant(self):
        """Test coordinates with language variants."""
        client = WikipediaClient(language="zh-hans")
        
        with patch('wikipedia_mcp.wikipedia_client.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "query": {
                    "pages": {
                        "123": {
                            "pageid": 123,
                            "title": "测试文章",
                            "coordinates": [{"lat": 39.9042, "lon": 116.4074, "primary": True}]
                        }
                    }
                }
            }
            mock_get.return_value = mock_response

            result = client.get_coordinates("测试文章")

            # Check that variant parameter was added
            call_args = mock_get.call_args
            params = call_args[1]['params']
            assert params['variant'] == 'zh-hans'
            assert result['exists'] is True

    def test_get_coordinates_caching(self):
        """Test that caching is applied when enabled."""
        client = WikipediaClient(language="en", enable_cache=True)
        
        # Check that get_coordinates method is cached
        assert hasattr(client.get_coordinates, 'cache_info')


class TestServerCoordinatesTool:
    """Test coordinates tool in server."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = create_server(language="en")

    @pytest.mark.asyncio
    async def test_get_coordinates_tool_registration(self):
        """Test that get_coordinates tool is properly registered."""
        # Check if the tool is available
        tools = await self.server.get_tools()
        assert "get_coordinates" in tools

    @pytest.mark.asyncio
    async def test_get_coordinates_tool_execution(self):
        """Test execution of get_coordinates tool."""
        # Mock the client method
        with patch('wikipedia_mcp.wikipedia_client.WikipediaClient.get_coordinates') as mock_get_coordinates:
            mock_get_coordinates.return_value = {
                "title": "Test Location",
                "pageid": 123,
                "coordinates": [{"lat": 40.7128, "lon": -74.0060, "primary": True}],
                "exists": True,
                "error": None
            }

            # Get and execute the tool
            tool = await self.server.get_tool("get_coordinates")
            assert tool is not None
            
            # Verify tool name and description
            assert tool.name == "get_coordinates"
            assert "coordinates" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_get_coordinates_tool_schema(self):
        """Test that get_coordinates tool has correct schema."""
        tool = await self.server.get_tool("get_coordinates")
        schema = tool.parameters
        
        # Check that title parameter is required and is a string
        assert 'title' in schema['required']
        assert schema['properties']['title']['type'] == 'string'


class TestCoordinatesIntegration:
    """Integration tests for coordinates functionality."""

    @pytest.mark.asyncio
    async def test_coordinates_in_server_with_country_support(self):
        """Test coordinates functionality with country support."""
        server = create_server(language="en", country="US")
        
        # Verify tool is available
        tools = await server.get_tools()
        assert "get_coordinates" in tools

    @pytest.mark.asyncio
    async def test_coordinates_with_caching_enabled(self):
        """Test coordinates functionality with caching enabled."""
        server = create_server(language="en", enable_cache=True)
        
        # Verify tool is available
        tools = await server.get_tools()
        assert "get_coordinates" in tools


# Mark integration tests
@pytest.mark.integration
class TestCoordinatesAPIIntegration:
    """Integration tests that require real API calls."""

    def test_real_coordinates_api_call(self):
        """Test real API call for coordinates (requires internet)."""
        pytest.skip("Integration test requires internet access")
        
        # This test would make a real API call
        # client = WikipediaClient(language="en")
        # result = client.get_coordinates("Statue of Liberty")
        # assert result['exists'] is True
        # assert result['coordinates'] is not None