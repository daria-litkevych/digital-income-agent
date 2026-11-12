import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.approval_queue import ApprovalError, ApprovalQueue


class ApprovalQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "approvals.json"
        self.queue = ApprovalQueue(self.path)
        self.now = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)

    def request(self, payload=None, **kwargs):
        return self.queue.request(
            "publish", "Publish a reviewed listing",
            {"listing_id": "draft-1"} if payload is None else payload,
            now=self.now, **kwargs,
        )

    def approve(self, record):
        return self.queue.approve(
            record["id"], approved_by="human-reviewer",
            expected_payload_sha256=record["payload_sha256"], now=self.now,
        )

    def test_request_is_persisted_as_pending_and_json_has_real_newlines(self):
        record = self.request()
        raw = self.path.read_text(encoding="utf-8")
        self.assertIn("\n", raw)
        self.assertNotIn("\\\\n", raw)
        self.assertEqual(json.loads(raw)["requests"][record["id"]]["status"], "pending")

    def test_approval_requires_exact_payload_hash_and_can_be_consumed_once(self):
        record = self.request()
        self.approve(record)
        result = self.queue.consume(record["id"], record["payload"], now=self.now)
        self.assertTrue(result["consumed"])
        with self.assertRaises(ApprovalError):
            self.queue.consume(record["id"], record["payload"], now=self.now)

    def test_tampered_payload_is_not_approved_or_consumed(self):
        record = self.request()
        stored = json.loads(self.path.read_text(encoding="utf-8"))
        stored["requests"][record["id"]]["payload"]["listing_id"] = "changed"
        self.path.write_text(json.dumps(stored), encoding="utf-8")
        with self.assertRaises(ApprovalError):
            self.approve(record)

    def test_expired_request_cannot_be_approved_or_consumed(self):
        record = self.request(ttl_hours=1)
        with self.assertRaises(ApprovalError):
            self.queue.approve(
                record["id"], approved_by="reviewer",
                expected_payload_sha256=record["payload_sha256"],
                now=self.now + timedelta(hours=1),
            )
        self.assertEqual(self.queue.list_requests()[0]["status"], "expired")

    def test_nested_secret_like_keys_are_rejected(self):
        for key in ("provider_api_key", "refresh_token_value", "client_secret_text", "private_key_pem"):
            with self.subTest(key=key), self.assertRaises(ApprovalError):
                self.request(payload={"metadata": {key: "do-not-store"}})

    def test_non_json_payload_is_rejected(self):
        with self.assertRaises(ApprovalError):
            self.request(payload={"not_json": object()})

    def test_pending_queue_limit_is_enforced(self):
        queue = ApprovalQueue(self.path, max_pending=1)
        queue.request("publish", "First", {"id": 1}, now=self.now)
        with self.assertRaises(ApprovalError):
            queue.request("publish", "Second", {"id": 2}, now=self.now)

    def test_rejected_request_cannot_be_consumed(self):
        record = self.request()
        self.queue.reject(record["id"], rejected_by="reviewer", reason="Not ready")
        with self.assertRaises(ApprovalError):
            self.queue.consume(record["id"], record["payload"], now=self.now)

    def test_rejector_identity_must_be_text(self):
        record = self.request()
        with self.assertRaises(ApprovalError):
            self.queue.reject(record["id"], rejected_by=None)


if __name__ == "__main__":
    unittest.main()
