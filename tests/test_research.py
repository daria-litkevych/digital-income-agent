import unittest
import tempfile
from pathlib import Path
from datetime import timezone

from agent.main import SEARCHES, atomic_write_text, clean_text, parse_date

class ResearchParsingTests(unittest.TestCase):
    def test_search_configuration_covers_all_studio_segments(self):
        self.assertEqual({item["segment"] for item in SEARCHES}, {"B2C", "B2B", "Prosumer"})
        self.assertGreaterEqual(len(SEARCHES), 6)

    def test_clean_text_removes_html_and_decodes_entities(self):
        self.assertEqual(clean_text("<b>Café</b> &amp; coffee"), "Café & coffee")

    def test_parse_date_normalises_to_utc(self):
        parsed = parse_date("Wed, 12 Nov 2026 10:00:00 +0200")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.hour, 8)

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_date("not a date"))

    def test_atomic_write_replaces_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            target.write_text('{"old": true}', encoding="utf-8")
            atomic_write_text(target, '{"new": true}\\n')
            self.assertEqual(target.read_text(encoding="utf-8"), '{"new": true}\\n')
            self.assertFalse(target.with_suffix(".json.tmp").exists())

if __name__ == "__main__":
    unittest.main()
