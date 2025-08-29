"""
Wikipedia API client implementation.
"""

import logging
import wikipediaapi
import requests
from typing import Dict, List, Optional, Any
import functools

logger = logging.getLogger(__name__)

class WikipediaClient:
    """Client for interacting with the Wikipedia API."""

    # Language variant mappings - maps variant codes to their base language
    LANGUAGE_VARIANTS = {
        'zh-hans': 'zh',  # Simplified Chinese
        'zh-hant': 'zh',  # Traditional Chinese
        'zh-tw': 'zh',    # Traditional Chinese (Taiwan)
        'zh-hk': 'zh',    # Traditional Chinese (Hong Kong)
        'zh-mo': 'zh',    # Traditional Chinese (Macau)
        'zh-cn': 'zh',    # Simplified Chinese (China)
        'zh-sg': 'zh',    # Simplified Chinese (Singapore)
        'zh-my': 'zh',    # Simplified Chinese (Malaysia)
        # Add more language variants as needed
        # Serbian variants
        'sr-latn': 'sr',  # Serbian Latin
        'sr-cyrl': 'sr',  # Serbian Cyrillic
        # Norwegian variants
        'no': 'nb',       # Norwegian Bokmål (default)
        # Kurdish variants  
        'ku-latn': 'ku',  # Kurdish Latin
        'ku-arab': 'ku',  # Kurdish Arabic
    }

    def __init__(self, language: str = "en", enable_cache: bool = False):
        """Initialize the Wikipedia client.
        
        Args:
            language: The language code for Wikipedia (default: "en" for English).
                     Supports language variants like 'zh-hans', 'zh-tw', etc.
            enable_cache: Whether to enable caching for API calls (default: False).
        """
        self.original_language = language
        self.enable_cache = enable_cache
        self.user_agent = "WikipediaMCPServer/0.1.0 (https://github.com/rudra-ravi/wikipedia-mcp)"
        
        # Parse language and variant
        self.base_language, self.language_variant = self._parse_language_variant(language)
        
        # Use base language for API and library initialization
        self.wiki = wikipediaapi.Wikipedia(
            user_agent=self.user_agent,
            language=self.base_language,
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        self.api_url = f"https://{self.base_language}.wikipedia.org/w/api.php"
        
        if self.enable_cache:
            self.search = functools.lru_cache(maxsize=128)(self.search)
            self.get_article = functools.lru_cache(maxsize=128)(self.get_article)
            self.get_summary = functools.lru_cache(maxsize=128)(self.get_summary)
            self.get_sections = functools.lru_cache(maxsize=128)(self.get_sections)
            self.get_links = functools.lru_cache(maxsize=128)(self.get_links)
            self.get_related_topics = functools.lru_cache(maxsize=128)(self.get_related_topics)
            self.summarize_for_query = functools.lru_cache(maxsize=128)(self.summarize_for_query)
            self.summarize_section = functools.lru_cache(maxsize=128)(self.summarize_section)
            self.extract_facts = functools.lru_cache(maxsize=128)(self.extract_facts)

    def _parse_language_variant(self, language: str) -> tuple[str, Optional[str]]:
        """Parse language code and extract base language and variant.
        
        Args:
            language: The language code, possibly with variant (e.g., 'zh-hans', 'zh-tw').
            
        Returns:
            A tuple of (base_language, variant) where variant is None if not a variant.
        """
        if language in self.LANGUAGE_VARIANTS:
            base_language = self.LANGUAGE_VARIANTS[language]
            return base_language, language
        else:
            return language, None
    
    def _add_variant_to_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add language variant parameter to API request parameters if needed.
        
        Args:
            params: The API request parameters.
            
        Returns:
            Updated parameters with variant if applicable.
        """
        if self.language_variant:
            params = params.copy()
            params['variant'] = self.language_variant
        return params

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Wikipedia for articles matching a query.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return.
            
        Returns:
            A list of search results.
        """
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'utf8': 1,
            'srsearch': query,
            'srlimit': limit
        }
        
        # Add variant parameter if needed
        params = self._add_variant_to_params(params)
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('query', {}).get('search', []):
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'pageid': item.get('pageid', 0),
                    'wordcount': item.get('wordcount', 0),
                    'timestamp': item.get('timestamp', '')
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []

    def get_article(self, title: str) -> Dict[str, Any]:
        """Get the full content of a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article.
            
        Returns:
            A dictionary containing the article information.
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                return {
                    'title': title,
                    'exists': False,
                    'error': 'Page does not exist'
                }
            
            # Get sections
            sections = self._extract_sections(page.sections)
            
            # Get categories
            categories = [cat for cat in page.categories.keys()]
            
            # Get links
            links = [link for link in page.links.keys()]
            
            return {
                'title': page.title,
                'pageid': page.pageid,
                'summary': page.summary,
                'text': page.text,
                'url': page.fullurl,
                'sections': sections,
                'categories': categories,
                'links': links[:100],  # Limit to 100 links to avoid too much data
                'exists': True
            }
        except Exception as e:
            logger.error(f"Error getting Wikipedia article: {e}")
            return {
                'title': title,
                'exists': False,
                'error': str(e)
            }

    def get_summary(self, title: str) -> str:
        """Get a summary of a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article.
            
        Returns:
            The article summary.
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                return f"No Wikipedia article found for '{title}'."
            
            return page.summary
        except Exception as e:
            logger.error(f"Error getting Wikipedia summary: {e}")
            return f"Error retrieving summary for '{title}': {str(e)}"

    def get_sections(self, title: str) -> List[Dict[str, Any]]:
        """Get the sections of a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article.
            
        Returns:
            A list of sections.
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                return []
            
            return self._extract_sections(page.sections)
        except Exception as e:
            logger.error(f"Error getting Wikipedia sections: {e}")
            return []

    def get_links(self, title: str) -> List[str]:
        """Get the links in a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article.
            
        Returns:
            A list of links.
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                return []
            
            return [link for link in page.links.keys()]
        except Exception as e:
            logger.error(f"Error getting Wikipedia links: {e}")
            return []

    def get_related_topics(self, title: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get topics related to a Wikipedia article based on links and categories.
        
        Args:
            title: The title of the Wikipedia article.
            limit: Maximum number of related topics to return.
            
        Returns:
            A list of related topics.
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                return []
            
            # Get links from the page
            links = list(page.links.keys())
            
            # Get categories
            categories = list(page.categories.keys())
            
            # Combine and limit
            related = []
            
            # Add links first
            for link in links[:limit]:
                link_page = self.wiki.page(link)
                if link_page.exists():
                    related.append({
                        'title': link,
                        'summary': link_page.summary[:200] + '...' if len(link_page.summary) > 200 else link_page.summary,
                        'url': link_page.fullurl,
                        'type': 'link'
                    })
                
                if len(related) >= limit:
                    break
            
            # Add categories if we still have room
            remaining = limit - len(related)
            if remaining > 0:
                for category in categories[:remaining]:
                    # Remove "Category:" prefix if present
                    clean_category = category.replace("Category:", "")
                    related.append({
                        'title': clean_category,
                        'type': 'category'
                    })
            
            return related
        except Exception as e:
            logger.error(f"Error getting related topics: {e}")
            return []

    def _extract_sections(self, sections, level=0) -> List[Dict[str, Any]]:
        """Extract sections recursively.
        
        Args:
            sections: The sections to extract.
            level: The current section level.
            
        Returns:
            A list of sections.
        """
        result = []
        
        for section in sections:
            section_data = {
                'title': section.title,
                'level': level,
                'text': section.text,
                'sections': self._extract_sections(section.sections, level + 1)
            }
            result.append(section_data)
        
        return result

    def summarize_for_query(self, title: str, query: str, max_length: int = 250) -> str:
        """
        Get a summary of a Wikipedia article tailored to a specific query.
        This is a simplified implementation that returns a snippet around the query.
        
        Args:
            title: The title of the Wikipedia article.
            query: The query to focus the summary on.
            max_length: The maximum length of the summary.
            
        Returns:
            A query-focused summary.
        """
        try:
            page = self.wiki.page(title)
            if not page.exists():
                return f"No Wikipedia article found for '{title}'."

            text_content = page.text
            query_lower = query.lower()
            text_lower = text_content.lower()

            start_index = text_lower.find(query_lower)
            if start_index == -1:
                # If query not found, return the beginning of the summary or article text
                summary_part = page.summary[:max_length]
                if not summary_part:
                    summary_part = text_content[:max_length]
                return summary_part + "..." if len(summary_part) >= max_length else summary_part


            # Try to get context around the query
            context_start = max(0, start_index - (max_length // 2))
            context_end = min(len(text_content), start_index + len(query) + (max_length // 2))
            
            snippet = text_content[context_start:context_end]
            
            if len(snippet) > max_length:
                snippet = snippet[:max_length]

            return snippet + "..." if len(snippet) >= max_length or context_end < len(text_content) else snippet

        except Exception as e:
            logger.error(f"Error generating query-focused summary for '{title}': {e}")
            return f"Error generating query-focused summary for '{title}': {str(e)}"

    def summarize_section(self, title: str, section_title: str, max_length: int = 150) -> str:
        """
        Get a summary of a specific section of a Wikipedia article.
        
        Args:
            title: The title of the Wikipedia article.
            section_title: The title of the section to summarize.
            max_length: The maximum length of the summary.
            
        Returns:
            A summary of the specified section.
        """
        try:
            page = self.wiki.page(title)
            if not page.exists():
                return f"No Wikipedia article found for '{title}'."

            target_section = None
            
            # Helper function to find the section
            def find_section_recursive(sections_list, target_title):
                for sec in sections_list:
                    if sec.title.lower() == target_title.lower():
                        return sec
                    # Check subsections
                    found_in_subsection = find_section_recursive(sec.sections, target_title)
                    if found_in_subsection:
                        return found_in_subsection
                return None

            target_section = find_section_recursive(page.sections, section_title)

            if not target_section or not target_section.text:
                return f"Section '{section_title}' not found or is empty in article '{title}'."
            
            summary = target_section.text[:max_length]
            return summary + "..." if len(target_section.text) > max_length else summary
            
        except Exception as e:
            logger.error(f"Error summarizing section '{section_title}' for article '{title}': {e}")
            return f"Error summarizing section '{section_title}': {str(e)}"

    def extract_facts(self, title: str, topic_within_article: Optional[str] = None, count: int = 5) -> List[str]:
        """
        Extract key facts from a Wikipedia article.
        This is a simplified implementation returning the first few sentences of the summary
        or a relevant section if topic_within_article is provided.
        
        Args:
            title: The title of the Wikipedia article.
            topic_within_article: Optional topic/section to focus fact extraction.
            count: The number of facts to extract.
            
        Returns:
            A list of key facts (strings).
        """
        try:
            page = self.wiki.page(title)
            if not page.exists():
                return [f"No Wikipedia article found for '{title}'."]

            text_to_process = ""
            if topic_within_article:
                # Try to find the section text
                def find_section_text_recursive(sections_list, target_title):
                    for sec in sections_list:
                        if sec.title.lower() == target_title.lower():
                            return sec.text
                        found_in_subsection = find_section_text_recursive(sec.sections, target_title)
                        if found_in_subsection:
                            return found_in_subsection
                    return None
                
                section_text = find_section_text_recursive(page.sections, topic_within_article)
                if section_text:
                    text_to_process = section_text
                else:
                    # Fallback to summary if specific topic section not found
                    text_to_process = page.summary
            else:
                text_to_process = page.summary
            
            if not text_to_process:
                return ["No content found to extract facts from."]

            # Basic sentence splitting (can be improved with NLP libraries like nltk or spacy)
            sentences = [s.strip() for s in text_to_process.split('.') if s.strip()]
            
            facts = []
            for sentence in sentences[:count]:
                if sentence: # Ensure not an empty string after strip
                    facts.append(sentence + ".") # Add back the period
            
            return facts if facts else ["Could not extract facts from the provided text."]

        except Exception as e:
            logger.error(f"Error extracting key facts for '{title}': {e}")
            return [f"Error extracting key facts for '{title}': {str(e)}"] 