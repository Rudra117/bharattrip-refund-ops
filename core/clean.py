"""Deterministic data cleaning and normalization for BharatTrip Refund Operations.
NO LLM imports or logic allowed in this module.
"""
import re
import datetime
from pathlib import Path
import pandas as pd
from rapidfuzz import process, fuzz
from core.config import CANONICAL_AGENTS, CANONICAL_AGENT_MAP, DEFAULT_WORKBOOK_PATH


def clean_id(val: object) -> str:
    """Normalize ticket/ref IDs to 'RF-' + digits only (e.g. 'RF 1750', 'RF1109' -> 'RF-1750')."""
    if pd.isna(val) or val is None:
        return ""
    digits = re.sub(r"\D", "", str(val))
    return f"RF-{digits}" if digits else ""


def clean_esc_ticket_ref(val: object) -> str:
    """Normalize escalation related ticket/ref to 'RF-' + 4-digit number.
    Treat a value as usable only if it contains a 4-digit number.
    Returns 'RF-' + 4 digits, or '' if not usable.
    """
    if pd.isna(val) or val is None:
        return ""
    m = re.findall(r"\d{4}", str(val))
    if m:
        return f"RF-{m[0]}"
    return ""


def normalize_agent_name(name: object) -> str:
    """Normalize agent names: collapse whitespace, strip, and map to 22 canonical agents."""
    if pd.isna(name) or name is None:
        return ""
    raw = str(name).strip()
    collapsed = re.sub(r"\s+", " ", raw)
    lookup_key = collapsed.lower().replace(" ", "")
    
    # Direct dictionary lookup
    if lookup_key in CANONICAL_AGENT_MAP:
        return CANONICAL_AGENT_MAP[lookup_key]
    
    # Fuzzy match fallback via rapidfuzz
    match = process.extractOne(
        collapsed,
        CANONICAL_AGENTS,
        scorer=fuzz.WRatio,
        score_cutoff=75.0,
    )
    if match:
        return match[0]
    return collapsed.title()


def parse_date_safe(val: object) -> pd.Timestamp:
    """Safely parse mixed dates (real Timestamp or DD-MM-YYYY / DD/MM/YY string).
    CRITICAL: Real datetimes are preserved as-is to avoid day/month swapping bugs.
    """
    if pd.isna(val) or val is None or val == "":
        return pd.NaT
    if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date)):
        return pd.Timestamp(val)
    s = str(val).strip()
    if not s or s.lower() in ("none", "nat", "nan"):
        return pd.NaT
    # Explicitly parse string using dayfirst=True
    return pd.to_datetime(s, dayfirst=True)


def clean_support_tracker(
    df: pd.DataFrame,
    finance_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean Support Tracker:
    - Clean IDs
    - Clean Agent names
    - Clean Status whitespace
    - Safe date parsing
    - Deduplicate keeping row with latest 'Last Updated';
      on a tie keep the row whose Refund Amount equals Finance Amount Paid or Amount Paid + Deduction;
      if none matches keep the later row in the sheet.
    - Flag conflicting duplicate rows
    """
    df = df.copy()
    df["orig_idx"] = df.index
    df["raw_id"] = df["Ticket ID"].astype(str).str.strip()
    df["clean_id"] = df["Ticket ID"].apply(clean_id)
    df["canonical_agent"] = df["Agent"].apply(normalize_agent_name)
    df["clean_status"] = df["Status"].astype(str).str.strip()
    df["parsed_request_date"] = df["Request Date"].apply(parse_date_safe)
    df["parsed_last_updated"] = df["Last Updated"].apply(parse_date_safe)

    # Detect duplicates & conflicts
    dupes_mask = df.duplicated("clean_id", keep=False)
    dupe_rows = df[dupes_mask].copy()

    conflicts = []
    for cid, group in dupe_rows.groupby("clean_id"):
        amounts = group["Refund Amount (INR)"].dropna().unique()
        statuses = group["clean_status"].dropna().unique()
        if len(amounts) > 1 or len(statuses) > 1:
            for idx, r in group.iterrows():
                conflicts.append({
                    "Ticket ID": cid,
                    "Row Index": idx,
                    "Agent": r["canonical_agent"],
                    "Refund Amount (INR)": r["Refund Amount (INR)"],
                    "Status": r["clean_status"],
                    "Last Updated": r["parsed_last_updated"],
                    "Handled By": r.get("Handled By", ""),
                })
    conflicts_df = pd.DataFrame(conflicts)

    # Build Finance matching map for tie-breaking
    fin_matches = {}
    if finance_df is not None:
        f_clean = finance_df.copy()
        if "clean_id" not in f_clean.columns:
            f_clean["clean_id"] = f_clean["Ref No"].apply(clean_id)
        for _, r in f_clean.iterrows():
            cid = r["clean_id"]
            paid = r.get("Amount Paid (INR)")
            ded = r.get("Deduction (INR)")
            ded_val = ded if pd.notna(ded) else 0.0
            if pd.notna(paid):
                fin_matches.setdefault(cid, set()).add(float(paid))
                fin_matches[cid].add(float(paid) + float(ded_val))

    # Tie-breaking scoring: (parsed_last_updated, matches_finance, orig_idx)
    def compute_sort_score(r):
        cid = r["clean_id"]
        amt = r["Refund Amount (INR)"]
        matches_fin = 1 if (cid in fin_matches and pd.notna(amt) and float(amt) in fin_matches[cid]) else 0
        return (r["parsed_last_updated"], matches_fin, r["orig_idx"])

    df["_dedup_score"] = df.apply(compute_sort_score, axis=1)

    # Sort ascending and keep='last':
    # 1. Latest Last Updated wins
    # 2. On tie, matching Finance amount wins (1 > 0)
    # 3. If still tied / none matches, later row in sheet wins (higher orig_idx)
    cleaned_df = (
        df.sort_values(by="_dedup_score", ascending=True)
        .drop_duplicates(subset=["clean_id"], keep="last")
        .drop(columns=["_dedup_score", "orig_idx"], errors="ignore")
        .copy()
    )

    return cleaned_df, conflicts_df


def clean_finance_tracker(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean Finance Tracker:
    - Clean IDs
    - Clean Agent names
    - Clean Payout Status whitespace
    - Safe date parsing (flagging dates > 2026-06-30 without crashing)
    - Filter re-entry / duplicate checks keeping valid payout row
    - Return cleaned records and flagged duplicate rows
    """
    df = df.copy()
    df["raw_id"] = df["Ref No"].astype(str).str.strip()
    df["clean_id"] = df["Ref No"].apply(clean_id)
    df["canonical_agent"] = df["Agent Name"].apply(normalize_agent_name)
    df["clean_payout_status"] = df["Payout Status"].astype(str).str.strip()
    df["parsed_received_on"] = df["Received On"].apply(parse_date_safe)
    df["parsed_processed_on"] = df["Processed On"].apply(parse_date_safe)
    
    # Flag dates after snapshot
    df["processed_post_snapshot"] = df["parsed_processed_on"] > pd.Timestamp("2026-06-30")

    # Re-entry / duplicate priority scoring
    df["remarks_clean"] = df["Remarks"].fillna("").astype(str).str.strip().str.lower()
    df["is_reentry_flag"] = df["remarks_clean"].apply(
        lambda r: 1 if ("re-entry" in r or "duplicate check" in r) else 0
    )

    # Track duplicates
    dupes_mask = df.duplicated("clean_id", keep=False)
    dupe_rows = df[dupes_mask].copy()

    # Deduplicate keeping non-re-entry (lowest is_reentry_flag)
    cleaned_df = (
        df.sort_values(by=["clean_id", "is_reentry_flag"], ascending=[True, True])
        .drop_duplicates(subset=["clean_id"], keep="first")
        .copy()
    )

    # Rows that were dropped
    dropped_mask = dupes_mask & (~df.index.isin(cleaned_df.index))
    dropped_df = df[dropped_mask].copy()

    return cleaned_df, dropped_df


def clean_escalations(df: pd.DataFrame) -> pd.DataFrame:
    """Clean Escalations log:
    - Clean Escalation ID and Status
    - Clean Related Ticket / Ref, categorizing blanks/no-ref as 'unlinked'
    - Treat a value as usable only if it contains a 4-digit number
    - Safe date parsing for Raised On and Resolved On
    - Calculate and standardize Days Open
    """
    df = df.copy()
    df["raw_id"] = df["Escalation ID"].astype(str).str.strip()
    df["clean_escalation_id"] = df["Escalation ID"].apply(clean_id)
    df["clean_status"] = df["Status"].astype(str).str.strip()
    df["parsed_raised_on"] = df["Raised On"].apply(parse_date_safe)
    df["parsed_resolved_on"] = df["Resolved On"].apply(parse_date_safe)
    df["canonical_agent"] = df["Agent / Team"].apply(normalize_agent_name)

    raw_ref = df["Related Ticket / Ref"].fillna("").astype(str).str.strip()
    df["raw_ticket_ref"] = raw_ref
    df["clean_ticket_id"] = raw_ref.apply(clean_esc_ticket_ref)
    df["is_unlinked"] = df["clean_ticket_id"] == ""
    df["has_usable_id"] = df["clean_ticket_id"] != ""

    return df


def compute_id_format_audit(
    support_raw: pd.DataFrame,
    finance_raw: pd.DataFrame,
    escalations_raw: pd.DataFrame,
) -> dict:
    """Generate ID format audit table: count of raw IDs needing normalization per tracker with examples."""
    s_diff = support_raw[support_raw["Ticket ID"].apply(lambda x: str(x).strip() != clean_id(x))]
    f_diff = finance_raw[finance_raw["Ref No"].apply(lambda x: str(x).strip() != clean_id(x))]
    e_usable = escalations_raw[escalations_raw["Related Ticket / Ref"].apply(lambda x: clean_esc_ticket_ref(x) != "")]
    e_diff = e_usable[e_usable["Related Ticket / Ref"].apply(lambda x: str(x).strip() != clean_esc_ticket_ref(x))]
    e_unusable = escalations_raw[escalations_raw["Related Ticket / Ref"].apply(lambda x: clean_esc_ticket_ref(x) == "")]

    return {
        "support": {
            "tracker": "Support_Tracker",
            "total_rows": len(support_raw),
            "needed_normalization_count": len(s_diff),
            "examples": [str(x) for x in s_diff["Ticket ID"].dropna().head(5).tolist()],
        },
        "finance": {
            "tracker": "Finance_Tracker",
            "total_rows": len(finance_raw),
            "needed_normalization_count": len(f_diff),
            "examples": [str(x) for x in f_diff["Ref No"].dropna().head(5).tolist()],
        },
        "escalations": {
            "tracker": "Escalations",
            "total_rows": len(escalations_raw),
            "usable_ids_count": len(e_usable),
            "unusable_no_ref_count": len(e_unusable),
            "unusable_examples": [
                "(blank)" if pd.isna(x) or str(x).strip().lower() == "nan" else str(x).strip()
                for x in e_unusable["Related Ticket / Ref"].head(5).tolist()
            ],
            "needed_normalization_count": len(e_diff),
            "examples": [str(x) for x in e_diff["Related Ticket / Ref"].dropna().head(5).tolist()],
        },
    }


def load_and_clean_all(workbook_path: str | Path = DEFAULT_WORKBOOK_PATH) -> dict:
    """Load and clean all tabs from the BharatTrip workbook."""
    wb_path = Path(workbook_path)
    if not wb_path.exists():
        raise FileNotFoundError(f"Workbook not found at {wb_path}")

    support_raw = pd.read_excel(wb_path, sheet_name="Support_Tracker")
    finance_raw = pd.read_excel(wb_path, sheet_name="Finance_Tracker")
    escalations_raw = pd.read_excel(wb_path, sheet_name="Escalations")

    support_clean, support_conflicts = clean_support_tracker(support_raw, finance_df=finance_raw)
    finance_clean, finance_duplicates = clean_finance_tracker(finance_raw)
    escalations_clean = clean_escalations(escalations_raw)
    id_format_audit = compute_id_format_audit(support_raw, finance_raw, escalations_raw)

    return {
        "support": support_clean,
        "support_conflicts": support_conflicts,
        "finance": finance_clean,
        "finance_duplicates": finance_duplicates,
        "escalations": escalations_clean,
        "id_format_audit": id_format_audit,
        "raw": {
            "support": support_raw,
            "finance": finance_raw,
            "escalations": escalations_raw,
        },
    }
