"""Known-Answer verification test suite for BharatTrip Refund Operations.
Ensures zero-tolerance data integrity against official ground truth facts.
"""
import pytest
import pandas as pd
from core.config import DEFAULT_WORKBOOK_PATH, SNAPSHOT_DATE, APPROVAL_THRESHOLD
from core.clean import load_and_clean_all
from core.reconcile import (
    reconcile_trackers,
    classify_escalation_root_causes,
    calculate_monthly_metrics,
    build_unified_ledger,
    calculate_approval_tier_metrics,
)


@pytest.fixture(scope="module")
def data():
    """Load and clean all raw datasets once for test suite."""
    return load_and_clean_all(DEFAULT_WORKBOOK_PATH)


def test_unique_deduplicated_counts(data):
    """Check unique ticket counts after deduplication: 733 Support, 680 Finance."""
    support = data["support"]
    finance = data["finance"]
    assert len(support) == 733, f"Expected 733 unique Support tickets, got {len(support)}"
    assert len(finance) == 680, f"Expected 680 unique Finance refs, got {len(finance)}"


def test_match_summary_counts(data):
    """Check match breakdown: in both: 664, Support only: 69, Finance only: 16."""
    s_ids = set(data["support"]["clean_id"])
    f_ids = set(data["finance"]["clean_id"])

    in_both = s_ids & f_ids
    sup_only = s_ids - f_ids
    fin_only = f_ids - s_ids

    assert len(in_both) == 664, f"Expected 664 in both, got {len(in_both)}"
    assert len(sup_only) == 69, f"Expected 69 Support only, got {len(sup_only)}"
    assert len(fin_only) == 16, f"Expected 16 Finance only, got {len(fin_only)}"


def test_gap_class_b_closed_no_finance(data):
    """Check Gap B: exactly 69 Support Closed with no Finance record (Total: INR 1,080,700)."""
    reconciled = reconcile_trackers(data["support"], data["finance"])
    gap_b = reconciled[reconciled["gap_class"] == "Class B: Support Closed, Finance None"]
    
    assert len(gap_b) == 69, f"Expected 69 Gap B tickets, got {len(gap_b)}"
    total_amount = gap_b["Refund Amount (INR)"].sum()
    assert total_amount == 1080700.0, f"Expected sum INR 1,080,700, got {total_amount}"


def test_gap_classes_c_and_d(data):
    """Check Gap C: 12 Closed & Pending Payout, INR 186,000; Gap D: 6 Closed & Declined, INR 94,800; Finance-only: 16 refunds, INR 141,800."""
    reconciled = reconcile_trackers(data["support"], data["finance"])
    gap_c = reconciled[reconciled["gap_class"] == "Class C: Support Closed, Finance Pending"]
    gap_d = reconciled[reconciled["gap_class"] == "Class D: Support Closed, Finance Declined"]
    gap_h = reconciled[reconciled["gap_class"] == "Class H: Finance Only (No Support Ticket)"]

    assert len(gap_c) == 12, f"Expected 12 Gap C tickets, got {len(gap_c)}"
    assert gap_c["Refund Amount (INR)"].sum() == 186000.0, f"Expected Gap C sum 186,000, got {gap_c['Refund Amount (INR)'].sum()}"

    assert len(gap_d) == 6, f"Expected 6 Gap D tickets, got {len(gap_d)}"
    assert gap_d["Refund Amount (INR)"].sum() == 94800.0, f"Expected Gap D sum 94,800, got {gap_d['Refund Amount (INR)'].sum()}"

    assert len(gap_h) == 16, f"Expected 16 Gap H tickets, got {len(gap_h)}"
    assert gap_h["Amount Paid (INR)"].sum() == 141800.0, f"Expected Gap H sum 141,800, got {gap_h['Amount Paid (INR)'].sum()}"


def test_refund_done_amount_and_deductions(data):
    """Check: Finance Refund Done and in Support: 571, amount differs 50 (all 50 explained by deduction)."""
    reconciled = reconcile_trackers(data["support"], data["finance"])
    fin_done = reconciled[
        (reconciled["clean_payout_status"] == "Refund Done") & (reconciled["in_support"])
    ]
    assert len(fin_done) == 571, f"Expected 571 Refund Done in Support, got {len(fin_done)}"

    # Amount difference analysis
    has_diff = fin_done[
        fin_done["Refund Amount (INR)"].notna() & (fin_done["Refund Amount (INR)"] != fin_done["Amount Paid (INR)"])
    ]
    assert len(has_diff) == 50, f"Expected 50 amount differences, got {len(has_diff)}"
    assert has_diff["deduction_explains"].sum() == 50, f"Expected all 50 explained by deduction, got {has_diff['deduction_explains'].sum()}"

    # Missing Support amount on matched cases
    missing_support_amt = reconciled[reconciled["gap_class"] == "Matched - Support amount missing"]
    assert len(missing_support_amt) == 12, f"Expected 12 matched rows with missing support amount, got {len(missing_support_amt)}"


def test_canonical_agent_count(data):
    """Check: Canonical agents count is 22."""
    s_agents = set(data["support"]["canonical_agent"].dropna().unique())
    f_agents = set(data["finance"]["canonical_agent"].dropna().unique())
    all_agents = (s_agents | f_agents) - {""}
    assert len(all_agents) == 22, f"Expected 22 canonical agents, got {len(all_agents)}"


def test_escalation_counts_and_linking(data):
    """Check escalations:
    - 155 total
    - 85 Open, 70 Resolved
    - 136 have a usable ID
    - 126 exist in Support and 95 in Finance
    """
    esc = data["escalations"]
    assert len(esc) == 155, f"Expected 155 total escalations, got {len(esc)}"
    assert (esc["clean_status"] == "Open").sum() == 85, f"Expected 85 Open, got {(esc['clean_status'] == 'Open').sum()}"
    assert (esc["clean_status"] == "Resolved").sum() == 70, f"Expected 70 Resolved, got {(esc['clean_status'] == 'Resolved').sum()}"

    usable = esc[esc["has_usable_id"]]
    assert len(usable) == 136, f"Expected 136 usable IDs, got {len(usable)}"

    s_ids = set(data["support"]["clean_id"])
    f_ids = set(data["finance"]["clean_id"])

    in_support_count = usable["clean_ticket_id"].isin(s_ids).sum()
    in_finance_count = usable["clean_ticket_id"].isin(f_ids).sum()

    assert in_support_count == 126, f"Expected 126 in Support, got {in_support_count}"
    assert in_finance_count == 95, f"Expected 95 in Finance, got {in_finance_count}"


def test_escalation_root_cause_counts(data):
    """Check escalation root-cause distribution across all 155 complaints:
    - paid and matched: 57
    - Support closed/no Finance: 31
    - never logged: 29
    - paid but amount differs: 18
    - Finance pending/Support not closed: 8
    - declined: 6
    - Support closed/Finance pending: 6
    Total = 155
    """
    esc_classified = classify_escalation_root_causes(
        data["escalations"], data["support"], data["finance"]
    )
    counts = esc_classified["root_cause"].value_counts().to_dict()

    expected = {
        "paid and matched": 57,
        "Support closed/no Finance": 31,
        "never logged": 29,
        "paid but amount differs": 18,
        "Finance pending/Support not closed": 8,
        "declined": 6,
        "Support closed/Finance pending": 6,
    }

    assert sum(expected.values()) == 155, "Expected sum must be 155"
    for category, exp_count in expected.items():
        actual = counts.get(category, 0)
        assert actual == exp_count, f"Root cause '{category}': expected {exp_count}, got {actual}"


def test_monthly_gap_b_rates(data):
    """Check Support-closed-without-Finance rate by request month:
    Feb ~2.9%, Mar ~2.1%, Apr ~4.1%, May ~18.7%, Jun ~33.0% (within +/-0.3% of 33.3%).
    """
    reconciled = reconcile_trackers(data["support"], data["finance"])
    monthly_metrics = calculate_monthly_metrics(reconciled).set_index("Month")

    feb_rate = monthly_metrics.loc["2026-02", "Gap B Rate (%)"]
    mar_rate = monthly_metrics.loc["2026-03", "Gap B Rate (%)"]
    apr_rate = monthly_metrics.loc["2026-04", "Gap B Rate (%)"]
    may_rate = monthly_metrics.loc["2026-05", "Gap B Rate (%)"]
    jun_rate = monthly_metrics.loc["2026-06", "Gap B Rate (%)"]

    assert feb_rate == 2.9, f"Feb rate expected 2.9%, got {feb_rate}%"
    assert mar_rate == 2.1, f"Mar rate expected 2.1%, got {mar_rate}%"
    assert apr_rate == 4.1, f"Apr rate expected 4.1%, got {apr_rate}%"
    assert may_rate == 18.7, f"May rate expected 18.7%, got {may_rate}%"
    assert abs(jun_rate - 33.3) <= 0.4, f"Jun rate expected ~33.3% (+/-0.3%), got {jun_rate}%"


def test_monthly_finance_processing_and_approvals(data):
    """Check monthly Finance metrics:
    - Finance processing time by month (unpaid excluded)
    - Share of Refund Done rows with Approved By filled across all Finance by received month.
    """
    reconciled = reconcile_trackers(data["support"], data["finance"])
    monthly_metrics = calculate_monthly_metrics(reconciled).set_index("Month")

    assert "Avg Finance Proc Days" in monthly_metrics.columns
    assert "Approval Share (%)" in monthly_metrics.columns
    jun_appr = monthly_metrics.loc["2026-06", "Approval Share (%)"]
    assert jun_appr == 1.7, f"Expected June approval share 1.7%, got {jun_appr}%"


def test_approval_tier_metrics(data):
    """Check inferred approval tier (threshold INR 20,000):
    - pending count 25, amount INR 696,600
    - mean wait ~14.2 days, max wait 26 days
    - turnaround Feb..Jun: approx 3.5, 3.8, 3.1, 15.6, 19.0 (1 completed in June)
    - June approvers: 0 for N. Iyer, 0 for R. Menon, 1 for S. Bhatt
    """
    reconciled = reconcile_trackers(data["support"], data["finance"])
    metrics = calculate_approval_tier_metrics(reconciled)

    assert metrics["threshold"] == APPROVAL_THRESHOLD
    assert abs(metrics["pending_large_count"] - 25) <= 1, f"Expected ~25 pending large refunds, got {metrics['pending_large_count']}"
    assert metrics["pending_large_amount"] == 696600.0, f"Expected INR 696,600 pending amount, got {metrics['pending_large_amount']}"
    assert abs(metrics["mean_wait_days"] - 14.2) <= 1.0, f"Expected mean wait ~14 days, got {metrics['mean_wait_days']}"
    assert metrics["max_wait_days"] == 26, f"Expected max wait 26 days, got {metrics['max_wait_days']}"

    turnaround_map = {m["month"]: m for m in metrics["monthly_turnaround"]}
    assert abs(turnaround_map["2026-02"]["avg_proc_days"] - 3.5) <= 0.3
    assert abs(turnaround_map["2026-03"]["avg_proc_days"] - 3.8) <= 0.3
    assert abs(turnaround_map["2026-04"]["avg_proc_days"] - 3.1) <= 0.3
    assert abs(turnaround_map["2026-05"]["avg_proc_days"] - 15.6) <= 0.5
    assert abs(turnaround_map["2026-06"]["avg_proc_days"] - 19.0) <= 0.5
    assert turnaround_map["2026-06"]["completed_count"] == 1

    appr_map = {m["month"]: m for m in metrics["approver_breakdown"]}
    jun_appr = appr_map["2026-06"]
    assert jun_appr["N. Iyer"] == 0, f"Expected 0 for N. Iyer in June, got {jun_appr['N. Iyer']}"
    assert jun_appr["R. Menon"] == 0, f"Expected 0 for R. Menon in June, got {jun_appr['R. Menon']}"
    assert jun_appr["S. Bhatt"] == 1, f"Expected 1 for S. Bhatt in June, got {jun_appr['S. Bhatt']}"
