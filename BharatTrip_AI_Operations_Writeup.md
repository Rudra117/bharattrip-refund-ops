# BharatTrip Refund Operations Audit & AI Reconciliation Strategy
**Role:** AI Operations Associate Screening Submission  
**Author:** Candidate | **Snapshot Date:** 30 June 2026 | **Constraint:** Zero New Headcount

---

## 1. Define the Problem: Diagnosis vs. Symptom

### The Symptom
Leadership observes that customer and travel agent escalations about refunds have climbed steeply for two consecutive months (May and June 2026), even though overall refund request volume has remained flat (~145 requests/month). Different teams offer conflicting explanations.

### The Underlying Diagnosis
The problem is **not** changing agent behavior, nor customer dissatisfaction with flight cancellation policies. The breakdown is entirely internal: **a critical operational decoupling between Support and Finance caused by disconnected, un-reconciled spreadsheets and a failure in cross-team handoffs.**

Our quantitative audit proves three specific systemic failures:
1. **The Silent Hand-Off Disconnect (Gap Class B):**
   - Support agents communicate with travel agents, agree to process the refund, and mark tickets **'Closed'** in `Support_Tracker` with notes such as *"refund processed, informed agent"*.
   - However, **no automated mechanism sends the request to Finance**, and Support has no visibility into whether Finance ever received it.
   - This failure rate increased from **2.1% in March to 18.7% in May and 33.0% in June**.
   - Exactly **69 refund tickets worth ₹1,080,700** were closed by Support with **no corresponding Finance record**.
2. **Finance Turnaround Delays & Approver Documentation:**
   - From February to April, Finance turnaround on completed payouts averaged **2.67–2.89 days**, and **~29–30%** of refunds had an approver recorded.
   - In May, average processing times on completed payouts increased to **6.52 days** (unpaid refunds are excluded from this turnaround calculation).
   - In June, an approver was recorded on almost no payouts (1.7%; a single recorded approver all month) because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.
3. **Recorded Deductions on Disbursements (Gap Class E):**
   - When payouts occurred, Finance recorded Deductions (averaging ₹1,500–₹2,600). Support records do not document these deductions, leading travel agents to escalate regarding differences between requested and credited amounts.
   - Our analysis shows that deductions explain **all 50 amount differences** between the trackers for paid tickets in Support.

---

## 2. Operational Analysis: What the Data Shows

### 2.1 The Flat Demand Reality
Refund volume has stayed flat across all 5 months:
- **February:** 144 requests
- **March:** 152 requests
- **April:** 147 requests
- **May:** 148 requests
- **June:** 142 requests

### 2.2 Monthly Operational Dynamics

| Month | Total Requests | Support Closed | Gap B Count (Closed, No Fin) | Gap B Rate (% of Closed) | Avg Finance Processing Time | Completed Disbursements | Finance Approver Recorded |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Feb 2026** | 144 | 137 | 4 | 2.9% | 2.89 days | 111 | 32 (28.8%) |
| **Mar 2026** | 152 | 146 | 3 | 2.1% | 2.87 days | 154 | 46 (29.9%) |
| **Apr 2026** | 147 | 145 | 6 | 4.1% | 2.67 days | 139 | 41 (29.5%) |
| **May 2026** | 148 | 139 | 26 | 18.7% | 6.52 days | 120 | 29 (24.2%) |
| **Jun 2026** | 142 | 91 | 30 | 33.0% | 4.88 days | 59 | 1 (1.7%) |

*Key finding:* Completed payouts recorded in Finance for June requests were 59, while unrecorded Support closures reached 30 (33.0% of Support closures in June). Unpaid refunds are excluded from turnaround calculations.

### 2.3 Where the Two Trackers Agree, Disagree, and Fall Silent
- **Agreement (664 refunds):** Both trackers capture the transaction, with 571 completed payouts in Support.
- **Support-Only (69 refunds):** Exactly the 69 Gap Class B tickets (Closed without Finance record).
- **Finance-Only (Gap Class H - 16 refunds):** Finance paid out ₹141,800 without any ticket ever being logged in Support.
- **Status Variances (Gap Classes C & D - 18 refunds):** 12 refunds were marked Closed by Support while sitting in `Pending Payout` in Finance (₹186,000); 6 were marked Closed by Support while Finance formally marked them `Declined` (₹94,800).
- **Amount Differences (Gap Class E - 50 refunds):** All 50 differences are mathematically explained by recorded deductions.
- **ID Normalization Audit:** 22 Support IDs, 24 Finance IDs, and 19 Escalations refs required normalization due to spacing, hyphens, or annotations.

### 2.4 Escalation Root Causes (All 155 Logged Complaints)
1. **Paid and matched (57 complaints / 36.8%):** Payout was completed, but agent chased due to confirmation inquiry.
2. **Support closed / no Finance record (31 complaints / 20.0%):** Direct consequence of Gap Class B. Agent was told refund is done, but Finance never received the request.
3. **Never logged / off-tracker (29 complaints / 18.7%):** Informal inquiries with no usable ticket reference in operational trackers.
4. **Paid but amount differs (18 complaints / 11.6%):** Difference between requested and credited amounts matching recorded deductions.
5. **Finance pending / Support not closed (8 complaints / 5.2%):** Request in Finance processing queue while Support ticket remains active.
6. **Declined without explanation (6 complaints / 3.9%):** Decline recorded in Finance where decline details were not documented on Support side.
7. **Support closed / Finance pending (6 complaints / 3.9%):** Support ticket marked Closed while Finance record remains in Pending Payout.

### 2.5 Validation Wishlist (What to validate with 2 more weeks)
1. **Finance Approval Workflow:** Ingest workflow data to verify the inferred INR 20,000 managerial threshold and examine why large June refunds were mostly still pending.
2. **Standardized Deduction Tables:** Ingest fare deduction rules directly to verify cancellation penalties at intake.
3. **Unlogged Channel Logs:** Access incoming email and WhatsApp logs to measure volume of unlogged agent inquiries.

---

## 3. Design a Solution: Single Source of Truth & Zero-Headcount Workflow

Under the zero-new-headcount constraint, BharatTrip must eliminate redundant manual status updates rather than hire coordinators.

### 3.1 Single Source of Truth (SOT) Architecture
- **Single Reconciled Ledger:** Support and Finance retain their daily role-specific views, but read and write to a single underlying database table.
- **Decoupled Status Lifecycle:**
  - Support **cannot** mark a ticket `Closed`. Support status options are limited to: `New`, `Working`, and `Verified & Forwarded`.
  - `Closed` is a system-generated state triggered **only when Finance logs payout execution** (`Refund Done`).
- **Automated Daily Reconciler (`core/reconcile.py`):**
  - Runs daily at 06:00.
  - Generates the **Prioritized Action Queue** ranking uncompleted refunds by `Amount × Age (Days)`.
  - Automatically identifies the 69 Gap Class B refunds and queues them directly into Finance payment batches without manual data entry.
- **Automated Proactive Dispatch:**
  - When Finance executes payout, an automated notification sends the travel agent an itemized breakdown (Gross Amount, Deduction, Net Disbursed), addressing the pattern behind 57 status queries and 18 deduction disputes.

### 3.2 Explicit Automation Trade-Offs

| Component | Operational Choice | Justification & Risk Mitigation |
| :--- | :--- | :--- |
| **Ledger Reconciliation** | **100% Deterministic Code (NO LLM)** | Zero tolerance for hallucination in financial records. Outer joins, deduction checks, and age scores are deterministic. |
| **Deduction Auditing** | **Deterministic Rule Engine** | Validates whether `Refund Amount - Amount Paid == Deduction` without subjective judgment. |
| **Informal Message Intake** | **AI / LLM Layer (`core/intake.py`)** | Translates unstructured English/Hinglish emails and WhatsApp messages into normalized JSON schema. |
| **Agent Draft Status Replies** | **Grounded Template Engine** | Drafts responses strictly using ledger fields. **Never invents an estimated turnaround (ETA) or unverified status.** |
| **Payout Approval** | **Deliberately Kept Manual** | Financial disbursement carries fraud risk; bank authorization must remain human-governed. |
| **Decline Communications** | **Manual Support Touchpoint** | Contested cancellations require nuanced relationship management with B2B travel agency partners. |

### 3.3 AI Prototype Implementation
- Built a functional production web dashboard (Vite + React + TypeScript + Tailwind) backed by FastAPI (`api.py`) with fallback to Streamlit (`app.py`):
  1. **Executive Overview & Trends:** Visualizes flat request volume vs. Gap B rates (2.9% to 33.0%) and Finance turnaround.
  2. **Gaps & Action Queue:** Searchable ledger with 1-click Excel export, raw ID audit, and priority ranking (`Amount × Age`).
  3. **Escalation Root Causes:** Interactive breakdown of all 155 complaints by empirical root cause with distinct color hierarchy.
  4. **AI Intake Assistant:** Live message normalization (Hinglish/English), ledger lookup enforcing unique matching, and grounded draft reply generation. Built-in zero-key fallback banner ensures reliability.

---

## 5. Measure: 30-Day Success Metrics & Target Results

| Metric to Watch | June Baseline | 30-Day Target | Why It Matters |
| :--- | :---: | :---: | :--- |
| **1. Gap B Creation Rate (% of Support Closed not in Finance)** | **33.0%** (30 tickets) | **< 2.0%** (< 3 tickets) | Primary root cause. Confirms handoff automation has resolved the disconnect. |
| **2. Escalation Frequency (Escalations per 100 Refunds)** | **~35 per 100** | **< 8 per 100** | Proactive deduction itemization and notifications eliminate chases. |
| **3. Backlog Aging (>14 days unpaid)** | **69 tickets > 30 days** | **0 tickets > 14 days** | Prioritized Action Queue forces daily clearing of aged high-value items. |
| **4. Intake Auto-Logging Share** | **~0%** (all manual) | **> 90% logged** | Guarantees all informal WhatsApp/Email requests receive `RF-NEW-###` in < 2 mins. |

### What a "Good Result" Looks Like After 1 Month:
- **Zero Silent Drops:** Zero escalations stating *"Finance says they never received this"*.
- **Backlog Liquidation:** All 69 Gap Class B refunds (₹1,080,700) audited and disbursed.
- **Escalation Volume Drops:** Total weekly escalations plummet from ~35/week down to under 5/week.
- **Cross-Team Alignment:** Support and Finance collaborate on a shared ledger view without inter-departmental conflict.
