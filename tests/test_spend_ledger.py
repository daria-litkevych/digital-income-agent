import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from agent.spend_ledger import SpendLedger, SpendLimitExceeded


class SpendLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "spend.sqlite3"
        self.ledger = SpendLedger(self.path, monthly_limit_usd=1.0)
        self.now = datetime(2026, 11, 12, tzinfo=timezone.utc)

    def test_reservations_count_before_settlement(self):
        self.ledger.reserve("a", 0.6, self.now)
        with self.assertRaises(SpendLimitExceeded):
            self.ledger.reserve("b", 0.5, self.now)
        self.assertAlmostEqual(self.ledger.monthly_committed_usd(self.now), 0.6)

    def test_settlement_replaces_reservation_with_actual_cost(self):
        self.ledger.reserve("a", 0.6, self.now)
        self.ledger.settle("a", 0.2)
        self.assertAlmostEqual(self.ledger.monthly_committed_usd(self.now), 0.2)

    def test_unsettled_reservation_remains_committed(self):
        self.ledger.reserve("a", 0.4, self.now)
        self.assertAlmostEqual(self.ledger.monthly_committed_usd(self.now), 0.4)

    def test_duplicate_and_unknown_reservations_rejected(self):
        self.ledger.reserve("a", 0.1, self.now)
        with self.assertRaises(ValueError):
            self.ledger.reserve("a", 0.1, self.now)
        with self.assertRaises(KeyError):
            self.ledger.settle("missing", 0.1)

    def test_month_is_utc(self):
        nov = datetime(2026, 11, 30, 23, 30, tzinfo=timezone.utc)
        dec = datetime(2026, 12, 1, 0, 30, tzinfo=timezone.utc)
        self.ledger.reserve("nov", 0.9, nov)
        self.assertAlmostEqual(self.ledger.monthly_committed_usd(dec), 0.0)


if __name__ == "__main__":
    unittest.main()
