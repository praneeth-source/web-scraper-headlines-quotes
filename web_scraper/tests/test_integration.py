"""Integration tests for Project 04: Web Scraper for Headlines & Quotes."""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure web_scraper directory is on python path for imports
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scraper import create_soup, fetch_page, FetchResult
from headlines_scraper import extract_headlines, scrape_headlines
from quotes_scraper import extract_quotes, scrape_quotes
import storage
import main


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests combining scraping, extraction, and persistence."""

    def setUp(self):
        """Create a temporary directory for isolated integration storage."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, "headlines.csv")
        self.txt_path = os.path.join(self.temp_dir.name, "quotes.txt")

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    def test_end_to_end_headlines_pipeline(self):
        """Verify fetching HTML, extracting headlines, and saving to CSV end-to-end."""
        html_fixture = """
        <html>
        <head><title>Tech News</title></head>
        <body>
            <h1><a href="/lead-story">Major Breakthrough in Artificial Intelligence 🚀</a></h1>
            <h2><a href="https://example.com/quantum">Quantum Algorithm Scales to New Limits</a></h2>
            <h3><a href="">Community Announcement Without Link</a></h3>
        </body>
        </html>
        """
        # 1. Extract headlines
        headlines = extract_headlines(
            html_fixture,
            base_url="https://news.example.com/",
            default_source="Tech World",
        )
        self.assertEqual(len(headlines), 3)

        # 2. Save to CSV
        saved_count = storage.save_headlines_to_csv(headlines, filepath=self.csv_path)
        self.assertEqual(saved_count, 3)

        # 3. Read back from CSV
        stored = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(stored), 3)
        self.assertEqual(stored[0]["Headline"], "Major Breakthrough in Artificial Intelligence 🚀")
        self.assertEqual(stored[0]["URL"], "https://news.example.com/lead-story")
        self.assertEqual(stored[1]["Headline"], "Quantum Algorithm Scales to New Limits")
        self.assertEqual(stored[1]["URL"], "https://example.com/quantum")

        # 4. Re-save identical batch -> duplicate prevention
        second_run_count = storage.save_headlines_to_csv(headlines, filepath=self.csv_path)
        self.assertEqual(second_run_count, 0)
        self.assertEqual(len(storage.read_headlines_from_csv(filepath=self.csv_path)), 3)

    def test_end_to_end_quotes_pipeline(self):
        """Verify fetching HTML, extracting quotes, and saving to TXT end-to-end."""
        html_fixture = """
        <html>
        <body>
            <div class="quote">
                <span class="text">“Stay hungry, stay foolish. 💡”</span>
                <small class="author">Steve Jobs</small>
                <div class="tags"><a class="tag">inspiration</a></div>
            </div>
            <div class="quote">
                <span class="text">“Talk is cheap. Show me the code.”</span>
                <small class="author">Linus Torvalds</small>
            </div>
        </body>
        </html>
        """
        # 1. Extract quotes
        quotes = extract_quotes(html_fixture)
        self.assertEqual(len(quotes), 2)

        # 2. Save to TXT
        saved_count = storage.save_quotes_to_txt(quotes, filepath=self.txt_path)
        self.assertEqual(saved_count, 2)

        # 3. Read back from TXT
        stored = storage.read_quotes_from_txt(filepath=self.txt_path)
        self.assertEqual(len(stored), 2)
        self.assertIn('"Stay hungry, stay foolish. 💡" - Steve Jobs (Tags: inspiration)', stored[0])
        self.assertIn('"Talk is cheap. Show me the code." - Linus Torvalds', stored[1])

        # 4. Re-save identical batch -> duplicate prevention
        second_run_count = storage.save_quotes_to_txt(quotes, filepath=self.txt_path)
        self.assertEqual(second_run_count, 0)
        self.assertEqual(len(storage.read_quotes_from_txt(filepath=self.txt_path)), 2)

    def test_main_demo_mode_executes_without_error(self):
        """Verify main.run_demo_mode() executes cleanly and outputs expected sections."""
        captured_out = io.StringIO()
        with patch("sys.stdout", captured_out):
            main.run_demo_mode()

        output = captured_out.getvalue()
        self.assertIn("PROJECT 04: WEB SCRAPER FOR HEADLINES & QUOTES", output)
        self.assertIn("Component Architecture & Readiness", output)
        self.assertIn("Offline Headline Extraction", output)
        self.assertIn("Offline Quote Extraction", output)
        self.assertIn("Live Connection Verification", output)
        self.assertIn("Storage Stats", output)

    def test_main_menu_view_functions(self):
        """Verify main menu view functions display content without crashing."""
        captured_out = io.StringIO()
        with patch("sys.stdout", captured_out):
            main.menu_view_headlines()
            main.menu_view_quotes()
            main.menu_view_stats()

        output = captured_out.getvalue()
        self.assertIn("Stored Headlines", output)
        self.assertIn("Stored Quotes", output)
        self.assertIn("Storage Inventory & File Statistics", output)


if __name__ == "__main__":
    unittest.main()
