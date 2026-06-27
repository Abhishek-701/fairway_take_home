"""Deterministic computations over tool evidence."""

from __future__ import annotations

from datetime import UTC, datetime


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _revenue_from_evidence(evidence: list[dict]) -> tuple[str | None, str | None, float | None, str | None]:
    for chunk in evidence:
        if chunk.get("kind") != "xbrl":
            continue
        for fact in chunk.get("facts", []):
            concept = fact.get("concept", "").lower()
            if "revenue" in concept and fact.get("label") == "annual_recent":
                return (
                    chunk.get("ticker"),
                    chunk.get("company"),
                    fact.get("value_scaled"),
                    chunk.get("chunk_id"),
                )
    return None, None, None, None


def _market_cap_from_evidence(evidence: list[dict]) -> tuple[float | None, str | None]:
    for chunk in evidence:
        if chunk.get("kind") == "market":
            market_cap = chunk.get("data", {}).get("market_cap")
            if market_cap is not None:
                return market_cap, chunk.get("chunk_id")
    return None, None


def _compute_chunk(ticker: str, company: str, metric: str, value: float,
                   formula: str, inputs: dict, source_ids: list[str]) -> dict:
    as_of = _now_iso()
    chunk_id = f"{ticker}-CALC-{metric}-{as_of.replace('+00:00', 'Z').replace('-', '').replace(':', '')}"
    text = (
        f"[{company}] Deterministic calculation as of {as_of}. "
        f"Metric: {metric}. Formula: {formula}. Inputs: {inputs}. "
        f"Result: {value:.4f}. Source chunks: {', '.join(source_ids)}."
    )
    return {
        "chunk_id": chunk_id,
        "ticker": ticker,
        "company": company,
        "item": "Calculation",
        "section_title": "Deterministic Metric",
        "filing_date": as_of,
        "fused_score": 1.0,
        "text": text,
        "kind": "compute",
        "data": {"metric": metric, "value": value, "formula": formula, "inputs": inputs,
                 "source_ids": source_ids},
    }


def compute_metric(metric: str, inputs: dict | None = None, evidence: list[dict] | None = None,
                   **_: object) -> dict:
    """Compute small ratios from explicit inputs.

    The agent only calls this when structured inputs are already available. It
    does not parse model prose or filing text.
    """
    inputs = inputs or {}
    evidence = evidence or []
    if metric == "market_cap_to_revenue":
        ticker, company, evidence_revenue, revenue_source = _revenue_from_evidence(evidence)
        evidence_market_cap, market_source = _market_cap_from_evidence(evidence)
        market_cap = inputs.get("market_cap", evidence_market_cap)
        revenue = inputs.get("revenue", evidence_revenue)
        if market_cap is None or revenue in (None, 0):
            return {"status": "missing_input", "data": {}, "evidence": []}
        ratio = market_cap / revenue
        source_ids = [sid for sid in [market_source, revenue_source] if sid]
        chunk = _compute_chunk(
            ticker or "CALC",
            company or "Computed Metric",
            metric,
            ratio,
            "market_cap / annual_revenue",
            {"market_cap": market_cap, "annual_revenue": revenue},
            source_ids,
        )
        return {"status": "ok", "data": chunk["data"], "evidence": [chunk]}
    return {"status": "unsupported", "data": {"metric": metric}, "evidence": []}
