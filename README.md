# FinSight

A financial analysis agent over the most recent 10-K filings of **Apple, JPMorgan Chase, Walmart, Coca-Cola, NVIDIA, and Caterpillar**. Answers filing questions with cited passages, mixes in live market data, and returns an inspectable tool trace.

## Pipeline

```
question
  → router          (regex/alias, no LLM)         single | decompose | out-of-corpus | clarify
  → xbrl_lookup     (fact store, no LLM)           XBRL fast path: returns answer if metric found
       ↓ miss only
  → [decompose]     (one temp-0 Claude call)       one self-contained sub-query per company
  → hybrid retrieve (BM25 + dense embeddings, RRF) + optional cross-encoder rerank
  → threshold gate  (dense cosine sim of top chunk)  refuse if out-of-corpus
  → synthesize      (temp-0 Claude, streamed)       grounded answer, inline [chunk_id] citations
```

The FastAPI app wraps this deterministic core in a lightweight research orchestration layer: `plan → act → reflect`. The plan selects bounded tool actions (`facts_lookup`, `filing_rag`, `multi_company_compare`, `market_quote`, `synthesize_report`); the tool trace and reflection are returned with each response.

**XBRL fast path:** before touching RAG, the system checks a structured fact store extracted from inline XBRL tags in the 10-K HTML files. Known numeric metrics (revenue, operating income, net income, EPS, R&D, operating cash flow, etc.) are returned directly with no LLM call. RAG runs only on a miss.

Three refusal layers: a **retrieval threshold** (out-of-corpus questions score low on cosine similarity), a **synthesis gaps gate** (in-corpus but undisclosed facts), and a **synthesis-level OOS guard** (system prompt explicitly declines for any company outside the six).

## Prerequisites

- **Python 3.11+**
- **Two API keys** (set in `.env`):
  - `OPENAI_API_KEY` — embeddings only (`text-embedding-3-small`)
  - `ANTHROPIC_API_KEY` — chat model (`claude-sonnet-4-6`) for decomposition and synthesis
- **Optional**:
  - `FINSIGHT_API_KEY` — require `x-api-key` on expensive endpoints when set
  - `FINSIGHT_RATE_LIMIT_PER_MINUTE` — simple per-IP rate limit (default: 60)

Embedding the full corpus costs well under $0.05. Each question is a fraction of a cent in embeddings plus one or two Claude calls. XBRL extraction is local with no API calls.

## Setup

```bash
git clone https://github.com/Abhishek-701/FinSight.git
cd FinSight

python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in OPENAI_API_KEY and ANTHROPIC_API_KEY
```

> The reranker pulls `sentence-transformers` + `torch` (large download). Set `USE_RERANKER = False` in `app/config.py` to skip it.

## Ingest

Run once; outputs are cached and reproducible.

```bash
python ingest/download.py   # fetch 6 latest 10-Ks from SEC EDGAR → data/raw/, data/manifest.json
python ingest/parse.py      # HTML → ordered prose/table blocks → data/parsed/
python ingest/chunk.py      # blocks → retrieval chunks → data/chunks.json
python ingest/embed.py      # embed chunks → Chroma at data/chroma/
python ingest/xbrl.py       # parse inline XBRL tags → data/facts.json
python ingest/validate.py   # OPTIONAL: section coverage, CSS residue, table alignment report
```

`download.py` rate-limits and caches — it won't re-fetch files already in `data/raw/`. `data/` is gitignored except `data/manifest.json`; `data/facts.json` is regenerated from the raw HTML.

## Run

```bash
python -m uvicorn app.main:app --port 8000
# open http://127.0.0.1:8000
```

API endpoints:

| Endpoint | Description |
|---|---|
| `GET /api/stream?q=...` | Streams answer tokens then finishes with citations, gaps, plan, and tool trace |
| `GET /api/research?q=...` | Full structured result in one JSON response |
| `POST /api/chat` | `{ "message": "...", "session_id": null, "stream": false }` — preferred product endpoint |
| `GET /api/sessions/{session_id}` | Stored chat messages |
| `GET /api/quote/{ticker}` | Live yfinance quote |
| `GET /api/companies` | Supported tickers |
| `GET /api/corpus/status` | Corpus health |
| `GET /health` | Deployment health check |

`POST /api/chat` uses session history to resolve follow-ups. Answer metadata is appended to `data/audit.jsonl`.

Or run four checkpoint questions from the CLI:

```bash
python -m app.main
```

## Evaluate

```bash
# filing regression suite
python eval/run_eval.py

# offline unit tests (no LLM calls)
python -m unittest discover -s tests

# market and hybrid suites
python eval/run_eval.py eval/questions_market.yaml eval/results_market.md eval/results_market.json
python eval/run_eval.py eval/questions_hybrid.yaml eval/results_hybrid.md eval/results_hybrid.json
```

Offline tests cover planner short-circuiting, segment routing, compute evidence, and corpus status. Questions are hand-written in `eval/questions.yaml`.

## Configuration

All tunables are in `app/config.py`: chat model, retrieval `top_k`, RRF constant, refusal threshold, context cap, reranker toggle, XBRL maps, market cache TTLs, agent step cap, and API/rate-limit settings.

## Repo layout

```
ingest/   download.py  parse.py  chunk.py  embed.py  xbrl.py  validate.py  incremental.py
app/      main.py      research.py  audit.py  corpus.py  config.py
          agent/       (executor, router, context, session store)
          tools/       (filings, market, compute, registry)
          router.py  retrieve.py  decompose.py  facts.py  synthesize.py  rerank.py
eval/     questions.yaml  run_eval.py  results.md
static/   index.html
tests/    offline unit tests
data/     raw/  parsed/  chunks.json  facts.json  chroma/  manifest.json
```
