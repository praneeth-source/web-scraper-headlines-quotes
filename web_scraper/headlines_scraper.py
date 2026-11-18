"""Headlines scraper module.

This module provides functions to parse, extract, normalize, and format news headlines,
source names, article URLs, and extraction timestamps from HTML documents using BeautifulSoup4.

Phase 3 Features:
- BeautifulSoup DOM parsing supporting h1, h2, and h3 heading hierarchies.
- Article URL extraction with automatic conversion of relative URLs to absolute URLs.
- De-duplication of headlines and filtering of empty titles.
- Graceful handling of missing links, malformed HTML, and non-ASCII Unicode characters.
- Integration with the HTTP fetching engine in scraper.py via scrape_headlines().
"""

from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from scraper import fetch_page, create_soup


def get_current_timestamp():
    """Return the current timestamp formatted as YYYY-MM-DD HH:MM:SS."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_url(href, base_url=""):
    """Convert a relative URL into an absolute URL using base_url.

    Args:
        href (str): The raw link href (may be relative, absolute, empty, or an anchor).
        base_url (str): The base webpage URL to resolve against.

    Returns:
        str: Absolute URL string, or empty string if link is missing or an internal anchor.
    """
    if not href or not isinstance(href, str):
        return ""

    cleaned = href.strip()
    # Ignore empty links, javascript placeholders, and pure anchor jumps
    if not cleaned or cleaned.startswith("javascript:") or cleaned.startswith("#"):
        return ""

    if base_url and isinstance(base_url, str) and base_url.strip():
        return urljoin(base_url.strip(), cleaned)

    return cleaned


def extract_headlines(soup_or_html, base_url="", default_source="Tech News"):
    """Extract news headlines, links, sources, and timestamps from HTML or BeautifulSoup.

    Supports:
    - Multiple heading structures: h1, h2, h3 tags (nested anchors or parent anchors).
    - Common article containers and news item classes.
    - Automatic conversion of relative URLs to absolute URLs using base_url.
    - Removal of empty titles and de-duplication.
    - Full support for Unicode characters, accents, and emojis.
    - Graceful degradation on missing links or malformed HTML.

    Args:
        soup_or_html (BeautifulSoup or str): HTML content string or parsed BeautifulSoup tree.
        base_url (str, optional): Base URL of the page used to resolve relative links.
        default_source (str, optional): Default source name to assign.

    Returns:
        list: List of dictionaries, each containing:
            - 'Headline' (str): Title of the headline.
            - 'URL' (str): Absolute article URL (or empty string if missing).
            - 'Source' (str): Source publication or website name.
            - 'Timestamp' (str): Extraction timestamp (YYYY-MM-DD HH:MM:SS).
    """
    if soup_or_html is None:
        return []

    # 1. Parse HTML into BeautifulSoup if a string was passed
    if isinstance(soup_or_html, str):
        if not soup_or_html.strip():
            return []
        try:
            soup = create_soup(soup_or_html)
        except (ValueError, TypeError):
            return []
    elif isinstance(soup_or_html, BeautifulSoup):
        soup = soup_or_html
    else:
        return []

    headlines = []
    seen_titles = set()

    # 2. Extract from standard heading tags (h1, h2, h3)
    heading_elements = soup.find_all(["h1", "h2", "h3"])

    for heading in heading_elements:
        # Extract title text cleanly, normalizing internal whitespace
        raw_title = heading.get_text(separator=" ", strip=True)
        title = " ".join(raw_title.split())

        # Requirement 6: Discard empty headlines
        if not title:
            continue

        # Requirement 6: Remove duplicate headlines
        norm_key = title.lower()
        if norm_key in seen_titles:
            continue

        # Requirement 5 & 8: Extract associated article link
        link_tag = heading.find("a", href=True)

        # Check if heading itself is wrapped inside an <a> tag
        if not link_tag and heading.parent and heading.parent.name == "a":
            if heading.parent.get("href"):
                link_tag = heading.parent

        # Check if heading is inside an article container with a link
        if not link_tag:
            container = heading.find_parent(["article", "div"])
            if container:
                # Find an anchor whose text matches or is adjacent
                candidate = container.find("a", href=True)
                if candidate:
                    cand_href = candidate.get("href", "").strip()
                    if cand_href and not cand_href.startswith("#"):
                        link_tag = candidate

        raw_href = link_tag.get("href", "").strip() if link_tag else ""

        # Requirement 7: Convert relative URL to absolute URL
        article_url = resolve_url(raw_href, base_url=base_url)

        # Detect publication source if available in metadata container
        source = default_source
        container = heading.find_parent(["article", "div"])
        if container:
            source_tag = container.find(class_=lambda c: c and "source" in c.lower().split())
            if source_tag:
                source_text = source_tag.get_text(strip=True)
                if source_text:
                    source = source_text

        seen_titles.add(norm_key)
        item = {
            "Headline": title,
            "URL": article_url,
            "Source": source,
            "Timestamp": get_current_timestamp(),
            # Lowercase aliases for convenience
            "title": title,
            "url": article_url,
            "source": source,
            "timestamp": get_current_timestamp(),
        }
        headlines.append(item)

    # 3. Fallback: If no h1/h2/h3 tags existed, search common news container classes
    if not headlines:
        container_links = soup.select(".titleline > a, .storylink, article a")
        for link in container_links:
            raw_title = link.get_text(strip=True)
            title = " ".join(raw_title.split())
            if not title:
                continue

            norm_key = title.lower()
            if norm_key in seen_titles:
                continue

            raw_href = link.get("href", "").strip()
            article_url = resolve_url(raw_href, base_url=base_url)

            seen_titles.add(norm_key)
            item = {
                "Headline": title,
                "URL": article_url,
                "Source": default_source,
                "Timestamp": get_current_timestamp(),
                "title": title,
                "url": article_url,
                "source": default_source,
                "timestamp": get_current_timestamp(),
            }
            headlines.append(item)

    return headlines


def scrape_headlines(url, default_source=None, timeout=10):
    """Fetch webpage HTML using scraper.fetch_page() and extract all headlines.

    Args:
        url (str): Target webpage URL.
        default_source (str, optional): Default source name. If None, derived from domain.
        timeout (int or float, optional): Request timeout in seconds. Defaults to 10.

    Returns:
        tuple: (headlines_list, error_message)
            - On success: (list_of_headline_dicts, None)
            - On failure: ([], error_string)
    """
    html, error = fetch_page(url, timeout=timeout)
    if error:
        return [], error

    source = default_source
    if not source:
        parsed = urlparse(url)
        source = parsed.netloc or "News"

    headlines = extract_headlines(html, base_url=url, default_source=source)
    return headlines, None


def format_headline(headline_data):
    """Format a headline dictionary for clean terminal display.

    Args:
        headline_data (dict): Dictionary with 'Headline', 'Source', 'URL', 'Timestamp'.

    Returns:
        str: Formatted string representation.
    """
    title = headline_data.get("Headline") or headline_data.get("title", "Untitled")
    source = headline_data.get("Source") or headline_data.get("source", "Unknown")
    url = headline_data.get("URL") or headline_data.get("url", "N/A")
    timestamp = headline_data.get("Timestamp") or headline_data.get("timestamp", "N/A")

    link_display = url if url else "No link available"
    return f"[{source}] {title}\n  Link      : {link_display}\n  Extracted : {timestamp}"
