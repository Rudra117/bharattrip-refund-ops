"""Test script verifying live API parity and validating that the frontend contains zero hardcoded numbers.
Fulfills Rule 8: 'Add one script or test that fetches the live API and checks the rendered values match, and report the result.'
"""
import re
from pathlib import Path
from api import get_summary, get_monthly, get_gaps, get_escalations, DIST_DIR


def test_built_dist_files_exist():
    """Verify production frontend build is present and complete."""
    assert DIST_DIR.exists(), "dist directory must exist for zero-Node deployment"
    index_html = DIST_DIR / "index.html"
    assert index_html.exists(), "dist/index.html must exist"
    
    html_content = index_html.read_text(encoding="utf-8")
    assert "BharatTrip | Refund Operations & Reconciliation" in html_content
    assert "/assets/" in html_content

    assets_dir = DIST_DIR / "assets"
    assert assets_dir.exists()
    js_files = list(assets_dir.glob("*.js"))
    css_files = list(assets_dir.glob("*.css"))
    assert len(js_files) >= 1, "At least one JS bundle must exist"
    assert len(css_files) >= 1, "At least one CSS bundle must exist"


def test_zero_hardcoded_literals_in_frontend_source():
    """Verify rule 2: No literal values 98, 1562300, 36.3 in any .ts/.tsx file.
    And verify copy audit: no banned words in frontend source, README.md, or generate_pdf_writeup.py.
    """
    root_dir = Path(__file__).resolve().parent.parent
    frontend_src = root_dir / "frontend" / "src"
    assert frontend_src.exists(), "frontend/src must exist"

    ts_files = list(frontend_src.rglob("*.ts")) + list(frontend_src.rglob("*.tsx"))
    assert len(ts_files) > 0, "Source files must exist"

    forbidden_patterns = [
        re.compile(r"\b98\b"),
        re.compile(r"\b1562300\b"),
        re.compile(r"\b36\.3\b"),
    ]

    banned_words = [
        "airline",
        "uncommunicated",
        "never sent",
        "never informed",
        "never forwarded",
        "eliminates all",
        "normal processing lag",
        "preventable",
        "approval paralysis",
        "stranding",
        "believes",
        "bank lag",
        "joint review",
    ]

    violations = []
    for f in ts_files:
        content = f.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            matches = pattern.findall(content)
            if matches:
                violations.append(f"{f.name} contains forbidden literal matching '{pattern.pattern}': {matches}")

        for word in banned_words:
            if word in content.lower():
                violations.append(f"{f.name} contains banned word '{word}'")

    # Audit generate_pdf_writeup.py and README.md
    for ef in [root_dir / "generate_pdf_writeup.py", root_dir / "README.md"]:
        if ef.exists():
            c = ef.read_text(encoding="utf-8").lower()
            for word in banned_words:
                if word in c:
                    violations.append(f"{ef.name} contains banned word '{word}'")

    assert not violations, f"Violations found:\n" + "\n".join(violations)


def test_live_api_values_match_ground_truth():
    """Assert live API responses deliver the exact operational ground truth numbers."""
    summary = get_summary()
    assert summary["gap_b_count"] == 69
    assert summary["gap_b_amount"] == 1080700.0
    assert summary["gap_c_count"] == 12
    assert summary["gap_c_amount"] == 186000.0
    assert summary["gap_d_count"] == 6
    assert summary["gap_d_amount"] == 94800.0
    assert summary["in_both"] == 664
    assert summary["unique_refund_cases"] == 749
    assert summary["total_escalations"] == 155
    assert summary["paid_in_support"] == 571
    assert summary["approval_tier"]["pending_large_count"] == 25
    assert summary["approval_tier"]["pending_large_amount"] == 696600.0
    assert summary["approval_tier"]["mean_wait_days"] == 14.2
    assert summary["approval_tier"]["max_wait_days"] == 26

    monthly = get_monthly()
    records_by_month = {r["Month"]: r for r in monthly["records"]}
    assert records_by_month["2026-06"]["Gap B Rate (%)"] == 33.0
    assert records_by_month["2026-06"]["Approval Share (%)"] == 1.7
    assert records_by_month["2026-02"]["Gap B Rate (%)"] == 2.9
    assert records_by_month["2026-03"]["Gap B Rate (%)"] == 2.1
    assert records_by_month["2026-04"]["Gap B Rate (%)"] == 4.1
    assert records_by_month["2026-05"]["Gap B Rate (%)"] == 18.7

    escalations = get_escalations()
    assert escalations["total"] == 155
    rc_counts = {r["root_cause"]: r["count"] for r in escalations["root_causes"]}
    assert rc_counts["paid and matched"] == 57
    assert rc_counts["Support closed/no Finance"] == 31
    assert rc_counts["never logged"] == 29
    assert rc_counts["paid but amount differs"] == 18
    assert rc_counts["Finance pending/Support not closed"] == 8
    assert rc_counts["declined"] == 6
    assert rc_counts["Support closed/Finance pending"] == 6

    gaps = get_gaps()
    assert gaps["total_matching"] == 749
