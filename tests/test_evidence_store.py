import json
import tempfile
import unittest
from pathlib import Path

from agent.evidence_store import EvidenceStore, canonicalize_url, discovery_record


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "evidence.json"
        self.store = EvidenceStore(self.path)
        self.item = {
            "title": "Independent creator workflow report",
            "link": "https://Example.com/story?utm_source=newsletter&id=7#comments",
            "description": "A discovery snippet, not independently checked.",
            "published_date": "2026-11-10",
            "segment": "Prosumer",
            "hypothesis": "prosumer_creator",
        }

    def test_url_canonicalization_removes_tracking_and_fragment(self):
        self.assertEqual(
            canonicalize_url(self.item["link"]),
            "https://example.com/story?id=7",
        )

    def test_unsafe_or_malformed_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "https://user:pass@example.com/a", "/relative/path"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonicalize_url(url)

    def test_discovery_record_is_explicitly_unverified_and_has_provenance(self):
        record = discovery_record(self.item, checked_at="2026-11-12T00:00:00+00:00")
        self.assertEqual(record["confidence"], "Unverified")
        self.assertEqual(record["evidence_status"], "unreviewed")
        self.assertEqual(record["source_type"], "discovery_signal")
        self.assertEqual(record["segment"], "Prosumer")
        self.assertIsNone(record["payment_signal"])
        self.assertTrue(record["content_sha256"])

    def test_ingest_is_persistent_and_deduplicates_canonical_url(self):
        first = self.store.ingest_discovery([self.item], checked_at="2026-11-12T00:00:00+00:00")
        second_item = dict(self.item, link="https://example.com/story?id=7&utm_medium=email#top")
        second = self.store.ingest_discovery([second_item], checked_at="2026-11-12T01:00:00+00:00")
        self.assertEqual(first, {"added": 1, "total": 1})
        self.assertEqual(second, {"added": 0, "total": 1})
        stored = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["records"]), 1)
        self.assertEqual(stored["records"][0]["confidence"], "Unverified")

    def test_discovery_item_requires_title(self):
        with self.assertRaises(ValueError):
            discovery_record({"link": "https://example.com"})

    def test_main_research_runner_connects_evidence_store(self):
        source = Path(__file__).resolve().parents[1] / "agent" / "main.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("EvidenceStore(EVIDENCE_STORE_PATH)", text)
        self.assertIn("ingest_discovery(merged[:200]", text)


if __name__ == "__main__":
    unittest.main()
