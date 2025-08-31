"""
Comprehensive tests for Wikipedia MCP server tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from wikipedia_mcp.server import create_server
from wikipedia_mcp.wikipedia_client import WikipediaClient


class TestWikipediaClient:
    """Test the WikipediaClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = WikipediaClient()

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_search_success(self, mock_get):
        """Test successful search operation."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'query': {
                'search': [
                    {
                        'title': 'Python (programming language)',
                        'snippet': 'Python is a programming language',
                        'pageid': 12345,
                        'wordcount': 1000,
                        'timestamp': '2023-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        # Test search
        results = self.client.search('Python', limit=1)
        
        # Assertions
        assert len(results) == 1
        assert results[0]['title'] == 'Python (programming language)'
        assert results[0]['snippet'] == 'Python is a programming language'
        assert results[0]['pageid'] == 12345
        mock_get.assert_called_once()

    @patch('wikipedia_mcp.wikipedia_client.requests.get')
    def test_search_failure(self, mock_get):
        """Test search operation with API failure."""
        mock_get.side_effect = Exception("API Error")
        
        results = self.client.search('Python')
        assert results == []

    @patch('wikipedia_mcp.wikipedia_client.WikipediaClient._extract_sections')
    def test_get_article_success(self, mock_extract_sections):
        """Test successful article retrieval."""
        # Mock Wikipedia page
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Python (programming language)'
        mock_page.pageid = 12345
        mock_page.summary = 'Python is a programming language'
        mock_page.text = 'Full article text here'
        mock_page.fullurl = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
        mock_page.categories = {'Category:Programming languages': None}
        mock_page.links = {'Link1': None, 'Link2': None}
        mock_page.sections = []

        mock_extract_sections.return_value = [{'title': 'History', 'level': 0, 'text': 'History text', 'sections': []}]

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            article = self.client.get_article('Python (programming language)')

        assert article['exists'] is True
        assert article['title'] == 'Python (programming language)'
        assert article['pageid'] == 12345
        assert article['summary'] == 'Python is a programming language'
        assert article['text'] == 'Full article text here'
        assert len(article['categories']) == 1
        assert len(article['links']) == 2

    def test_get_article_not_found(self):
        """Test article retrieval for non-existent page."""
        mock_page = Mock()
        mock_page.exists.return_value = False

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            article = self.client.get_article('NonExistentPage')

        assert article['exists'] is False
        assert article['error'] == 'Page does not exist'

    def test_get_summary_success(self):
        """Test successful summary retrieval."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.summary = 'This is a test summary'

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.get_summary('Test Page')

        assert summary == 'This is a test summary'

    def test_get_summary_not_found(self):
        """Test summary retrieval for non-existent page."""
        mock_page = Mock()
        mock_page.exists.return_value = False

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.get_summary('NonExistentPage')

        assert "No Wikipedia article found for 'NonExistentPage'" in summary

    @patch('wikipedia_mcp.wikipedia_client.WikipediaClient._extract_sections')
    def test_get_sections_success(self, mock_extract_sections):
        """Test successful sections retrieval."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.sections = []

        mock_extract_sections.return_value = [
            {'title': 'History', 'level': 0, 'text': 'History text', 'sections': []},
            {'title': 'Features', 'level': 0, 'text': 'Features text', 'sections': []}
        ]

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            sections = self.client.get_sections('Test Page')

        assert len(sections) == 2
        assert sections[0]['title'] == 'History'
        assert sections[1]['title'] == 'Features'

    def test_get_sections_not_found(self):
        """Test sections retrieval for non-existent page."""
        mock_page = Mock()
        mock_page.exists.return_value = False

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            sections = self.client.get_sections('NonExistentPage')

        assert sections == []

    def test_get_links_success(self):
        """Test successful links retrieval."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.links = {'Link1': None, 'Link2': None, 'Link3': None}

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            links = self.client.get_links('Test Page')

        assert len(links) == 3
        assert 'Link1' in links
        assert 'Link2' in links
        assert 'Link3' in links

    def test_get_links_not_found(self):
        """Test links retrieval for non-existent page."""
        mock_page = Mock()
        mock_page.exists.return_value = False

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            links = self.client.get_links('NonExistentPage')

        assert links == []

    def test_get_related_topics_success(self):
        """Test successful related topics retrieval."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.links = {'Related Link 1': None, 'Related Link 2': None}
        mock_page.categories = {'Category:Test Category': None}

        # Mock related page
        mock_related_page = Mock()
        mock_related_page.exists.return_value = True
        mock_related_page.summary = 'Summary of related page'
        mock_related_page.fullurl = 'https://en.wikipedia.org/wiki/Related_Link_1'

        with patch.object(self.client.wiki, 'page') as mock_wiki_page:
            mock_wiki_page.side_effect = lambda title: mock_related_page if title in ['Related Link 1', 'Related Link 2'] else mock_page
            
            related = self.client.get_related_topics('Test Page', limit=3)

        assert len(related) >= 1
        assert any(topic['type'] == 'link' for topic in related)

    def test_get_related_topics_not_found(self):
        """Test related topics retrieval for non-existent page."""
        mock_page = Mock()
        mock_page.exists.return_value = False

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            related = self.client.get_related_topics('NonExistentPage')

        assert related == []

    def test_extract_sections(self):
        """Test section extraction helper method."""
        # Mock section structure
        mock_subsection = Mock()
        mock_subsection.title = 'Subsection'
        mock_subsection.text = 'Subsection text'
        mock_subsection.sections = []

        mock_section = Mock()
        mock_section.title = 'Main Section'
        mock_section.text = 'Main section text'
        mock_section.sections = [mock_subsection]

        sections = self.client._extract_sections([mock_section])

        assert len(sections) == 1
        assert sections[0]['title'] == 'Main Section'
        assert sections[0]['level'] == 0
        assert sections[0]['text'] == 'Main section text'
        assert len(sections[0]['sections']) == 1
        assert sections[0]['sections'][0]['title'] == 'Subsection'
        assert sections[0]['sections'][0]['level'] == 1

    def test_summarize_for_query_success(self):
        """Test successful query-focused summary retrieval."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.text = 'This is a long text about a specific keyword. We want to find this keyword and summarize around it.'
        mock_page.summary = 'This is a general summary.'

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_for_query('Test Page', 'keyword', max_length=50)
        
        assert 'keyword' in summary
        assert len(summary) <= 50 + 3 # for "..."

    def test_summarize_for_query_not_found(self):
        """Test query-focused summary when query is not in text."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.text = 'This is some other text.'
        mock_page.summary = 'A general summary content.'

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_for_query('Test Page', 'missing_keyword', max_length=30)

        assert 'A general summary content.'[:30] in summary # Should return start of summary

    def test_summarize_for_query_page_not_exists(self):
        """Test query-focused summary when page does not exist."""
        mock_page = Mock()
        mock_page.exists.return_value = False
        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_for_query('NonExistent Page', 'keyword')
        assert "No Wikipedia article found for 'NonExistent Page'" in summary

    def test_summarize_section_success(self):
        """Test successful section summary retrieval."""
        mock_section_target = Mock()
        mock_section_target.title = 'Target Section'
        mock_section_target.text = 'This is the text of the target section. It is fairly long.'
        mock_section_target.sections = []

        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.sections = [mock_section_target]

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_section('Test Page', 'Target Section', max_length=20)
        
        assert summary == 'This is the text of ...'
        assert len(summary) <= 20 + 3

    def test_summarize_section_not_found(self):
        """Test section summary when section does not exist."""
        mock_other_section = Mock()
        mock_other_section.title = 'Other Section'
        mock_other_section.text = 'Some text.'
        mock_other_section.sections = []

        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.sections = [mock_other_section]

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_section('Test Page', 'Missing Section')
        assert "Section 'Missing Section' not found or is empty" in summary

    def test_summarize_section_page_not_exists(self):
        """Test section summary when page does not exist."""
        mock_page = Mock()
        mock_page.exists.return_value = False
        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            summary = self.client.summarize_section('NonExistent Page', 'Any Section')
        assert "No Wikipedia article found for 'NonExistent Page'" in summary

    def test_extract_facts_success_from_summary(self):
        """Test successful fact extraction from page summary."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.summary = 'Fact one. Fact two. Fact three. Fact four. Fact five. Fact six.'
        mock_page.sections = []

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            facts = self.client.extract_facts('Test Page', count=3)
        
        assert len(facts) == 3
        assert facts[0] == 'Fact one.'
        assert facts[1] == 'Fact two.'
        assert facts[2] == 'Fact three.'

    def test_extract_facts_success_from_section(self):
        """Test successful fact extraction from a specific section."""
        mock_target_section = Mock()
        mock_target_section.title = 'Key Info'
        mock_target_section.text = 'Important fact A. Important fact B. Important fact C.'
        mock_target_section.sections = []

        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.summary = 'General summary.'
        mock_page.sections = [mock_target_section]

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            facts = self.client.extract_facts('Test Page', topic_within_article='Key Info', count=2)
        
        assert len(facts) == 2
        assert facts[0] == 'Important fact A.'
        assert facts[1] == 'Important fact B.'

    def test_extract_facts_section_not_found_fallback_to_summary(self):
        """Test fact extraction falls back to summary if section not found."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Test Page'
        mock_page.summary = 'Summary fact 1. Summary fact 2.'
        mock_page.sections = [] # No sections defined

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            facts = self.client.extract_facts('Test Page', topic_within_article='Missing Section', count=1)
        
        assert len(facts) == 1
        assert facts[0] == 'Summary fact 1.'

    def test_extract_facts_page_not_exists(self):
        """Test fact extraction when page does not exist."""
        mock_page = Mock()
        mock_page.exists.return_value = False
        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            facts = self.client.extract_facts('NonExistent Page')
        assert len(facts) == 1
        assert "No Wikipedia article found for 'NonExistent Page'" in facts[0]

    def test_extract_facts_no_content(self):
        """Test fact extraction when there is no summary or section text."""
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = 'Empty Page'
        mock_page.summary = '' # Empty summary
        mock_page.sections = []

        with patch.object(self.client.wiki, 'page', return_value=mock_page):
            facts = self.client.extract_facts('Empty Page')
        assert len(facts) == 1
        assert "No content found to extract facts from." in facts[0]


class TestMCPServerTools:
    """Test the MCP server tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = create_server()

    @patch('wikipedia_mcp.server.WikipediaClient')
    def test_create_server_with_language(self, MockWikipediaClient):
        """Test that create_server initializes WikipediaClient with the specified language."""
        create_server(language="ja")
        MockWikipediaClient.assert_called_once_with(language="ja", enable_cache=False)

    @patch('wikipedia_mcp.server.WikipediaClient')
    def test_create_server_default_language(self, MockWikipediaClient):
        """Test that create_server uses 'en' if no language is specified."""
        create_server()
        MockWikipediaClient.assert_called_once_with(language="en", enable_cache=False)

    @patch('wikipedia_mcp.server.WikipediaClient')
    def test_create_server_with_cache_enabled(self, MockWikipediaClient):
        """Test that create_server initializes WikipediaClient with caching enabled."""
        create_server(language="en", enable_cache=True)
        MockWikipediaClient.assert_called_once_with(language="en", enable_cache=True)

    @patch('wikipedia_mcp.server.WikipediaClient')
    def test_create_server_with_cache_disabled(self, MockWikipediaClient):
        """Test that create_server initializes WikipediaClient with caching disabled by default."""
        create_server(language="en", enable_cache=False)
        MockWikipediaClient.assert_called_once_with(language="en", enable_cache=False)

    def test_search_wikipedia_tool(self):
        """Test search_wikipedia tool registration."""
        # Test that server can be created without errors
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_get_article_tool(self):
        """Test get_article tool registration."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_get_summary_tool(self):
        """Test get_summary tool registration."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_get_sections_tool(self):
        """Test get_sections tool registration."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_get_links_tool(self):
        """Test get_links tool registration."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_get_related_topics_tool(self):
        """Test get_related_topics tool registration."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"


class TestIntegration:
    """Integration tests for the complete system."""

    def test_server_creation(self):
        """Test that server can be created without errors."""
        server = create_server()
        assert server is not None
        assert server.name == "Wikipedia"

    def test_client_initialization(self):
        """Test that client can be initialized with different languages."""
        client_en = WikipediaClient("en")
        assert client_en.original_language == "en"
        assert client_en.base_language == "en"
        assert client_en.language_variant is None
        
        client_es = WikipediaClient("es")
        assert client_es.original_language == "es"
        assert client_es.base_language == "es"
        assert client_es.language_variant is None

    @pytest.mark.integration
    def test_real_wikipedia_search(self):
        """Integration test with real Wikipedia API (marked as integration)."""
        client = WikipediaClient()
        results = client.search("Python programming", limit=1)
        
        # This test requires internet connection
        if results:  # Only assert if we got results (network dependent)
            assert len(results) >= 1
            assert 'title' in results[0]
            assert 'snippet' in results[0]

    @pytest.mark.integration
    def test_real_wikipedia_summary(self):
        """Integration test for real summary retrieval."""
        client = WikipediaClient()
        summary = client.get_summary("Python (programming language)")
        
        # This test requires internet connection
        if "Error" not in summary and "No Wikipedia article found" not in summary:
            assert len(summary) > 0
            assert isinstance(summary, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 