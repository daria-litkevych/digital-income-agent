import unittest
from datetime import timezone

from agent.main import clean_text, parse_date

class ResearchParsingTests(unittest.TestCase):
    def test_clean_text_removes_html_and_decodes_entities(self):
        self.assertEqual(clean_text("<b>Café</b> &amp; coffee"), "Café & coffee")

    def test_parse_date_normalises_to_utc(self):
        parsed = parse_date("Wed, 12 Nov 2026 10:00:00 +0200")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.hour, 8)

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_date("not a date"))

if __name__ == "__main__":
    unittest.main()
