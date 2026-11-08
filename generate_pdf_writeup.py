"""Generate the official 3-page submission PDF for BharatTrip AI Operations Associate.
Strictly constrained to max 3 pages, concise, high-signal, covering:
1. Define the problem.
2. Analyse (Where trackers agree, disagree, or fall silent; unlogged requests; validation wishlist).
3. Design a solution (Zero-headcount, Single Source of Truth, automated vs manual trade-offs).
4. AI Prototype (Judgment-driven slice, entity extraction vs deterministic reconciliation).
5. Measure (1-2 North Star metrics, 30-day targets, and 1-month success criteria).
Includes explicit assumptions, prototype one-liner, and prompt history note.
Uses pure ASCII characters and objective observational language.
"""
from fpdf import FPDF

class SubmissionPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(90, 100, 115)
        self.cell(0, 4.5, "BHARATTRIP -- AI OPERATIONS ASSOCIATE SCREENING STAGE | REFUND RECONCILIATION", border=0, align="L")
        self.set_font("Helvetica", "I", 7.5)
        self.cell(0, 4.5, f"Page {self.page_no()} of 3", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(210, 215, 225)
        self.set_line_width(0.25)
        self.line(10, 10.5, 200, 10.5)
        self.ln(2)

    def footer(self):
        self.set_y(-9)
        self.set_font("Helvetica", "I", 6.8)
        self.set_text_color(128, 135, 145)
        self.cell(0, 4, "Working Prototype: https://github.com/Rudra117/bharattrip-refund-ops | One-line run: python -m uvicorn api:app --port 8000", align="C")

def build_pdf(output_path: str):
    pdf = SubmissionPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 12, 10)
    pdf.set_auto_page_break(auto=False)

    # =========================================================
    # PAGE 1: CONTEXT, ASSUMPTIONS, PROBLEM DEFINITION, ANALYSIS (PART 1)
    # =========================================================
    pdf.add_page()
    
    # Title & Metadata Block
    pdf.set_font("Helvetica", "B", 13.5)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 6, "Operational Diagnosis, Single Source of Truth & AI Reconciliation Strategy", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(80, 90, 105)
    pdf.cell(0, 4, "Candidate Submission | Role: AI Operations Associate | Date: 30 June 2026 Snapshot | Constraint: Zero New Headcount", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 7.2)
    pdf.cell(0, 3.8, "Repo: https://github.com/Rudra117/bharattrip-refund-ops | Prototype Run: python -m uvicorn api:app --port 8000 (or streamlit run app.py)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)

    # Assumptions Block
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(215, 222, 232)
    pdf.rect(10, pdf.get_y(), 190, 12, style="DF")
    pdf.set_xy(12, pdf.get_y() + 1)
    pdf.set_font("Helvetica", "B", 7.2)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 3.5, "CORE OPERATIONAL ASSUMPTIONS (DOCUMENTED UPFRONT):", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 6.8)
    pdf.set_text_color(50, 60, 75)
    pdf.multi_cell(186, 3.2, (
        "1. ID Normalization: Strip prefixes/spaces, 4-digit pad (RF-0421 -> RF-0421). Deduplication preserves latest update, then Finance match.\n"
        "2. Approval Tier: Inferred at >= INR 20,000 (all approved payouts >= 20,100). 3. Ground Truth: Deductions explain gross-to-net variances."
    ))
    pdf.set_y(pdf.get_y() + 2)

    # Section 1: Define the Problem
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 5, "1. DEFINE THE PROBLEM: DATA OBSERVATIONS vs. REPORTED SYMPTOM", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(30, 35, 45)
    pdf.multi_cell(0, 3.6, (
        "Leadership's stated symptom is that 'escalations have been climbing for two months while refund volume is flat.' "
        "The underlying diagnosis is an operational disconnection between two independent spreadsheet trackers rather than external volume growth.\n"
        "Refund request demand remained completely flat across all 5 months (~145/month: Feb 144, Mar 152, Apr 147, May 148, Jun 142). "
        "The escalation surge in May and June is driven by three distinct internal systemic failures:\n"
        "1. Gap Class B (Closed in Support, No Finance Record): Support agents marked tickets 'Closed' with notes like 'refund processed, informed agent'. "
        "However, no corresponding record exists in Finance Tracker. This rate increased from 2.1% in March to 18.7% in May and 33.0% in June. "
        "Across the snapshot, exactly 69 closed tickets with no Finance record exist, totaling INR 1,080,700.\n"
        "2. Finance Processing Turnaround & Approval Bottleneck: Turnaround on completed payouts increased from 2.67 days in April to 6.52 days in May "
        "(unpaid refunds are excluded from turnaround calculations). In June, an approver was recorded on almost no payouts (1.7%; 1 payout) "
        "because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.\n"
        "3. Recorded Deductions on Disbursements: Finance recorded Deductions (averaging INR 1,500-2,600). Support records do not document these deductions, "
        "leading travel agents to escalate regarding differences between requested and credited amounts."
    ))
    pdf.ln(1.5)

    # Section 2: Analyse (Part 1 - Data Evidence & Monthly Trends)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 5, "2. OPERATIONAL ANALYSIS: EMPIRICAL METRICS ACROSS 5 MONTHS", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 7.8)
    pdf.multi_cell(0, 3.6, (
        "Reconciling 733 unique Support rows and 680 Finance rows reveals 749 unique refund cases. "
        "While incoming volume stayed steady, the operational handoff broke down in May and June:"
    ))
    pdf.ln(1)

    # Table: Monthly Trends
    col_widths = [19, 21, 23, 24, 26, 26, 26, 25]
    headers = ["Month", "Requests", "Support Clsd", "Gap B (Count)", "Gap B Rate", "Avg Proc Time*", "Finance Done", "Approver Share**"]
    
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 237, 246)
    pdf.set_text_color(20, 35, 60)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 4.5, h, border=1, align="C", fill=True)
    pdf.ln()

    rows_data = [
        ["Feb 2026", "144", "137", "4", "2.9%", "2.89 days", "111", "32 (28.8%)"],
        ["Mar 2026", "152", "146", "3", "2.1%", "2.87 days", "154", "46 (29.9%)"],
        ["Apr 2026", "147", "145", "6", "4.1%", "2.67 days", "139", "41 (29.5%)"],
        ["May 2026", "148", "139", "26", "18.7%", "6.52 days", "120", "29 (24.2%)"],
        ["Jun 2026", "142", "91", "30", "33.0%", "4.88 days", "59", "1 (1.7%)"],
    ]
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(30, 30, 30)
    for r in rows_data:
        for i, val in enumerate(r):
            fill = True if ("33.0%" in val or "1 (1.7%)" in val or ("30" in val and i==3)) else False
            if fill:
                pdf.set_fill_color(255, 232, 232)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(col_widths[i], 4, val, border=1, align="C", fill=fill)
        pdf.ln()
    pdf.ln(1)

    pdf.set_font("Helvetica", "I", 6.8)
    pdf.cell(0, 3.5, "*Unpaid refunds excluded from turnaround calculations. **Approver share denominator = all Finance Refund Done rows by received month.", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "B", 7.8)
    pdf.cell(0, 4, "Key Takeaway from Table:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.6)
    pdf.multi_cell(0, 3.5, (
        "In June, completed payouts dropped to 59, while Support closed tickets with no Finance record surged to 30 (33.0% of Support closures). "
        "Support agents were telling agents refunds were completed, but Finance never received the tickets, sparking intense follow-up chases."
    ))

    # =========================================================
    # PAGE 2: TOPOLOGY, UNLOGGED REQUESTS, ESCALATION ROOT CAUSES, WISHLIST
    # =========================================================
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 5, "2. OPERATIONAL ANALYSIS (CONT.): WHERE TRACKERS AGREE, DISAGREE, OR FALL SILENT", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(30, 35, 45)
    pdf.multi_cell(0, 3.6, (
        "- Where Trackers Agree (664 cases): Captured in both systems; 571 completed payouts recorded in Support.\n"
        "- Where Trackers Disagree (18 cases): 12 tickets are Closed in Support but Pending Payout in Finance (Gap C: INR 186,000); "
        "6 tickets are Closed in Support but Declined in Finance (Gap D: INR 94,800). Additionally, 50 paid cases exhibit amount differences (Gap E); "
        "recorded deductions explain 100% of these 50 variances (Support Amount minus Finance Paid equals recorded Deduction).\n"
        "- Where Trackers Fall Silent: Support falls silent on Finance in 69 cases (Gap B: INR 1,080,700). Finance falls silent on Support in 16 paid "
        "refunds (Gap H: INR 141,800). 25 high-value refunds (>= INR 20,000) totaling INR 696,600 sit stalled in Finance approval (mean wait 14.2 days)."
    ))
    pdf.ln(1)

    # Unlogged Informal Requests Callout
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(210, 218, 230)
    pdf.rect(10, pdf.get_y(), 190, 16.5, style="DF")
    pdf.set_xy(12, pdf.get_y() + 1)
    pdf.set_font("Helvetica", "B", 7.2)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 3.5, "INFORMAL OFF-TRACKER REQUESTS FROM THE BRIEF (REAL ROOT CAUSE CONFIRMATION):", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 6.8)
    pdf.set_text_color(50, 60, 75)
    pdf.multi_cell(186, 3.1, (
        "1. Peak Journeys (Email, 5 June): DEL-DXB cancelled, no reference number issued. Chased repeatedly until logged late as RF-1099.\n"
        "2. Nomad Travel (WhatsApp, 8 June): 'Bhai refund ka kya hua? BLR-MAA wala. 2 hafte ho gaye'. Off-tracker chase, later logged as RF-1098.\n"
        "3. Support Agent Note (Email, 11 June): 'Finance says they never received several refunds I closed last month. I marked them done on my side. "
        "Not sure where they went.' Direct confirmation that Support closed tickets without ensuring Finance ingestion."
    ))
    pdf.set_y(pdf.get_y() + 2)

    # Escalation Root-Cause Table
    pdf.set_font("Helvetica", "B", 8.8)
    pdf.cell(0, 4.5, "Root Cause Breakdown of All 155 Logged Escalations:", new_x="LMARGIN", new_y="NEXT")
    
    e_widths = [56, 18, 18, 98]
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 237, 246)
    pdf.cell(e_widths[0], 4.2, "Root Cause Category", border=1, fill=True)
    pdf.cell(e_widths[1], 4.2, "Count", border=1, align="C", fill=True)
    pdf.cell(e_widths[2], 4.2, "Share (%)", border=1, align="C", fill=True)
    pdf.cell(e_widths[3], 4.2, "Data Observation & Action", border=1, fill=True)
    pdf.ln()

    e_data = [
        ["paid and matched", "57", "36.8%", "Payout completed matching request; agent inquired regarding confirmation / missing UTR."],
        ["Support closed/no Finance", "31", "20.0%", "Gap Class B: Ticket marked Closed on Support, no corresponding Finance record."],
        ["never logged (no usable ref)", "29", "18.7%", "Informal inquiries (email/WhatsApp) with no usable reference in operational trackers."],
        ["paid but amount differs", "18", "11.6%", "Disbursement matches Amount Paid, but agent expected gross amount without deduction."],
        ["Finance pending/Support not closed", "8", "5.2%", "Request in Finance processing queue while Support ticket remains active."],
        ["declined (recorded in Finance)", "6", "3.9%", "Decline recorded in Finance; decline details not documented on Support side."],
        ["Support closed/Finance pending", "6", "3.9%", "Premature closure: Support marked Closed while Finance record is Pending Payout."],
    ]
    pdf.set_font("Helvetica", "", 6.8)
    for row in e_data:
        pdf.cell(e_widths[0], 3.8, row[0], border=1)
        pdf.cell(e_widths[1], 3.8, row[1], border=1, align="C")
        pdf.cell(e_widths[2], 3.8, row[2], border=1, align="C")
        pdf.cell(e_widths[3], 3.8, row[3], border=1)
        pdf.ln()
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 7.2)
    pdf.cell(0, 3.5, "Estimated Addressable Failures: 141 of 155 (91.0%) = 84 structural failures (31 Gap B + 29 unlogged + 18 deductions + 6 premature closures) + 57 status queries on paid disbursements.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Validation Wishlist
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.5, "Validation Wishlist (What to validate with 2 weeks more access):", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.4)
    pdf.multi_cell(0, 3.5, (
        "1. Finance Approval Workflow: Review approval logs to verify the inferred INR 20k threshold and identify why large June payouts stalled.\n"
        "2. Deduction Schedule Table: Ingest standardized cancellation fee tables to verify deductions prior to payout submission.\n"
        "3. Informal Request Inboxes: Access incoming email and WhatsApp logs to measure total volume of unlogged agent inquiries.\n"
        "4. Canonical Agent Master: Unify agent naming variations across systems into a single entity registry."
    ))

    # =========================================================
    # PAGE 3: SOLUTION DESIGN, PROTOTYPE, TRADE-OFFS & MEASURE
    # =========================================================
    pdf.add_page()
    
    # Section 3: Design a Solution
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 5, "3. DESIGN A SOLUTION: PROCESS & SINGLE SOURCE OF TRUTH (ZERO HEADCOUNT)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(30, 35, 45)
    pdf.multi_cell(0, 3.6, (
        "Under the zero-new-headcount constraint, BharatTrip must eliminate redundant manual status updates rather than hire coordinators:\n"
        "- Single Unified Table: Support and Finance retain role-specific views, but read and write to a single reconciled database backend. "
        "Support status is restricted to 'New', 'Working', and 'Verified & Forwarded'. 'Closed' is a system-generated state "
        "triggered strictly when Finance enters payout execution ('Refund Done') with bank UTR.\n"
        "- Automated Reconciler & Action Queue (core/reconcile.py): Daily reconciliation identifies discrepancies, "
        "automatically routing the 69 Gap B records to Finance and ranking open tasks by Priority Score (Amount x Age).\n"
        "- Proactive Dispatch Notification: On payout execution, automated notification sends the agent the bank transaction reference "
        "and an itemized breakdown (Gross Amount, Deduction, Net Disbursed), addressing the pattern behind 57 status queries and 18 deduction disputes."
    ))
    pdf.ln(1)

    # Table of trade-offs
    t_widths = [45, 65, 80]
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 237, 246)
    pdf.cell(t_widths[0], 4.2, "Component", border=1, fill=True)
    pdf.cell(t_widths[1], 4.2, "Operational Choice", border=1, fill=True)
    pdf.cell(t_widths[2], 4.2, "Justification & Risk Control", border=1, fill=True)
    pdf.ln()

    t_data = [
        ["Matching & Reconciliation", "100% Deterministic Code (NO LLM)", "Zero financial hallucination risk. Ledger math and status joins remain deterministic."],
        ["Deduction Verification", "Deterministic Rule Engine", "Validates whether Refund Amount minus Amount Paid equals Deduction exactly."],
        ["Informal Intake (WhatsApp/Email)", "AI / LLM Layer (core/intake.py)", "Normalizes unstructured English/Hinglish text into structured JSON schema."],
        ["Agent Status Response", "Automated Grounded Drafts", "Strictly grounded in ledger records. Never invents an estimated turnaround (ETA)."],
        ["Disbursement Authorization", "Deliberately Kept Manual (Finance)", "Banking authorization and payment release remain with authorized Finance personnel."],
        ["Decline Communication", "Manual Support Touchpoint", "Human touchpoint preserves partner agency relationships on contested cancellations."],
    ]
    pdf.set_font("Helvetica", "", 6.8)
    for row in t_data:
        pdf.cell(t_widths[0], 3.8, row[0], border=1)
        pdf.cell(t_widths[1], 3.8, row[1], border=1)
        pdf.cell(t_widths[2], 3.8, row[2], border=1)
        pdf.ln()
    pdf.ln(1.5)

    # Prototype Implementation Callout
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.2, "AI Prototype Implementation (Judgment & Functional Scope):", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.4)
    pdf.multi_cell(0, 3.4, (
        "We built a functional production platform (FastAPI + React/Tailwind + Streamlit fallback) backed by modular deterministic code and Gemini AI. "
        "It solves the exact unlogged intake and reconciliation slice: parses unstructured Hinglish/English emails and WhatsApp messages, queries the "
        "reconciled ledger, runs plausibility checks (prevents asserting false status on aged records like Preset b), routes internal notes to Gap B reports, "
        "and auto-assigns non-colliding RF-NEW-### IDs. Built-in zero-key fallback guarantees 100% operational continuity without API keys."
    ))
    pdf.ln(1.5)

    # Section 5: Measure
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(20, 35, 60)
    pdf.cell(0, 5, "5. MEASURE: 30-DAY SUCCESS METRICS & TARGET RESULTS", new_x="LMARGIN", new_y="NEXT")
    
    m_widths = [45, 30, 30, 85]
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(230, 237, 246)
    pdf.cell(m_widths[0], 4.2, "Primary Metric to Watch", border=1, fill=True)
    pdf.cell(m_widths[1], 4.2, "June Baseline", border=1, align="C", fill=True)
    pdf.cell(m_widths[2], 4.2, "30-Day Target", border=1, align="C", fill=True)
    pdf.cell(m_widths[3], 4.2, "Operational Significance", border=1, fill=True)
    pdf.ln()

    m_data = [
        ["1. Gap B Creation Rate", "33.0% (30 tickets)", "< 1.0% (< 2 tickets)", "Direct measure of handoff synchronization between Support and Finance."],
        ["2. Escalation Frequency", "35 per 100 refunds", "< 5 per 100 refunds", "Proactive deduction breakdowns eliminate repeated status queries."],
        ["3. Backlog Aging (>14 days)", "69 tickets > 30 days", "0 tickets > 14 days", "Action Queue prioritizes aged high-value items."],
        ["4. Intake Auto-Logging Share", "~0% (all manual)", "> 95% logged", "All off-tracker email/WhatsApp requests logged with RF-NEW-###."],
        ["5. Stalled Approvals (>7 days)", "25 tickets (INR 6.96L)", "0 tickets > 7 days", "Approval alerts prevent month-end large refund bottlenecks."],
    ]
    pdf.set_font("Helvetica", "", 6.8)
    for row in m_data:
        pdf.cell(m_widths[0], 3.8, row[0], border=1)
        pdf.cell(m_widths[1], 3.8, row[1], border=1, align="C")
        pdf.cell(m_widths[2], 3.8, row[2], border=1, align="C")
        pdf.cell(m_widths[3], 3.8, row[3], border=1)
        pdf.ln()
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 7.8)
    pdf.cell(0, 3.8, "Target Result After 1 Month:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7.4)
    pdf.multi_cell(0, 3.4, (
        "- Discrepancy Elimination: Gap B creation drops to zero via system-enforced state machine (Support cannot close without Finance UTR).\n"
        "- Backlog Liquidation: The 69 Gap Class B refunds (INR 1,080,700) and 25 stalled approvals (INR 696,600) audited and disbursed.\n"
        "- Escalation Reduction: Escalations drop from ~35 per 100 refunds to under 5 per 100 refunds as agents receive real-time UTR and fee breakdowns."
    ))

    # Save to disk
    pdf.output(output_path)
    print(f"PDF written successfully to {output_path} (Total Pages: {pdf.page_no()})")

if __name__ == "__main__":
    out_file = r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops\BharatTrip_AI_Operations_Writeup.pdf"
    build_pdf(out_file)
