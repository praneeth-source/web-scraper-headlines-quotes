"""Unit tests for headlines_scraper.py (Headline Extraction using BeautifulSoup4)."""

import os
import sys
import unittest
from unittest.mock import patch
from datetime import datetime

# Ensure web_scraper directory is on python path for imports
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from headlines_scraper import (
    extract_headlines,
    scrape_headlines,
    format_headline,
    resolve_url,
    get_current_timestamp,
)
from scraper import FetchResult


class TestHeadlinesExtractionPhase3(unittest.TestCase):
    """Comprehensive test suite for Phase 3 headline extraction functionality."""

    def test_extract_multiple_headlines_h1_h2_h3(self):
        """Verify extraction across h1, h2, and h3 heading hierarchies."""
        sample_html = """
        <html>
        <body>
            <h1><a href="https://example.com/h1-lead">Breaking: Major AI Benchmark Released</a></h1>
            <h2><a href="https://example.com/h2-sub">Cloud Computing Quarterly Revenue Gains</a></h2>
            <h3><a href="https://example.com/h3-topic">Open Source Community Milestone</a></h3>
        </body>
        </html>
        """
        results = extract_headlines(sample_html, default_source="Tech Daily")
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["Headline"], "Breaking: Major AI Benchmark Released")
        self.assertEqual(results[0]["URL"], "https://example.com/h1-lead")

        self.assertEqual(results[1]["Headline"], "Cloud Computing Quarterly Revenue Gains")
        self.assertEqual(results[1]["URL"], "https://example.com/h2-sub")

        self.assertEqual(results[2]["Headline"], "Open Source Community Milestone")
        self.assertEqual(results[2]["URL"], "https://example.com/h3-topic")

        for r in results:
            self.assertEqual(r["Source"], "Tech Daily")
            self.assertIn("Timestamp", r)
            self.assertTrue(len(r["Timestamp"]) > 0)

    def test_relative_urls_converted_to_absolute(self):
        """Verify that relative article URLs are converted to absolute URLs using base_url."""
        sample_html = """
        <html>
        <body>
            <h2><a href="/news/2026/quantum-update">Quantum Computing Leap</a></h2>
            <h3><a href="articles/deep-dive.html">In-Depth Architecture Review</a></h3>
            <h2><a href="https://other.com/already-absolute">External Article</a></h2>
        </body>
        </html>
        """
        base_url = "https://techinsider.org/portal/"
        results = extract_headlines(sample_html, base_url=base_url)

        self.assertEqual(len(results), 3)
        # Root-relative path resolved against domain root
        self.assertEqual(results[0]["URL"], "https://techinsider.org/news/2026/quantum-update")
        # Relative path resolved against current directory
        self.assertEqual(results[1]["URL"], "https://techinsider.org/portal/articles/deep-dive.html")
        # Already absolute URL preserved
        self.assertEqual(results[2]["URL"], "https://other.com/already-absolute")

    def test_missing_links_handled_gracefully(self):
        """Verify that headlines without anchor tags or with empty hrefs return empty string URL."""
        sample_html = """
        <html>
        <body>
            <h1>Announcement: Maintenance Window Scheduled</h1>
            <h2><a href="">Empty Link Article</a></h2>
            <h3><a href="#">Anchor Link Only</a></h3>
        </body>
        </html>
        """
        results = extract_headlines(sample_html)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["Headline"], "Announcement: Maintenance Window Scheduled")
        self.assertEqual(results[0]["URL"], "")

        self.assertEqual(results[1]["Headline"], "Empty Link Article")
        self.assertEqual(results[1]["URL"], "")

        self.assertEqual(results[2]["Headline"], "Anchor Link Only")
        self.assertEqual(results[2]["URL"], "")

    def test_missing_titles_and_empty_headings_discarded(self):
        """Verify that empty, whitespace-only, or tag-only headings are ignored."""
        sample_html = """
        <html>
        <body>
            <h1></h1>
            <h2>   \n\t  </h2>
            <h3><span></span></h3>
            <h2><a href="/story">Valid Technology Headline</a></h2>
        </body>
        </html>
        """
        results = extract_headlines(sample_html)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["Headline"], "Valid Technology Headline")

    def test_duplicate_headlines_removed(self):
        """Verify that duplicate headlines are de-duplicated preserving the first instance."""
        sample_html = """
        <div>
            <h2><a href="/link1">New Microprocessor Architecture</a></h2>
            <h2><a href="/link2">New Microprocessor Architecture</a></h2>
            <h3><a href="/link3">NEW MICROPROCESSOR ARCHITECTURE</a></h3>
            <h2><a href="/link4">Distinct Secondary Headline</a></h2>
        </div>
        """
        results = extract_headlines(sample_html)
        self.assertEqual(len(results), 2)
        titles = [r["Headline"] for r in results]
        self.assertEqual(titles, ["New Microprocessor Architecture", "Distinct Secondary Headline"])

    def test_malformed_html_handled_gracefully(self):
        """Verify that unclosed tags, broken quotes, and missing tags do not crash parsing."""
        malformed_html = """
        <div>
            <h2><a href=/broken-link>Unclosed Heading 1
            <h3><a href="https://example.com/ok">Heading Two</a>
            <p>Unclosed paragraph text
            <h2>Third Heading Without Close
        """
        results = extract_headlines(malformed_html)
        self.assertTrue(len(results) >= 2)
        titles = [r["Headline"] for r in results]
        self.assertTrue(any("Unclosed Heading 1" in t for t in titles))
        self.assertTrue(any("Heading Two" in t for t in titles))

    def test_empty_html_and_none(self):
        """Verify that empty strings, whitespace, None, and non-strings return empty lists."""
        self.assertEqual(extract_headlines(""), [])
        self.assertEqual(extract_headlines("   \n\t "), [])
        self.assertEqual(extract_headlines(None), [])
        self.assertEqual(extract_headlines(999), [])
        self.assertEqual(extract_headlines("<html><body><p>No headlines</p></body></html>"), [])

    def test_unicode_headline_text(self):
        """Verify that Unicode headline text, accents, symbols, and emojis are preserved intact."""
        sample_html = """
        <html>
        <body>
            <h2><a href="/unicode-1">Python 3.13 🚀: Neue Features & Événements</a></h2>
            <h3><a href="/unicode-2">AI-Driven Coding: 智能编程与自然语言处理</a></h3>
            <h1><a href="/unicode-3">¿Cómo funciona la computación cuántica? — Análisis</a></h1>
        </body>
        </html>
        """
        results = extract_headlines(sample_html)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["Headline"], "Python 3.13 🚀: Neue Features & Événements")
        self.assertEqual(results[1]["Headline"], "AI-Driven Coding: 智能编程与自然语言处理")
        self.assertEqual(results[2]["Headline"], "¿Cómo funciona la computación cuántica? — Análisis")

    def test_extraction_timestamp_format(self):
        """Verify that extraction timestamp is populated and adheres to YYYY-MM-DD HH:MM:SS format."""
        sample_html = "<h2><a href='/story'>Timestamp Verification Story</a></h2>"
        results = extract_headlines(sample_html)
        self.assertEqual(len(results), 1)

        timestamp_str = results[0]["Timestamp"]
        parsed_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        self.assertIsInstance(parsed_dt, datetime)

    def test_resolve_url_helper(self):
        """Test resolve_url directly across edge cases."""
        self.assertEqual(resolve_url("article.html", "https://example.com/news/"), "https://example.com/news/article.html")
        self.assertEqual(resolve_url("/root.html", "https://example.com/news/"), "https://example.com/root.html")
        self.assertEqual(resolve_url("https://external.com", "https://example.com"), "https://external.com")
        self.assertEqual(resolve_url("#comments", "https://example.com"), "")
        self.assertEqual(resolve_url("javascript:void(0)", "https://example.com"), "")
        self.assertEqual(resolve_url("", "https://example.com"), "")
        self.assertEqual(resolve_url(None, "https://example.com"), "")

    @patch("headlines_scraper.fetch_page")
    def test_scrape_headlines_success(self, mock_fetch):
        """Verify scrape_headlines integrates fetch_page and returns headlines list on success."""
        mock_html = """
        <html>
        <body>
            <h2><a href="/tech/ai">AI Revolutionizes Developer Productivity</a></h2>
            <h2><a href="/tech/security">New Zero-Trust Security Protocol</a></h2>
        </body>
        </html>
        """
        mock_fetch.return_value = FetchResult(mock_html, None, status_code=200)

        headlines, error = scrape_headlines("https://news.ycombinator.com", default_source="Hacker News")

        self.assertIsNone(error)
        self.assertEqual(len(headlines), 2)
        self.assertEqual(headlines[0]["Headline"], "AI Revolutionizes Developer Productivity")
        self.assertEqual(headlines[0]["URL"], "https://news.ycombinator.com/tech/ai")
        self.assertEqual(headlines[0]["Source"], "Hacker News")

    @patch("headlines_scraper.fetch_page")
    def test_scrape_headlines_failure_returns_error(self, mock_fetch):
        """Verify scrape_headlines returns empty list and error string on fetch failure."""
        mock_fetch.return_value = FetchResult(None, "HTTP Error 404: Not Found", status_code=404)

        headlines, error = scrape_headlines("https://example.com/nonexistent")

        self.assertEqual(headlines, [])
        self.assertIn("HTTP Error 404", error)

    def test_format_headline_output(self):
        """Verify format_headline returns a structured multi-line string."""
        item = {
            "Headline": "Python 3.13 Performance Breakthroughs",
            "Source": "Python Insider",
            "URL": "https://blog.python.org/2026/python-313",
            "Timestamp": "2026-11-18 15:00:00",
        }
        output = format_headline(item)
        self.assertIn("[Python Insider] Python 3.13 Performance Breakthroughs", output)
        self.assertIn("https://blog.python.org/2026/python-313", output)
        self.assertIn("2026-11-18 15:00:00", output)

    def test_real_tech_news_html_structure(self):
        """Test parsing realistic tech news HTML structure (Python Blog pattern)."""
        real_sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Python Insider</title></head>
        <body>
            <header><h1>Python Insider Blog</h1></header>
            <main>
                <h2>Latest Releases & Updates</h2>
                <div class="post">
                    <h3><a href="/2026/11/python-3-14-alpha.html">Python 3.14 Alpha 1 Released</a></h3>
                    <span class="source">PSF Blog</span>
                </div>
                <div class="post">
                    <h3><a href="/2026/11/security-update.html">Security Advisory: Pip Package Auditing</a></h3>
                    <span class="source">Security Team</span>
                </div>
            </main>
        </body>
        </html>
        """
        results = extract_headlines(real_sample_html, base_url="https://blog.python.org")
        self.assertTrue(len(results) >= 2)
        urls = [r["URL"] for r in results]
        self.assertIn("https://blog.python.org/2026/11/python-3-14-alpha.html", urls)
        self.assertIn("https://blog.python.org/2026/11/security-update.html", urls)


if __name__ == "__main__":
    unittest.main()
