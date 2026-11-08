"""Generate the official 3-page submission PDF for BharatTrip AI Operations Associate.
Strictly constrained to max 3 pages, concise, high-signal, covering:
1. Define the problem.
2. Analyse.
3. Design a solution.
5. Measure.
Uses pure ASCII characters and objective observational language.
"""
from fpdf import FPDF

class SubmissionPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "BHARATTRIP -- AI OPERATIONS ASSOCIATE SCREENING STAGE | REFUND RECONCILIATION", border=0, align="L")
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, f"Page {self.page_no()}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, 12, 200, 12)
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "Confidential -- BharatTrip Operational Evaluation | Working Prototype: streamlit run app.py / uvicorn api:app", align="C")

def build_pdf(output_path: str):
    pdf = SubmissionPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(12, 14, 12)
    pdf.set_auto_page_break(auto=False)

    # =========================================================
    # PAGE 1
    # =========================================================
    pdf.add_page()
    
    # Title Block
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 7, "Operational Audit & AI Reconciliation Strategy", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 100, 115)
    pdf.cell(0, 5, "Author: AI Operations Associate Candidate | Date: 30 June 2026 Snapshot | Focus: Zero-Headcount Optimization", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Section 1: Define the Problem
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 6, "1. DEFINE THE PROBLEM: DATA OBSERVATIONS vs. REPORTED SYMPTOM", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 4.2, (
        "Leadership's stated symptom is that 'escalations have been climbing for two months while refund volume is flat.' "
        "The underlying diagnosis is an operational disconnection between the two independent trackers rather than external volume growth.\n\n"
        "Three distinct empirical observations explain the escalation pattern while refund request volume remains steady (~145/month):\n"
        "1. Gap Class B (Closed in Support, No Finance Record): Support marked tickets 'Closed' with notes like 'refund processed, informed agent'. "
        "However, no corresponding record exists in Finance Tracker. This rate increased from 2.1% in March to 18.7% in May and 33.0% in June. "
        "Across the snapshot, exactly 69 closed tickets with no Finance record exist, totaling INR 1,080,700.\n"
        "2. Finance Processing Turnaround & Documentation: Turnaround measured from Finance received date to payout date on completed records "
        "increased from an average of 2.67 days in April to 6.52 days in May (unpaid refunds are excluded from this calculation). "
        "Additionally, an approver was recorded on almost no June payouts because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.\n"
        "3. Recorded Deductions on Disbursements: When payouts occurred, Finance recorded Deductions (averaging INR 1,500-2,600). Support records "
        "do not document these deductions, leading travel agents to escalate regarding differences between requested and credited amounts."
    ))
    pdf.ln(3)

    # Section 2: Analyse (Part 1 - Data Evidence)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "2. OPERATIONAL ANALYSIS: EMPIRICAL METRICS ACROSS 5 MONTHS", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.multi_cell(0, 4.2, (
        "Reconciling 733 unique Support rows and 680 Finance rows reveals 749 unique refund cases. "
        "Request volume remained steady across all 5 months (Feb: 144, Mar: 152, Apr: 147, May: 148, Jun: 142). "
        "Below is the verified monthly operational summary:"
    ))
    pdf.ln(2)

    # Table: Monthly Trends
    col_widths = [20, 22, 24, 25, 27, 26, 22, 20]
    headers = ["Month", "Requests", "Support Clsd", "Gap B (Count)", "Gap B Rate", "Avg Proc Time", "Done Count", "Approver %"]
    
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(235, 240, 248)
    pdf.set_text_color(20, 35, 60)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 5, h, border=1, align="C", fill=True)
    pdf.ln()

    rows_data = [
        ["Feb 2026", "144", "137", "4", "2.9%", "2.89 days", "111", "32 (28.8%)"],
        ["Mar 2026", "152", "146", "3", "2.1%", "2.87 days", "154", "46 (29.9%)"],
        ["Apr 2026", "147", "145", "6", "4.1%", "2.67 days", "139", "41 (29.5%)"],
        ["May 2026", "148", "139", "26", "18.7%", "6.52 days", "120", "29 (24.2%)"],
        ["Jun 2026", "142", "91", "30", "33.0%", "4.88 days", "59", "1 (1.7%)"],
    ]
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(30, 30, 30)
    for r in rows_data:
        for i, val in enumerate(r):
            fill = True if ("33.0%" in val or "1 (1.7%)" in val or ("30" in val and i==3)) else False
            if fill:
                pdf.set_fill_color(255, 230, 230)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(col_widths[i], 4.5, val, border=1, align="C", fill=fill)
        pdf.ln()
    pdf.ln(2)

    pdf.set_font("Helvetica", "I", 7.5)
    pdf.cell(0, 4, "Footnote: Unpaid refunds are excluded from turnaround calculations. Approver share denominator = all Finance Refund Done rows by received month.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.5, "Key Takeaway from Table:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.multi_cell(0, 4, (
        "While request volume stayed steady (~145/mo), completed disbursements recorded in Finance for June requests were 59, "
        "while Support closed tickets with no Finance record reached 30 (33.0% of Support closures in June). "
        "This explains the concentration of agent chases in May and June."
    ))

    # =========================================================
    # PAGE 2
    # =========================================================
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "2. OPERATIONAL ANALYSIS (CONT.): TRACKER COMPARISONS & ROOT CAUSES", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 4.2, (
        "The two trackers agree on 664 refunds, with 571 completed payouts in Support, but show specific variances in other records:\n"
        "- Finance Only (Class H - 16 refunds): Finance recorded INR 141,800 in disbursements with no ticket in Support_Tracker.\n"
        "- Status Variances (Gap C & D - 18 refunds): 12 tickets are Closed in Support but Pending Payout in Finance (INR 186,000 Support sum). "
        "6 tickets are Closed in Support but Declined in Finance (INR 94,800 Support sum).\n"
        "- Amount Differences (Gap Class E - 47 refunds): Support and Finance record different amounts for 47 completed payouts in Support. "
        "Deduction exactly explains all 47 of these differences (Support Refund Amount minus Amount Paid equals recorded Deduction).\n"
        "- Duplicate Rule: Conflicting duplicate ticket IDs in Support were resolved by keeping the latest Last Updated; on a tie, "
        "keeping the row whose Refund Amount equals Finance Amount Paid or Amount Paid + Deduction; otherwise keeping the later row in the sheet."
    ))
    pdf.ln(2)

    # Escalation Root-Cause Table
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Root Cause Classification of All 155 Logged Escalations:", new_x="LMARGIN", new_y="NEXT")
    
    e_widths = [60, 20, 20, 86]
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(235, 240, 248)
    pdf.cell(e_widths[0], 5, "Root Cause Category", border=1, fill=True)
    pdf.cell(e_widths[1], 5, "Count", border=1, align="C", fill=True)
    pdf.cell(e_widths[2], 5, "Share (%)", border=1, align="C", fill=True)
    pdf.cell(e_widths[3], 5, "Data Observation & Action", border=1, fill=True)
    pdf.ln()

    e_data = [
        ["paid and matched", "57", "36.8%", "Payout recorded in Finance matching request; agent inquired regarding status confirmation."],
        ["Support closed/no Finance", "31", "20.0%", "Gap Class B: Ticket marked Closed on Support, no corresponding Finance record."],
        ["never logged (no usable ref)", "29", "18.7%", "Informal inquiries with no usable reference found in operational trackers."],
        ["paid but amount differs", "18", "11.6%", "Disbursement matches Amount Paid, but agent expected gross amount without deduction."],
        ["Finance pending/Support not closed", "8", "5.2%", "Request in Finance processing queue while Support ticket remains active."],
        ["declined (unexplained)", "6", "3.9%", "Record declined in Finance; decline details not documented on Support side."],
        ["Support closed/Finance pending", "6", "3.9%", "Support ticket marked Closed while Finance record remains in Pending Payout."],
    ]
    pdf.set_font("Helvetica", "", 7.2)
    for row in e_data:
        pdf.cell(e_widths[0], 4.3, row[0], border=1)
        pdf.cell(e_widths[1], 4.3, row[1], border=1, align="C")
        pdf.cell(e_widths[2], 4.3, row[2], border=1, align="C")
        pdf.cell(e_widths[3], 4.3, row[3], border=1)
        pdf.ln()
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.5, "Validation Wishlist (What to validate with 2 weeks more access):", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, (
        "1. Finance Approval Workflow: Review workflow logs to verify inferred INR 20k approval threshold and understand pending large refunds.\n"
        "2. Deduction Schedule Table: Ingest standardized cancellation fee tables to verify deductions prior to payout submission.\n"
        "3. Informal Request Inboxes: Access incoming email and WhatsApp logs to measure volume of unlogged agent inquiries."
    ))
    pdf.ln(3)

    # Section 3: Design a Solution
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "3. DESIGN A SOLUTION: PROCESS & SINGLE SOURCE OF TRUTH (ZERO HEADCOUNT)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 4.2, (
        "Under the no-new-headcount constraint, BharatTrip must link existing workflows into a single source of truth without adding manual checkers:"
    ))
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, (
        "- Single Unified Table: Support and Finance retain operational interfaces, but read/write to a shared backend. "
        "Support status is limited to 'New', 'Working', and 'Verified & Forwarded'. 'Closed' is a system-generated state "
        "triggered strictly when Finance records 'Payout Status = Refund Done'.\n"
        "- Automated Reconciler & Action Queue (core/reconcile.py): Daily reconciliation identifies discrepancies, "
        "automatically routing the 69 Gap B records to Finance and ranking open tasks by Priority Score (Amount x Age).\n"
        "- Proactive Dispatch Notification: On payout execution, automated notification sends the agent the bank transaction reference "
        "and an itemized breakdown (Gross Amount, Deduction, Net Disbursed), addressing the pattern behind 57 status queries and 18 deduction disputes."
    ))

    # =========================================================
    # PAGE 3
    # =========================================================
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "3. DESIGN A SOLUTION (CONT.): AUTOMATION TRADE-OFFS & AI PROTOTYPE", new_x="LMARGIN", new_y="NEXT")
    
    # Table of trade-offs
    t_widths = [45, 65, 76]
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(235, 240, 248)
    pdf.cell(t_widths[0], 5, "Component", border=1, fill=True)
    pdf.cell(t_widths[1], 5, "Operational Choice", border=1, fill=True)
    pdf.cell(t_widths[2], 5, "Justification & Risk Control", border=1, fill=True)
    pdf.ln()

    t_data = [
        ["Matching & Reconciliation", "100% Deterministic Code (NO LLM)", "Zero financial hallucination risk. Ledger math and status joins remain deterministic."],
        ["Deduction Verification", "Deterministic Rule Engine", "Validates whether Refund Amount minus Amount Paid equals Deduction exactly."],
        ["Informal Intake (WhatsApp/Email)", "AI / LLM Layer (core/intake.py)", "Normalizes unstructured English/Hinglish text into structured JSON schema."],
        ["Agent Status Response", "Automated Grounded Drafts", "Strictly grounded in ledger records. Never invents an estimated turnaround (ETA)."],
        ["Disbursement Authorization", "Deliberately Kept Manual (Finance)", "Banking authorization remains with Finance personnel."],
        ["Decline Communication", "Manual Support Touchpoint", "Maintains partner agency communication on contested cancellations."],
    ]
    pdf.set_font("Helvetica", "", 7.2)
    pdf.set_text_color(30, 30, 30)
    for row in t_data:
        pdf.cell(t_widths[0], 4.5, row[0], border=1)
        pdf.cell(t_widths[1], 4.5, row[1], border=1)
        pdf.cell(t_widths[2], 4.5, row[2], border=1)
        pdf.ln()
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "AI Prototype Implementation:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.2)
    pdf.multi_cell(0, 3.8, (
        "We built a functional platform backed by modular deterministic code (core/clean.py, core/reconcile.py), "
        "FastAPI backend (api.py), and an AI intake engine (core/intake.py):\n"
        "1. Executive Overview: Visualizes Gap B trends (2.9% to 33.0%) and turnaround on paid refunds.\n"
        "2. Action Queue & SOT Ledger: Filterable ledger ranking items by priority score with Excel export.\n"
        "3. Escalation Diagnostics: Categorization across the 8 root cause classes.\n"
        "4. AI Intake Assistant: Extracts fields from raw messages, queries the ledger, and drafts grounded replies. "
        "Enforces unique matching (requests clarification on multiple candidates, routes internal notes to Gap B reports, "
        "and assigns non-colliding RF-NEW-### IDs for new inquiries). Built-in zero-key fallback ensures reliable operation without API keys."
    ))
    pdf.ln(4)

    # Section 5: Measure
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 6, "5. MEASURE: 30-DAY SUCCESS METRICS & TARGET RESULTS", new_x="LMARGIN", new_y="NEXT")
    
    m_widths = [45, 30, 30, 81]
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_fill_color(235, 240, 248)
    pdf.cell(m_widths[0], 5, "Metric to Watch", border=1, fill=True)
    pdf.cell(m_widths[1], 5, "June Baseline", border=1, align="C", fill=True)
    pdf.cell(m_widths[2], 5, "30-Day Target", border=1, align="C", fill=True)
    pdf.cell(m_widths[3], 5, "Operational Significance", border=1, fill=True)
    pdf.ln()

    m_data = [
        ["1. Gap B Creation Rate", "33.0% (30 tickets)", "< 2.0% (< 3 tickets)", "Direct measure of Support-Finance handoff synchronization."],
        ["2. Escalation Rate", "35 per 100 refunds", "< 8 per 100 refunds", "Proactive deduction breakdowns eliminate repeated status queries."],
        ["3. Backlog Aging (>14 days)", "69 tickets > 30 days", "0 tickets > 14 days", "Action Queue prioritizes aged high-value items."],
        ["4. Intake Auto-Logging Share", "~0% (all manual)", "> 90% logged", "All off-tracker email/WhatsApp requests logged with RF-NEW-###."],
    ]
    pdf.set_font("Helvetica", "", 7.5)
    for row in m_data:
        pdf.cell(m_widths[0], 4.5, row[0], border=1)
        pdf.cell(m_widths[1], 4.5, row[1], border=1, align="C")
        pdf.cell(m_widths[2], 4.5, row[2], border=1, align="C")
        pdf.cell(m_widths[3], 4.5, row[3], border=1)
        pdf.ln()
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(0, 4.5, "Target Result After 1 Month:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 3.8, (
        "- Unrecorded Discrepancy Elimination: Weekly complaints of unrecorded requests drop toward zero.\n"
        "- Backlog Resolution: The 69 Gap Class B refunds (INR 1,080,700) audited and queued for payment.\n"
        "- Escalation Volume: Overall escalation rate drops from ~35 per 100 refunds to under 8 per 100 refunds."
    ))

    # Save to disk
    pdf.output(output_path)
    print(f"PDF written successfully to {output_path} (Total Pages: {pdf.page_no()})")

if __name__ == "__main__":
    out_file = r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops\BharatTrip_AI_Operations_Writeup.pdf"
    build_pdf(out_file)
