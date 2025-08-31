# tests/test_server.py
import unittest
import asyncio
import os
from paper_search_mcp import server

class TestPaperSearchServer(unittest.TestCase):
    def test_search_arxiv(self):
        """Test the search_arxiv tool returns 10 results."""
        result = asyncio.run(server.search_arxiv("machine learning", max_results=10))
        self.assertIsInstance(result, list, "Result should be a list")
        self.assertEqual(len(result), 10, "Should return exactly 10 results")
        for paper in result:
            self.assertIn('title', paper, "Each result should contain a title")
            self.assertIn('paper_id', paper, "Each result should contain a paper_id")

    def test_download_arxiv_from_search(self):
        """Test downloading 10 arXiv papers based on search results."""
        # 先搜索 10 个结果
        search_results = asyncio.run(server.search_arxiv("machine learning", max_results=10))
        self.assertEqual(len(search_results), 10, "Search should return 10 results")

        # 下载目录
        save_path = "./downloads"
        os.makedirs(save_path, exist_ok=True)  # 确保目录存在

        # 下载每个搜索结果的 PDF
        for paper in search_results:
            paper_id = paper['paper_id']
            result = asyncio.run(server.download_arxiv(paper_id, save_path))
            self.assertIsInstance(result, str, f"Result for {paper_id} should be a file path")
            self.assertTrue(result.endswith(".pdf"), f"Result for {paper_id} should be a PDF file path")
            self.assertTrue(os.path.exists(result), f"PDF file for {paper_id} should exist on disk")

if __name__ == "__main__":
    unittest.main()