# BharatTrip Refund Operations Audit & AI Reconciliation Strategy
**Role:** AI Operations Associate Screening Submission  
**Candidate Submission** | **Snapshot Date:** 30 June 2026 | **Constraint:** Zero New Headcount  
**Repository:** [https://github.com/Rudra117/bharattrip-refund-ops](https://github.com/Rudra117/bharattrip-refund-ops)  
**One-Line Run Command:** `python -m uvicorn api:app --port 8000` (or `streamlit run app.py`)

---

### Core Operational Assumptions (Documented Upfront)
1. **ID Normalization & Deduplication:** Support and Finance IDs were normalized by stripping whitespace and non-standard prefixes (`REF-`, raw integers) and left-padding numeric sequences to 4 digits (`RF-0421`). Duplicate ticket conflicts in Support were resolved by selecting the record with the latest `Last Updated`; on ties, selecting the record matching Finance's `Amount Paid` or `Amount Paid + Deduction`; otherwise preserving row order.
2. **Inferred Managerial Approval Tier:** Inferred at $\ge$ **INR 20,000** based on empirical ground truth (every single approved payout in the dataset is $\ge$ INR 20,100).
3. **Deductions:** Ground truth reveals that recorded Finance deductions explain 100% of the gross-to-net variances on paid refunds.

---

## 1. Define the Problem: Data Observations vs. Reported Symptom

### The Reported Symptom
Leadership's observation is that *"customer and agent escalations about refunds have been climbing for two months (May and June 2026), while refund volume has stayed roughly flat over the same period."* Different teams offer conflicting explanations.

### The Underlying Diagnosis
The problem is **not** changing agent behavior, external market volatility, or customer dissatisfaction with cancellation policies. Total incoming refund requests remained completely flat across all 5 months (~145/month: Feb 144, Mar 152, Apr 147, May 148, Jun 142).

The escalation surge is driven by an internal operational breakdown: **a critical structural decoupling between Support and Finance caused by disconnected, un-reconciled spreadsheets and a failure in cross-team handoffs.**

Our empirical audit confirms three distinct root drivers:
1. **The Silent Handoff Disconnect (Gap Class B):**
   - Support agents communicate with travel agents, agree to process the refund, and mark tickets **'Closed'** in `Support_Tracker` with notes such as *"refund processed, informed agent"*.
   - However, **no automated mechanism sends the request to Finance**, and Support has no visibility into whether Finance ever received it.
   - This failure rate increased from **2.1% in March to 18.7% in May and 33.0% in June**.
   - Exactly **69 refund tickets worth INR 1,080,700** were closed by Support with **no corresponding Finance record**.
2. **Finance Processing Turnaround & Approval Bottleneck:**
   - From February to April, Finance turnaround on completed payouts averaged **2.67–2.89 days**, and **~29–30%** of refunds had an approver recorded.
   - In May, average processing times on completed payouts increased to **6.52 days** *(unpaid refunds are excluded from turnaround calculations)*.
   - In June, an approver was recorded on almost no payouts (**1.7%**; a single recorded approver all month) because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.
3. **Recorded Deductions on Disbursements (Gap Class E):**
   - When payouts occurred, Finance recorded Deductions (averaging INR 1,500–2,600). Support records do not document these deductions, leading travel agents to escalate regarding differences between requested and credited amounts.
   - Our analysis shows that deductions explain **all 50 amount differences** between the trackers for paid tickets in Support.

---

## 2. Operational Analysis: What the Data Shows

### 2.1 Monthly Operational Dynamics (5-Month Audit)

| Month | Requests | Support Closed | Gap B Count (Closed, No Fin) | Gap B Rate (% of Closed) | Avg Finance Proc Time* | Completed Disbursements | Finance Approver Share** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Feb 2026** | 144 | 137 | 4 | 2.9% | 2.89 days | 111 | 32 (28.8%) |
| **Mar 2026** | 152 | 146 | 3 | 2.1% | 2.87 days | 154 | 46 (29.9%) |
| **Apr 2026** | 147 | 145 | 6 | 4.1% | 2.67 days | 139 | 41 (29.5%) |
| **May 2026** | 148 | 139 | 26 | 18.7% | 6.52 days | 120 | 29 (24.2%) |
| **Jun 2026** | 142 | 91 | 30 | 33.0% | 4.88 days | 59 | 1 (1.7%) |

*\*Unpaid refunds are excluded from turnaround calculations. \*\*Approver share denominator = all Finance Refund Done rows by received month.*

*Key Finding:* In June, completed payouts dropped to 59, while unrecorded Support closures reached 30 (33.0% of Support closures in June). Support told agents refunds were completed, but Finance never received the tickets, triggering intense escalation waves.

### 2.2 Where the Two Trackers Agree, Disagree, or Fall Silent
- **Where Trackers Agree (664 cases):** Both trackers capture the transaction, with 571 completed payouts in Support.
- **Where Trackers Disagree (18 cases):**
  - **Gap C (12 refunds / INR 186,000):** Marked `Closed` by Support while sitting in `Pending Payout` in Finance.
  - **Gap D (6 refunds / INR 94,800):** Marked `Closed` by Support while Finance formally recorded them as `Declined`.
  - **Gap E (50 refunds):** Support and Finance record different amounts on completed payouts; recorded deductions explain **100% of these 50 variances**.
- **Where Trackers Fall Silent:**
  - Support falls silent on Finance in **69 cases** (Gap Class B: INR 1,080,700).
  - Finance falls silent on Support in **16 paid refunds** (Gap Class H: INR 141,800 paid without Support tickets).
  - Both trackers fall silent on **29 off-tracker informal inquiries** that never received a usable ticket reference until chased.
  - Finance approval workflow fell silent in June on **25 large refunds ($\ge$ INR 20,000)** totaling **INR 696,600** (mean wait 14.2 days, max 26 days).

### 2.3 Informal Off-Tracker Inquiries from the Brief
The 3 unstructured messages in the brief provide real operational evidence confirming this diagnosis:
1. **Peak Journeys (Email, 5 June):** DEL-DXB booking cancelled, agent promised refund but given no reference ID. Chased off-tracker until logged late as `RF-1099`.
2. **Nomad Travel (WhatsApp, 8 June):** *"Bhai refund ka kya hua? BLR-MAA wala. 2 hafte ho gaye, koi jawab nahi."* Off-tracker chase, later logged as `RF-1098`.
3. **Support Agent Internal Note (Email, 11 June):** *"Finance says they never received several of the refunds I closed last month. I marked them done on my side. Not sure where they went."* Direct proof that Support agents closed tickets without ensuring Finance ingestion.

### 2.4 Escalation Root Causes (All 155 Logged Complaints)

| Root Cause Category | Count | Share (%) | Data Observation & Operational Context |
| :--- | :---: | :---: | :--- |
| **paid and matched** | 57 | 36.8% | Payout completed in Finance matching request; agent inquired regarding confirmation / missing UTR. |
| **Support closed/no Finance** | 31 | 20.0% | Gap Class B: Ticket marked Closed on Support, no corresponding Finance record. |
| **never logged (no usable ref)** | 29 | 18.7% | Informal inquiries (email/WhatsApp) with no usable reference in operational trackers. |
| **paid but amount differs** | 18 | 11.6% | Disbursement matches Amount Paid, but agent expected gross amount without deduction. |
| **Finance pending/Support not closed**| 8 | 5.2% | Request in Finance processing queue while Support ticket remains active. |
| **declined (recorded in Finance)** | 6 | 3.9% | Decline recorded in Finance; decline details not documented on Support side. |
| **Support closed/Finance pending** | 6 | 3.9% | Premature closure: Support marked Closed while Finance record is Pending Payout. |

*Estimated Addressable Failures: 141 of 155 (91.0%) = 84 structural failures (31 Gap B + 29 unlogged + 18 deductions + 6 premature closures) + 57 status queries on completed disbursements.*

### 2.5 Validation Wishlist (What to Validate with 2 More Weeks Access)
1. **Finance Approval Workflow:** Audit approval logs to verify the inferred INR 20,000 threshold and investigate why large June payouts stalled.
2. **Standardized Deduction Tables:** Ingest supplier/airline cancellation penalty schedules to verify deductions at intake.
3. **Omnichannel Inbound Inboxes:** Connect email and WhatsApp webhooks to measure the true volume of unlogged agent inquiries.
4. **Canonical Agency Master:** Map agency name variations across systems into a single canonical ID.

---

## 3. Design a Solution: Single Source of Truth & Zero-Headcount Workflow

Under the zero-new-headcount constraint, BharatTrip must eliminate redundant manual status updates rather than hire coordinators:

```
               CUSTOMER / TRAVEL AGENT
                          │ (Inbound Request)
                          ▼
            AUTOMATED INTAKE ASSISTANT (AI)
    (Extracts entities, assigns RF-NEW-###, runs plausibility check)
                          │
                          ▼
          CENTRAL RECONCILED DATABASE (SOT)
   ┌──────────────────────────────────────────────┐
   │  SUPPORT VIEW         │     FINANCE VIEW     │
   │  Status:              │     Payout Status:   │
   │  • New                │     • In Queue       │
   │  • Working            │     • Pending Auth   │
   │  • Verified/Forwarded │     • Refund Done    │
   │  (Cannot mark Closed) │     • Declined       │
   └──────────────────────────────────────────────┘
                          │
                          ▼
             BANK DISBURSEMENT & UTR ISSUANCE
                          │
                          ▼
        SYSTEM-AUTOMATED CLOSURE & NOTIFICATION
    (Sends UTR + Net Breakdown -> Support Ticket Closed)
```

1. **State Machine Decoupling:** Support agents are stripped of the ability to mark a ticket `Closed`. Support status options are limited to `New`, `Working`, and `Verified & Forwarded`. A ticket enters `Closed` **strictly and automatically** when Finance attaches a bank UTR and marks `Payout Status = Refund Done`. This structurally eliminates Gap B.
2. **Automated Daily Reconciler & Action Queue (`core/reconcile.py`):** A daily 06:00 AM automated audit script reconciles tables, flags discrepancies, and generates a dynamic Action Queue ranked by Priority Score ($\text{Amount} \times \text{Age}$).
3. **Proactive Disbursement Notification:** When Finance executes a payout, the system automatically dispatches an itemized notification to the travel agency containing the UTR, Gross Amount, Recorded Deduction, and Net Amount Disbursed, addressing the issues behind 57 status queries and 18 deduction disputes.

### Explicit Automation vs. Manual Trade-Offs

| Component | Operational Choice | Justification & Risk Mitigation |
| :--- | :--- | :--- |
| **Matching & Reconciliation** | **100% Deterministic Code (NO LLM)** | Zero financial hallucination risk. Ledger math and status joins remain deterministic. |
| **Deduction Verification** | **Deterministic Rule Engine** | Validates whether `Refund Amount - Amount Paid == Deduction` without subjective judgment. |
| **Informal Message Intake** | **AI / LLM Layer (`core/intake.py`)** | Normalizes unstructured English/Hinglish text into structured JSON schema. |
| **Agent Status Response** | **Automated Grounded Drafts** | Strictly grounded in ledger records. Never invents an estimated turnaround (ETA). |
| **Disbursement Authorization** | **Deliberately Kept Manual (Finance)** | Banking authorization and payment release remain with authorized Finance personnel. |
| **Decline Communication** | **Manual Support Touchpoint** | Human touchpoint preserves partner agency relationships on contested cancellations. |

---

## 4. AI Prototype Implementation (Functional Scope & Judgment)

We built and verified a functional production prototype combining deterministic Python reconciliation with an LLM intake assistant:
* **Backend:** FastAPI (`api.py`) exposing 10 REST endpoints with deterministic math, input sanitization, and rate limiting.
* **Frontend:** Production single-page application (React, TypeScript, Tailwind CSS, Recharts) with live dark/light mode and 1-click Excel ledger export.
* **Deterministic Core (`core/clean.py`, `core/reconcile.py`):** Normalizes IDs, deduplicates canonical records, classifies all 8 gap classes, and ranks tickets by Priority Score.
* **AI Intake Assistant (`core/intake.py`):** Uses Google Gemini 2.5 Flash to parse unstructured emails/WhatsApp messages (including Peak Journeys, Nomad Travel, and internal notes). Enforces unique matching, executes plausibility guards (never asserting "Refund Done" on conflicting/aged records), issues non-colliding `RF-NEW-###` IDs, and provides a built-in zero-key fallback parser.

---

## 5. Measure: 30-Day Success Metrics & Target Results

### Primary North Star Metrics to Watch

| Metric to Watch | June Baseline | 30-Day Target | Operational Significance |
| :--- | :---: | :---: | :--- |
| **1. Gap B Creation Rate** | **33.0%** (30 tickets) | **< 1.0%** (< 2 tickets) | Direct measure of handoff synchronization between Support and Finance. |
| **2. Escalation Frequency** | **35 per 100 refunds** | **< 5 per 100 refunds** | Proactive UTR and deduction notifications eliminate repeated status chases. |
| **3. Backlog Aging (>14 days)** | **69 tickets > 30 days** | **0 tickets > 14 days** | Prioritized Action Queue forces daily clearing of aged high-value items. |
| **4. Intake Auto-Logging Share** | **~0%** (manual logging) | **> 95% logged** | Guarantees all informal email/WhatsApp requests receive `RF-NEW-###` immediately. |
| **5. Stalled Approvals (>7 days)** | **25 tickets (INR 6.96L)** | **0 tickets > 7 days** | Approval alerts prevent month-end large refund bottlenecks. |

### What a Good Result Looks Like After 1 Month
1. **Discrepancy Elimination:** Gap B creation drops to zero because the system state machine prevents manual premature closures.
2. **Backlog Clearance:** The existing 69 Gap Class B refunds (INR 1,080,700) and 25 stalled approvals (INR 696,600) are audited, approved, and disbursed.
3. **Escalation Reduction:** Total escalations drop from ~35 per 100 refunds to under 5 per 100 refunds as partner agencies receive real-time UTR and fee breakdown alerts upon disbursement.
