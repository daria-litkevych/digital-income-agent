"""Append-only, provenance-aware store for public research leads.

Discovery leads are never upgraded to validated evidence automatically.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
DISCOVERY_CONFIDENCE = "Unverified"


def canonicalize_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 4000:
        raise ValueError("A bounded source URL is required.")
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("Only absolute HTTP(S) source URLs are supported.")
    if parts.username or parts.password:
        raise ValueError("Credentials are not allowed in evidence URLs.")
    host = parts.hostname.lower().rstrip(".")
    port = parts.port
    netloc = host if port is None or (parts.scheme.lower(), port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKING_KEYS and not k.lower().startswith("utm_")]
    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query, doseq=True), ""))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def discovery_record(item: dict[str, Any], *, checked_at: str | None = None) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("A discovery item must be an object.")
    url = canonicalize_url(item.get("link", ""))
    title = str(item.get("title") or "").strip()[:500]
    description = str(item.get("description") or "").strip()[:3000]
    if not title:
        raise ValueError("A source title is required.")
    checked = checked_at or datetime.now(timezone.utc).isoformat()
    content_hash = _digest(title + "\n" + description)
    return {
        "evidence_id": _digest(url + "\n" + content_hash),
        "claim": "Discovery lead only; inspect source before extracting a claim.",
        "title": title,
        "source_url": url,
        "source_type": "discovery_signal",
        "publisher_interest": "unknown",
        "published_at": item.get("published_date") or item.get("published"),
        "checked_at": checked,
        "segment": item.get("segment", "Unclassified"),
        "hypothesis": item.get("hypothesis"),
        "first_hand": False,
        "pain_signal": None,
        "workaround": None,
        "payment_signal": None,
        "confidence": DISCOVERY_CONFIDENCE,
        "evidence_status": "unreviewed",
        "content_sha256": content_hash,
        "limitations": [
            "News/RSS discovery signal only",
            "Publisher page has not been independently inspected by this record",
            "No customer demand or willingness-to-pay inference is permitted",
        ],
    }


class EvidenceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "records": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("records"), list):
            raise ValueError("Evidence store has an unsupported or invalid structure.")
        return data

    def ingest_discovery(self, items: list[dict[str, Any]], *, checked_at: str | None = None) -> dict[str, int]:
        data = self._load()
        by_id = {record.get("evidence_id"): record for record in data["records"]}
        added = 0
        for item in items:
            record = discovery_record(item, checked_at=checked_at)
            if record["evidence_id"] not in by_id:
                by_id[record["evidence_id"]] = record
                added += 1
        data["records"] = sorted(by_id.values(), key=lambda row: (row.get("checked_at") or "", row.get("evidence_id") or ""))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.path)
        return {"added": added, "total": len(data["records"])}

    def enrich_source(self, evidence_id: str, fetched: dict[str, Any]) -> dict[str, Any]:
        """Attach a bounded, hash-addressed source excerpt without grading its claims."""
        if not isinstance(evidence_id, str) or len(evidence_id) != 64:
            raise ValueError("A valid evidence ID is required.")
        if not isinstance(fetched, dict):
            raise ValueError("Fetched source data must be an object.")
        data = self._load()
        record = next((row for row in data["records"] if row.get("evidence_id") == evidence_id), None)
        if record is None:
            raise ValueError("Evidence record was not found.")
        requested_url = canonicalize_url(fetched.get("requested_url", ""))
        returned_url = canonicalize_url(fetched.get("url", ""))
        stored_url = canonicalize_url(record.get("source_url", ""))
        if requested_url != stored_url or returned_url != stored_url:
            raise ValueError("Fetched source URL does not match the stored evidence record.")
        content_type = fetched.get("content_type")
        if content_type not in {"text/html", "application/xhtml+xml", "text/plain", "application/xml", "text/xml", "application/rss+xml"}:
            raise ValueError("Fetched source content type is not allowed.")
        text = fetched.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 12000:
            raise ValueError("Fetched source text is empty or exceeds the configured limit.")
        retrieved_at = fetched.get("retrieved_at")
        if not isinstance(retrieved_at, str) or len(retrieved_at) > 80:
            raise ValueError("A bounded retrieval timestamp is required.")
        content_hash = _digest(text)
        inspections = record.setdefault("source_inspections", [])
        if not isinstance(inspections, list):
            raise ValueError("Stored source inspection history is invalid.")
        if not any(item.get("content_sha256") == content_hash for item in inspections):
            inspections.append({
                "retrieved_at": retrieved_at,
                "content_type": content_type,
                "content_sha256": content_hash,
                "excerpt": text[:2000],
                "excerpt_truncated": len(text) > 2000,
                "untrusted_source_text": True,
                "review_status": "ungraded",
                "note": "Source retrieval is not independent verification; page content may be incomplete or self-interested.",
            })
        record["evidence_status"] = "source_retrieved_ungraded"
        record["confidence"] = DISCOVERY_CONFIDENCE
        record["limitations"] = list(dict.fromkeys(record.get("limitations", []) + [
            "Public page fetched but claims have not been independently graded",
            "Stored excerpt is untrusted source content and may contain errors or instructions",
        ]))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.path)
        return {"evidence_id": evidence_id, "content_sha256": content_hash, "excerpt_characters": min(len(text), 2000), "review_status": "ungraded"}
