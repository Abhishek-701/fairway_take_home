import unittest

from app import corpus, research, router
from app.tools.compute import compute_metric


class OfflineProductTests(unittest.TestCase):
    def test_xbrl_only_question_short_circuits_rag_plan(self):
        question = "What was NVIDIA's total revenue?"
        plan = research.plan(question, router.route(question))
        tools = [action["tool"] for action in plan["actions"]]
        self.assertIn("facts_lookup", tools)
        self.assertNotIn("filing_rag", tools)

    def test_segment_question_uses_rag_not_xbrl(self):
        question = "What was NVIDIA's Data Center segment revenue?"
        plan = research.plan(question, router.route(question))
        tools = [action["tool"] for action in plan["actions"]]
        self.assertNotIn("facts_lookup", tools)
        self.assertIn("filing_rag", tools)

    def test_hybrid_question_plans_market_and_compute(self):
        question = "Compare Apple's current market cap to its latest reported revenue."
        plan = research.plan(question, router.route(question))
        tools = [action["tool"] for action in plan["actions"]]
        self.assertIn("facts_lookup", tools)
        self.assertIn("market_quote", tools)
        self.assertIn("compute_metric", tools)

    def test_compute_metric_emits_citable_evidence(self):
        evidence = [
            {
                "kind": "xbrl",
                "ticker": "AAPL",
                "company": "Apple",
                "chunk_id": "AAPL-XBRL-Revenue",
                "facts": [{"concept": "us-gaap:Revenues", "label": "annual_recent",
                           "value_scaled": 400_000_000_000}],
            },
            {
                "kind": "market",
                "chunk_id": "AAPL-MKT-TEST",
                "data": {"market_cap": 4_000_000_000_000},
            },
        ]
        result = compute_metric("market_cap_to_revenue", evidence=evidence)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["value"], 10)
        self.assertEqual(result["evidence"][0]["kind"], "compute")

    def test_corpus_status_has_version(self):
        status = corpus.status()
        self.assertIn("corpus_version", status)
        self.assertIn("manifest_count", status)


if __name__ == "__main__":
    unittest.main()
