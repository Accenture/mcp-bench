"""
Tests for country/locale support functionality.
"""

import pytest
from unittest.mock import patch, Mock
from wikipedia_mcp.wikipedia_client import WikipediaClient
from wikipedia_mcp.server import create_server


class TestCountryToLanguageMapping:
    """Test country code to language code mapping functionality."""

    def test_resolve_country_to_language_basic_codes(self):
        """Test basic country code resolution."""
        client = WikipediaClient()
        
        test_cases = [
            ('US', 'en'),
            ('CN', 'zh-hans'),
            ('TW', 'zh-tw'),
            ('JP', 'ja'),
            ('DE', 'de'),
            ('FR', 'fr'),
            ('ES', 'es'),
            ('IT', 'it'),
            ('RU', 'ru'),
            ('BR', 'pt'),
        ]
        
        for country, expected_lang in test_cases:
            result = client._resolve_country_to_language(country)
            assert result == expected_lang, f"Failed for {country}: expected {expected_lang}, got {result}"

    def test_resolve_country_to_language_full_names(self):
        """Test country full name resolution."""
        client = WikipediaClient()
        
        test_cases = [
            ('United States', 'en'),
            ('China', 'zh-hans'),
            ('Taiwan', 'zh-tw'),
            ('Japan', 'ja'),
            ('Germany', 'de'),
            ('France', 'fr'),
            ('Spain', 'es'),
            ('Italy', 'it'),
            ('Russia', 'ru'),
            ('Brazil', 'pt'),
        ]
        
        for country, expected_lang in test_cases:
            result = client._resolve_country_to_language(country)
            assert result == expected_lang, f"Failed for {country}: expected {expected_lang}, got {result}"

    def test_resolve_country_case_insensitive(self):
        """Test that country resolution is case insensitive."""
        client = WikipediaClient()
        
        test_cases = [
            ('us', 'en'),
            ('Us', 'en'),
            ('US', 'en'),
            ('uS', 'en'),
            ('china', 'zh-hans'),
            ('CHINA', 'zh-hans'),
            ('China', 'zh-hans'),
        ]
        
        for country, expected_lang in test_cases:
            result = client._resolve_country_to_language(country)
            assert result == expected_lang, f"Failed for {country}: expected {expected_lang}, got {result}"

    def test_resolve_country_invalid_code(self):
        """Test error handling for invalid country codes."""
        client = WikipediaClient()
        
        with pytest.raises(ValueError) as exc_info:
            client._resolve_country_to_language('INVALID')
        
        error_msg = str(exc_info.value)
        assert 'Unsupported country/locale' in error_msg
        assert 'INVALID' in error_msg
        assert 'Supported country codes include:' in error_msg
        assert '--language parameter' in error_msg

    def test_resolve_country_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        client = WikipediaClient()
        
        test_cases = [
            ('  US  ', 'en'),
            ('\tJP\t', 'ja'),
            (' China ', 'zh-hans'),
        ]
        
        for country, expected_lang in test_cases:
            result = client._resolve_country_to_language(country)
            assert result == expected_lang, f"Failed for '{country}': expected {expected_lang}, got {result}"


class TestWikipediaClientCountrySupport:
    """Test WikipediaClient initialization with country codes."""

    def test_client_init_with_country_code(self):
        """Test initializing client with country code."""
        client = WikipediaClient(country='TW')
        
        assert client.original_input == 'TW'
        assert client.input_type == 'country'
        assert client.resolved_language == 'zh-tw'
        assert client.base_language == 'zh'
        assert client.language_variant == 'zh-tw'
        assert client.api_url == 'https://zh.wikipedia.org/w/api.php'

    def test_client_init_with_country_name(self):
        """Test initializing client with country full name."""
        client = WikipediaClient(country='Japan')
        
        assert client.original_input == 'Japan'
        assert client.input_type == 'country'
        assert client.resolved_language == 'ja'
        assert client.base_language == 'ja'
        assert client.language_variant is None
        assert client.api_url == 'https://ja.wikipedia.org/w/api.php'

    def test_client_init_with_language_fallback(self):
        """Test that language parameter still works when country is not provided."""
        client = WikipediaClient(language='zh-hans')
        
        assert client.original_input == 'zh-hans'
        assert client.input_type == 'language'
        assert client.resolved_language == 'zh-hans'
        assert client.base_language == 'zh'
        assert client.language_variant == 'zh-hans'

    def test_client_init_country_overrides_language(self):
        """Test that country parameter overrides language parameter."""
        client = WikipediaClient(language='en', country='JP')
        
        assert client.original_input == 'JP'
        assert client.input_type == 'country'
        assert client.resolved_language == 'ja'
        assert client.base_language == 'ja'
        assert client.language_variant is None

    def test_client_init_invalid_country(self):
        """Test error handling for invalid country during initialization."""
        with pytest.raises(ValueError) as exc_info:
            WikipediaClient(country='INVALID')
        
        error_msg = str(exc_info.value)
        assert 'Unsupported country/locale: \'INVALID\'' in error_msg

    def test_client_init_with_country_and_cache(self):
        """Test initializing client with country and caching enabled."""
        client = WikipediaClient(country='US', enable_cache=True)
        
        assert client.original_input == 'US'
        assert client.input_type == 'country'
        assert client.resolved_language == 'en'
        assert client.enable_cache is True


class TestServerCountryIntegration:
    """Test server creation with country support."""

    def test_create_server_with_country(self):
        """Test creating server with country parameter."""
        server = create_server(country='TW')
        
        assert server is not None
        assert server.name == "Wikipedia"

    def test_create_server_with_country_and_cache(self):
        """Test creating server with country and caching."""
        server = create_server(country='Japan', enable_cache=True)
        
        assert server is not None
        assert server.name == "Wikipedia"

    def test_create_server_country_overrides_language(self):
        """Test that country parameter overrides language in server creation."""
        server = create_server(language='en', country='CN')
        
        assert server is not None
        assert server.name == "Wikipedia"

    def test_create_server_invalid_country(self):
        """Test error handling for invalid country in server creation."""
        with pytest.raises(ValueError):
            create_server(country='INVALID')


class TestCountryAPIIntegration:
    """Test API integration with country codes."""

    @patch('requests.get')
    def test_search_with_country_code(self, mock_get):
        """Test that search works correctly with country-resolved language."""
        # Setup mock response for Chinese Wikipedia
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': '中華民國',
                        'snippet': 'Taiwan search result',
                        'pageid': 123,
                        'wordcount': 1000,
                        'timestamp': '2024-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test search with Taiwan country code
        client = WikipediaClient(country='TW')
        results = client.search('Taiwan', limit=5)

        # Verify API was called with correct language
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == 'https://zh.wikipedia.org/w/api.php'
        
        params = call_args[1]['params']
        assert params['variant'] == 'zh-tw'  # Should use Taiwan variant
        assert params['srsearch'] == 'Taiwan'

        # Verify results
        assert len(results) == 1
        assert results[0]['title'] == '中華民國'


class TestCountryMappingCompleteness:
    """Test the completeness and consistency of country mappings."""

    def test_country_mapping_structure(self):
        """Test that country mappings have proper structure."""
        client = WikipediaClient()
        
        for country, language in client.COUNTRY_TO_LANGUAGE.items():
            assert isinstance(country, str), f"Country key must be string: {country}"
            assert isinstance(language, str), f"Language value must be string: {language}"
            assert len(country) > 0, f"Country cannot be empty: {country}"
            assert len(language) > 0, f"Language cannot be empty: {language}"

    def test_major_countries_covered(self):
        """Test that major countries are covered in the mapping."""
        client = WikipediaClient()
        
        # Major countries that should be supported
        major_countries = [
            'US', 'CN', 'JP', 'DE', 'FR', 'UK', 'IN', 'BR', 'RU', 'CA',
            'AU', 'IT', 'ES', 'KR', 'MX', 'ID', 'TR', 'SA', 'TH', 'TW'
        ]
        
        for country in major_countries:
            assert country in client.COUNTRY_TO_LANGUAGE, f"Major country missing: {country}"

    def test_language_variants_consistency(self):
        """Test that country mappings are consistent with language variants."""
        client = WikipediaClient()
        
        # Countries that should map to language variants
        variant_mappings = [
            ('CN', 'zh-hans'),
            ('TW', 'zh-tw'),
            ('HK', 'zh-hk'),
            ('MO', 'zh-mo'),
            ('SG', 'zh-sg'),
            ('MY', 'zh-my'),
        ]
        
        for country, expected_variant in variant_mappings:
            assert client.COUNTRY_TO_LANGUAGE[country] == expected_variant

    def test_english_speaking_countries(self):
        """Test that major English-speaking countries map to English."""
        client = WikipediaClient()
        
        english_countries = ['US', 'UK', 'CA', 'AU', 'NZ', 'IE', 'ZA']
        
        for country in english_countries:
            assert client.COUNTRY_TO_LANGUAGE[country] == 'en', f"{country} should map to 'en'"

    def test_no_duplicate_country_names(self):
        """Test that there are no conflicting country names."""
        client = WikipediaClient()
        
        # Check for potential conflicts (case-insensitive)
        seen_countries = set()
        conflicts = []
        
        for country in client.COUNTRY_TO_LANGUAGE.keys():
            country_lower = country.lower()
            if country_lower in seen_countries:
                conflicts.append(country)
            seen_countries.add(country_lower)
        
        assert len(conflicts) == 0, f"Found conflicting country entries: {conflicts}"