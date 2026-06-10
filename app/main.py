"""Phase 3 — pipeline orchestration: router -> [decompose] -> hybrid retrieval -> threshold gate
-> synthesis with citations. Deterministic; no agent (see DECISIONS.md).

Run the four checkpoint questions:  python -m app.main
(FastAPI/SSE endpoint is added to this file in Phase 4.)
"""

import json
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse

from app import config, decompose, retrieve, router, synthesize

CITATION_RE = re.compile(r"\[([A-Z]{2,4}-\d{3,4})\]")

CLARIFY_MSG = ("I can only answer about Apple, JPMorgan Chase, Walmart, Coca-Cola, NVIDIA, and "
               "Caterpillar. Which company do you mean?")


def _refusal(reason: str, msg: str, meta: dict) -> dict:
    return {"answer": msg, "citations": [], "gaps": [], "refused": True,
            "refusal_reason": reason, **meta}


def prepare(question: str) -> dict:
    """Route, retrieve, and apply the threshold gate. Returns everything except the synthesized
    answer (so the caller can stream it). Sets refused=True for the two non-synthesis paths."""
    r = router.route(question)
    mode, tickers = r["mode"], r["tickers"]
    meta = {"route": r, "sub_queries": [], "retrieval": []}

    if mode == "clarify":
        return _refusal("clarify", CLARIFY_MSG, meta)

    # Build sub-queries.
    if mode == "decompose":
        subs = decompose.decompose(question, tickers)
    elif mode == "single":
        subs = [{"ticker": tickers[0], "query": question}]
    else:  # oos — unfiltered retrieval, let the threshold decide
        subs = [{"ticker": None, "query": question}]
    meta["sub_queries"] = subs

    # Retrieve per sub-query.
    k = config.TOP_K_SINGLE if mode in ("single", "oos") else config.TOP_K_SUB
    all_chunks: dict[str, dict] = {}
    top_sims = []
    for s in subs:
        res = retrieve.retrieve(s["query"], [s["ticker"]] if s["ticker"] else None, k)
        top_sims.append(res["top_sim"])
        meta["retrieval"].append({"ticker": s["ticker"], "query": s["query"],
                                  "top_sim": round(res["top_sim"], 3),
                                  "chunk_ids": [c["chunk_id"] for c in res["chunks"]]})
        for c in res["chunks"]:
            if c["chunk_id"] not in all_chunks or c["fused_score"] > all_chunks[c["chunk_id"]]["fused_score"]:
                all_chunks[c["chunk_id"]] = c

    # Gate 1 (out-of-corpus): every sub-query's best chunk is below the dense-similarity threshold.
    if top_sims and max(top_sims) < config.DENSE_SIM_THRESHOLD:
        return _refusal(
            "threshold",
            "I couldn't find this in the six filings I cover (Apple, JPMorgan Chase, Walmart, "
            "Coca-Cola, NVIDIA, Caterpillar), so I can't answer it.",
            meta,
        )

    # Assemble bounded context (G12): highest fused score first, cap total chunks.
    chunks = sorted(all_chunks.values(), key=lambda c: c["fused_score"], reverse=True)
    meta["context_chunks"] = chunks[: config.MAX_CONTEXT_CHUNKS]
    meta["refused"] = False
    return meta


def answer(question: str) -> dict:
    """Full (non-streaming) answer for the CLI/eval: runs synthesis and derives citations + gaps."""
    meta = prepare(question)
    if meta.get("refused"):
        return meta
    text = "".join(synthesize.stream_answer(question, meta["context_chunks"]))
    cited = set(CITATION_RE.findall(text))
    # Gate 2 surfaced as gaps: a target company whose chunks were retrieved but never cited.
    cited_tickers = {cid.split("-")[0] for cid in cited}
    gaps = [config.COMPANIES[t] for t in meta["route"]["tickers"] if t not in cited_tickers]
    return {**meta, "answer": text, "citations": sorted(cited), "gaps": gaps, "refused": False}


# --- Phase 4: FastAPI app + SSE streaming endpoint ---
app = FastAPI()

INDEX_HTML = config._ROOT / "static" / "index.html"


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_events(question: str):
    """SSE generator: stream answer tokens, then a 'done' event with citations + gaps."""
    meta = prepare(question)
    if meta.get("refused"):
        yield _sse("token", {"text": meta["answer"]})
        yield _sse("done", {"citations": [], "gaps": [], "refused": True,
                            "refusal_reason": meta["refusal_reason"]})
        return

    ctx = {c["chunk_id"]: c for c in meta["context_chunks"]}
    acc = []
    for t in synthesize.stream_answer(question, meta["context_chunks"]):
        acc.append(t)
        yield _sse("token", {"text": t})

    text = "".join(acc)
    cited = sorted(set(CITATION_RE.findall(text)))
    cited_tickers = {cid.split("-")[0] for cid in cited}
    gaps = [config.COMPANIES[t] for t in meta["route"]["tickers"] if t not in cited_tickers]
    citations = [{
        "chunk_id": cid, "company": ctx[cid]["company"],
        "section": ctx[cid].get("section_title") or ctx[cid].get("item") or "",
        "text": ctx[cid]["text"],
    } for cid in cited if cid in ctx]
    yield _sse("done", {"citations": citations, "gaps": gaps, "refused": False})


@app.get("/")
def index():
    return FileResponse(INDEX_HTML)


@app.get("/api/stream")
def stream(q: str):
    return StreamingResponse(_stream_events(q), media_type="text/event-stream")


def _print(question: str, res: dict) -> None:
    print("\n" + "=" * 78)
    print("Q:", question)
    print("route:", res["route"])
    for r in res.get("retrieval", []):
        print(f"  sub[{r['ticker']}] top_sim={r['top_sim']}  q={r['query'][:60]!r}")
    if res.get("refused"):
        print(f"REFUSED ({res['refusal_reason']}): {res['answer']}")
        return
    print("\nANSWER:\n" + res["answer"])
    print("\ncitations:", res["citations"])
    print("gaps:", res["gaps"])


if __name__ == "__main__":
    questions = [
        "What was NVIDIA's total revenue?",
        "Which of these companies reported the highest R&D spend?",
        "What was Tesla's revenue?",
        "What is Coca-Cola's employee attrition rate?",
    ]
    for q in questions:
        _print(q, answer(q))
