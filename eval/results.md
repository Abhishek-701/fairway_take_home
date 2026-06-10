# Eval results

Generated 2026-06-10 - model `claude-sonnet-4-6` - dense-similarity threshold 0.5

Grades are BLANK by design (G4 — fill these in by hand):
- **correct** = the figure/claim is right
- **grounded** = it cited the passage that actually contains the answer
- **refusal-correct** = it refused iff it should have

| # | cat | question | route | refused | reason | top_sim | citations | gaps | correct | grounded | refusal-correct |
|---|-----|----------|-------|---------|--------|---------|-----------|------|---------|----------|-----------------|
| 1 | lookup | What were Coca-Cola's net operating revenues for fiscal year 2024? | single | no |  | 0.756 | KO-0117 |  |  |  |  |
| 2 | lookup | What were Walmart's total assets at the end of its most recent fiscal year? | single | no |  | 0.678 | WMT-0063, WMT-0185 |  |  |  |  |
| 3 | comparison | Which of these companies reported the highest total revenue in its most recent fiscal year, and what were the figures? | decompose | no |  | 0.716 | CAT-0114, JPM-0220, KO-0280, NVDA-0178, WMT-0070 | Apple |  |  |  |
| 4 | units | What was Apple's diluted weighted-average share count for fiscal 2025? | single | no |  | 0.694 | AAPL-0059, AAPL-0074 |  |  |  |  |
| 5 | fiscal_year | Compare Walmart's and Coca-Cola's most recent annual total revenue. What period does each figure cover? | decompose | no |  | 0.656 | KO-0280, WMT-0182 |  |  |  |  |
| 6 | footnote | What does NVIDIA's most recent 10-K disclose about customer concentration, and what portion of revenue did its largest customer(s) represent? | single | no |  | 0.694 | NVDA-0071, NVDA-0178 |  |  |  |  |
| 7 | precision | What was Caterpillar's total sales and revenues, and separately its profit (net income), for 2024? | single | no |  | 0.716 | CAT-0114, CAT-0117 |  |  |  |  |
| 8 | refusal_oos | What was Microsoft's total revenue in its latest fiscal year? | oos | yes | threshold | 0.454 |  |  |  |  |  |
| 9 | refusal_undisclosed | What is JPMorgan Chase's customer Net Promoter Score (NPS)? | single | no |  | 0.548 |  | JPMorgan Chase |  |  |  |


## Answers (for grading)

### 1. What were Coca-Cola's net operating revenues for fiscal year 2024?
- **category:** lookup  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.756
- **your note:** Income-statement top line. Coca-Cola labels it 'Net operating revenues', not 'Revenue', so this also tests terminology. Record the exact figure + units (millions) from Item 8.
- **sub-queries:**
  - KO: sim=0.756  q="What were Coca-Cola's net operating revenues for fiscal year 2024?"
- **citations:** KO-0117  |  **gaps:** (none)

**Answer:**

Coca-Cola's net operating revenues for fiscal year 2024 were **$47,061 million** [KO-0117].

---

### 2. What were Walmart's total assets at the end of its most recent fiscal year?
- **category:** lookup  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.678
- **your note:** Balance-sheet lookup â€” confirms the system reads statements beyond the income statement. Record the figure + units.
- **sub-queries:**
  - WMT: sim=0.678  q="What were Walmart's total assets at the end of its most recent fiscal year?"
- **citations:** WMT-0063, WMT-0185  |  **gaps:** (none)

**Answer:**

Based on the provided filings, Walmart's total consolidated assets at the end of its most recent fiscal year (January 31, 2026) were **$284,668 million** [WMT-0063][WMT-0185].

---

### 3. Which of these companies reported the highest total revenue in its most recent fiscal year, and what were the figures?
- **category:** comparison  |  **route:** decompose  |  **refused:** False ()  |  **top_sim:** 0.716
- **your note:** Fans out across all six. A correct answer must also state each company's fiscal-year-end, since the periods are not the same. Fill in the six top-line figures from each Item 8 to grade. Watch terminology: Apple 'net sales', Coca-Cola 'net operating revenues', Caterpillar 'total sales and revenues', JPMorgan 'total net revenue'.
- **sub-queries:**
  - AAPL: sim=0.646  q="What was Apple's total revenue in its most recent fiscal year as reported in its 10-K?"
  - JPM: sim=0.716  q="What was JPMorgan Chase's total revenue (net revenue) in its most recent fiscal year as reported in its 10-K?"
  - WMT: sim=0.687  q="What was Walmart's total revenue in its most recent fiscal year as reported in its 10-K?"
  - KO: sim=0.696  q="What was Coca-Cola's total revenue (net revenues) in its most recent fiscal year as reported in its 10-K?"
  - NVDA: sim=0.699  q="What was NVIDIA's total revenue in its most recent fiscal year as reported in its 10-K?"
  - CAT: sim=0.693  q="What was Caterpillar's total revenue (total sales and revenues) in its most recent fiscal year as reported in its 10-K?"
- **citations:** CAT-0114, JPM-0220, KO-0280, NVDA-0178, WMT-0070  |  **gaps:** Apple

**Answer:**

Based on the provided filings, here are the most recent fiscal year total revenues for each company:

- **NVIDIA** (FY ended January 26, 2025... actually January 2026): Not directly stated as a single total revenue figure in the provided chunks, but revenue from international customers was 31% of total [NVDA-0178]. The exact total is not provided in the excerpts given.

- **Apple** (FY ended September 27, 2025): Total revenue figure not directly stated in a summary income statement chunk provided.

- **Walmart** (FY ended January 31, 2026): Total revenues increased $32.2 billion or 4.7% [WMT-0070], but the absolute total is not stated in the provided chunks.

- **Caterpillar** (FY ended December 31, 2025): Total sales and revenues = **$67,589 million** [CAT-0114].

- **JPMorgan Chase** (FY ended December 31, 2025): Total net revenue = **$185,581 million** [JPM-0220].

- **Coca-Cola** (FY ended December 31, 2025): Net operating revenues = **$47,941 million** [KO-0280].

Among the figures available in the provided context, **JPMorgan Chase reported the highest total revenue at $185,581 million** for the fiscal year ended December 31, 2025 [JPM-0220].

---

### 4. What was Apple's diluted weighted-average share count for fiscal 2025?
- **category:** units  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.694
- **your note:** Trap: on Apple's income statement, dollars are in millions but share counts are in THOUSANDS. A system that stamps one 'in millions' label on the whole table is off by 1000x. Verify the scale on the face of the statement and record the correct number + unit.
- **sub-queries:**
  - AAPL: sim=0.694  q="What was Apple's diluted weighted-average share count for fiscal 2025?"
- **citations:** AAPL-0059, AAPL-0074  |  **gaps:** (none)

**Answer:**

Apple's diluted weighted-average share count for fiscal 2025 (fiscal year ended September 27, 2025) was **15,004,697 thousand shares** [AAPL-0074][AAPL-0059].

---

### 5. Compare Walmart's and Coca-Cola's most recent annual total revenue. What period does each figure cover?
- **category:** fiscal_year  |  **route:** decompose  |  **refused:** False ()  |  **top_sim:** 0.656
- **your note:** Walmart's FY ends ~Jan 31, 2025; Coca-Cola's ends Dec 31, 2024. Correct answer must flag that the two figures cover DIFFERENT periods and not present them as the same year. Record both figures.
- **sub-queries:**
  - WMT: sim=0.656  q="What was Walmart's most recent annual total revenue, and what fiscal period does this figure cover?"
  - KO: sim=0.654  q="What was Coca-Cola's most recent annual total revenue, and what fiscal period does this figure cover?"
- **citations:** KO-0280, WMT-0182  |  **gaps:** (none)

**Answer:**

Based on the provided filings:

**Walmart** (fiscal year ended **January 31, 2026**):
Total revenues = **$485,599 million** [WMT-0182]

**Coca-Cola** (fiscal year ended **December 31, 2025**):
Net operating revenues = **$47,941 million** [KO-0280]

Walmart's total revenue is approximately **10x larger** than Coca-Cola's most recent annual revenue. Note that the two figures cover different fiscal periods — Walmart's year ends in late January while Coca-Cola's ends in December — and the companies operate in very different industries (retail vs. beverages), so direct comparison has limited analytical value.

---

### 6. What does NVIDIA's most recent 10-K disclose about customer concentration, and what portion of revenue did its largest customer(s) represent?
- **category:** footnote  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.694
- **your note:** Note/MD&A-driven (concentration of revenue, significant customers). The percentage is meaningless without the surrounding disclosure. VERIFY the exact wording/figure exists in NVIDIA's filing; if phrased differently (e.g. 'one customer accounted for ~X%'), match it. Tests whether the system surfaces the qualifier, not just a bare number.
- **sub-queries:**
  - NVDA: sim=0.694  q="What does NVIDIA's most recent 10-K disclose about customer concentration, and what portion of revenue did its largest customer(s) represent?"
- **citations:** NVDA-0071, NVDA-0178  |  **gaps:** (none)

**Answer:**

## NVIDIA Customer Concentration Disclosure (Fiscal Year 2026, ended January 2026)

### Direct Customer Concentration

NVIDIA's most recent 10-K (filed 2026-02-25) discloses significant revenue concentration among a limited number of customers, and notes that "this trend may continue" [NVDA-0071].

**Fiscal Year 2026:**
- One direct customer represented **22%** of total revenue
- Another direct customer represented **14%** of total revenue
- Both were primarily attributable to the **Compute & Networking segment** [NVDA-0071][NVDA-0178]

**Fiscal Year 2025 (for comparison):**
- One direct customer represented **12%** of total revenue
- Two other direct customers each represented **11%** of total revenue [NVDA-0071][NVDA-0178]

**Fiscal Year 2024 (for comparison):**
- One direct customer represented **13%** of total revenue [NVDA-0178]

### Indirect Customer Concentration

NVIDIA also generates "a significant amount of revenue from a limited number of indirect customers, some individually representing 10% or more of revenue." Additionally, the filing estimates that "one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in fiscal year 2026" [NVDA-0071].

### Geographic Concentration

Revenue from customers headquartered **outside the United States** accounted for **31%** of total revenue in fiscal year 2026, down from **41%** in fiscal year 2025 and **48%** in fiscal year 2024, reflecting growing U.S.-based Compute & Networking demand [NVDA-0178].

---

### 7. What was Caterpillar's total sales and revenues, and separately its profit (net income), for 2024?
- **category:** precision  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.716
- **your note:** Tests whether the system confuses the top line ('total sales and revenues') with the bottom line ('profit'/'net income'). Both are on the income statement; record both exact figures. A precisely-cited but wrong-concept answer is the failure to watch for.
- **sub-queries:**
  - CAT: sim=0.716  q="What was Caterpillar's total sales and revenues, and separately its profit (net income), for 2024?"
- **citations:** CAT-0114, CAT-0117  |  **gaps:** (none)

**Answer:**

Based on the provided filings:

**Caterpillar's 2024 figures (fiscal year ended December 31, 2024):**

- **Total sales and revenues:** $64,809 million [CAT-0114]
- **Profit (net income) of consolidated and affiliated companies:** $10,788 million [CAT-0114] [CAT-0117]

---

### 8. What was Microsoft's total revenue in its latest fiscal year?
- **category:** refusal_oos  |  **route:** oos  |  **refused:** True (threshold)  |  **top_sim:** 0.454
- **your note:** Microsoft is NOT in the corpus. Expected: refuse via the threshold gate (no relevant chunks retrieved). Grade refusal-correct, not a number.
- **sub-queries:**
  - None: sim=0.454  q="What was Microsoft's total revenue in its latest fiscal year?"
- **citations:** (none)  |  **gaps:** (none)

**Answer:**

I couldn't find this in the six filings I cover (Apple, JPMorgan Chase, Walmart, Coca-Cola, NVIDIA, Caterpillar), so I can't answer it.

---

### 9. What is JPMorgan Chase's customer Net Promoter Score (NPS)?
- **category:** refusal_undisclosed  |  **route:** single  |  **refused:** False ()  |  **top_sim:** 0.548
- **your note:** JPMorgan IS covered, but a 10-K does not report NPS. Retrieval WILL return JPMorgan chunks that lack the answer, so the threshold won't fire â€” this must be caught by the synthesis/gaps gate stating 'not found', not a guess. Grade refusal-correct. This is the hardest refusal case.
- **sub-queries:**
  - JPM: sim=0.548  q="What is JPMorgan Chase's customer Net Promoter Score (NPS)?"
- **citations:** (none)  |  **gaps:** JPMorgan Chase

**Answer:**

Not found in the provided filings for JPMorgan Chase.
