"""Plan incremental corpus refreshes from a target manifest.

This module intentionally does not download in-process. It compares a target
manifest with the current committed manifest and reports which tickers need the
existing download/parse/chunk/embed pipeline to run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_MANIFEST = ROOT / "data" / "manifest.json"


def _load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    items = json.loads(path.read_text(encoding="utf-8"))
    return {item["ticker"]: item for item in items}


def plan_refresh(target_manifest: Path, current_manifest: Path = CURRENT_MANIFEST) -> dict:
    current = _load(current_manifest)
    target = _load(target_manifest)
    added, changed, unchanged = [], [], []
    for ticker, target_item in target.items():
        current_item = current.get(ticker)
        if not current_item:
            added.append(ticker)
        elif current_item.get("accession") != target_item.get("accession"):
            changed.append(ticker)
        else:
            unchanged.append(ticker)
    removed = [ticker for ticker in current if ticker not in target]
    return {"added": added, "changed": changed, "removed": removed, "unchanged": unchanged}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python ingest/incremental.py target_manifest.json")
    print(json.dumps(plan_refresh(Path(sys.argv[1])), indent=2))
