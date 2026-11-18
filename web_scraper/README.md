# Project 04: Web Scraper for Headlines & Quotes

A modular, robust, and beginner-friendly Python web scraper designed to extract technology news headlines and inspirational quotes from the web, with automatic de-duplication, relative-to-absolute URL conversion, timestamp tracking, and persistent export to CSV and TXT files.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Required Dependencies](#required-dependencies)
- [Project Architecture & Structure](#project-architecture--structure)
- [Installation & Setup](#installation--setup)
- [How to Run the Application](#how-to-run-the-application)
- [Interactive CLI Menu Options](#interactive-cli-menu-options)
- [Example Outputs](#example-outputs)
- [Automated Testing](#automated-testing)
- [6-Phase Development Roadmap](#6-phase-development-roadmap)

---

## Project Overview

Project 04 is built following professional software engineering principles:
- **Modular Design**: Distinct layers for HTTP networking, HTML parsing, data extraction, file persistence, and CLI presentation.
- **Cross-Platform**: Fully compatible across Windows, macOS, and Linux using standard library pathing and UTF-8 encoding.
- **Resilient**: Graceful handling of network timeouts, connection failures, HTTP 404/500 errors, unclosed or malformed HTML, and missing links/authors.
- **Data Integrity**: Idempotent exports ensure no duplicate records are added across repeated scraping cycles.

---

## Key Features

1. **HTTP Networking Engine (`scraper.py`)**:
   - HTTP GET requests using `requests`.
   - Polite browser `User-Agent` headers.
   - Configurable network timeout (default: 10s).
   - Automatic HTTP status code validation (`response.raise_for_status()`).
   - Exception handling for `ConnectionError`, `Timeout`, `HTTPError`, and general `RequestException`.

2. **Headline Scraper (`headlines_scraper.py`)**:
   - Parses `<h1>`, `<h2>`, and `<h3>` tags using BeautifulSoup4.
   - Converts relative URLs into absolute URLs using `urllib.parse.urljoin`.
   - Filters out empty titles and discards duplicates.
   - Extracts source publication names and ISO extraction timestamps.
   - Preserves Unicode characters, accents, and emojis (e.g. `🚀`, `¿Cómo...?`).

3. **Quotes Scraper (`quotes_scraper.py`)**:
   - Extracts quote text, author attributions, and category tags.
   - Supports standard `.quote` containers as well as HTML `<blockquote>` and `<cite>` fallbacks.
   - Defaults missing authors to `"Unknown"` and missing tags to `[]`.
   - Normalizes text and eliminates duplicate quotes.

4. **Persistent Storage Manager (`storage.py`)**:
   - **CSV Export**: Saves headlines to `data/headlines.csv` with standard headers (`Headline,Source,URL,Timestamp`).
   - **TXT Export**: Appends formatted quotes to `data/quotes.txt`.
   - **Cross-Run De-Duplication**: Checks existing stored records before writing, preventing duplicate rows across consecutive scraping runs.
   - **Safety**: Safe directory creation, UTF-8 encoding, and `PermissionError` / `OSError` resilience.

5. **Dual Interface (`main.py`)**:
   - **Interactive Terminal Menu**: 8-option terminal menu with `while`-loop input validation and clean `KeyboardInterrupt` (`Ctrl+C`) handling.
   - **Non-Interactive Mode**: Automatically detected via `--demo` or `sys.stdin.isatty()` for CI/CD pipelines and automated testing.

---

## Required Dependencies

This project relies on only two carefully selected third-party packages:

| Library | Version | Purpose |
| :--- | :--- | :--- |
| **`requests`** | `>=2.31.0` | High-level HTTP communication, request headers, timeouts, status codes, and HTML payload retrieval. |
| **`beautifulsoup4` (`bs4`)** | `>=4.12.0` | Fast, robust HTML/XML parsing, tag searching, class filtering, and DOM tree traversal. |

Install dependencies via:
```bash
pip install -r web_scraper/requirements.txt
```

---

## Project Architecture & Structure

```text
web_scraper/
│
├── main.py                 # Interactive CLI menu & non-interactive demonstration pipeline
├── scraper.py              # Base HTTP networking, headers, timeout, & BeautifulSoup creation
├── headlines_scraper.py    # Headline extraction, URL resolution, timestamps, & de-duplication
├── quotes_scraper.py       # Quote text, author, & tag extraction with de-duplication
├── storage.py              # CSV/TXT persistence, cross-run de-duplication, & inventory stats
├── requirements.txt        # Explicit external dependencies (requests, beautifulsoup4)
├── README.md               # Complete project documentation and usage guide
├── .gitignore              # Ignores __pycache__, virtual environments, and IDE artifacts
│
├── data/
│   ├── headlines.csv       # Persistent CSV storage (Headline, Source, URL, Timestamp)
│   └── quotes.txt          # Persistent plain text storage for formatted quotes
│
└── tests/
    ├── __init__.py         # Test package initializer
    ├── test_scraper.py     # 19 unit tests for networking, headers, mocks, & errors
    ├── test_headlines.py   # 14 unit tests for h1/h2/h3 parsing, URLs, & timestamps
    ├── test_quotes.py      # 15 unit tests for quote/author/tag extraction & mocks
    ├── test_storage.py     # 17 unit tests for CSV/TXT persistence & de-duplication
    └── test_integration.py # 4 end-to-end pipeline & CLI integration tests
```

---

## Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Clone & Install
```bash
# Clone the repository
git clone https://github.com/praneeth-source/web-scraper-headlines-quotes.git
cd web-scraper-headlines-quotes

# Install dependencies
pip install -r web_scraper/requirements.txt
```

---

## How to Run the Application

### 1. Interactive Menu Mode
Launch the interactive terminal application:
```bash
python web_scraper/main.py
```

### 2. Non-Interactive Demonstration Mode
Run the self-test and demonstration mode directly (ideal for headless or automated testing):
```bash
python web_scraper/main.py --demo
```

---

## Interactive CLI Menu Options

```text
==========================================================================
       PROJECT 04: WEB SCRAPER FOR HEADLINES & QUOTES
       Multi-Source Scraper with CSV & TXT Persistence
==========================================================================

--------------------------------------------------------------------------
                         MAIN MENU
--------------------------------------------------------------------------
  [1] Scrape Technology News Headlines (Export to CSV)
  [2] Scrape Inspirational Quotes (Export to TXT)
  [3] Run Full Automated Pipeline (Headlines + Quotes)
  [4] View Stored Headlines (data/headlines.csv)
  [5] View Stored Quotes (data/quotes.txt)
  [6] View Storage Inventory & Statistics
  [7] Run Self-Test & Component Verification Demo
  [8] Exit
--------------------------------------------------------------------------
```

---

## Example Outputs

### 1. Live Technology News Headlines Preview
```text
[+] Fetching headlines from: https://www.python.org/blogs/ ...
[+] Successfully extracted 20 headlines.

Preview of first 3 headlines:
  [1] [Python.org Blogs] Python 3.16.0 alpha 2 is now available
      URL: https://blog.python.org/2026/11/python-3160-alpha-2-is-now-available/
  [2] [Python.org Blogs] Python is for everyone: Join in the PSF year-end fundraiser!
      URL: https://pyfound.blogspot.com/2026/11/python-is-for-everyone-join-in-psf-year.html
  [3] [Python.org Blogs] XTM Transifex sponsors Python’s documentation translations
      URL: https://blog.python.org/2026/11/transifex-sponsors-python-docs/
```

### 2. Saved CSV Record (`data/headlines.csv`)
```csv
Headline,Source,URL,Timestamp
"Python 3.16.0 alpha 2 is now available",Python.org Blogs,https://blog.python.org/2026/11/python-3160-alpha-2-is-now-available/,2026-11-18 15:19:55
"Annual Technology Forecast 2026 🚀",Tech Daily,https://techdaily.example.com/special-report,2026-11-18 15:19:54
```

### 3. Live Quotes Preview (`data/quotes.txt`)
```text
# Quotes Collection
# Format: "Quote text" - Author (Tags: tag1, tag2)
"The only way to do great work is to love what you do. 💡" - Steve Jobs (Tags: inspiration, work)
"Simplicity is prerequisite for reliability." - Edsger W. Dijkstra (Tags: programming, design)
"The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking." - Albert Einstein (Tags: change, deep-thoughts, thinking, world)
"It is our choices, Harry, that show what we truly are, far more than our abilities." - J.K. Rowling (Tags: abilities, choices)
```

---

## Automated Testing

All 69 unit and integration tests use `unittest.mock` for network operations, ensuring instantaneous, reliable, and completely offline test runs.

Run the complete test suite:
```bash
python -m unittest discover web_scraper/tests -v
```

### Test Coverage Breakdown:
- **`test_scraper.py`** (19 tests): HTTP GET, custom headers, timeout, 404, 500, ConnectionError, Timeout error, empty body, invalid URLs, and soup creation.
- **`test_headlines.py`** (14 tests): Multi-heading extraction (`h1`, `h2`, `h3`), relative URL resolution, missing link handling, duplicate removal, empty title removal, Unicode text, malformed HTML, and timestamps.
- **`test_quotes.py`** (15 tests): Container extraction, blockquote fallbacks, missing author default, missing tags default, de-duplication, empty/malformed HTML, Unicode characters, and mocked HTTP failures.
- **`test_storage.py`** (17 tests): CSV and TXT writing, timestamp recording, cross-run duplicate prevention, empty/missing files, Unicode preservation, `PermissionError` handling, repeated exports, and inventory statistics.
- **`test_integration.py`** (4 tests): End-to-end headline pipeline, end-to-end quote pipeline, demo mode execution, and CLI view functions.

**Total**: **69 tests passing (100% success rate)**.

---

## 6-Phase Development Roadmap

- [x] **Phase 1: Project Setup & Dependencies** – Structure creation, dependency management, starter modules, and initial unit test suite.
- [x] **Phase 2: HTTP Requests & Website Connection** – Reusable `fetch_page` function with HTTP GET, User-Agent headers, timeout handling, status validation, and exception handling for connection errors, timeouts, and HTTP errors.
- [x] **Phase 3: Headline Extraction using BeautifulSoup4** – Live and offline news headline extraction across h1/h2/h3 headings, relative-to-absolute URL conversion, extraction timestamps, de-duplication, and graceful error handling.
- [x] **Phase 4: Quotes Scraper** – Quote, author, and tag extraction using BeautifulSoup, missing field fallbacks, de-duplication, Unicode preservation, and `scrape_quotes()` integration.
- [x] **Phase 5: Data Persistence & Export** – CSV persistence for headlines with timestamps, TXT persistence for quotes, duplicate prevention across exports, Unicode preservation, and I/O error resilience.
- [x] **Phase 6: Final Polish & Packaging** – Production interactive CLI, input validation, integration test suite, cross-platform validation, and documentation.
