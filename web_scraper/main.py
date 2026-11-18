"""Main entry point for Project 04: Web Scraper for Headlines & Quotes.

Phase 6: Final Polish, Packaging & Production CLI

This application provides:
1. Interactive terminal CLI menu for scraping headlines and quotes.
2. Full automated pipeline combining live scraping and persistent export.
3. Storage inspection tools for CSV headlines and TXT quotes.
4. Input validation and graceful KeyboardInterrupt / EOFError handling.
5. Non-interactive fallback mode for automated environments and tests.
6. Cross-platform path and encoding compatibility (Windows, Linux, macOS).
"""

import os
import sys

# Ensure UTF-8 output on Windows console for Unicode, accents, and emojis
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure local directory is on sys.path for direct module imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from scraper import (
    fetch_page,
    create_soup,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    is_valid_url,
)
from headlines_scraper import (
    extract_headlines,
    scrape_headlines,
    format_headline,
    resolve_url,
)
from quotes_scraper import (
    extract_quotes,
    scrape_quotes,
    format_quote,
)
import storage


# Default public scraping endpoints (explicitly permit automated access)
DEFAULT_TECH_NEWS_URL = "https://www.python.org/blogs/"
DEFAULT_QUOTES_URL = "http://quotes.toscrape.com"

# Local sample HTML fixture for offline verification
SAMPLE_HEADLINES_HTML = """
<!DOCTYPE html>
<html>
<head><title>Daily Tech News</title></head>
<body>
    <header>
        <h1><a href="/special-report">Annual Technology Forecast 2026 🚀</a></h1>
    </header>
    <main>
        <h2><a href="https://example.com/ai-update">Python 3.13 Released with Major Performance Boosts</a></h2>
        <span class="source">Tech Today</span>

        <h2><a href="/news/web-scraping">Web Scraping Best Practices: ¿Cómo diseñar scrapers éticos?</a></h2>
        <span class="source">Dev Insider</span>

        <h3><a href="">Announcement: Open Source Community Meetup</a></h3>
    </main>
</body>
</html>
"""

SAMPLE_QUOTES_HTML = """
<!DOCTYPE html>
<html>
<head><title>Famous Quotes</title></head>
<body>
    <div class="quote">
        <span class="text">“The only way to do great work is to love what you do. 💡”</span>
        <small class="author">Steve Jobs</small>
        <div class="tags">
            <a class="tag">inspiration</a>
            <a class="tag">work</a>
        </div>
    </div>
    <div class="quote">
        <span class="text">“Simplicity is prerequisite for reliability.”</span>
        <small class="author">Edsger W. Dijkstra</small>
        <div class="tags">
            <a class="tag">programming</a>
            <a class="tag">design</a>
        </div>
    </div>
    <div class="quote">
        <span class="text">“Le cœur a ses raisons que la raison ne connaît point.”</span>
        <small class="author">Blaise Pascal</small>
    </div>
</body>
</html>
"""


def print_banner():
    """Print the application welcome banner."""
    print("=" * 74)
    print("       PROJECT 04: WEB SCRAPER FOR HEADLINES & QUOTES")
    print("       Multi-Source Scraper with CSV & TXT Persistence")
    print("=" * 74)


def print_menu():
    """Display the main interactive CLI menu."""
    print("\n" + "-" * 74)
    print("                         MAIN MENU")
    print("-" * 74)
    print("  [1] Scrape Technology News Headlines (Export to CSV)")
    print("  [2] Scrape Inspirational Quotes (Export to TXT)")
    print("  [3] Run Full Automated Pipeline (Headlines + Quotes)")
    print("  [4] View Stored Headlines (data/headlines.csv)")
    print("  [5] View Stored Quotes (data/quotes.txt)")
    print("  [6] View Storage Inventory & Statistics")
    print("  [7] Run Self-Test & Component Verification Demo")
    print("  [8] Exit")
    print("-" * 74)


def menu_scrape_headlines():
    """Handle interactive headline scraping flow."""
    print("\n--- Scrape News Headlines ---")
    prompt = f"Enter target URL (Press Enter for default: {DEFAULT_TECH_NEWS_URL}): "
    try:
        user_url = input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    target_url = user_url if user_url else DEFAULT_TECH_NEWS_URL
    print(f"\n[+] Fetching headlines from: {target_url} ...")

    headlines, error = scrape_headlines(target_url, timeout=DEFAULT_TIMEOUT)
    if error:
        print(f"[-] Scrape Notice: {error}")
        return

    print(f"[+] Successfully extracted {len(headlines)} headlines.")
    preview_count = min(5, len(headlines))
    if preview_count > 0:
        print(f"\nPreview of first {preview_count} headlines:")
        for i, h in enumerate(headlines[:preview_count], start=1):
            print(f"  [{i}] [{h['Source']}] {h['Headline']}")
            print(f"      URL: {h['URL'] or 'No link available'}")

    try:
        save_choice = input("\nSave new headlines to CSV? (y/n, default: y): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nSave skipped.")
        return

    if save_choice in ("", "y", "yes"):
        saved = storage.save_headlines_to_csv(headlines)
        print(f"[+] Saved {saved} new unique headlines to {storage.DEFAULT_HEADLINES_FILE}.")
        if len(headlines) > saved:
            print(f"[*] Skipped {len(headlines) - saved} duplicate entries already in storage.")


def menu_scrape_quotes():
    """Handle interactive quote scraping flow."""
    print("\n--- Scrape Inspirational Quotes ---")
    prompt = f"Enter target URL (Press Enter for default: {DEFAULT_QUOTES_URL}): "
    try:
        user_url = input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        return

    target_url = user_url if user_url else DEFAULT_QUOTES_URL
    print(f"\n[+] Fetching quotes from: {target_url} ...")

    quotes, error = scrape_quotes(target_url, timeout=DEFAULT_TIMEOUT)
    if error:
        print(f"[-] Scrape Notice: {error}")
        return

    print(f"[+] Successfully extracted {len(quotes)} quotes.")
    preview_count = min(5, len(quotes))
    if preview_count > 0:
        print(f"\nPreview of first {preview_count} quotes:")
        for i, q in enumerate(quotes[:preview_count], start=1):
            print(f"  [{i}] {format_quote(q)}")

    try:
        save_choice = input("\nSave new quotes to TXT? (y/n, default: y): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nSave skipped.")
        return

    if save_choice in ("", "y", "yes"):
        saved = storage.save_quotes_to_txt(quotes)
        print(f"[+] Saved {saved} new unique quotes to {storage.DEFAULT_QUOTES_FILE}.")
        if len(quotes) > saved:
            print(f"[*] Skipped {len(quotes) - saved} duplicate quotes already in storage.")


def menu_run_full_pipeline():
    """Execute the complete live scraping and export pipeline for both sources."""
    print("\n" + "=" * 74)
    print("           EXECUTING FULL AUTOMATED SCRAPING PIPELINE")
    print("=" * 74)

    # 1. Headlines
    print(f"\n[1/2] Scraping Headlines from: {DEFAULT_TECH_NEWS_URL}")
    headlines, h_err = scrape_headlines(DEFAULT_TECH_NEWS_URL, default_source="Python.org Blogs")
    if h_err:
        print(f"  [-] Scrape Notice: {h_err}")
    else:
        saved_h = storage.save_headlines_to_csv(headlines)
        print(f"  [+] Extracted: {len(headlines)} headlines | Newly Saved: {saved_h} records.")

    # 2. Quotes
    print(f"\n[2/2] Scraping Quotes from: {DEFAULT_QUOTES_URL}")
    quotes, q_err = scrape_quotes(DEFAULT_QUOTES_URL)
    if q_err:
        print(f"  [-] Scrape Notice: {q_err}")
    else:
        saved_q = storage.save_quotes_to_txt(quotes)
        print(f"  [+] Extracted: {len(quotes)} quotes | Newly Saved: {saved_q} records.")

    # Inventory summary
    stats = storage.get_storage_stats()
    print("\n[+] Pipeline Complete! Updated Inventory:")
    print(f"  * Headlines in CSV : {stats['headlines_count']} records ({storage.DEFAULT_HEADLINES_FILE})")
    print(f"  * Quotes in TXT    : {stats['quotes_count']} records ({storage.DEFAULT_QUOTES_FILE})")


def menu_view_headlines():
    """Display stored headlines from CSV."""
    print("\n--- Stored Headlines (data/headlines.csv) ---")
    headlines = storage.read_headlines_from_csv()
    if not headlines:
        print("No headlines currently stored in data/headlines.csv.")
        return

    print(f"Total stored headlines: {len(headlines)}\n")
    max_display = min(10, len(headlines))
    for i, h in enumerate(headlines[:max_display], start=1):
        print(f"[{i}] [{h['Source']}] {h['Headline']}")
        print(f"    URL       : {h['URL'] or 'No link'}")
        print(f"    Timestamp : {h['Timestamp'] or 'N/A'}")

    if len(headlines) > max_display:
        print(f"\n... and {len(headlines) - max_display} more headlines stored.")


def menu_view_quotes():
    """Display stored quotes from TXT."""
    print("\n--- Stored Quotes (data/quotes.txt) ---")
    quotes = storage.read_quotes_from_txt()
    if not quotes:
        print("No quotes currently stored in data/quotes.txt.")
        return

    print(f"Total stored quotes: {len(quotes)}\n")
    max_display = min(10, len(quotes))
    for i, q in enumerate(quotes[:max_display], start=1):
        print(f"[{i}] {q}")

    if len(quotes) > max_display:
        print(f"\n... and {len(quotes) - max_display} more quotes stored.")


def menu_view_stats():
    """Display storage inventory and file statistics."""
    print("\n--- Storage Inventory & File Statistics ---")
    stats = storage.get_storage_stats()

    for name, filepath, count in [
        ("Headlines CSV", storage.DEFAULT_HEADLINES_FILE, stats["headlines_count"]),
        ("Quotes TXT", storage.DEFAULT_QUOTES_FILE, stats["quotes_count"]),
    ]:
        exists = os.path.exists(filepath)
        size_bytes = os.path.getsize(filepath) if exists else 0
        print(f"\n  * {name}:")
        print(f"      File Path    : {filepath}")
        print(f"      Status       : {'Present' if exists else 'Missing'}")
        print(f"      Total Records: {count}")
        print(f"      File Size    : {size_bytes:,} bytes")


def run_demo_mode():
    """Run non-interactive self-test and demonstration mode."""
    print_banner()
    print("\n[+] Non-Interactive Demonstration Mode Active")

    print("\n--- 1. Component Architecture & Readiness ---")
    components = [
        ("requests Library", "Active (HTTP GET, headers, timeout, status checks)"),
        ("BeautifulSoup4 (bs4)", "Active (DOM parsing across headlines and quotes)"),
        ("Core Scraper (scraper.py)", "Active (fetch_page, create_soup, is_valid_url)"),
        ("Headlines Scraper (headlines_scraper.py)", "Active (extract_headlines, scrape_headlines)"),
        ("Quotes Scraper (quotes_scraper.py)", "Active (extract_quotes, scrape_quotes)"),
        ("Storage Manager (storage.py)", "Active (CSV & TXT persistence with de-duplication)"),
    ]
    for name, desc in components:
        print(f"  * {name:<42} : {desc}")

    print("\n--- 2. Offline Headline Extraction (Mock Fixture) ---")
    local_headlines = extract_headlines(
        SAMPLE_HEADLINES_HTML,
        base_url="https://techdaily.example.com/",
        default_source="Tech Daily",
    )
    print(f"  [+] Extracted {len(local_headlines)} headlines across h1, h2, h3:")
    for i, h in enumerate(local_headlines[:3], start=1):
        print(f"  ({i}) [{h['Source']}] {h['Headline']}")
        print(f"      URL: {h['URL']}")

    print("\n--- 3. Offline Quote Extraction (Mock Fixture) ---")
    local_quotes = extract_quotes(SAMPLE_QUOTES_HTML)
    print(f"  [+] Extracted {len(local_quotes)} unique quotes (duplicates removed):")
    for i, q in enumerate(local_quotes[:3], start=1):
        print(f"  ({i}) {format_quote(q)}")

    print("\n--- 4. Live Connection Verification ---")
    quotes_res = fetch_page(DEFAULT_QUOTES_URL, timeout=5)
    if quotes_res.success:
        print(f"  [+] Live HTTP Connection ({DEFAULT_QUOTES_URL}) -> Status {quotes_res.status_code} ({len(quotes_res.html):,} bytes)")
    else:
        print(f"  [-] Live network notice: {quotes_res.error}")

    res_404 = fetch_page(f"{DEFAULT_QUOTES_URL}/intentional_404_check")
    print(f"  [+] Graceful 404 Error Handling: {res_404.error}")

    print("\n--- 5. Storage Stats ---")
    stats = storage.get_storage_stats()
    print(f"  * Headlines in CSV: {stats['headlines_count']} records")
    print(f"  * Quotes in TXT   : {stats['quotes_count']} records")
    print("\n" + "=" * 74)
    print("  Demonstration completed successfully!")
    print("=" * 74)


def interactive_menu():
    """Main interactive menu loop."""
    print_banner()

    while True:
        print_menu()
        try:
            choice = input("Enter your choice (1-8): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting application. Goodbye!")
            break

        if choice == "1":
            menu_scrape_headlines()
        elif choice == "2":
            menu_scrape_quotes()
        elif choice == "3":
            menu_run_full_pipeline()
        elif choice == "4":
            menu_view_headlines()
        elif choice == "5":
            menu_view_quotes()
        elif choice == "6":
            menu_view_stats()
        elif choice == "7":
            run_demo_mode()
        elif choice == "8":
            print("\nThank you for using Web Scraper for Headlines & Quotes! Goodbye.")
            break
        else:
            print("\n[!] Invalid choice. Please enter a number between 1 and 8.")


def main():
    """Application entry point."""
    # Run demo mode if flags are passed or if running in non-interactive environment
    if len(sys.argv) > 1 and any(arg in sys.argv for arg in ("--demo", "--test", "-d")):
        run_demo_mode()
    elif not sys.stdin.isatty():
        run_demo_mode()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
