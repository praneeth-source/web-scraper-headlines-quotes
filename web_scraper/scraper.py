"""Core scraper module for web scraping operations.

This module provides foundation utilities for HTTP networking using the requests
library, HTML parsing using BeautifulSoup4, request configuration, and URL validation.

Library Roles:
- requests: Used to perform HTTP GET requests, send custom headers (like
  User-Agent), handle timeouts and redirects, validate response status codes,
  and safely download webpage HTML content.
- BeautifulSoup (bs4): Used to parse raw HTML strings into a navigable DOM tree.
"""

from urllib.parse import urlparse
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException
from bs4 import BeautifulSoup

# Standard HTTP headers sent with all outbound requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (Web Scraper Educational Project)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Default network request timeout in seconds
DEFAULT_TIMEOUT = 10


class FetchResult(tuple):
    """Result container for an HTTP fetch operation.

    Subclasses tuple (html, error) for beginner-friendly usage:
    1. Direct tuple unpacking:
       html, error = fetch_page(url)

    2. Property-based inspection:
       result = fetch_page(url)
       if result.success:
           print("Fetched:", len(result.html), "characters")
       else:
           print("Error:", result.error)
    """

    def __new__(cls, html, error, status_code=None):
        return super().__new__(cls, (html, error))

    def __init__(self, html, error, status_code=None):
        self.html = html
        self.error = error
        self.status_code = status_code

    @property
    def success(self):
        """Return True if the request succeeded with non-empty HTML."""
        return self.error is None and self.html is not None

    def __bool__(self):
        return self.success

    def __repr__(self):
        if self.success:
            return f"<FetchResult success=True status_code={self.status_code} bytes={len(self.html)}>"
        return f"<FetchResult success=False status_code={self.status_code} error='{self.error}'>"


def is_valid_url(url):
    """Validate whether the given string is a syntactically valid HTTP/HTTPS URL.

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if URL is valid and uses http or https, False otherwise.
    """
    if not isinstance(url, str) or not url.strip():
        return False

    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def create_soup(html_content, parser="html.parser"):
    """Parse raw HTML content into a BeautifulSoup document tree.

    Args:
        html_content (str): The raw HTML string.
        parser (str): The parser to use (default: 'html.parser').

    Returns:
        BeautifulSoup: Parsed BeautifulSoup object.

    Raises:
        ValueError: If html_content is empty or not a string.
    """
    if html_content is None or not isinstance(html_content, str):
        raise ValueError("HTML content must be a non-empty string.")

    if not html_content.strip():
        raise ValueError("HTML content cannot be empty.")

    return BeautifulSoup(html_content, parser)


def fetch_page(url, headers=None, timeout=DEFAULT_TIMEOUT):
    """Fetch webpage HTML content using an HTTP GET request.

    Features:
    - Custom User-Agent and headers configuration.
    - Configurable network timeout.
    - Response HTTP status validation (e.g. 404, 500 error detection).
    - Empty response detection.
    - Comprehensive exception handling for ConnectionError, Timeout,
      HTTPError, and general RequestException.

    Args:
        url (str): Target webpage URL (must use http:// or https://).
        headers (dict, optional): Custom HTTP headers. Merged with DEFAULT_HEADERS.
        timeout (int or float, optional): Request timeout in seconds. Defaults to 10.

    Returns:
        FetchResult: A 2-tuple (html, error) with attributes:
            - html (str or None): Raw HTML string on success, None on error.
            - error (str or None): Error message string on error, None on success.
            - status_code (int or None): HTTP status code.
            - success (bool): True if fetch succeeded.
    """
    # 1. URL syntax validation
    if not is_valid_url(url):
        error_msg = (
            f"Invalid URL: '{url}'. Target URL must be a non-empty string "
            "starting with 'http://' or 'https://'."
        )
        return FetchResult(None, error_msg, status_code=None)

    # 2. Merge request headers with defaults
    request_headers = DEFAULT_HEADERS.copy()
    if headers and isinstance(headers, dict):
        request_headers.update(headers)

    # 3. Execute HTTP GET request with exception handling
    try:
        response = requests.get(
            url.strip(),
            headers=request_headers,
            timeout=timeout,
        )

        # Validate HTTP status code (raises HTTPError for 4xx/5xx)
        response.raise_for_status()

        # Validate response content
        html_content = response.text
        if not html_content or not html_content.strip():
            error_msg = (
                f"Empty Response: Server returned status {response.status_code} "
                f"with an empty response body for URL: {url}"
            )
            return FetchResult(None, error_msg, status_code=response.status_code)

        # Success: return HTML content
        return FetchResult(html_content, None, status_code=response.status_code)

    except HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        error_msg = f"HTTP Error {status}: Server responded with status {status} for URL: {url}"
        return FetchResult(None, error_msg, status_code=status)

    except ConnectionError:
        error_msg = (
            f"Connection Error: Unable to connect to '{url}'. "
            "Please check your internet connection or verify the domain name."
        )
        return FetchResult(None, error_msg, status_code=None)

    except Timeout:
        error_msg = (
            f"Timeout Error: Request timed out after {timeout} seconds for URL: {url}."
        )
        return FetchResult(None, error_msg, status_code=None)

    except RequestException as exc:
        status = getattr(exc.response, "status_code", None) if getattr(exc, "response", None) is not None else None
        error_msg = f"Request Error: An unexpected network error occurred while requesting {url}: {exc}"
        return FetchResult(None, error_msg, status_code=status)
