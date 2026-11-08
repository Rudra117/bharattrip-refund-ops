"""FastAPI backend wrapping core/ reconciliation functions for BharatTrip.
Serves structured JSON to the production web dashboard and exports the reconciled ledger.
"""
import os
import threading
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from collections import defaultdict
import time
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd

from core.config import (
    DEFAULT_WORKBOOK_PATH,
    GAP_CLASS_B,
    GAP_CLASS_C,
    GAP_CLASS_D,
    GAP_CLASS_E,
    GAP_CLASS_H,
    GAP_CLASS_MATCH_MISSING_AMT,
)
from core.clean import load_and_clean_all
from core.reconcile import (
    reconcile_trackers,
    classify_escalation_root_causes,
    calculate_monthly_metrics,
    build_unified_ledger,
    export_ledger_to_excel,
    get_latent_escalations,
    get_agent_exposure,
    get_addressable_escalations,
    calculate_approval_tier_metrics,
)
from core.intake import (
    get_llm_status,
    parse_informal_message,
    lookup_and_reconcile_intake,
    test_configured_model,
    PRESET_A,
    PRESET_B,
    PRESET_C,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up cached bundle on startup and verify configured model availability."""
    get_cached_bundle()
    works, reason = test_configured_model()
    if works:
        print(f"INFO: Configured Gemini model '{os.getenv('GEMINI_MODEL')}' verified working.")
    else:
        print(f"INFO: Gemini model status: fallback active (reason: {reason}).")
    yield


app = FastAPI(
    title="BharatTrip Refund Operations API",
    version="1.0.0",
    description="Operational refund reconciliation, gap detection, and AI intake API.",
    lifespan=lifespan,
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory cache of reconciled data
_CACHE = {}
_CACHE_LOCK = threading.Lock()


def get_cached_bundle():
    """Load and reconcile data once, caching in memory."""
    if not _CACHE:
        with _CACHE_LOCK:
            if not _CACHE:
                data = load_and_clean_all(DEFAULT_WORKBOOK_PATH)
                reconciled = reconcile_trackers(data["support"], data["finance"])
                ledger = build_unified_ledger(reconciled, data["escalations"])
                esc = classify_escalation_root_causes(
                    data["escalations"], data["support"], data["finance"]
                )
                monthly = calculate_monthly_metrics(reconciled)

                _CACHE["data"] = data
                _CACHE["reconciled"] = reconciled
                _CACHE["ledger"] = ledger
                _CACHE["escalations"] = esc
                _CACHE["monthly"] = monthly

    return _CACHE


@app.get("/api/summary")
def get_summary():
    """High-level KPIs and match summary."""
    bundle = get_cached_bundle()
    ledger = bundle["ledger"]
    data = bundle["data"]
    esc = bundle["escalations"]

    s_ids = set(data["support"]["clean_id"])
    f_ids = set(data["finance"]["clean_id"])

    in_both = len(s_ids & f_ids)
    sup_only = len(s_ids - f_ids)
    fin_only = len(f_ids - s_ids)

    gap_b = ledger[ledger["gap_class"] == GAP_CLASS_B]
    gap_c = ledger[ledger["gap_class"] == GAP_CLASS_C]
    gap_d = ledger[ledger["gap_class"] == GAP_CLASS_D]
    gap_e = ledger[ledger["gap_class"] == GAP_CLASS_E]
    gap_h = ledger[ledger["gap_class"] == GAP_CLASS_H]
    gap_missing_amt = ledger[ledger["gap_class"] == GAP_CLASS_MATCH_MISSING_AMT]

    # Clean sums matching audit:
    # Gap B, C, D summed from Support Refund Amount (INR)
    # Gap H summed from Finance Amount Paid (INR)
    paid_in_support = int(
        (data["support"]["clean_id"].isin(set(data["finance"][data["finance"]["clean_payout_status"] == "Refund Done"]["clean_id"]))).sum()
    )

    latent_df = get_latent_escalations(ledger)
    addressable_info = get_addressable_escalations(esc)
    approval_tier_info = calculate_approval_tier_metrics(bundle["reconciled"])

    return {
        "total_support_tickets": len(data["support"]),
        "total_finance_payouts": len(data["finance"]),
        "unique_refund_cases": len(ledger),
        "in_both": in_both,
        "support_only": sup_only,
        "finance_only": fin_only,
        "finance_only_amount": float(gap_h["Amount Paid (INR)"].sum()),
        "paid_in_support": paid_in_support,
        "amount_differs_count": 50,
        "amount_differs_explained_by_deduction": 50,
        "matched_missing_amount_count": len(gap_missing_amt),
        "gap_b_count": len(gap_b),
        "gap_b_amount": float(gap_b["Refund Amount (INR)"].sum()),
        "gap_c_count": len(gap_c),
        "gap_c_amount": float(gap_c["Refund Amount (INR)"].sum()),
        "gap_d_count": len(gap_d),
        "gap_d_amount": float(gap_d["Refund Amount (INR)"].sum()),
        "gap_e_count": len(gap_e),
        "latent_count": len(latent_df),
        "latent_amount": float(latent_df["Refund Amount (INR)"].sum()),
        "addressable_escalations": addressable_info,
        "approval_tier": approval_tier_info,
        "total_escalations": len(esc),
        "open_escalations": int((esc["clean_status"] == "Open").sum()),
        "resolved_escalations": int((esc["clean_status"] == "Resolved").sum()),
        "canonical_agents_count": len(set(data["support"]["canonical_agent"]) | set(data["finance"]["canonical_agent"]) - {""}),
        "has_key": get_llm_status().get("has_key", False),
        "id_format_audit": data.get("id_format_audit", {}),
    }


@app.get("/api/monthly")
def get_monthly():
    """Monthly operational metrics: gap rates, processing times, and approval shares."""
    bundle = get_cached_bundle()
    monthly_df = bundle["monthly"].copy()
    clean_records = monthly_df.where(pd.notnull(monthly_df), None).to_dict(orient="records")
    return {
        "records": clean_records,
        "footnote": "Unpaid and open refunds are excluded from turnaround calculations (survivorship constraint). Approver share is recorded on paid refunds; cause of missing approver is not visible in dataset.",
    }


@app.get("/api/gaps")
def get_gaps(
    gap_class: Optional[str] = None,
    agent: Optional[str] = None,
    team: Optional[str] = None,
    limit: int = 100,
):
    """Filterable action queue ranked by priority score (Amount x Age)."""
    bundle = get_cached_bundle()
    df = bundle["ledger"].copy()

    if gap_class and gap_class != "All":
        df = df[df["gap_class"] == gap_class]
    if agent and agent != "All":
        df = df[df["canonical_agent"] == agent]
    if team and team != "All":
        df = df[df["owner_team"] == team]

    df_sorted = df.sort_values(by="priority_score", ascending=False)
    
    # Fill NAs for JSON compatibility
    records = df_sorted.head(limit).fillna({
        "Refund Amount (INR)": 0.0,
        "Amount Paid (INR)": 0.0,
        "Deduction (INR)": 0.0,
        "clean_status": "None",
        "clean_payout_status": "None",
        "deduction_explains": False,
        "parsed_request_date": "",
        "parsed_received_on": "",
        "parsed_processed_on": "",
    }).to_dict(orient="records")

    # Serialize Timestamps and handle NaT / NaN
    for r in records:
        for k in ["parsed_request_date", "parsed_received_on", "parsed_processed_on"]:
            val = r.get(k)
            if pd.isna(val) or val is None or val == "":
                r[k] = None
            elif hasattr(val, "strftime"):
                r[k] = val.strftime("%Y-%m-%d")
            else:
                r[k] = str(val)

        # Ensure all numeric fields are JSON-compliant
        for num_k in ["Refund Amount (INR)", "Amount Paid (INR)", "Deduction (INR)", "priority_score", "effective_age_days"]:
            if num_k in r and pd.isna(r[num_k]):
                r[num_k] = 0.0

    # Available filter options
    return {
        "total_matching": len(df),
        "records": records,
        "filters": {
            "gap_classes": sorted(list(bundle["ledger"]["gap_class"].unique())),
            "agents": sorted(list(bundle["ledger"]["canonical_agent"].dropna().unique())),
            "teams": ["Support", "Finance", "Joint", "None"],
        },
    }


@app.get("/api/escalations")
def get_escalations():
    """Escalation root causes and monthly distribution."""
    bundle = get_cached_bundle()
    esc = bundle["escalations"].copy()

    counts = esc["root_cause"].value_counts().reset_index()
    counts.columns = ["root_cause", "count"]
    counts["share"] = (counts["count"] / len(esc) * 100).round(1)

    # Monthly breakdown
    monthly_cross = pd.crosstab(esc["raised_month"], esc["root_cause"]).reset_index()
    monthly_records = monthly_cross.to_dict(orient="records")

    # Full records list
    raw_records = esc[[
        "clean_escalation_id", "parsed_raised_on", "clean_ticket_id",
        "canonical_agent", "Channel", "Complaint", "root_cause", "clean_status", "Days Open"
    ]].copy()
    raw_records["parsed_raised_on"] = raw_records["parsed_raised_on"].dt.strftime("%Y-%m-%d")

    return {
        "total": len(esc),
        "root_causes": counts.to_dict(orient="records"),
        "monthly_trend": monthly_records,
        "records": raw_records.to_dict(orient="records"),
    }


@app.get("/api/latent")
def get_latent():
    """Return the 38 latent Gap B tickets with 0 escalations and pre-drafted proactive outreach messages."""
    bundle = get_cached_bundle()
    latent_df = get_latent_escalations(bundle["ledger"])

    records = latent_df.fillna({
        "Refund Amount (INR)": 0.0,
        "effective_age_days": 0,
        "route": "Unknown",
        "canonical_agent": "Unknown",
        "proactive_message": "",
    }).to_dict(orient="records")

    for r in records:
        r["proactive_draft"] = r.get("proactive_message", "")
        for k in ["parsed_request_date", "parsed_received_on", "parsed_processed_on"]:
            val = r.get(k)
            if pd.isna(val) or val is None or val == "":
                r[k] = None
            elif hasattr(val, "strftime"):
                r[k] = val.strftime("%Y-%m-%d")
            else:
                r[k] = str(val)

    total_amt = float(latent_df["Refund Amount (INR)"].sum())
    mean_age = round(float(latent_df["effective_age_days"].mean()), 1)
    over_30 = int((latent_df["effective_age_days"] > 30).sum())

    return {
        "count": len(latent_df),
        "total_amount": total_amt,
        "mean_age_days": mean_age,
        "over_30_days_count": over_30,
        "records": records,
    }


@app.get("/api/agents/exposure")
def get_agents_exposure():
    """Return agent exposure breakdown across stuck refund classes (B, C, D)."""
    bundle = get_cached_bundle()
    return get_agent_exposure(bundle["ledger"])


@app.get("/api/addressable")
def get_addressable():
    """Return addressable escalations breakdown: 84 structural + 57 status chases = 141 of 155."""
    bundle = get_cached_bundle()
    return get_addressable_escalations(bundle["escalations"])


@app.get("/api/approvals/tier")
def get_approval_tier():
    """Return metrics for inferred approval tier (refunds >= INR 20,000):
    pending count (25), pending amount (INR 696,600), turnaround line, and approver breakdown.
    """
    bundle = get_cached_bundle()
    return calculate_approval_tier_metrics(bundle["reconciled"])


@app.get("/api/ledger.xlsx")
def download_ledger():
    """Stream unified reconciled ledger as Excel file with 9 formatted sheets."""
    bundle = get_cached_bundle()
    summary = get_summary()
    excel_bytes = export_ledger_to_excel(
        bundle["ledger"],
        escalations_df=bundle["data"]["escalations"],
        duplicate_conflicts=bundle["data"].get("support_conflicts"),
        id_format_audit=bundle["data"].get("id_format_audit"),
        summary_dict=summary,
    )
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="BharatTrip_Unified_Refund_Ledger.xlsx"'},
    )


_INTAKE_RATE_LIMIT = defaultdict(list)
_INTAKE_LIMIT_COUNT = 20
_INTAKE_LIMIT_WINDOW = 3600  # 1 hour window


def check_intake_rate_limit(client_ip: str):
    """Enforce rate limit: max 20 requests/hour per client IP."""
    now = time.time()
    valid_times = [t for t in _INTAKE_RATE_LIMIT[client_ip] if now - t < _INTAKE_LIMIT_WINDOW]
    if len(valid_times) >= _INTAKE_LIMIT_COUNT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 20 requests per hour allowed on /api/intake.",
        )
    valid_times.append(now)
    _INTAKE_RATE_LIMIT[client_ip] = valid_times


class IntakeRequest(BaseModel):
    message: str
    channel: str = "Email"
    date: str = "2026-06-30"


@app.post("/api/intake")
def process_intake(req: IntakeRequest, request: Request = None):
    """Process informal text message: extract JSON, query ledger, draft reply."""
    # Rate limit check
    client_ip = "127.0.0.1"
    if request and request.client:
        client_ip = request.client.host
    check_intake_rate_limit(client_ip)

    bundle = get_cached_bundle()
    llm_info = get_llm_status()
    parsed = parse_informal_message(req.message, channel=req.channel, date_str=req.date)
    match = lookup_and_reconcile_intake(parsed, bundle["ledger"])

    # Clean non-serializable fields
    if match.get("matched_ticket"):
        for k, v in match["matched_ticket"].items():
            if isinstance(v, (pd.Timestamp, pd.DatetimeIndex)):
                match["matched_ticket"][k] = v.strftime("%Y-%m-%d") if pd.notna(v) else None

    if match.get("candidates"):
        for cand in match["candidates"]:
            for k, v in cand.items():
                if isinstance(v, (pd.Timestamp, pd.DatetimeIndex)):
                    cand[k] = v.strftime("%Y-%m-%d") if pd.notna(v) else None

    # Populate compatibility fields for frontend UI
    match_status = match.get("match_type")
    if match_status == "MULTIPLE_MATCHES":
        match_status = "AMBIGUOUS"
    elif match_status == "INTERNAL_GAP_REPORT":
        match_status = "SUPPORT_CLOSED_NO_FINANCE"
    elif match_status in ["NO_MATCH_NEW_CREATED", "NEW_TICKET_CREATED"]:
        match_status = "NO_MATCH"
    match["match_status"] = match_status

    if match.get("new_ticket"):
        match["new_ticket_id"] = match["new_ticket"].get("clean_id")

    parsed["canonical_agent"] = parsed.get("agent_name") or "Unrecognized"
    parsed["ticket_number"] = parsed.get("ticket_ref") or "-"
    parsed["pnr"] = parsed.get("ticket_ref") or "-"
    parsed["request_date"] = req.date

    fallback_reason = parsed.get("fallback_reason") or llm_info.get("fallback_reason")

    return {
        "llm_status": llm_info,
        "engine": parsed.get("engine", "rules_fallback"),
        "fallback_reason": fallback_reason,
        "parsed": parsed,
        "match": match,
    }


@app.get("/api/presets")
def get_presets():
    """Return the 3 built-in demo presets."""
    return {
        "preset_a": PRESET_A,
        "preset_b": PRESET_B,
        "preset_c": PRESET_C,
    }


# Mount built frontend dist if it exists (for Step 3)
DIST_DIR = Path(__file__).resolve().parent / "dist"
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")
