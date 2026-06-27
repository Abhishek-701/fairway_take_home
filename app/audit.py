"""Append-only audit log for answers and evidence lineage."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app import config


def record(event: dict) -> None:
    config.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"created_at": datetime.now(UTC).replace(microsecond=0).isoformat(), **event}
    with config.AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")


def status() -> dict:
    return {"path": str(config.AUDIT_LOG_PATH), "exists": config.AUDIT_LOG_PATH.exists()}
