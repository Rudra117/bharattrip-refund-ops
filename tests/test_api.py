"""API endpoint validation tests asserting exact parity with known-answer ground truth.
"""
from fastapi import HTTPException
from api import (
    get_summary,
    get_monthly,
    get_gaps,
    get_escalations,
    download_ledger,
    process_intake,
    get_latent,
    get_agents_exposure,
    get_addressable,
    get_approval_tier,
    check_intake_rate_limit,
    IntakeRequest,
)


def test_api_summary_ground_truth():
    """Assert /api/summary returns exact known-answer values."""
    data = get_summary()

    assert data["total_support_tickets"] == 733
    assert data["total_finance_payouts"] == 680
    assert data["in_both"] == 664
    assert data["support_only"] == 69
    assert data["finance_only"] == 16
    assert data["finance_only_amount"] == 141800.0
    assert data["paid_in_support"] == 571

    assert data["gap_b_count"] == 69
    assert data["gap_b_amount"] == 1080700.0

    assert data["gap_c_count"] == 12
    assert data["gap_c_amount"] == 186000.0

    assert data["gap_d_count"] == 6
    assert data["gap_d_amount"] == 94800.0

    assert data["total_escalations"] == 155
    assert data["open_escalations"] == 85
    assert data["resolved_escalations"] == 70
    assert data["canonical_agents_count"] == 22


def test_api_monthly_metrics():
    """Assert /api/monthly returns gap rates and approval shares."""
    data = get_monthly()
    records = {r["Month"]: r for r in data["records"]}

    assert len(records) == 5
    assert records["2026-06"]["Gap B Rate (%)"] == 33.0
    assert records["2026-06"]["Approval Share (%)"] == 1.7
    assert "footnote" in data


def test_api_escalations_root_causes():
    """Assert /api/escalations returns exact root cause distribution."""
    data = get_escalations()

    assert data["total"] == 155
    rc_map = {r["root_cause"]: r["count"] for r in data["root_causes"]}

    expected = {
        "paid and matched": 57,
        "Support closed/no Finance": 31,
        "never logged": 29,
        "paid but amount differs": 18,
        "Finance pending/Support not closed": 8,
        "declined": 6,
        "Support closed/Finance pending": 6,
    }

    for k, v in expected.items():
        assert rc_map.get(k) == v, f"{k}: expected {v}, got {rc_map.get(k)}"


def test_api_gaps_action_queue():
    """Assert /api/gaps returns filterable action queue."""
    gaps = get_gaps()
    assert gaps["total_matching"] == 749
    assert len(gaps["records"]) == 100
    assert "filters" in gaps

    # Filter by Gap B
    gap_b = get_gaps(gap_class="Class B: Support Closed, Finance None")
    assert gap_b["total_matching"] == 69


def test_api_ledger_download():
    """Assert /api/ledger.xlsx returns valid Excel bytes with 9 sheets including Stalled_Approvals."""
    import openpyxl, io
    res = download_ledger()
    assert res.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(res.body) > 50000

    wb = openpyxl.load_workbook(io.BytesIO(res.body))
    expected_sheets = [
        "README_Legend", "Summary", "Action_Queue", "Unified_Ledger",
        "Escalations_Linked", "Duplicate_Conflicts", "ID_Format_Audit",
        "Chase_First", "Stalled_Approvals"
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Expected sheet '{s}' in ledger.xlsx"


def test_api_approval_tier_endpoint():
    """Assert /api/approvals/tier returns inferred tier metrics."""
    tier = get_approval_tier()
    assert tier["threshold"] == 20000.0
    assert tier["pending_large_count"] == 25
    assert tier["pending_large_amount"] == 696600.0
    assert tier["mean_wait_days"] == 14.2
    assert tier["max_wait_days"] == 26
    assert len(tier["monthly_turnaround"]) == 5
    assert len(tier["approver_breakdown"]) == 5
    assert len(tier["pending_records"]) == 25
    assert "observation_note" in tier


def test_api_intake_endpoints():
    """Assert POST /api/intake functions for presets."""
    # Preset (a)
    req_a = IntakeRequest(
        message="Hi, I cancelled booking for DEL-DXB last week and was told I'd get a refund. I haven't received anything and I don't have any reference number. Please help, my client is asking.",
        channel="Email",
        date="2026-06-05",
    )
    res_a = process_intake(req_a)
    assert res_a["parsed"]["agent_name"] == "Peak Journeys"
    assert res_a["parsed"]["route"] == "DEL-DXB"

    # Preset (c)
    req_c = IntakeRequest(
        message="Finance says they never received several of the refunds I closed last month. I marked them done on my side. Not sure where they went.",
        channel="Email",
        date="2026-06-11",
    )
    res_c = process_intake(req_c)
    assert res_c["match"]["match_type"] == "INTERNAL_GAP_REPORT"
    assert res_c["match"]["gap_b_count"] == 69
    assert res_c["match"]["gap_b_sum"] == 1080700.0
    assert res_c["match"]["new_ticket"] is None


def test_api_latent_endpoint():
    """Assert /api/latent returns 38 Gap B tickets with 0 escalations totaling INR 616,600."""
    res = get_latent()
    assert res["count"] == 38
    assert res["total_amount"] == 616600.0
    assert abs(res["mean_age_days"] - 39.6) < 0.5
    assert res["over_30_days_count"] == 19
    assert len(res["records"]) == 38
    assert all("proactive_draft" in r for r in res["records"])


def test_api_agents_exposure_endpoint():
    """Assert /api/agents/exposure returns 21 agents holding INR 13.6L with top 5 concentration at 50.9%."""
    res = get_agents_exposure()
    assert res["total_agents"] == 21
    assert res["total_stuck_value"] == 1361500.0
    assert res["top5_share_pct"] == 50.9
    assert len(res["agents"]) == 21
    top_agent = res["agents"][0]
    assert top_agent["canonical_agent"] == "GoFly Holidays"
    assert top_agent["stuck_amount"] == 170900.0


def test_api_addressable_escalations_endpoint():
    """Assert /api/addressable returns 141 of 155 addressable (84 structural + 57 status chases)."""
    res = get_addressable()
    assert res["total_escalations"] == 155
    assert res["addressable_total"] == 141
    assert res["addressable_share_pct"] == 91.0
    assert res["structural_failure_count"] == 84
    assert res["paid_matched_chases"] == 57


def test_api_intake_rate_limiting():
    """Assert rate limit enforces 20 req/hr per IP and returns 429 on 21st."""
    test_ip = "192.0.2.100"
    for _ in range(20):
        check_intake_rate_limit(test_ip)

    try:
        check_intake_rate_limit(test_ip)
        assert False, "Should have raised 429 HTTPException"
    except HTTPException as e:
        assert e.status_code == 429
        assert "Rate limit exceeded" in e.detail
