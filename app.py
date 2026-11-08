"""BharatTrip Refund Operations & AI Reconciliation Platform.
Streamlit Web Application (4 Tabs).
"""
import streamlit as st
import pandas as pd
import altair as alt

from core.config import (
    SNAPSHOT_DATE,
    GAP_CLASS_A,
    GAP_CLASS_B,
    GAP_CLASS_C,
    GAP_CLASS_D,
    GAP_CLASS_E,
    GAP_CLASS_H,
    GAP_CLASS_MATCH,
    DEFAULT_WORKBOOK_PATH,
)
from core.clean import load_and_clean_all
from core.reconcile import (
    reconcile_trackers,
    classify_escalation_root_causes,
    calculate_monthly_metrics,
    build_unified_ledger,
    export_ledger_to_excel,
)
from core.intake import (
    PRESET_A,
    PRESET_B,
    PRESET_C,
    get_llm_status,
    parse_informal_message,
    lookup_and_reconcile_intake,
)

# Page configuration
st.set_page_config(
    page_title="BharatTrip | Refund Operations & Reconciliation",
    page_icon="✈️",
    layout="wide",
)

# Cache data loading & reconciliation
@st.cache_data
def get_processed_data():
    data = load_and_clean_all(DEFAULT_WORKBOOK_PATH)
    reconciled = reconcile_trackers(data["support"], data["finance"])
    ledger = build_unified_ledger(reconciled, data["escalations"])
    esc_classified = classify_escalation_root_causes(
        data["escalations"], data["support"], data["finance"]
    )
    monthly_kpis = calculate_monthly_metrics(reconciled)
    return {
        "data": data,
        "reconciled": reconciled,
        "ledger": ledger,
        "escalations": esc_classified,
        "monthly_kpis": monthly_kpis,
    }

data_bundle = get_processed_data()
ledger = data_bundle["ledger"]
escalations = data_bundle["escalations"]
monthly_kpis = data_bundle["monthly_kpis"]
data = data_bundle["data"]
llm_status = get_llm_status()

# Header & Runtime Banner
st.title("✈️ BharatTrip | Refund Operations & Reconciliation Platform")
st.caption(f"Operational snapshot date fixed at: **{SNAPSHOT_DATE.strftime('%d %B %Y')}** | Single Source of Truth Prototype")

if llm_status["is_fallback"]:
    st.info(f"ℹ️ **Runtime Status:** {llm_status['banner']}. The platform is fully operational in standalone mode.")
else:
    st.success(f"✨ **Runtime Status:** {llm_status['banner']}.")

# 4 Core Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Overview & Trends",
    "🔍 Gaps & Action Queue",
    "⚠️ Escalation Root Causes",
    "🤖 AI Intake Assistant",
])

# ---------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW & TRENDS
# ---------------------------------------------------------
with tab1:
    st.header("Executive Operational Overview")
    
    # Top Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Support Tickets", len(data["support"]))
    with col2:
        st.metric("Total Finance Payouts", len(data["finance"]))
    with col3:
        st.metric("Matched in Both Trackers", len(ledger[ledger["clean_id"].isin(data["finance"]["clean_id"]) & ledger["clean_id"].isin(data["support"]["clean_id"])]))
    with col4:
        gap_b_len = len(ledger[ledger["gap_class"] == GAP_CLASS_B])
        gap_b_sum = ledger[ledger["gap_class"] == GAP_CLASS_B]["Refund Amount (INR)"].sum()
        # Red delta indicator for unrecorded gap B tickets
        st.metric("Gap B (Closed, No Fin)", f"{gap_b_len} tickets", delta=f"{gap_b_len} unrecorded (INR {gap_b_sum:,.0f})", delta_color="inverse")
    with col5:
        open_esc = (escalations["clean_status"] == "Open").sum()
        st.metric("Escalations", f"{len(escalations)} ({open_esc} Open)", delta=f"{open_esc} Unresolved", delta_color="inverse")

    st.markdown("---")
    st.subheader("Data Observations (Empirical Findings)")

    st.markdown("""
    * **Refund Request Volume Flat:** Total refund request volume remained steady across all 5 months (~140-150 requests per month).
    * **Gap Class B (Closed in Support, No Finance Record):** Support tickets marked 'Closed' with no corresponding Finance record increased from **2.1% in March to 18.7% in May and 33.0% in June** (representing **69 closed tickets with no Finance record**, totaling **INR 1,080,700**).
    * **Turnaround on Completed Payouts:** Average turnaround from Finance received date to payout date on completed records increased from **2.67 days in April to 6.52 days in May** *(unpaid refunds are excluded from this calculation)*.
    * **Approver Field Documentation:** Approver recorded on almost no June payouts because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data.
    * **Amount Differences:** Differences between Support requested amounts and Finance paid amounts matched the recorded Deduction in **47 out of 47** discrepancy cases.
    """)

    # Monthly Metrics Table & Charts
    st.markdown("### Monthly Operational Trends (Feb 2026 - Jun 2026)")
    st.dataframe(monthly_kpis, use_container_width=True)
    st.caption("Footnote: Unpaid and open refunds are excluded from turnaround calculations (survivorship constraint). Approver share denominator = all Refund Done rows in Finance (including Finance-only) by received month.")

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("#### Gap B Rate (% of Support Closed not in Finance)")
        chart_b = alt.Chart(monthly_kpis).mark_line(point=True, color="#d9534f").encode(
            x=alt.X("Month:N", title="Request Month"),
            y=alt.Y("Gap B Rate (%):Q", title="Gap B Rate (%)", scale=alt.Scale(domain=[0, 45])),
            tooltip=["Month", "Gap B Rate (%)", "Gap B (Closed, No Fin)", "Support Closed"]
        ).properties(height=280)
        st.altair_chart(chart_b, use_container_width=True)

    with c_right:
        st.markdown("#### Turnaround on Paid Refunds vs Finance Approver Share")
        base = alt.Chart(monthly_kpis).encode(x=alt.X("Month:N", title="Month"))
        bar_p = base.mark_bar(color="#0275d8", opacity=0.7).encode(
            y=alt.Y("Avg Finance Proc Days:Q", title="Avg Turnaround on Paid Refunds (Days)"),
            tooltip=["Month", "Avg Finance Proc Days", "Approval Share (%)"]
        )
        line_a = base.mark_line(point=True, color="#d9534f").encode(
            y=alt.Y("Approval Share (%):Q", title="Approver Recorded Share (%)"),
            tooltip=["Month", "Approval Share (%)"]
        )
        chart_p = alt.layer(bar_p, line_a).resolve_scale(y="independent").properties(height=280)
        st.altair_chart(chart_p, use_container_width=True)


# ---------------------------------------------------------
# TAB 2: GAPS & ACTION QUEUE
# ---------------------------------------------------------
with tab2:
    st.header("Refund Gaps & Prioritized Action Queue")
    st.markdown("Ranked by **Priority Score (Refund Amount x Age in Days)** to target maximum financial and agent risk under zero headcount additions.")

    # Ledger Download
    excel_bytes = export_ledger_to_excel(ledger)
    st.download_button(
        label="Download Unified Reconciled Ledger (.xlsx)",
        data=excel_bytes,
        file_name="BharatTrip_Unified_Refund_Ledger.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        gap_options = ["All Problem Gaps", "All Records"] + sorted(list(ledger["gap_class"].unique()))
        selected_gap = st.selectbox("Filter by Gap Class", gap_options, index=0)
    with f2:
        agent_list = ["All Agents"] + sorted(list(ledger["canonical_agent"].dropna().unique()))
        selected_agent = st.selectbox("Filter by Travel Agent", agent_list, index=0)
    with f3:
        team_filter = st.selectbox("Filter by Owner Team", ["All Teams", "Finance", "Support", "Joint"])

    # Apply filters
    filtered_df = ledger.copy()
    if selected_gap == "All Problem Gaps":
        filtered_df = filtered_df[filtered_df["gap_class"].isin([GAP_CLASS_B, GAP_CLASS_C, GAP_CLASS_D, GAP_CLASS_E, GAP_CLASS_H])]
    elif selected_gap != "All Records":
        filtered_df = filtered_df[filtered_df["gap_class"] == selected_gap]

    if selected_agent != "All Agents":
        filtered_df = filtered_df[filtered_df["canonical_agent"] == selected_agent]

    if team_filter != "All Teams":
        filtered_df = filtered_df[filtered_df["owner_team"] == team_filter]

    # Sort by priority score
    filtered_df = filtered_df.sort_values(by="priority_score", ascending=False)

    st.markdown(f"**Showing {len(filtered_df)} records:**")
    st.dataframe(
        filtered_df[[
            "clean_id", "canonical_agent", "route", "Refund Amount (INR)", "Amount Paid (INR)",
            "Deduction (INR)", "clean_status", "clean_payout_status", "gap_class",
            "deduction_explains", "effective_age_days", "open_escalations", "owner_team",
            "recommended_action", "priority_score"
        ]],
        use_container_width=True,
    )

    # Flagged Discrepancy Tables
    with st.expander("View Flagged Duplicate & Conflicting Records (Audit Trail)"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Support Duplicate Conflicts (10 tickets with conflicting amount/status):**")
            st.dataframe(data["support_conflicts"], use_container_width=True)
        with c2:
            st.markdown("**Finance Re-entries / Duplicates Dropped (9 entries):**")
            st.dataframe(data["finance_duplicates"][["clean_id", "Amount Paid (INR)", "Processed On", "Remarks"]], use_container_width=True)


# ---------------------------------------------------------
# TAB 3: ESCALATION ROOT CAUSES
# ---------------------------------------------------------
with tab3:
    st.header("Escalation Root Causes (All 155 Logged Complaints)")

    esc_counts = escalations["root_cause"].value_counts().reset_index()
    esc_counts.columns = ["Root Cause Category", "Complaint Count"]
    esc_counts["Share (%)"] = (esc_counts["Complaint Count"] / len(escalations) * 100).round(1)

    c_left, c_right = st.columns([1, 1])
    with c_left:
        st.markdown("### Escalation Breakdown by Diagnosis")
        st.dataframe(esc_counts, use_container_width=True)

    with c_right:
        st.markdown("### Distribution")
        chart_esc = alt.Chart(esc_counts).mark_bar().encode(
            x=alt.X("Complaint Count:Q", title="Complaints"),
            y=alt.Y("Root Cause Category:N", sort="-x", title="Root Cause"),
            color=alt.Color("Complaint Count:Q", legend=None, scale=alt.Scale(scheme="reds")),
            tooltip=["Root Cause Category", "Complaint Count", "Share (%)"]
        ).properties(height=300)
        st.altair_chart(chart_esc, use_container_width=True)

    st.markdown("### Detailed Escalation Log")
    filter_rc = st.selectbox("Filter Complaints by Root Cause", ["All"] + list(esc_counts["Root Cause Category"]))
    display_esc = escalations.copy()
    if filter_rc != "All":
        display_esc = display_esc[display_esc["root_cause"] == filter_rc]

    st.dataframe(
        display_esc[[
            "clean_escalation_id", "parsed_raised_on", "clean_ticket_id", "canonical_agent",
            "Channel", "Complaint", "root_cause", "clean_status", "Days Open"
        ]],
        use_container_width=True,
    )


# ---------------------------------------------------------
# TAB 4: AI INTAKE ASSISTANT
# ---------------------------------------------------------
with tab4:
    st.header("AI Intake Assistant & Message Normalizer")
    st.markdown("""
    Captures informal requests (Email, WhatsApp, Hinglish), normalizes them into structured JSON,
    performs unique ledger reconciliation, and generates grounded, truthful agent draft replies.
    """)

    st.markdown("#### 1-Click Interactive Demo Presets")
    col_a, col_b, col_c = st.columns(3)
    
    preset_choice = None
    with col_a:
        if st.button("Preset (a): Peak Journeys (Email)"):
            preset_choice = PRESET_A
    with col_b:
        if st.button("Preset (b): Nomad Travel (Hinglish WA)"):
            preset_choice = PRESET_B
    with col_c:
        if st.button("Preset (c): Internal Support Note"):
            preset_choice = PRESET_C

    # Set initial text
    default_text = preset_choice["text"] if preset_choice else PRESET_B["text"]
    default_channel = preset_choice["channel"] if preset_choice else "WhatsApp"
    default_date = preset_choice["date"] if preset_choice else "2026-06-08"

    in_col1, in_col2 = st.columns([3, 1])
    with in_col1:
        message_input = st.text_area("Customer / Agent Raw Message:", value=default_text, height=110)
    with in_col2:
        channel_input = st.selectbox("Channel", ["WhatsApp", "Email", "Phone", "Portal"], index=0 if default_channel == "WhatsApp" else 1)
        date_input = st.text_input("Date Received", value=default_date)

    if st.button("Process & Reconcile Message", type="primary"):
        with st.spinner("Analyzing message and querying unified ledger..."):
            parsed_json = parse_informal_message(message_input, channel=channel_input, date_str=date_input)
            match_result = lookup_and_reconcile_intake(parsed_json, ledger)

        st.markdown("---")
        res_col1, res_col2 = st.columns([1, 1])

        with res_col1:
            st.markdown("### 1. Extracted Structured JSON")
            st.json(parsed_json)

            st.markdown("### 2. Reconciliation & Match Status")
            m_type = match_result["match_type"]
            if m_type == "UNIQUE_MATCH":
                st.success(f"Unique Match Found: Ticket `{match_result['ticket_id']}`")
                st.write(f"**Ledger Status:** {match_result['status_summary']}")
                st.dataframe(pd.DataFrame([match_result["matched_ticket"]]))
            elif m_type == "MULTIPLE_MATCHES":
                st.warning(f"Multiple Matches Found ({match_result['candidate_count']} tickets):")
                st.write(match_result["message"])
                st.dataframe(pd.DataFrame(match_result["candidates"]))
            elif m_type == "INTERNAL_GAP_REPORT":
                st.info(f"{match_result['message']}")
                st.metric("Total Gap B Tickets", f"{match_result['gap_b_count']} refunds", f"INR {match_result['gap_b_sum']:,.0f}")
                st.dataframe(pd.DataFrame(match_result["candidates"]))
            else:
                st.warning(f"{match_result['message']}")
                st.dataframe(pd.DataFrame([match_result["new_ticket"]]))

        with res_col2:
            st.markdown("### 3. Grounded Draft Agent Reply")
            st.text_area("Draft Response (Read-only, strictly verified against ledger):", value=match_result["draft_reply"], height=240)
            st.info("Operational Safeguard: This draft was generated strictly from ledger facts. It will never state an estimated turnaround (ETA) or unverified completion.")
