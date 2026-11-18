"""Unit tests for scraper.py (Core Scraper & HTTP Request Module)."""

import os
import sys
import unittest
from unittest.mock import patch, Mock
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException
from bs4 import BeautifulSoup

# Ensure web_scraper directory is on python path for imports
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from scraper import (
    create_soup,
    is_valid_url,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    FetchResult,
    fetch_page,
)


class TestScraperPhase1(unittest.TestCase):
    """Test suite for Phase 1 utility functions (headers, soup, URL validation)."""

    def test_default_headers_contain_user_agent(self):
        """Verify that DEFAULT_HEADERS defines a valid User-Agent string."""
        self.assertIn("User-Agent", DEFAULT_HEADERS)
        self.assertTrue(len(DEFAULT_HEADERS["User-Agent"]) > 10)
        self.assertIn("Web Scraper", DEFAULT_HEADERS["User-Agent"])

    def test_create_soup_valid_html(self):
        """Verify that create_soup creates a navigable BeautifulSoup object."""
        html = "<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
        soup = create_soup(html)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertEqual(soup.title.string, "Test Page")
        self.assertEqual(soup.find("h1").get_text(), "Hello World")

    def test_create_soup_empty_string_raises_value_error(self):
        """Verify that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            create_soup("")

    def test_create_soup_whitespace_raises_value_error(self):
        """Verify that whitespace-only string raises ValueError."""
        with self.assertRaises(ValueError):
            create_soup("   \n\t  ")

    def test_create_soup_none_raises_value_error(self):
        """Verify that None raises ValueError."""
        with self.assertRaises(ValueError):
            create_soup(None)

    def test_create_soup_invalid_type_raises_value_error(self):
        """Verify that non-string types raise ValueError."""
        with self.assertRaises(ValueError):
            create_soup(12345)

    def test_is_valid_url_http_and_https(self):
        """Verify valid HTTP and HTTPS URLs."""
        self.assertTrue(is_valid_url("https://quotes.toscrape.com"))
        self.assertTrue(is_valid_url("http://example.com/news"))
        self.assertTrue(is_valid_url("https://news.ycombinator.com/item?id=123"))

    def test_is_valid_url_invalid_urls(self):
        """Verify that invalid URLs are rejected."""
        self.assertFalse(is_valid_url("not_a_url"))
        self.assertFalse(is_valid_url("ftp://example.com"))
        self.assertFalse(is_valid_url("file:///C:/path/file.txt"))
        self.assertFalse(is_valid_url(""))
        self.assertFalse(is_valid_url("   "))
        self.assertFalse(is_valid_url(None))


class TestScraperPhase2HttpRequests(unittest.TestCase):
    """Test suite for Phase 2 HTTP request functionality using mocks and live checks."""

    @patch("requests.get")
    def test_fetch_page_successful_http_response(self, mock_get):
        """Verify successful HTTP 200 response returns HTML content and None for error."""
        sample_html = "<html><body><h1>Live Quotes</h1></body></html>"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_page("https://quotes.toscrape.com")

        self.assertTrue(result.success)
        self.assertEqual(result.html, sample_html)
        self.assertIsNone(result.error)
        self.assertEqual(result.status_code, 200)

        # Verify requests.get was invoked with correct arguments
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://quotes.toscrape.com")
        self.assertEqual(kwargs["timeout"], DEFAULT_TIMEOUT)
        self.assertIn("User-Agent", kwargs["headers"])

    @patch("requests.get")
    def test_fetch_page_tuple_unpacking(self, mock_get):
        """Verify FetchResult can be unpacked cleanly as a 2-tuple (html, error)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<p>Unpack test</p>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        html, error = fetch_page("https://example.com")
        self.assertEqual(html, "<p>Unpack test</p>")
        self.assertIsNone(error)

    @patch("requests.get")
    def test_fetch_page_http_404_response(self, mock_get):
        """Verify HTTP 404 response is handled gracefully with clear error info."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(
            "404 Client Error: Not Found", response=mock_response
        )
        mock_get.return_value = mock_response

        result = fetch_page("https://quotes.toscrape.com/missing-page")

        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertEqual(result.status_code, 404)
        self.assertIn("HTTP Error 404", result.error)
        self.assertIn("quotes.toscrape.com/missing-page", result.error)

    @patch("requests.get")
    def test_fetch_page_http_500_response(self, mock_get):
        """Verify HTTP 500 response is handled gracefully with clear error info."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError(
            "500 Server Error: Internal Server Error", response=mock_response
        )
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com/server-error")

        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertEqual(result.status_code, 500)
        self.assertIn("HTTP Error 500", result.error)

    @patch("requests.get")
    def test_fetch_page_connection_failure(self, mock_get):
        """Verify network connection failures are caught and return clear error info."""
        mock_get.side_effect = ConnectionError("Failed to establish a new connection")

        result = fetch_page("https://nonexistent-domain-12345.xyz")

        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertIsNone(result.status_code)
        self.assertIn("Connection Error", result.error)
        self.assertIn("nonexistent-domain-12345.xyz", result.error)

    @patch("requests.get")
    def test_fetch_page_request_timeout(self, mock_get):
        """Verify request timeout exceptions are caught and return clear timeout error."""
        mock_get.side_effect = Timeout("Request timed out")

        result = fetch_page("https://slow-server.org", timeout=3)

        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertIsNone(result.status_code)
        self.assertIn("Timeout Error", result.error)
        self.assertIn("3", result.error)

    @patch("requests.get")
    def test_fetch_page_empty_response(self, mock_get):
        """Verify empty response body returns clear empty response error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "   \n\t  "
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com/empty-page")

        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertEqual(result.status_code, 200)
        self.assertIn("Empty Response", result.error)

    @patch("requests.get")
    def test_fetch_page_invalid_url_avoids_network_call(self, mock_get):
        """Verify invalid URLs return error immediately without calling requests.get."""
        invalid_urls = ["not_a_url", "ftp://example.com", "", "   ", None]
        for url in invalid_urls:
            result = fetch_page(url)
            self.assertFalse(result.success)
            self.assertIsNone(result.html)
            self.assertIn("Invalid URL", result.error)

        mock_get.assert_not_called()

    @patch("requests.get")
    def test_fetch_page_custom_headers_merge(self, mock_get):
        """Verify custom headers merge with DEFAULT_HEADERS."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<p>OK</p>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_page("https://example.com", headers={"X-Custom-Token": "secret123"})

        args, kwargs = mock_get.call_args
        sent_headers = kwargs["headers"]
        self.assertIn("User-Agent", sent_headers)
        self.assertEqual(sent_headers.get("X-Custom-Token"), "secret123")

    @patch("requests.get")
    def test_fetch_page_generic_request_exception(self, mock_get):
        """Verify general RequestException subclasses are caught gracefully."""
        mock_get.side_effect = RequestException("Unknown protocol error")

        result = fetch_page("https://example.com")
        self.assertFalse(result.success)
        self.assertIsNone(result.html)
        self.assertIn("Request Error", result.error)

    def test_fetch_page_live_public_website(self):
        """Verify live connection against public scraping test website (quotes.toscrape.com)."""
        try:
            result = fetch_page("http://quotes.toscrape.com", timeout=5)
            # If online, verify 200 OK and HTML content received
            if result.success:
                self.assertEqual(result.status_code, 200)
                self.assertIsNotNone(result.html)
                self.assertIn("Quotes to Scrape", result.html)
            else:
                # If network is restricted in testing environment, verify error is informative
                self.assertIsNotNone(result.error)
        except Exception as exc:
            self.fail(f"fetch_page raised unexpected unhandled exception on live test: {exc}")


if __name__ == "__main__":
    unittest.main()
