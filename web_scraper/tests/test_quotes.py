"""Unit tests for quotes_scraper.py (Quotes Scraper using BeautifulSoup4)."""

import os
import sys
import unittest
from unittest.mock import patch

# Ensure web_scraper directory is on python path for imports
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from quotes_scraper import extract_quotes, scrape_quotes, format_quote
from scraper import FetchResult, create_soup


class TestQuotesScraperPhase4(unittest.TestCase):
    """Test suite for Phase 4 quotes scraper module."""

    def test_extract_multiple_quotes(self):
        """Verify extraction of multiple quotes with text, author, and tags."""
        sample_html = """
        <html>
        <body>
            <div class="quote">
                <span class="text">“The journey of a thousand miles begins with one step.”</span>
                <small class="author">Lao Tzu</small>
                <div class="tags">
                    <a class="tag">inspiration</a>
                    <a class="tag">philosophy</a>
                </div>
            </div>
            <div class="quote">
                <span class="text">“Stay hungry, stay foolish.”</span>
                <small class="author">Steve Jobs</small>
                <div class="tags">
                    <a class="tag">life</a>
                </div>
            </div>
        </body>
        </html>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 2)

        self.assertEqual(quotes[0]["text"], "The journey of a thousand miles begins with one step.")
        self.assertEqual(quotes[0]["author"], "Lao Tzu")
        self.assertEqual(quotes[0]["tags"], ["inspiration", "philosophy"])

        self.assertEqual(quotes[1]["text"], "Stay hungry, stay foolish.")
        self.assertEqual(quotes[1]["author"], "Steve Jobs")
        self.assertEqual(quotes[1]["tags"], ["life"])

    def test_extract_quotes_missing_author(self):
        """Verify that quotes without author elements default gracefully to 'Unknown'."""
        sample_html = """
        <div class="quote">
            <span class="text">“An anonymous word of wisdom.”</span>
            <div class="tags"><a class="tag">wisdom</a></div>
        </div>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["text"], "An anonymous word of wisdom.")
        self.assertEqual(quotes[0]["author"], "Unknown")
        self.assertEqual(quotes[0]["tags"], ["wisdom"])

    def test_extract_quotes_missing_tags(self):
        """Verify that quotes with no tags return an empty list [] for tags."""
        sample_html = """
        <div class="quote">
            <span class="text">“Simplicity is prerequisite for reliability.”</span>
            <small class="author">Edsger W. Dijkstra</small>
        </div>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["text"], "Simplicity is prerequisite for reliability.")
        self.assertEqual(quotes[0]["author"], "Edsger W. Dijkstra")
        self.assertEqual(quotes[0]["tags"], [])

    def test_extract_quotes_duplicate_quotes_removed(self):
        """Verify that duplicate quote entries are de-duplicated."""
        sample_html = """
        <div>
            <div class="quote">
                <span class="text">“First, solve the problem. Then, write the code.”</span>
                <small class="author">John Johnson</small>
            </div>
            <div class="quote">
                <span class="text">“First, solve the problem. Then, write the code.”</span>
                <small class="author">John Johnson</small>
            </div>
            <div class="quote">
                <span class="text">“Experience is the name everyone gives to their mistakes.”</span>
                <small class="author">Oscar Wilde</small>
            </div>
        </div>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 2)
        texts = [q["text"] for q in quotes]
        self.assertEqual(
            texts,
            [
                "First, solve the problem. Then, write the code.",
                "Experience is the name everyone gives to their mistakes.",
            ],
        )

    def test_extract_quotes_empty_html_and_none(self):
        """Verify that empty string, whitespace, None, and non-string inputs return empty list."""
        self.assertEqual(extract_quotes(""), [])
        self.assertEqual(extract_quotes("   \n\t "), [])
        self.assertEqual(extract_quotes(None), [])
        self.assertEqual(extract_quotes(456), [])
        self.assertEqual(extract_quotes("<html><body><p>No quotes here</p></body></html>"), [])

    def test_extract_quotes_malformed_html(self):
        """Verify that malformed and unclosed tags do not crash quote extraction."""
        malformed_html = """
        <div class="quote">
            <span class="text">“Unclosed quote block
            <small class="author">Unclosed Author
            <div class="tags">
                <a class="tag">tag1</a>
                <a class="tag">tag2</a>
            </div>
        """
        quotes = extract_quotes(malformed_html)
        self.assertEqual(len(quotes), 1)
        self.assertIn("Unclosed quote block", quotes[0]["text"])
        self.assertIn("Unclosed Author", quotes[0]["author"])
        self.assertIn("tag1", quotes[0]["tags"])
        self.assertIn("tag2", quotes[0]["tags"])

    def test_extract_quotes_unicode_characters(self):
        """Verify that Unicode quotes, accents, emojis, and non-Latin text are preserved."""
        sample_html = """
        <div class="quote">
            <span class="text">“Le cœur a ses raisons que la raison ne connaît point. 💡”</span>
            <small class="author">Blaise Pascal</small>
            <div class="tags">
                <a class="tag">philosophie</a>
                <a class="tag">cœur</a>
            </div>
        </div>
        <div class="quote">
            <span class="text">“千里之行，始于足下。”</span>
            <small class="author">老子 (Laozi)</small>
            <div class="tags">
                <a class="tag">古籍</a>
            </div>
        </div>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 2)

        self.assertEqual(quotes[0]["text"], "Le cœur a ses raisons que la raison ne connaît point. 💡")
        self.assertEqual(quotes[0]["author"], "Blaise Pascal")
        self.assertEqual(quotes[0]["tags"], ["philosophie", "cœur"])

        self.assertEqual(quotes[1]["text"], "千里之行，始于足下。")
        self.assertEqual(quotes[1]["author"], "老子 (Laozi)")
        self.assertEqual(quotes[1]["tags"], ["古籍"])

    def test_extract_quotes_blockquote_fallback(self):
        """Verify fallback extraction from standard blockquote and cite tags."""
        sample_html = """
        <html>
        <body>
            <blockquote>Do what you can, with what you have, where you are.</blockquote>
            <cite>Theodore Roosevelt</cite>
        </body>
        </html>
        """
        quotes = extract_quotes(sample_html)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["text"], "Do what you can, with what you have, where you are.")
        self.assertEqual(quotes[0]["author"], "Theodore Roosevelt")
        self.assertEqual(quotes[0]["tags"], [])

    def test_extract_quotes_accepts_beautifulsoup_object(self):
        """Verify that extract_quotes directly accepts a pre-parsed BeautifulSoup instance."""
        html = '<div class="quote"><p class="text">Knowledge is power.</p><span class="author">Francis Bacon</span></div>'
        soup = create_soup(html)
        quotes = extract_quotes(soup)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["text"], "Knowledge is power.")
        self.assertEqual(quotes[0]["author"], "Francis Bacon")

    @patch("quotes_scraper.fetch_page")
    def test_scrape_quotes_success_mock(self, mock_fetch):
        """Verify scrape_quotes reuses fetch_page and returns parsed quotes."""
        mock_html = """
        <div class="quote">
            <span class="text">“Code never lies, comments sometimes do.”</span>
            <small class="author">Ron Jeffries</small>
            <div class="tags"><a class="tag">programming</a></div>
        </div>
        """
        mock_fetch.return_value = FetchResult(mock_html, None, status_code=200)

        quotes, error = scrape_quotes("http://quotes.toscrape.com")

        self.assertIsNone(error)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0]["text"], "Code never lies, comments sometimes do.")
        self.assertEqual(quotes[0]["author"], "Ron Jeffries")
        self.assertEqual(quotes[0]["tags"], ["programming"])

    @patch("quotes_scraper.fetch_page")
    def test_scrape_quotes_http_failure_mock(self, mock_fetch):
        """Verify scrape_quotes handles HTTP 404/500 errors gracefully."""
        mock_fetch.return_value = FetchResult(None, "HTTP Error 404: Not Found", status_code=404)

        quotes, error = scrape_quotes("http://quotes.toscrape.com/invalid-page")

        self.assertEqual(quotes, [])
        self.assertIn("HTTP Error 404", error)

    @patch("quotes_scraper.fetch_page")
    def test_scrape_quotes_connection_failure_mock(self, mock_fetch):
        """Verify scrape_quotes handles connection failures gracefully."""
        mock_fetch.return_value = FetchResult(None, "Connection Error: Failed to connect", status_code=None)

        quotes, error = scrape_quotes("http://nonexistent-server-xyz.com")

        self.assertEqual(quotes, [])
        self.assertIn("Connection Error", error)

    def test_format_quote_with_tags(self):
        """Test format_quote with author and multiple tags."""
        item = {
            "text": "Code never lies, comments sometimes do.",
            "author": "Ron Jeffries",
            "tags": ["coding", "clean-code"],
        }
        result = format_quote(item)
        self.assertEqual(
            result,
            '"Code never lies, comments sometimes do." - Ron Jeffries (Tags: coding, clean-code)',
        )

    def test_format_quote_without_tags(self):
        """Test format_quote with no tags."""
        item = {
            "text": "Talk is cheap. Show me the code.",
            "author": "Linus Torvalds",
            "tags": [],
        }
        result = format_quote(item)
        self.assertEqual(result, '"Talk is cheap. Show me the code." - Linus Torvalds')

    def test_format_quote_missing_author_defaults_unknown(self):
        """Test format_quote defaults missing author to Unknown."""
        item = {
            "text": "A wise anonymous thought.",
            "author": "",
            "tags": ["wisdom"],
        }
        result = format_quote(item)
        self.assertEqual(result, '"A wise anonymous thought." - Unknown (Tags: wisdom)')


if __name__ == "__main__":
    unittest.main()
