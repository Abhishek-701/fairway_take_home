"""XBRL fact store — loaded once at import time from data/facts.json.

Provides two query functions used by xbrl_lookup() in main.py:

  query(metric, ticker, period)   -> single fact dict or None
  query_yoy(metric, ticker)       -> (annual_recent_fact, annual_prior_fact) or (None, None)

Both return None on any miss so the caller can fall through to RAG cleanly.

The concept map and keyword map live in config.py (single source of truth).
No bare excepts (G8). No synthetic data (G3).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app import config


@lru_cache(maxsize=1)
def _load_facts() -> list[dict]:
    """Load facts.json once and cache. Returns [] if the file is missing (graceful degradation)."""
    path: Path = config.FACTS_PATH
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _concepts_for(metric: str, ticker: str) -> list[str]:
    """Return the ordered list of XBRL concept strings to try for this metric + ticker."""
    mapping = config.XBRL_CONCEPT_MAP.get(metric, {})
    return mapping.get(ticker, mapping.get("_default", []))


def query(metric: str, ticker: str, period: str = "annual_recent") -> dict | None:
    """Return the best fact for (metric, ticker, period), or None if not found.

    When multiple facts match (duplicate tagging in the filing), the first one is returned
    — values are identical across duplicates for the same context.

    Args:
        metric:  canonical name from XBRL_CONCEPT_MAP, e.g. "revenue", "net_income"
        ticker:  e.g. "AAPL"
        period:  "annual_recent" | "annual_prior" | "annual_2prior"
    """
    concepts = _concepts_for(metric, ticker)
    if not concepts:
        return None

    facts = _load_facts()
    for concept in concepts:
        for f in facts:
            if f["ticker"] == ticker and f["concept"] == concept and f["label"] == period:
                return f
    return None


def query_yoy(metric: str, ticker: str) -> tuple[dict | None, dict | None]:
    """Return (annual_recent, annual_prior) facts for a year-over-year question.

    Either or both may be None if not found in the store.
    """
    return query(metric, ticker, "annual_recent"), query(metric, ticker, "annual_prior")


def query_all_tickers(metric: str, period: str = "annual_recent") -> dict[str, dict | None]:
    """Return {ticker: fact_or_None} for all six companies.

    Used for decompose-mode questions that compare all six companies.
    """
    return {ticker: query(metric, ticker, period) for ticker in config.COMPANIES}
