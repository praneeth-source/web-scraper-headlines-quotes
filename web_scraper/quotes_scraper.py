"""Quotes scraper module.

This module provides functions to parse, extract, normalize, and format inspirational
quotes, author names, and category tags from HTML documents using BeautifulSoup4.

Phase 4 Features:
- Quote extraction from standard quote containers (.quote, .text, .author, .tag) and standard blockquotes.
- Author extraction with graceful default to "Unknown" if missing.
- Tag/category extraction with default to empty list [] if missing.
- Duplicate quote removal.
- Preservation of Unicode characters, accents, and emojis.
- Graceful handling of malformed, unclosed, or empty HTML.
- Integration with scraper.fetch_page() via scrape_quotes().
"""

from bs4 import BeautifulSoup
from scraper import fetch_page, create_soup


def extract_quotes(soup_or_html):
    """Extract quotes, author names, and category tags from HTML or BeautifulSoup.

    Supports:
    - Standard quote containers (class="quote" with .text, .author, and .tag).
    - Standard HTML <blockquote> and <cite> elements.
    - Automatic de-duplication of identical quotes.
    - Graceful fallbacks for missing authors ("Unknown") and missing tags ([]).
    - Full preservation of Unicode characters, foreign accents, and emojis.
    - Resilient handling of malformed or empty HTML.

    Args:
        soup_or_html (BeautifulSoup or str): HTML content string or parsed BeautifulSoup tree.

    Returns:
        list: List of dictionaries, each containing:
            - 'text' (str): The quote text.
            - 'author' (str): The author name (defaults to "Unknown").
            - 'tags' (list): List of tag/category strings (defaults to []).
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

    quotes = []
    seen_texts = set()

    # 2. Look for standard quote containers (.quote)
    quote_elements = soup.find_all(class_=lambda c: c and "quote" in c.lower().split())

    if quote_elements:
        for element in quote_elements:
            # Extract quote text
            text_tag = element.find(class_=lambda c: c and "text" in c.lower().split())
            if not text_tag:
                text_tag = element.find(["p", "span", "q"])

            raw_text = text_tag.get_text(strip=True) if text_tag else element.get_text(strip=True)

            # Strip leading/trailing decorative quotation marks while preserving internal content
            clean_text = raw_text.strip('“”"\' \t\n\r')

            # Normalize internal whitespace
            clean_text = " ".join(clean_text.split())

            # Skip empty quotes
            if not clean_text:
                continue

            # Requirement 4: Remove duplicate quotes
            norm_key = clean_text.lower()
            if norm_key in seen_texts:
                continue

            # Requirement 2 & 5: Extract author name (default to "Unknown" if missing)
            author_tag = element.find(class_=lambda c: c and "author" in c.lower().split())
            if not author_tag:
                author_tag = element.find(["small", "cite"])

            author = author_tag.get_text(strip=True) if author_tag else ""
            author = " ".join(author.split()) if author else "Unknown"

            # Requirement 3 & 5: Extract tags/categories (default to [] if missing)
            tag_elements = element.find_all(class_=lambda c: c and "tag" in c.lower().split())
            tags = []
            for tag in tag_elements:
                tag_text = tag.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

            seen_texts.add(norm_key)
            quotes.append({
                "text": clean_text,
                "author": author,
                "tags": tags,
            })

    # 3. Fallback: Search for <blockquote> elements if no .quote classes matched
    if not quotes:
        for bq in soup.find_all("blockquote"):
            raw_text = bq.get_text(strip=True).strip('“”"\' \t\n\r')
            clean_text = " ".join(raw_text.split())

            if not clean_text:
                continue

            norm_key = clean_text.lower()
            if norm_key in seen_texts:
                continue

            # Check inside blockquote for <cite> or adjacent sibling
            cite_tag = bq.find("cite") or bq.find_next_sibling(["cite", "p", "small"])
            author = cite_tag.get_text(strip=True) if cite_tag else ""
            author = " ".join(author.split()) if author else "Unknown"

            seen_texts.add(norm_key)
            quotes.append({
                "text": clean_text,
                "author": author,
                "tags": [],
            })

    return quotes


def scrape_quotes(url, timeout=10):
    """Fetch webpage HTML using scraper.fetch_page() and extract all quotes.

    Args:
        url (str): Target webpage URL (e.g. 'http://quotes.toscrape.com').
        timeout (int or float, optional): Network timeout in seconds. Defaults to 10.

    Returns:
        tuple: (quotes_list, error_message)
            - On success: (list_of_quote_dicts, None)
            - On failure: ([], error_string)
    """
    html, error = fetch_page(url, timeout=timeout)
    if error:
        return [], error

    quotes = extract_quotes(html)
    return quotes, None


def format_quote(quote_data):
    """Format a quote dictionary for clean display and text file storage.

    Args:
        quote_data (dict): Dictionary with 'text', 'author', 'tags'.

    Returns:
        str: Formatted string: '"<text>" - <author> (Tags: <tags>)' or '"<text>" - <author>'
    """
    text = quote_data.get("text", "").strip()
    author = quote_data.get("author", "Unknown").strip() or "Unknown"
    tags = quote_data.get("tags", [])

    tag_str = f" (Tags: {', '.join(tags)})" if tags else ""
    return f'"{text}" - {author}{tag_str}'
