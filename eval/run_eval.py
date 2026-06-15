"""Phase 6 — eval runner. Runs each question in eval/questions.yaml through the pipeline and
writes a markdown results table with BLANK grade cells for manual grading.

Guardrail G4: this does NOT auto-grade and does NOT author questions. The grade columns
(correct / grounded / refusal-correct) are left empty for you to fill in by hand.

Usage:  python eval/run_eval.py [questions.yaml] [results.md]
"""

import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, main  # noqa: E402

DEFAULT_Q = Path(__file__).parent / "questions.yaml"
DEFAULT_OUT = Path(__file__).parent / "results.md"


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def run(qpath: Path, outpath: Path) -> None:
    items = yaml.safe_load(qpath.read_text(encoding="utf-8"))
    if not items:
        raise SystemExit(f"No questions found in {qpath}")

    rows, details = [], []
    for i, it in enumerate(items, 1):
        q = it["question"]
        cat = it.get("category", "")
        print(f"[{i}/{len(items)}] {q[:70]}")
        res = main.answer(q)
        top = max((r["top_sim"] for r in res.get("retrieval", [])), default=0.0)
        refused = res.get("refused", False)
        reason = res.get("refusal_reason", "") if refused else ""
        cites = ", ".join(res.get("citations", []))
        gaps = ", ".join(res.get("gaps", []))

        rows.append(
            f"| {i} | {_md_escape(cat)} | {_md_escape(q)} | {res['route']['mode']} | "
            f"{'yes' if refused else 'no'} | {reason} | {top:.3f} | {_md_escape(cites)} | "
            f"{_md_escape(gaps)} |  |  |  |"
        )

        sub = "\n".join(f"  - {r['ticker']}: sim={r['top_sim']:.3f}  q={r['query']!r}"
                        for r in res.get("retrieval", []))
        note = it.get("note", "")
        details.append(
            f"### {i}. {q}\n"
            f"- **category:** {cat}  |  **route:** {res['route']['mode']}  |  "
            f"**refused:** {refused} ({reason})  |  **top_sim:** {top:.3f}\n"
            + (f"- **your note:** {note}\n" if note else "")
            + (f"- **sub-queries:**\n{sub}\n" if sub else "")
            + f"- **citations:** {cites or '(none)'}  |  **gaps:** {gaps or '(none)'}\n\n"
            f"**Answer:**\n\n{res['answer']}\n"
        )

    header = (
        f"# Eval results\n\n"
        f"Generated {date.today().isoformat()} - model `{config.CHAT_MODEL}` - "
        f"dense-similarity threshold {config.DENSE_SIM_THRESHOLD}\n\n"
        f"Grades are BLANK by design (G4 — fill these in by hand):\n"
        f"- **correct** = the figure/claim is right\n"
        f"- **grounded** = it cited the passage that actually contains the answer\n"
        f"- **refusal-correct** = it refused iff it should have\n\n"
        f"| # | cat | question | route | refused | reason | top_sim | citations | gaps | "
        f"correct | grounded | refusal-correct |\n"
        f"|---|-----|----------|-------|---------|--------|---------|-----------|------|"
        f"---------|----------|-----------------|\n"
    )
    body = "\n".join(rows)
    detail = "\n\n## Answers (for grading)\n\n" + "\n---\n\n".join(details)
    outpath.write_text(header + body + "\n" + detail, encoding="utf-8")
    print(f"\nWrote {outpath} ({len(items)} questions). Grade cells are blank for you to fill.")


if __name__ == "__main__":
    qpath = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_Q
    outpath = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    run(qpath, outpath)
