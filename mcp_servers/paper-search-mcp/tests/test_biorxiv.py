import unittest
import os
import requests
from paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher

def check_api_accessible():
    """检查 bioRxiv API 是否可访问"""
    try:
        response = requests.get("https://api.biorxiv.org/details/biorxiv/0/1", timeout=5)
        return response.status_code == 200
    except:
        return False

class TestBioRxivSearcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_accessible = check_api_accessible()
        if not cls.api_accessible:
            print("\nWarning: bioRxiv API is not accessible, some tests will be skipped")

    def setUp(self):
        self.searcher = BioRxivSearcher()

    def test_search(self):
        if not self.api_accessible:
            self.skipTest("bioRxiv API is not accessible")
        
        papers = self.searcher.search("machine learning", max_results=10)
        print(f"Found {len(papers)} papers for query 'machine learning':")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.title} (ID: {paper.paper_id})")
        self.assertTrue(len(papers) > 0)
        self.assertTrue(papers[0].title)

    def test_download_and_read(self):
        if not self.api_accessible:
            self.skipTest("bioRxiv API is not accessible")
            
        papers = self.searcher.search("machine learning", max_results=1)
        if not papers:
            self.skipTest("No papers found for testing download")
            
        save_path = "./downloads"
        os.makedirs(save_path, exist_ok=True)
        paper = papers[0]
        pdf_path = None
        
        try:
            pdf_path = self.searcher.download_pdf(paper.paper_id, save_path)
            self.assertTrue(os.path.exists(pdf_path))
            
            text_content = self.searcher.read_paper(paper.paper_id, save_path)
            self.assertTrue(len(text_content) > 0)
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(save_path):
                os.rmdir(save_path)

if __name__ == '__main__':
    unittest.main()