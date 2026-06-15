# DECISIONS.md

A running log of every meaningful decision made while building this system — the why, the tradeoffs, and what broke along the way. Read this alongside the code, not instead of it.

---

## The pipeline

The core design is a deterministic pipeline, not an agent:

```
question → router → [XBRL fast path] → [decompose] → hybrid retrieval → threshold gate → synthesize
```

I chose a pipeline over an agent because the corpus is closed and fixed. An agent would add nondeterminism and debugging complexity for no real benefit. The downside is that the system can't autonomously recover from a bad retrieval — but that's exactly what the eval and manual grading are for.

---

## Core decisions

**Pipeline over agent.** Closed six-doc corpus doesn't need autonomous tool use. Every step is debuggable and deterministic. The cost is that bad retrievals surface as wrong answers rather than being caught and retried.

**Regex router over LLM router.** The router uses a regex/alias map with no LLM call. The same question always routes the same way and every branch is explainable in a walkthrough. The cost is brittleness on unlisted aliases and unusual phrasing — a deliberate tradeoff for determinism.

**Two-gate refusal.** A single threshold can't handle both cases:
- Gate 1 (out-of-corpus): if the top chunk's dense cosine similarity is below 0.50, refuse. This catches "Tesla's revenue" and "Amazon's net income."
- Gate 2 (in-corpus but undisclosed): if retrieval returns good in-corpus chunks but synthesis finds no figure, Claude says "not found" and the company appears in the gaps list. This catches "Coca-Cola's attrition rate" and "JPMorgan's NPS."

The threshold sits on normalized dense similarity, not the RRF score — RRF is rank-based and has no absolute meaning, so you can't threshold on it.

**XBRL fast path over RAG for numeric lookups.** The 10-K HTML files embed XBRL tags (`ix:nonFraction`) for every tagged financial figure. For known metrics (revenue, net income, EPS, R&D, provision for credit losses, operating cash flow, operating income), reading the tag directly is more reliable than retrieving a table chunk — no retrieval noise, no serialization errors, period and scale are machine-readable. Facts are formatted as synthetic chunks using the same schema as RAG chunks, so synthesis and citation logic is unchanged. The fast path runs before retrieval; a miss falls through to RAG.

**Hybrid retrieval (BM25 + dense + RRF).** BM25 catches exact line-item terms ("provision for credit losses"); dense catches paraphrase and semantic intent. Reciprocal rank fusion blends them without needing a calibrated cross-scorer. Company metadata filtering happens before fusion to avoid returning chunks from the wrong filing.

**Cross-encoder reranker (optional).** `ms-marco-MiniLM-L-6-v2` over the top-30 fused candidates surfaces buried table rows above prose. It's toggleable (`USE_RERANKER` in config) because it pulls a heavy `torch` dependency. The tradeoff: net positive on recall, but phrasing-sensitive — the same consolidated row can win or lose depending on how the question is worded.

**Claude Sonnet 4.6, not Opus 4.8.** The system requires `temperature=0` everywhere for determinism. Opus 4.8/4.7 removed the `temperature` parameter entirely — passing it returns HTTP 400. Sonnet 4.6 accepts it and is well-suited to the extractive decomposition + synthesis task. It's also cheaper.

**OpenAI embeddings, Anthropic for chat.** Anthropic has no embeddings API, so `text-embedding-3-small` fills that role. Two API keys are needed as a result.

---

## Filings

Fetched from SEC EDGAR on 2026-06-10. All are exact 10-K filings (no amendments).

| Ticker | Company        | Accession            | Filed      | Fiscal year end |
|--------|----------------|----------------------|------------|-----------------|
| AAPL   | Apple          | 0000320193-25-000079 | 2025-10-31 | 2025-09-27      |
| JPM    | JPMorgan Chase | 0001628280-26-008131 | 2026-02-13 | 2025-12-31      |
| WMT    | Walmart        | 0000104169-26-000055 | 2026-03-13 | 2026-01-31      |
| KO     | Coca-Cola      | 0001628280-26-010047 | 2026-02-20 | 2025-12-31      |
| NVDA   | NVIDIA         | 0001045810-26-000021 | 2026-02-25 | 2026-01-25      |
| CAT    | Caterpillar    | 0000018230-26-000008 | 2026-02-13 | 2025-12-31      |

The different fiscal year ends (Apple in September, NVIDIA/Walmart in January, others in December) matter for any cross-company comparison — answers must label the period alongside each figure.

---

## Build log

### Ingest (Phase 1–2)

Fetching from EDGAR directly was cleaner than working from saved copies — EDGAR files are real Inline XBRL HTML with no viewer-injected CSS noise. The CSS-residue stripping in `parse.py` is kept defensively but rarely triggers.

The trickiest part of parsing was tables. The approach:
- Expand colspan/rowspan into a dense grid so every row has the same width and values stay aligned to their column headers. Stripping `$`/`%` marker cells was the key bug fix — removing them naively caused numbers to drift off their year columns.
- Header zone = leading rows with no magnitude cell. Years and dates are column headers, not values.
- Serialize each data row as a self-contained string: `"section | label | year = value"` — so a chunk can be read in isolation without the surrounding table structure.
- Prepend the table's caption (the prose line just above it in the HTML) to the chunk text. This was added after an early test where "net sales by region for Apple" returned nothing — the table existed but was unretrievable because its text contained no words like "segment" or "region." The caption line carries exactly those words.
- Prepend `Consolidated` or `Segment-level` to every table row, inferred from the table caption. This was added after finding that Walmart's U.S.-segment "Total revenues" ($485,599M) and its consolidated "Total revenues" ($713,163M) were indistinguishable to the retrieval and synthesis steps. With the scope prefix, they're not.

Footnotes immediately following a table ride along in the same chunk so qualifiers aren't separated from the figures they qualify.

Prose chunks are ~800 tokens with 100-token overlap, flushed at Item boundaries so a chunk never straddles two Items. Tables are kept whole; if a table exceeds 1,000 tokens it's split by rows with the header line repeated on each piece.

### Retrieval and threshold calibration (Phase 3)

Initial top-k was 4 per sub-query for decomposed questions. That was too low — in a six-company fan-out, consolidated income-statement chunks for companies like Walmart ranked 17–30 and fell outside the window. Raised to 8 per sub-query.

The refusal threshold was set at 0.50 based on four calibration probes: NVIDIA revenue (0.697), R&D sub-queries (0.61–0.71), Coca-Cola attrition (0.503, in-corpus), Tesla revenue (0.487, out-of-corpus). The margin between in-corpus and out-of-corpus is thin — ~0.016 at the narrowest point. This is a known weakness.

One bug: the Gate 1 condition is `< 0.50` (strict), not `<= 0.50`. Amazon's query hit exactly 0.500 and slipped through to Gate 2. Gate 2 caught it correctly, but the off-by-one means the threshold doesn't behave as intended at the boundary. Not yet fixed.

### First eval failures and fixes (Phase 3–5, 9 questions)

The first eval caught two real failures:

**Q3 — wrong winner in "highest revenue" comparison.** The system said JPMorgan ($185,581M) when Walmart ($713,163M) is clearly highest. The consolidated Walmart chunk ranked ~17 in its sub-query and was trimmed by the global context cap. The model maxed over what it could see.

**Q5 — wrong Walmart revenue.** Returned $485,599M (U.S. segment) instead of $713,163M (consolidated). Both rows say "Total revenues" — retrieval couldn't distinguish them before the scope label was added.

Fixes applied in order:
1. Raised top-k sub from 4 to 8 — helped Q3 partially.
2. Added cross-encoder reranker — fixed Q5 (consolidated chunk surfaced), Q3 still wrong (phrasing-sensitive).
3. Added scope prefix at parse time — fixed Q5 permanently and moved the root cause of Q3 from a concept error to a context-budget problem. The correct Walmart chunk now ranks ~8 but the 24-chunk global cap still trims it in a six-company decompose.

Q3 is still not perfectly reliable for six-company comparisons that don't hit the XBRL fast path. The fix is per-sub-query budget allocation instead of a single global fused-score sort.

### Router bug (found via eval Q17)

"What was Amazon's net income for its **most recent** fiscal year?" was routing to `decompose` instead of `oos` because "most" in "most recent" matched `SUPERLATIVE_RE`. Fixed with a negative lookahead: `most(?!\s+recent)`. After the fix, Amazon correctly routes as out-of-corpus, retrieves nothing relevant, and Gate 2 produces a clean refusal.

### XBRL fast path (Phase 5–6)

Added `ingest/xbrl.py` to extract inline XBRL tags into `data/facts.json`, and `xbrl_lookup()` in `app/main.py` to check them before retrieval. Eight metric patterns are covered. Year-over-year questions retrieve both years. Multi-metric questions (e.g. "cash flow vs net income") collect all matching patterns and deduplicate.

The segment bail-out is a hardcoded allowlist of known segment names that should fall through to RAG. This is the root cause of the deliberate failure in Q24 (NVIDIA Data Center) — "revenue" matches before "Data Center" is checked. Claude says the segment figure is not found, which is honest, but the figure is in Item 8 and never reached. The fix is either a compound-noun heuristic or a classifier call.

### Multi-statement compound-query failure (found via eval Q21–Q23)

Questions asking for two metrics from different financial statements (e.g. "dividends paid and income tax provision") expose a structural retrieval problem: a single embedding for a compound question averages both intents, and the dominant intent fills the top-k slots, crowding out the second statement's chunk.

Evidence: WMT-0107 (shareholders' equity, balance sheet) ranks #1 with top_sim=0.782 in an isolated equity-only probe, but is not in the top-6 when the question also asks about share repurchases. The repurchase intent dominates and exhausts the budget.

The fix is to detect two distinct metric phrases in the question, issue two sub-queries, and merge the retrieval pools before synthesis. Not yet applied.

### AAPL-0068 ingest bug (found via eval Q21)

The "Purchases of property, plant and equipment" row (capital expenditures) is absent from the serialized Apple CFS chunk. Only marketable-security rows and a net "Other" investing total appear. The row is in the raw HTML; it didn't survive `expand_grid()` / `serialize_table()`, likely due to a colspan/rowspan in Apple's investing activities layout. Apple capex is unretrievable until this is patched.

---

## Known weaknesses

1. **Complex table serialization isn't exhaustive.** Multi-level headers and unusual colspan layouts can cause rows to serialize incorrectly or be dropped entirely (see AAPL-0068). Verified by sampling, not comprehensively.

2. **Footnote linkage is local.** A footnote marker like `[1]` is kept in the chunk text, but there's no graph linking it to the note that defines it. A figure with a material qualifier elsewhere in the filing can be returned without that qualifier.

3. **Segment vs. consolidated confusion.** Largely fixed by the scope prefix, but the XBRL fast path can still return a consolidated figure for a segment question if the segment name isn't in `_SEGMENT_BAIL_RE`. Q24 is the live example.

4. **Router is brittle on aliases and phrasing.** Regex routing is fast and explainable, but it misses unlisted aliases and unusual question phrasings. A temp-0 LLM router would close this.

5. **Refusal threshold is a single global value.** Calibrated on ~8 probes with thin margins. A generic metric for an out-of-corpus company can score above 0.50 because in-corpus chunks match the metric term. Per-query-type thresholds or a cross-encoder gate would help.

6. **Compound-query retrieval failure.** Single-embedding queries for two metrics systematically miss one of the two statements. See Q21–Q23.

---

## What's next (priority order)

1. **Fix the compound-query failure** — detect two metric phrases, issue two sub-queries, merge pools.
2. **Fix Gate 1 off-by-one** — `<` → `<=` in `app/main.py:160`.
3. **Fix AAPL-0068 ingest bug** — patch the CFS table serializer for Apple's colspan layout.
4. **Extend `_SEGMENT_BAIL_RE`** — add NVIDIA segment names ("Data Center", "Compute & Networking") so Q24-style questions fall through to RAG.
5. **LLM router** — replace regex routing with a temp-0 Haiku call for alias/phrasing robustness.
6. **Per-query-type threshold calibration** — or move the refusal gate onto the cross-encoder score.
7. **Footnote reference graph** — link `[fn1]` markers to their note text globally, not just locally.
8. **Harden the reranker** — it's phrasing-sensitive; explore a finance-tuned cross-encoder.
