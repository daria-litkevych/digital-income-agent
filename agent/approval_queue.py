"""Persistent human-approval queue for external side effects.

The queue records requests and one-time approvals. It never performs the
underlying action; a separately reviewed executor must consume an approved
request and re-check its payload hash immediately before acting.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ALLOWED_ACTIONS = {
    "publish", "deploy", "send_message", "send_email", "purchase",
    "change_billing", "change_account", "public_commit", "submit_listing",
}
FORBIDDEN_SECRET_MARKERS = ("api_key", "password", "token", "secret", "authorization", "private_key", "credential")


class ApprovalError(RuntimeError):
    pass


def _utc(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("Approval timestamps must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _reject_secrets(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = "".join(char for char in str(key).lower() if char.isalnum() or char == "_")
            if any(marker in normalized_key for marker in FORBIDDEN_SECRET_MARKERS):
                raise ApprovalError("Secrets and credentials must never be stored in approval requests.")
            _reject_secrets(child)
    elif isinstance(value, list):
        for child in value:
            _reject_secrets(child)


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ApprovalQueue:
    def __init__(self, path: str | Path, *, max_pending: int = 20, max_ttl_hours: int = 168):
        self.path = Path(path)
        if max_pending < 1 or max_pending > 100:
            raise ValueError("max_pending must be between 1 and 100")
        if max_ttl_hours < 1 or max_ttl_hours > 168:
            raise ValueError("max_ttl_hours must be between 1 and 168")
        self.max_pending = max_pending
        self.max_ttl_hours = max_ttl_hours

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"requests": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ApprovalError("Approval queue cannot be read safely.") from error
        if not isinstance(data, dict) or not isinstance(data.get("requests"), dict):
            raise ApprovalError("Approval queue has an invalid structure.")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        os.replace(temp, self.path)

    def request(self, action_type: str, description: str, payload: dict[str, Any], *, now: datetime | None = None, ttl_hours: int = 24) -> dict[str, Any]:
        if action_type not in ALLOWED_ACTIONS:
            raise ApprovalError("Unknown external action type.")
        if not isinstance(description, str) or not description.strip() or len(description) > 1000:
            raise ApprovalError("A concise action description is required.")
        if not isinstance(payload, dict):
            raise ApprovalError("Action payload must be a JSON object.")
        _reject_secrets(payload)
        try:
            _payload_hash(payload)
        except (TypeError, ValueError) as error:
            raise ApprovalError("Action payload must contain only JSON-safe values.") from error
        if ttl_hours < 1 or ttl_hours > self.max_ttl_hours:
            raise ApprovalError("Approval expiry exceeds the configured limit.")
        timestamp = _utc(now)
        data = self._load()
        pending = [item for item in data["requests"].values() if item.get("status") == "pending"]
        if len(pending) >= self.max_pending:
            raise ApprovalError("Pending approval queue is full.")
        request_id = str(uuid4())
        record = {
            "id": request_id,
            "action_type": action_type,
            "description": description.strip(),
            "payload": payload,
            "payload_sha256": _payload_hash(payload),
            "status": "pending",
            "created_at": timestamp.isoformat(),
            "expires_at": (timestamp + timedelta(hours=ttl_hours)).isoformat(),
            "approved_by": None,
            "consumed_at": None,
        }
        data["requests"][request_id] = record
        self._save(data)
        return dict(record)

    def approve(self, request_id: str, *, approved_by: str, expected_payload_sha256: str, now: datetime | None = None) -> dict[str, Any]:
        if not isinstance(approved_by, str) or not approved_by.strip():
            raise ApprovalError("Approver identity is required.")
        data = self._load()
        record = data["requests"].get(request_id)
        if not record:
            raise ApprovalError("Approval request was not found.")
        if record.get("status") != "pending":
            raise ApprovalError("Only pending requests can be approved.")
        if _utc(now) >= datetime.fromisoformat(record["expires_at"]):
            record["status"] = "expired"
            self._save(data)
            raise ApprovalError("Approval request has expired.")
        current_hash = _payload_hash(record["payload"])
        if current_hash != record.get("payload_sha256") or expected_payload_sha256 != current_hash:
            raise ApprovalError("Payload changed or approval hash does not match.")
        record["status"] = "approved"
        record["approved_by"] = approved_by.strip()
        record["approved_at"] = _utc(now).isoformat()
        self._save(data)
        return dict(record)

    def reject(self, request_id: str, *, rejected_by: str, reason: str = "") -> dict[str, Any]:
        data = self._load()
        record = data["requests"].get(request_id)
        if not record or record.get("status") != "pending":
            raise ApprovalError("Only an existing pending request can be rejected.")
        if not isinstance(rejected_by, str) or not rejected_by.strip():
            raise ApprovalError("Rejector identity is required.")
        record["status"] = "rejected"
        record["rejected_by"] = rejected_by.strip()
        if not isinstance(reason, str):
            raise ApprovalError("Rejection reason must be text.")
        record["rejection_reason"] = reason[:500]
        self._save(data)
        return dict(record)

    def consume(self, request_id: str, payload: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
        data = self._load()
        record = data["requests"].get(request_id)
        if not record or record.get("status") != "approved":
            raise ApprovalError("A current approved request is required before an external action.")
        timestamp = _utc(now)
        if timestamp >= datetime.fromisoformat(record["expires_at"]):
            record["status"] = "expired"
            self._save(data)
            raise ApprovalError("Approval has expired.")
        _reject_secrets(payload)
        try:
            actual_hash = _payload_hash(payload)
            stored_hash = _payload_hash(record["payload"])
        except (TypeError, ValueError, KeyError) as error:
            raise ApprovalError("Action payload is not valid JSON data.") from error
        if actual_hash != record.get("payload_sha256") or stored_hash != record.get("payload_sha256"):
            raise ApprovalError("Action payload does not match the approved payload.")
        record["status"] = "consumed"
        record["consumed_at"] = timestamp.isoformat()
        self._save(data)
        return {"request_id": request_id, "action_type": record["action_type"], "payload": record["payload"], "approved_by": record["approved_by"], "consumed": True}

    def list_requests(self) -> list[dict[str, Any]]:
        data = self._load()
        return sorted(data["requests"].values(), key=lambda item: item.get("created_at", ""))