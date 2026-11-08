# BharatTrip AI Operations Assessment — Prompt & Interaction History

This document logs the prompts, instructions, architectural planning steps, and verification commands used while solving the BharatTrip Refund Operations task.

---

### Step 0: Initial Task & Dataset Ingestion
**User Input:**
`@[c:\Users\Rudra Panchal\Downloads\BharatTrip_Refund_Prototype_Prompt.md]`

**Context Evaluated:**
- Task brief: Take-home assessment for AI Operations Associate screening stage.
- Problem: Flat refund volume (~145/month) but climbing escalations over May-June 2026.
- Constraints: No new headcount, zero tolerance for hallucinations in core ledger math, strict 4-tab Streamlit architecture, known-answer validation checks.
- Data: `BharatTrip_Refund_Data.xlsx` with tabs `Read_Me`, `Support_Tracker`, `Finance_Tracker`, `Escalations`.

---

### Step 1: Architectural Plan Proposed to User
**Prompt / Action:**
Proposed file structure, core modules (`core/clean.py`, `core/reconcile.py`, `core/intake.py`, `app.py`), run command, known-answer validation plan, and explicitly waited for user approval per "STEP 0 - PLAN FIRST".

---

### Step 2: User Amendments & Approval
**User Guidance Received:**
1. Unique matching rule: Only report ledger status when the match is UNIQUE (same agent + route + window). If multiple candidates match, return candidate list and ask for confirmation.
2. New refund IDs must use prefix `RF-NEW-###`.
3. Preset (c) (internal Support note) must NOT create a refund; route directly to Gap B report.
4. Add tests for escalation root-cause counts (55, 34, 29, 17, 8, 6, 5, 1 = 155), intake parsing with no API key, and fallback banner.
5. Add Finance processing turnaround by month and approval share by month to `reconcile.py` and expose in Tab 1.
6. Build order: `clean.py` and `reconcile.py` first -> verify tests -> only then build `intake.py` and `app.py`.

---

### Step 3: Package Installation & Environment Setup
**Command Executed:**
`pip install pandas openpyxl rapidfuzz pytest streamlit fpdf2`

---

### Step 4: Core Data Cleaning (`core/clean.py`)
**Implementation Highlights:**
- Standardized ID normalization: `strip() + upper()`.
- Safe datetime parsing without day-first corruption for native Timestamps.
- RapidFuzz fuzzy deduplication collapsing 56 Support spellings and 63 Finance spellings into exactly 22 canonical agencies.
- Duplicate resolution: sorted by `Last Updated` ascending, retaining latest row with `drop_duplicates(keep='last')`.
- Conflict detection: isolated 10 Support tickets with amount/status conflicts into an audit table.
- Finance duplicate filtering: penalized `re-entry` and `duplicate check pending` remarks, keeping valid payout rows.

---

### Step 5: Core Reconciliation & Gap Taxonomy (`core/reconcile.py`)
**Implementation Highlights:**
- Outer join on cleaned ticket ID across 780 total cases.
- Class A: Unlinked escalations.
- Class B: Support Closed without Finance record (exactly 98 tickets, ₹1,562,300).
- Class C: Support Closed with Finance Pending Payout (11 tickets).
- Class D: Support Closed with Finance Declined (6 tickets).
- Class E: Paid with amount discrepancy (48 cases; 47 exactly explained by airline deduction).
- Class H: Finance-only payouts (47 cases).
- Aging calculation relative to fixed snapshot date (30 June 2026).
- Prioritized Action Queue scored by `Refund Amount × Effective Age (Days)`.
- Escalation root-cause classifier covering all 155 complaints across 8 distinct categories.
- Monthly processing turnaround and manager approval velocity metrics.

---

### Step 6: Test Suite Verification (`tests/test_known_answers.py` & `tests/test_intake.py`)
**Command Executed:**
`python -m pytest tests/ -v`

**Result:**
`16 passed in 3.93s` with 100% precision across all known-answer ground truth assertions.

---

### Step 7: AI Intake Module (`core/intake.py`)
**Implementation Highlights:**
- Three one-click interactive demo presets (Peak Journeys email, Nomad Travel Hinglish WhatsApp, Internal Support note).
- Zero-key fallback: Deterministic regex and semantic pattern matching with active "Running without LLM" banner.
- Optional Gemini/Anthropic live API integration when keys are set in environment.
- Strict Unique Matching: Returns candidate lists on multiple matches; generates `RF-NEW-###` for new inquiries; routes internal note to Gap B report without creating a ticket.
- Grounded draft generation: Never invents an ETA or unverified status.

---

### Step 8: Streamlit Web UI (`app.py`)
**Four Clean Tabs:**
1. Executive Overview & Monthly Trends (visualizing Gap B surge to 36.3% and approval collapse to 2.2%).
2. Gaps & Prioritized Action Queue (with 1-click Excel download of the single source of truth).
3. Escalation Root Causes & Audit Breakdown (all 155 complaints).
4. AI Intake Assistant (live unstructured text parser and grounded draft generator).

---

### Step 9: Deliverable Artifacts Generated
- `BharatTrip_AI_Operations_Writeup.pdf` (official 3-page submission PDF generated via `generate_pdf_writeup.py`).
- `BharatTrip_AI_Operations_Writeup.md` (markdown version).
- `requirements.txt`, `.env.example`, `README.md`.
