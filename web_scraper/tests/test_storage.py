"""Unit tests for storage.py (Storage Persistence & Export Module)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure web_scraper directory is on python path for imports
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import storage


class TestStoragePhase5(unittest.TestCase):
    """Comprehensive test suite for Phase 5 data persistence and export functionality."""

    def setUp(self):
        """Create a temporary directory for isolated file testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, "headlines.csv")
        self.txt_path = os.path.join(self.temp_dir.name, "quotes.txt")

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    # --- 1. Save Multiple Headlines ---
    def test_save_multiple_headlines_creates_csv_with_timestamps(self):
        """Verify saving multiple headlines creates CSV with headers and timestamps."""
        headlines = [
            {
                "Headline": "Python 3.13 Performance Breakthroughs",
                "Source": "Python Weekly",
                "URL": "https://example.com/py313",
                "Timestamp": "2026-11-18 10:00:00",
            },
            {
                "Headline": "Next-Gen Quantum Processors Unveiled",
                "Source": "Quantum Tech",
                "URL": "https://example.com/quantum",
                "Timestamp": "2026-11-18 10:05:00",
            },
        ]
        saved_count = storage.save_headlines_to_csv(headlines, filepath=self.csv_path)
        self.assertEqual(saved_count, 2)
        self.assertTrue(os.path.exists(self.csv_path))

        loaded = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["Headline"], "Python 3.13 Performance Breakthroughs")
        self.assertEqual(loaded[0]["Source"], "Python Weekly")
        self.assertEqual(loaded[0]["URL"], "https://example.com/py313")
        self.assertEqual(loaded[0]["Timestamp"], "2026-11-18 10:00:00")

    # --- 2. Save Multiple Quotes ---
    def test_save_multiple_quotes_creates_txt(self):
        """Verify saving multiple quotes writes properly formatted lines."""
        quotes = [
            {"text": "Stay hungry, stay foolish.", "author": "Steve Jobs", "tags": ["life", "inspiration"]},
            {"text": "Talk is cheap. Show me the code.", "author": "Linus Torvalds", "tags": ["code"]},
        ]
        count = storage.save_quotes_to_txt(quotes, filepath=self.txt_path)
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(self.txt_path))

        lines = storage.read_quotes_from_txt(filepath=self.txt_path)
        self.assertEqual(len(lines), 2)
        self.assertIn('"Stay hungry, stay foolish." - Steve Jobs (Tags: life, inspiration)', lines[0])
        self.assertIn('"Talk is cheap. Show me the code." - Linus Torvalds (Tags: code)', lines[1])

    # --- 3. Duplicate Prevention ---
    def test_headlines_duplicate_prevention(self):
        """Verify that duplicate headlines are prevented across consecutive save calls."""
        batch1 = [
            {"Headline": "First News Item", "Source": "Source 1", "URL": "https://example.com/1"},
            {"Headline": "Second News Item", "Source": "Source 2", "URL": "https://example.com/2"},
        ]
        batch2 = [
            {"Headline": "First News Item", "Source": "Source 1", "URL": "https://example.com/1"},  # duplicate
            {"Headline": "Third News Item", "Source": "Source 3", "URL": "https://example.com/3"},  # unique
        ]

        count1 = storage.save_headlines_to_csv(batch1, filepath=self.csv_path)
        self.assertEqual(count1, 2)

        count2 = storage.save_headlines_to_csv(batch2, filepath=self.csv_path)
        self.assertEqual(count2, 1)  # Only 1 unique item should be written

        loaded = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(loaded), 3)
        titles = [h["Headline"] for h in loaded]
        self.assertEqual(titles, ["First News Item", "Second News Item", "Third News Item"])

    def test_quotes_duplicate_prevention(self):
        """Verify that duplicate quotes are prevented across consecutive save calls."""
        batch1 = [
            {"text": "Simplicity is prerequisite for reliability.", "author": "Dijkstra", "tags": ["programming"]},
            {"text": "Knowledge is power.", "author": "Francis Bacon", "tags": []},
        ]
        batch2 = [
            {"text": "Simplicity is prerequisite for reliability.", "author": "Dijkstra", "tags": ["programming"]},  # duplicate
            {"text": "Make it work, make it right, make it fast.", "author": "Kent Beck", "tags": ["refactoring"]},  # unique
        ]

        count1 = storage.save_quotes_to_txt(batch1, filepath=self.txt_path)
        self.assertEqual(count1, 2)

        count2 = storage.save_quotes_to_txt(batch2, filepath=self.txt_path)
        self.assertEqual(count2, 1)  # Only unique quote appended

        lines = storage.read_quotes_from_txt(filepath=self.txt_path)
        self.assertEqual(len(lines), 3)

    # --- 4. Preserve Existing Records ---
    def test_preserve_existing_records_on_append(self):
        """Verify appending headlines does not delete or overwrite existing records."""
        initial_data = [{"Headline": "Original Headline", "Source": "Orig", "URL": "https://orig.com"}]
        storage.save_headlines_to_csv(initial_data, filepath=self.csv_path)

        new_data = [{"Headline": "Appended Headline", "Source": "New", "URL": "https://new.com"}]
        storage.save_headlines_to_csv(new_data, filepath=self.csv_path)

        loaded = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["Headline"], "Original Headline")
        self.assertEqual(loaded[1]["Headline"], "Appended Headline")

    # --- 5. Empty Files Handling ---
    def test_save_empty_list_returns_zero(self):
        """Verify saving empty list returns 0 and does not create an unnecessary file."""
        self.assertEqual(storage.save_headlines_to_csv([], filepath=self.csv_path), 0)
        self.assertFalse(os.path.exists(self.csv_path))

        self.assertEqual(storage.save_quotes_to_txt([], filepath=self.txt_path), 0)
        self.assertFalse(os.path.exists(self.txt_path))

    def test_read_empty_files_returns_empty_list(self):
        """Verify reading from an existing 0-byte file returns empty list."""
        with open(self.csv_path, "w", encoding="utf-8") as f:
            pass  # create 0-byte file
        self.assertEqual(storage.read_headlines_from_csv(filepath=self.csv_path), [])

        with open(self.txt_path, "w", encoding="utf-8") as f:
            pass
        self.assertEqual(storage.read_quotes_from_txt(filepath=self.txt_path), [])

    # --- 6. Missing Files Handling ---
    def test_read_missing_files_returns_empty_list(self):
        """Verify reading non-existent files returns empty list without raising FileNotFoundError."""
        missing_csv = os.path.join(self.temp_dir.name, "does_not_exist.csv")
        missing_txt = os.path.join(self.temp_dir.name, "does_not_exist.txt")

        self.assertEqual(storage.read_headlines_from_csv(filepath=missing_csv), [])
        self.assertEqual(storage.read_quotes_from_txt(filepath=missing_txt), [])

    def test_ensure_directory_exists_creates_nested_directories(self):
        """Verify nested subdirectories are automatically created when saving."""
        deep_csv = os.path.join(self.temp_dir.name, "level1", "level2", "headlines.csv")
        data = [{"Headline": "Deep Path Headline", "Source": "Source", "URL": "http://deep"}]

        count = storage.save_headlines_to_csv(data, filepath=deep_csv)
        self.assertEqual(count, 1)
        self.assertTrue(os.path.exists(deep_csv))

    # --- 7. Unicode Content ---
    def test_unicode_content_preservation(self):
        """Verify headlines and quotes with emojis, accents, and non-Latin text are preserved."""
        unicode_headlines = [
            {
                "Headline": "Python 3.13 🚀: Neue Features & Événements",
                "Source": "Dev International",
                "URL": "https://example.com/py-unicode",
                "Timestamp": "2026-11-18 12:00:00",
            },
            {
                "Headline": "AI研究突破: 智能编程技术新进展",
                "Source": "AI Research",
                "URL": "https://example.com/ai-cn",
                "Timestamp": "2026-11-18 12:01:00",
            },
        ]
        storage.save_headlines_to_csv(unicode_headlines, filepath=self.csv_path)

        loaded_headlines = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(loaded_headlines), 2)
        self.assertEqual(loaded_headlines[0]["Headline"], "Python 3.13 🚀: Neue Features & Événements")
        self.assertEqual(loaded_headlines[1]["Headline"], "AI研究突破: 智能编程技术新进展")

        unicode_quotes = [
            {"text": "Le cœur a ses raisons que la raison ne connaît point. 💡", "author": "Blaise Pascal", "tags": ["cœur"]},
            {"text": "千里之行，始于足下。", "author": "老子 (Laozi)", "tags": ["古籍"]},
        ]
        storage.save_quotes_to_txt(unicode_quotes, filepath=self.txt_path)

        loaded_quotes = storage.read_quotes_from_txt(filepath=self.txt_path)
        self.assertEqual(len(loaded_quotes), 2)
        self.assertIn("Le cœur a ses raisons que la raison ne connaît point. 💡", loaded_quotes[0])
        self.assertIn("千里之行，始于足下。", loaded_quotes[1])

    # --- 8. File Permission and I/O Errors ---
    @patch("builtins.open")
    def test_save_headlines_permission_error_handled(self, mock_open):
        """Verify PermissionError is caught and handled gracefully when writing headlines."""
        mock_open.side_effect = PermissionError("Permission denied: 'protected.csv'")
        data = [{"Headline": "Test", "Source": "S", "URL": "http://test"}]

        count = storage.save_headlines_to_csv(data, filepath="/root/protected.csv")
        self.assertEqual(count, 0)

    @patch("builtins.open")
    def test_save_quotes_permission_error_handled(self, mock_open):
        """Verify PermissionError is caught and handled gracefully when writing quotes."""
        mock_open.side_effect = PermissionError("Permission denied: 'protected.txt'")
        data = [{"text": "Test quote", "author": "Test", "tags": []}]

        count = storage.save_quotes_to_txt(data, filepath="/root/protected.txt")
        self.assertEqual(count, 0)

    @patch("builtins.open")
    def test_read_headlines_permission_error_handled(self, mock_open):
        """Verify PermissionError during read returns empty list without crashing."""
        mock_open.side_effect = PermissionError("Permission denied")
        self.assertEqual(storage.read_headlines_from_csv(filepath=self.csv_path), [])

    @patch("builtins.open")
    def test_read_quotes_permission_error_handled(self, mock_open):
        """Verify PermissionError during quote read returns empty list without crashing."""
        mock_open.side_effect = PermissionError("Permission denied")
        self.assertEqual(storage.read_quotes_from_txt(filepath=self.txt_path), [])

    # --- 9. Repeated Exports (Idempotency) ---
    def test_repeated_exports_idempotency(self):
        """Verify running repeated export cycles leaves file with exactly unique items."""
        sample_headlines = [
            {"Headline": "News 1", "Source": "Source", "URL": "http://n1"},
            {"Headline": "News 2", "Source": "Source", "URL": "http://n2"},
        ]

        # Run 1: initial export
        res1 = storage.save_headlines_to_csv(sample_headlines, filepath=self.csv_path)
        self.assertEqual(res1, 2)

        # Run 2: exact re-export
        res2 = storage.save_headlines_to_csv(sample_headlines, filepath=self.csv_path)
        self.assertEqual(res2, 0)

        # Run 3: re-export with 1 new item
        batch3 = sample_headlines + [{"Headline": "News 3", "Source": "Source", "URL": "http://n3"}]
        res3 = storage.save_headlines_to_csv(batch3, filepath=self.csv_path)
        self.assertEqual(res3, 1)

        loaded = storage.read_headlines_from_csv(filepath=self.csv_path)
        self.assertEqual(len(loaded), 3)

    # --- 10. Comment Skipping in Quotes TXT ---
    def test_read_quotes_skips_comments(self):
        """Verify read_quotes_from_txt skips lines starting with #."""
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("# Quotes Collection\n")
            f.write("# Format description line\n")
            f.write('"Knowledge is power." - Francis Bacon\n')

        quotes = storage.read_quotes_from_txt(filepath=self.txt_path)
        self.assertEqual(len(quotes), 1)
        self.assertEqual(quotes[0], '"Knowledge is power." - Francis Bacon')

    # --- 11. Storage Stats Helper ---
    def test_get_storage_stats(self):
        """Verify get_storage_stats reports accurate counts and existence flags."""
        storage.save_headlines_to_csv([{"Headline": "H1", "Source": "S", "URL": "U"}], filepath=self.csv_path)
        storage.save_quotes_to_txt([{"text": "Q1", "author": "A", "tags": []}], filepath=self.txt_path)

        stats = storage.get_storage_stats(headlines_file=self.csv_path, quotes_file=self.txt_path)
        self.assertEqual(stats["headlines_count"], 1)
        self.assertEqual(stats["quotes_count"], 1)
        self.assertTrue(stats["headlines_file_exists"])
        self.assertTrue(stats["quotes_file_exists"])


if __name__ == "__main__":
    unittest.main()
