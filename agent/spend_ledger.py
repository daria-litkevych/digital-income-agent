"""SQLite-backed monthly spend guard for future paid LLM calls.

Reservations count against the monthly ceiling before a request is sent. An
unsettled reservation remains charged against the available budget (fail-safe).
This module is not wired into the agent or any provider call yet.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SpendLimitExceeded(RuntimeError):
    pass


class SpendLedger:
    def __init__(self, path: str | Path, monthly_limit_usd: float):
        if monthly_limit_usd <= 0:
            raise ValueError("monthly_limit_usd must be positive")
        self.path = str(path)
        self.monthly_limit_usd = float(monthly_limit_usd)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS llm_spend (
                    request_id TEXT PRIMARY KEY,
                    month_utc TEXT NOT NULL,
                    reserved_usd REAL NOT NULL,
                    actual_usd REAL,
                    status TEXT NOT NULL CHECK(status IN ('reserved','settled'))
                )
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.execute("PRAGMA busy_timeout=30000")
        return db

    @staticmethod
    def _month(now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return now.astimezone(timezone.utc).strftime("%Y-%m")

    def reserve(self, request_id: str, estimated_usd: float,
                now: datetime | None = None) -> None:
        if not request_id.strip():
            raise ValueError("request_id is required")
        if estimated_usd < 0:
            raise ValueError("estimated_usd cannot be negative")
        month = self._month(now)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT 1 FROM llm_spend WHERE request_id=?",
                              (request_id,)).fetchone():
                    raise ValueError("request_id already exists")
                row = db.execute("""
                    SELECT COALESCE(SUM(CASE WHEN status='reserved'
                        THEN reserved_usd ELSE actual_usd END),0)
                    FROM llm_spend WHERE month_utc=?
                """, (month,)).fetchone()
                committed = float(row[0])
                if committed + estimated_usd > self.monthly_limit_usd + 1e-12:
                    raise SpendLimitExceeded(
                        f"Monthly USD limit would be exceeded: "
                        f"{committed:.6f} + {estimated_usd:.6f} > "
                        f"{self.monthly_limit_usd:.6f}"
                    )
                db.execute("""INSERT INTO llm_spend
                    (request_id,month_utc,reserved_usd,actual_usd,status)
                    VALUES (?,?,?,NULL,'reserved')""",
                    (request_id, month, estimated_usd))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def settle(self, request_id: str, actual_usd: float) -> None:
        if actual_usd < 0:
            raise ValueError("actual_usd cannot be negative")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT status FROM llm_spend WHERE request_id=?",
                    (request_id,)
                ).fetchone()
                if row is None:
                    raise KeyError("Unknown spend reservation")
                if row[0] != "reserved":
                    raise ValueError("Reservation is already settled")
                db.execute("""UPDATE llm_spend SET actual_usd=?,status='settled'
                    WHERE request_id=?""", (actual_usd, request_id))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def monthly_committed_usd(self, now: datetime | None = None) -> float:
        with self._connect() as db:
            row = db.execute("""
                SELECT COALESCE(SUM(CASE WHEN status='reserved'
                    THEN reserved_usd ELSE actual_usd END),0)
                FROM llm_spend WHERE month_utc=?
            """, (self._month(now),)).fetchone()
            return float(row[0])
