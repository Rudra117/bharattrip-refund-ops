# BharatTrip | Refund Operations Reconciliation & AI Platform

> **AI Operations Associate -- Take-Home Screening Stage**  
> **One-Command Run:** `pip install -r requirements.txt && python -m uvicorn api:app --port 8000` (or `streamlit run app.py` for Streamlit fallback)

---

## 1. Quickstart

```bash
# 1. One-command run: install dependencies and launch unified platform (serves API and built frontend)
pip install -r requirements.txt && python -m uvicorn api:app --port 8000

# 2. Run complete automated test suite (29 tests verifying ground truth, intake, API, and rendered parity)
python -m pytest tests/ -v

# Alternative: Run Streamlit dashboard fallback
streamlit run app.py
```

*Note: The platform runs 100% locally with zero required external API keys. If `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is present in your environment, live LLM mode is enabled automatically.*

---

## 2. Operational Observations

Leadership observed that customer and travel agent escalations climbed sharply over May and June 2026, while overall refund volume remained steady (~140–150 refund requests per month).

An empirical audit of `Support_Tracker`, `Finance_Tracker`, and `Escalations` reveals three key data patterns:

1. **Gap Class B (Closed in Support, No Finance Record):**
   - Support tickets marked 'Closed' with no corresponding Finance record increased from **2.1% in March to 18.7% in May and 33.0% in June**.
   - Exactly **69 closed tickets with no Finance record** exist in the extract, totaling **INR 1,080,700**.
2. **Finance Processing Turnaround & Approver Documentation:**
   - Turnaround from Finance received date to payout date on completed records increased from an average of **2.67 days in April to 6.52 days in May** *(unpaid refunds are excluded from this calculation)*.
   - Approver recorded on almost no June payouts because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.
3. **Recorded Deductions on Disbursements:**
   - For completed refunds in Support with differing amounts, recorded Deductions in Finance account for **50 out of 50** discrepancy cases. Support records do not document these deductions, leading to short-payment inquiries.

---

## 3. Reconciliation Summary & Audited Figures (749 Unique Refunds)

Joining both trackers on normalized IDs (`clean_id`: `'RF-' + digits`) produces the single source of truth:

| Metric / Category | Count | Financial Amount (INR) | Summation Column & Definition |
| :--- | :---: | :---: | :--- |
| **Unique Support Tickets** | 733 | INR 10,958,100 | Deduplicated using the priority rule below. |
| **Unique Finance Payouts** | 680 | INR 10,214,300 | Deduplicated (9 re-entry/duplicate check rows filtered). |
| **Matched In Both Sheets** | 664 | INR 9,997,400 | Core overlap tracked by both teams (571 paid in Support). |
| **Support Only (Class B)** | **69** | **INR 1,080,700** | Summed from Support **`Refund Amount (INR)`**. |
| **Finance Only (Class H)** | **16** | **INR 141,800** | Summed from Finance **`Amount Paid (INR)`**. |
| **Gap Class C (Closed, Fin Pending)** | **12** | **INR 186,000** | Summed from Support **`Refund Amount (INR)`**. |
| **Gap Class D (Closed, Fin Declined)** | **6** | **INR 94,800** | Summed from Support **`Refund Amount (INR)`**. |
| **Gap Class E (Paid with Diff)** | 50 | INR 1,021,500 | 50 cases; all 50 exactly explained by recorded Deduction. |
| **Total Escalations Logged** | 155 | 85 Open, 70 Resolved | 136 usable IDs (126 in Support, 95 in Finance). |

### Escalation Root Cause Distribution (All 155 Complaints)
- **paid and matched:** 57 (36.8%) -- Payout recorded in Finance matching request; agent inquired regarding status confirmation.
- **Support closed/no Finance:** 31 (20.0%) -- Gap Class B: Ticket marked Closed on Support, no corresponding Finance record.
- **never logged (no usable ref):** 29 (18.7%) -- Informal inquiries with no usable ticket reference in operational trackers.
- **paid but amount differs:** 18 (11.6%) -- Payout completed with deduction not reflected in Support conversation.
- **Finance pending/Support not closed:** 8 (5.2%) -- Request in Finance processing queue while Support ticket remains active.
- **declined (unexplained):** 6 (3.9%) -- Record declined in Finance; decline details not documented on Support side.
- **Support closed/Finance pending:** 6 (3.9%) -- Support ticket marked Closed while Finance record remains in Pending Payout.

### ID Format Normalization Audit
- Support IDs normalized: 22 (e.g. `'RF 1750'`, `'RF-1313 (REVISED)'`)
- Finance Refs normalized: 24 (e.g. `'RF1109'`, `'RF 1205'`)
- Escalations unlinked / no usable ref: 19

---

## 4. Duplicate Resolution Rule (Applied in `core/clean.py`)

1. For duplicate ticket IDs in `Support_Tracker`, keep the row with the latest `Last Updated`.
2. On a tie in `Last Updated`, keep the row whose `Refund Amount (INR)` equals Finance `Amount Paid (INR)` or `Amount Paid + Deduction (INR)`.
3. If none matches, keep the later row in the sheet (highest sheet row index).
4. All conflicting duplicates in Support are isolated in an audit table for visibility.

---

## 5. Architecture & Explicit Trade-offs

```
                      Informal Message (Email / WhatsApp / Hinglish)
                                           |
                                           v
                             +---------------------------+
                             |      core/intake.py       |
                             | (LLM / Rule-Based Parser) |
                             +-------------+-------------+
                                           | Structured JSON
                                           v
+---------------------------------------------------------------------------------+
|                           DETERMINISTIC DATA ENGINE                             |
|                                                                                 |
|   Support_Tracker ----> core/clean.py ----+                                     |
|                                           +---> core/reconcile.py ---> SOT      |
|   Finance_Tracker ----> core/clean.py ----+     (Outer Join, Gaps,     Ledger   |
|                                                  Aging, Priorities)             |
+------------------------------------------+--------------------------------------+
                                           |
                        +------------------+------------------+
                        |                                     |
                        v                                     v
          +---------------------------+         +---------------------------+
          |          api.py           |         |          app.py           |
          | (FastAPI Endpoints / SPA) |         | (Streamlit Fallback UI)   |
          +---------------------------+         +---------------------------+
```

### Automation Decisions:
- **Ledger Reconciliation:** 100% deterministic code (no LLM). Arithmetic and status joins are strictly deterministic.
- **Informal Message Intake:** AI/LLM layer normalizes unstructured Hinglish/English text into structured JSON.
- **Agent Responses:** Automated draft replies are strictly grounded in ledger fields; never state an ETA or unverified status.
- **Disbursement Authorization:** Deliberately kept manual within Finance to preserve authorization controls.

---

## 6. Target Metrics (30-Day Plan)

1. **Gap B Creation Rate (% of Support Closed not in Finance):** Baseline: 33.0% in June 2026. Target: **< 2.0%**.
2. **Escalation Frequency (Escalations per 100 Refunds):** Baseline: ~35 per 100. Target: **< 8 per 100**.
3. **Aged Unpaid Backlog (>14 days):** Baseline: 69 tickets > 30 days. Target: **0 tickets > 14 days**.
4. **Intake Auto-Logging Share:** Baseline: ~0% (manual). Target: **> 90%** of off-tracker messages logged via `RF-NEW-###`.
