"""
Tests for language variant support functionality.
"""

import pytest
from unittest.mock import patch, Mock
from wikipedia_mcp.wikipedia_client import WikipediaClient
from wikipedia_mcp.server import create_server


class TestLanguageVariantParsing:
    """Test language variant parsing and mapping functionality."""

    def test_parse_basic_languages(self):
        """Test parsing of basic (non-variant) language codes."""
        client = WikipediaClient(language="en")
        base, variant = client._parse_language_variant("en")
        assert base == "en"
        assert variant is None

        client = WikipediaClient(language="ja")
        base, variant = client._parse_language_variant("ja")
        assert base == "ja"
        assert variant is None

    def test_parse_chinese_variants(self):
        """Test parsing of Chinese language variants."""
        test_cases = [
            ("zh-hans", "zh", "zh-hans"),  # Simplified Chinese
            ("zh-hant", "zh", "zh-hant"),  # Traditional Chinese
            ("zh-tw", "zh", "zh-tw"),      # Traditional Chinese (Taiwan)
            ("zh-hk", "zh", "zh-hk"),      # Traditional Chinese (Hong Kong)
            ("zh-mo", "zh", "zh-mo"),      # Traditional Chinese (Macau)
            ("zh-cn", "zh", "zh-cn"),      # Simplified Chinese (China)
            ("zh-sg", "zh", "zh-sg"),      # Simplified Chinese (Singapore)
            ("zh-my", "zh", "zh-my"),      # Simplified Chinese (Malaysia)
        ]

        for variant_code, expected_base, expected_variant in test_cases:
            client = WikipediaClient(language=variant_code)
            base, variant = client._parse_language_variant(variant_code)
            assert base == expected_base, f"Failed for {variant_code}: expected base {expected_base}, got {base}"
            assert variant == expected_variant, f"Failed for {variant_code}: expected variant {expected_variant}, got {variant}"

    def test_parse_serbian_variants(self):
        """Test parsing of Serbian language variants."""
        test_cases = [
            ("sr-latn", "sr", "sr-latn"),  # Serbian Latin
            ("sr-cyrl", "sr", "sr-cyrl"),  # Serbian Cyrillic
        ]

        for variant_code, expected_base, expected_variant in test_cases:
            client = WikipediaClient(language=variant_code)
            base, variant = client._parse_language_variant(variant_code)
            assert base == expected_base
            assert variant == expected_variant

    def test_parse_kurdish_variants(self):
        """Test parsing of Kurdish language variants."""
        test_cases = [
            ("ku-latn", "ku", "ku-latn"),  # Kurdish Latin
            ("ku-arab", "ku", "ku-arab"),  # Kurdish Arabic
        ]

        for variant_code, expected_base, expected_variant in test_cases:
            client = WikipediaClient(language=variant_code)
            base, variant = client._parse_language_variant(variant_code)
            assert base == expected_base
            assert variant == expected_variant

    def test_norwegian_special_case(self):
        """Test Norwegian language special mapping."""
        client = WikipediaClient(language="no")
        base, variant = client._parse_language_variant("no")
        assert base == "nb"  # Norwegian maps to Bokmål
        assert variant == "no"


class TestLanguageVariantAPIIntegration:
    """Test integration of language variants with API calls."""

    def test_client_initialization_with_variants(self):
        """Test that WikipediaClient initializes correctly with language variants."""
        client = WikipediaClient(language="zh-hans")
        assert client.original_language == "zh-hans"
        assert client.base_language == "zh"
        assert client.language_variant == "zh-hans"
        assert client.api_url == "https://zh.wikipedia.org/w/api.php"

    def test_client_initialization_without_variants(self):
        """Test that WikipediaClient initializes correctly with standard languages."""
        client = WikipediaClient(language="en")
        assert client.original_language == "en"
        assert client.base_language == "en"
        assert client.language_variant is None
        assert client.api_url == "https://en.wikipedia.org/w/api.php"

    def test_add_variant_to_params_with_variant(self):
        """Test adding variant parameter when client has a language variant."""
        client = WikipediaClient(language="zh-tw")
        params = {"action": "query", "format": "json"}
        updated_params = client._add_variant_to_params(params)
        
        expected_params = {"action": "query", "format": "json", "variant": "zh-tw"}
        assert updated_params == expected_params

    def test_add_variant_to_params_without_variant(self):
        """Test that params remain unchanged when no language variant."""
        client = WikipediaClient(language="en")
        params = {"action": "query", "format": "json"}
        updated_params = client._add_variant_to_params(params)
        
        assert updated_params == params

    def test_params_immutability(self):
        """Test that original params dict is not modified."""
        client = WikipediaClient(language="zh-hans")
        original_params = {"action": "query", "format": "json"}
        params_copy = original_params.copy()
        
        updated_params = client._add_variant_to_params(original_params)
        
        # Original params should remain unchanged
        assert original_params == params_copy
        # Updated params should have the variant
        assert "variant" in updated_params
        assert "variant" not in original_params

    @patch('requests.get')
    def test_search_with_language_variant(self, mock_get):
        """Test that search method includes variant parameter in API call."""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': '中国',
                        'snippet': 'Test snippet',
                        'pageid': 123,
                        'wordcount': 1000,
                        'timestamp': '2024-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test search with Chinese variant
        client = WikipediaClient(language="zh-hans")
        results = client.search("China", limit=5)

        # Verify the API was called with variant parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://zh.wikipedia.org/w/api.php"
        
        params = call_args[1]['params']
        assert params['variant'] == 'zh-hans'
        assert params['action'] == 'query'
        assert params['srsearch'] == 'China'
        assert params['srlimit'] == 5

        # Verify results
        assert len(results) == 1
        assert results[0]['title'] == '中国'

    @patch('requests.get')
    def test_search_without_language_variant(self, mock_get):
        """Test that search method doesn't include variant parameter for standard languages."""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': 'China',
                        'snippet': 'Test snippet',
                        'pageid': 123,
                        'wordcount': 1000,
                        'timestamp': '2024-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test search with standard language
        client = WikipediaClient(language="en")
        results = client.search("China", limit=5)

        # Verify the API was called without variant parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        assert 'variant' not in params
        assert params['action'] == 'query'
        assert params['srsearch'] == 'China'


class TestServerIntegrationWithVariants:
    """Test server creation and integration with language variants."""

    def test_create_server_with_language_variant(self):
        """Test creating server with language variant."""
        server = create_server(language="zh-tw")
        
        # Server should be created successfully
        assert server is not None
        assert server.name == "Wikipedia"

    def test_create_server_with_standard_language(self):
        """Test creating server with standard language."""
        server = create_server(language="ja")
        
        # Server should be created successfully
        assert server is not None
        assert server.name == "Wikipedia"

    def test_create_server_with_cache_and_variant(self):
        """Test creating server with both caching and language variant."""
        server = create_server(language="zh-hans", enable_cache=True)
        
        # Server should be created successfully
        assert server is not None
        assert server.name == "Wikipedia"


class TestLanguageVariantMapping:
    """Test the language variant mapping configuration."""

    def test_language_variants_mapping_completeness(self):
        """Test that all defined language variants have proper mappings."""
        client = WikipediaClient()
        
        for variant, base in client.LANGUAGE_VARIANTS.items():
            assert isinstance(variant, str), f"Variant key must be string: {variant}"
            assert isinstance(base, str), f"Base language must be string: {base}"
            assert len(variant) > 0, f"Variant cannot be empty: {variant}"
            assert len(base) > 0, f"Base language cannot be empty: {base}"

    def test_chinese_variants_comprehensive(self):
        """Test that all major Chinese variants are supported."""
        client = WikipediaClient()
        
        expected_chinese_variants = [
            'zh-hans', 'zh-hant', 'zh-tw', 'zh-hk', 
            'zh-mo', 'zh-cn', 'zh-sg', 'zh-my'
        ]
        
        for variant in expected_chinese_variants:
            assert variant in client.LANGUAGE_VARIANTS, f"Missing Chinese variant: {variant}"
            assert client.LANGUAGE_VARIANTS[variant] == 'zh', f"Wrong base for {variant}"

    def test_serbian_variants_comprehensive(self):
        """Test that Serbian script variants are supported."""
        client = WikipediaClient()
        
        expected_serbian_variants = ['sr-latn', 'sr-cyrl']
        
        for variant in expected_serbian_variants:
            assert variant in client.LANGUAGE_VARIANTS, f"Missing Serbian variant: {variant}"
            assert client.LANGUAGE_VARIANTS[variant] == 'sr', f"Wrong base for {variant}"