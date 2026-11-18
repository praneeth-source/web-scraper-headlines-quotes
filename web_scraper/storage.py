"""Storage operations for headlines and quotes.

This module handles persistent reading, writing, and de-duplication of data to:
1. data/headlines.csv - Persistent CSV storage for news headlines with timestamps.
2. data/quotes.txt    - Persistent text file storage for inspirational quotes.

Phase 5 Features:
- Reliable CSV storage with Timestamp headers.
- Plain text storage with Unicode support.
- Preservation of previous records on append.
- Cross-run de-duplication of headlines and quotes.
- Graceful handling of missing files, empty files, and PermissionError / OSError.
"""

import csv
import os
from datetime import datetime

DEFAULT_HEADLINES_FILE = os.path.join(os.path.dirname(__file__), "data", "headlines.csv")
DEFAULT_QUOTES_FILE = os.path.join(os.path.dirname(__file__), "data", "quotes.txt")

HEADLINE_HEADERS = ["Headline", "Source", "URL", "Timestamp"]


def get_current_timestamp():
    """Return formatted timestamp string (YYYY-MM-DD HH:MM:SS)."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_directory_exists(filepath):
    """Ensure that the parent directory for the given filepath exists.

    Args:
        filepath (str): Path to target file.
    """
    try:
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    except (PermissionError, OSError):
        pass


def normalize_quote_text(text):
    """Normalize quote text for reliable de-duplication."""
    if not text or not isinstance(text, str):
        return ""
    cleaned = text.strip('“”"\' \t\n\r').lower()
    return " ".join(cleaned.split())


def save_headlines_to_csv(headlines, filepath=DEFAULT_HEADLINES_FILE):
    """Save a list of headline dictionaries to a CSV file.

    Features:
    - Automatically creates file and directory if they do not exist.
    - Appends new records without deleting or overwriting previous records.
    - Prevents duplicate headlines and URLs across successive runs.
    - Automatically adds timestamps if missing.
    - Handles Unicode (UTF-8) and permission/IO errors gracefully.

    Args:
        headlines (list): List of dicts, each with keys 'Headline', 'Source', 'URL', 'Timestamp'.
        filepath (str): Path to destination CSV file.

    Returns:
        int: Number of new unique headlines successfully written.
    """
    if not headlines:
        return 0

    ensure_directory_exists(filepath)

    # 1. Read existing records to prevent duplicate entries
    existing_headlines = read_headlines_from_csv(filepath)
    seen_titles = {
        h.get("Headline", "").strip().lower()
        for h in existing_headlines
        if h.get("Headline")
    }
    seen_urls = {
        h.get("URL", "").strip().lower()
        for h in existing_headlines
        if h.get("URL")
    }

    # 2. Filter new unique records
    new_rows = []
    for item in headlines:
        if not isinstance(item, dict):
            continue

        title = (item.get("Headline") or item.get("headline") or "").strip()
        source = (item.get("Source") or item.get("source") or "").strip()
        url = (item.get("URL") or item.get("url") or "").strip()
        timestamp = (
            item.get("Timestamp")
            or item.get("timestamp")
            or get_current_timestamp()
        ).strip()

        if not title:
            continue

        norm_title = title.lower()
        norm_url = url.lower() if url else None

        # Duplicate check: skip if title or URL already exists
        if norm_title in seen_titles:
            continue
        if norm_url and norm_url in seen_urls:
            continue

        seen_titles.add(norm_title)
        if norm_url:
            seen_urls.add(norm_url)

        new_rows.append({
            "Headline": title,
            "Source": source,
            "URL": url,
            "Timestamp": timestamp,
        })

    if not new_rows:
        return 0

    # 3. Write rows to CSV file with exception handling
    try:
        file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
        with open(filepath, mode="a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADLINE_HEADERS, extrasaction="ignore")

            # Write header only if file is newly created or empty
            if not file_exists:
                writer.writeheader()

            for row in new_rows:
                writer.writerow(row)

        return len(new_rows)
    except (PermissionError, OSError, csv.Error):
        return 0


def read_headlines_from_csv(filepath=DEFAULT_HEADLINES_FILE):
    """Read saved headlines from a CSV file.

    Args:
        filepath (str): Path to CSV file.

    Returns:
        list: List of dictionaries with keys 'Headline', 'Source', 'URL', 'Timestamp'.
    """
    if not os.path.exists(filepath):
        return []

    headlines = []
    try:
        with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row and any(row.values()):
                    headlines.append({
                        "Headline": (row.get("Headline") or "").strip(),
                        "Source": (row.get("Source") or "").strip(),
                        "URL": (row.get("URL") or "").strip(),
                        "Timestamp": (row.get("Timestamp") or "").strip(),
                        # lowercase aliases for flexibility
                        "headline": (row.get("Headline") or "").strip(),
                        "source": (row.get("Source") or "").strip(),
                        "url": (row.get("URL") or "").strip(),
                        "timestamp": (row.get("Timestamp") or "").strip(),
                    })
    except (PermissionError, OSError, csv.Error):
        return []

    return headlines


def save_quotes_to_txt(quotes, filepath=DEFAULT_QUOTES_FILE):
    """Save a list of quotes to a text file.

    Features:
    - Automatically creates file and directory if they do not exist.
    - Appends new records without deleting previous records.
    - Prevents duplicate quotes across successive runs.
    - Handles Unicode (UTF-8) and permission/IO errors gracefully.

    Args:
        quotes (list): List of quote dicts or strings.
        filepath (str): Path to destination text file.

    Returns:
        int: Number of new unique quotes written.
    """
    if not quotes:
        return 0

    ensure_directory_exists(filepath)

    # 1. Read existing quotes to prevent duplicates
    existing_quotes = read_quotes_from_txt(filepath)
    seen_texts = set()
    for line in existing_quotes:
        seen_texts.add(normalize_quote_text(line))
        # If line contains quoted body e.g. "Text" - Author, extract the quote body
        if line.startswith('"') and '"' in line[1:]:
            end_idx = line.find('"', 1)
            seen_texts.add(normalize_quote_text(line[1:end_idx]))

    # 2. Filter new unique quotes
    lines_to_write = []
    for item in quotes:
        if isinstance(item, dict):
            text = item.get("text", "").strip()
            author = item.get("author", "Unknown").strip() or "Unknown"
            tags = item.get("tags", [])
            tag_str = f" (Tags: {', '.join(tags)})" if tags else ""

            norm = normalize_quote_text(text)
            if not norm or norm in seen_texts:
                continue

            seen_texts.add(norm)
            line = f'"{text}" - {author}{tag_str}\n'
            lines_to_write.append(line)

        elif isinstance(item, str):
            clean_str = item.strip()
            norm = normalize_quote_text(clean_str)
            if not norm or norm in seen_texts:
                continue

            seen_texts.add(norm)
            lines_to_write.append(clean_str + "\n")

    if not lines_to_write:
        return 0

    # 3. Write lines with exception handling
    try:
        with open(filepath, mode="a", encoding="utf-8") as file:
            for line in lines_to_write:
                file.write(line)

        return len(lines_to_write)
    except (PermissionError, OSError):
        return 0


def read_quotes_from_txt(filepath=DEFAULT_QUOTES_FILE):
    """Read saved quotes from a text file.

    Args:
        filepath (str): Path to text file.

    Returns:
        list: List of quote strings (excluding comment lines starting with #).
    """
    if not os.path.exists(filepath):
        return []

    quotes = []
    try:
        with open(filepath, mode="r", encoding="utf-8") as file:
            for line in file:
                cleaned = line.strip()
                if cleaned and not cleaned.startswith("#"):
                    quotes.append(cleaned)
    except (PermissionError, OSError):
        return []

    return quotes


def get_storage_stats(headlines_file=DEFAULT_HEADLINES_FILE, quotes_file=DEFAULT_QUOTES_FILE):
    """Return record counts and file statuses for headlines and quotes storage.

    Args:
        headlines_file (str): Path to headlines CSV file.
        quotes_file (str): Path to quotes TXT file.

    Returns:
        dict: Storage statistics with counts and file statuses.
    """
    headlines = read_headlines_from_csv(headlines_file)
    quotes = read_quotes_from_txt(quotes_file)
    return {
        "headlines_count": len(headlines),
        "quotes_count": len(quotes),
        "headlines_file_exists": os.path.exists(headlines_file),
        "quotes_file_exists": os.path.exists(quotes_file),
    }
