import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any, Optional

class WikiCFPScraper:
    """WikiCFP tool.search scraper for conference information"""
    
    def __init__(self):
        self.base_url = "http://www.wikicfp.com"
        self.search_url = "http://www.wikicfp.com/cfp/servlet/tool.search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def search_conferences(self, query: str, year: str = 't') -> List[Dict]:
        """
        Search for conferences on WikiCFP
        
        Args:
            query: Search term
            year: Year filter ('t' = this year, 'n' = next year, 'a' = all)
            
        Returns:
            Conference list
        """
        conferences = []
        
        try:
            params = {
                'q': query,
                'year': year
            }
            
            print(f"Searching for: {query}")
            response = requests.get(self.search_url, params=params, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Could not connect to WikiCFP! (status code: {response.status_code})")
                return conferences
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main conference table
            tables = soup.find_all('table', attrs={'cellpadding': '2', 'cellspacing': '1'})
            
            for table in tables:
                # Check for header row
                header_row = table.find('tr', attrs={'bgcolor': '#bbbbbb'})
                if header_row:
                    # This is a conference table, process it
                    conferences.extend(self._parse_conference_table(table))
            
        except Exception as e:
            print(f"Error occurred: {e}")
        
        return conferences
    
    def _parse_conference_table(self, table) -> List[Dict]:
        """Parse the conference table"""
        conferences = []
        
        # Get all rows (excluding header)
        rows = table.find_all('tr')[1:]  # First row is header
        
        i = 0
        while i < len(rows):
            # Each conference spans two rows
            if i + 1 < len(rows):
                first_row = rows[i]
                second_row = rows[i + 1]
                
                conference = self._parse_conference_pair(first_row, second_row)
                if conference:
                    conferences.append(conference)
                
                i += 2
            else:
                i += 1
        
        return conferences
    
    def _parse_conference_pair(self, first_row, second_row) -> Dict:
        """Parse the two rows containing conference information"""
        try:
            # From first row: conference name and link
            first_cells = first_row.find_all('td')
            if not first_cells:
                return None
            
            # First cell (with rowspan=2) contains conference name and link
            name_cell = first_cells[0]
            link = name_cell.find('a')
            
            if link:
                event_name = link.text.strip()
                event_link = self.base_url + link.get('href', '')
            else:
                event_name = name_cell.text.strip()
                event_link = ''
            
            # Second cell of first row usually contains conference description
            conference_description = ""
            if len(first_cells) > 1:
                conference_description = first_cells[1].text.strip()
            
            # From second row: date, location and deadline
            second_cells = second_row.find_all('td')
            
            event_time = ""
            event_location = ""
            deadline = ""
            
            if len(second_cells) >= 3:
                event_time = second_cells[0].text.strip()
                event_location = second_cells[1].text.strip()
                deadline = second_cells[2].text.strip()
            
            # Create description
            description = conference_description
            if not description:
                description_parts = []
                if event_location:
                    description_parts.append(f"Location: {event_location}")
                if deadline:
                    description_parts.append(f"Deadline: {deadline}")
                description = " | ".join(description_parts) if description_parts else "Conference"
            
            return {
                "event_name": event_name,
                "event_description": conference_description,
                "event_time": event_time,
                "event_location": event_location,
                "deadline": deadline,
                "description": description,
                "event_link": event_link
            }
            
        except Exception as e:
            print(f"Parse error: {e}")
            return None

def getEvents(keywords: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Get conference events matching the given keywords
    
    Args:
        keywords: Search terms for conferences
        limit: Maximum number of events to return (None for all)
        
    Returns:
        Dictionary with status and results
    """
    try:
        scraper = WikiCFPScraper()
        
        # Perform search
        conferences = scraper.search_conferences(keywords, year='t')
        
        # Limit results if specified
        if limit is not None and limit > 0:
            conferences = conferences[:limit]
        
        return {
            "status": "success",
            "count": len(conferences),
            "events": conferences
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "events": []
        }

# The following code only runs when directly executed, not when imported
if __name__ == "__main__":
    # Simple CLI test for the getEvents function
    import sys
    
    keywords = "ai agent"
    limit = 5
    
    if len(sys.argv) > 1:
        keywords = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            print(f"Invalid limit: {sys.argv[2]}. Using default: {limit}")
    
    result = getEvents(keywords, limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))