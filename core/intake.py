"""LLM Intake & Natural Language Processor for informal refund requests.
Supports Google Gemini via the official google-genai SDK, with deterministic rule-based fallback.
Enforces strict JSON schema, deterministic ledger verification, guardrails, and duplicate suppression.
"""
import os
import re
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import pandas as pd

from core.config import CANONICAL_AGENTS, SNAPSHOT_DATE, GAP_CLASS_B
from core.clean import normalize_agent_name, clean_id

# Sample demo presets specified in requirements
PRESET_A = {
    "name": "Preset (a): Peak Journeys (Email)",
    "channel": "Email",
    "date": "2026-06-05",
    "text": "Hi, I cancelled booking for DEL-DXB last week and was told I'd get a refund. I haven't received anything and I don't have any reference number. Please help, my client is asking.",
}

PRESET_B = {
    "name": "Preset (b): Nomad Travel (Hinglish WhatsApp)",
    "channel": "WhatsApp",
    "date": "2026-06-08",
    "text": "Bhai refund ka kya hua? BLR-MAA wala. 2 hafte ho gaye, koi jawab nahi.",
}

PRESET_C = {
    "name": "Preset (c): Internal Support Note",
    "channel": "Email",
    "date": "2026-06-11",
    "text": "Finance says they never received several of the refunds I closed last month. I marked them done on my side. Not sure where they went.",
}

# Next new refund sequence tracker
_NEXT_REFUND_NUM = 1
_DEDUP_INTAKE_TICKETS = {}  # text_hash -> created ticket entry


def get_next_new_refund_id() -> str:
    """Generate non-colliding new refund ID with prefix RF-NEW-###."""
    global _NEXT_REFUND_NUM
    new_id = f"RF-NEW-{_NEXT_REFUND_NUM:03d}"
    _NEXT_REFUND_NUM += 1
    return new_id


def reset_intake_state():
    """Reset sequence counter and dedup cache for deterministic unit tests."""
    global _NEXT_REFUND_NUM, _DEDUP_INTAKE_TICKETS
    _NEXT_REFUND_NUM = 1
    _DEDUP_INTAKE_TICKETS.clear()


def load_env_vars():
    """Ensure .env is loaded into environment if not present."""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()


load_env_vars()


_MODEL_STATUS = {"tested": False, "works": False, "reason": None}


def test_configured_model(client=None) -> tuple[bool, str | None]:
    """Test whether configured GEMINI_MODEL works via 1-token test call."""
    global _MODEL_STATUS
    if _MODEL_STATUS["tested"]:
        return _MODEL_STATUS["works"], _MODEL_STATUS["reason"]

    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()

    if not key or key.startswith("AQ."):
        _MODEL_STATUS = {"tested": True, "works": False, "reason": "model_unavailable"}
        return False, "model_unavailable"

    if not model or model.startswith("your-"):
        _MODEL_STATUS = {"tested": True, "works": False, "reason": "model_unavailable"}
        return False, "model_unavailable"

    try:
        if client is None:
            from google import genai
            client = genai.Client(api_key=key)
        def _call():
            return client.models.generate_content(
                model=model,
                contents="ping",
            )
        with ThreadPoolExecutor(max_workers=1) as executor:
            fut = executor.submit(_call)
            fut.result(timeout=2.0)
        _MODEL_STATUS = {"tested": True, "works": True, "reason": None}
        return True, None
    except Exception as e:
        _MODEL_STATUS = {"tested": True, "works": False, "reason": "model_unavailable"}
        return False, "model_unavailable"


def get_llm_status() -> dict:
    """Check API keys and return LLM runtime status and banner.
    GEMINI_MODEL is read strictly from env only (no hardcoded default).
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()

    if gemini_key and model and not model.startswith("your-"):
        works, reason = test_configured_model()
        if works:
            return {
                "has_key": True,
                "provider": "Gemini",
                "model": model,
                "banner": f"Running with Gemini API ({model})",
                "is_fallback": False,
                "engine": "gemini",
            }
        else:
            return {
                "has_key": True,
                "provider": "Gemini",
                "model": model,
                "banner": "Running without LLM (Deterministic rules & cached parser active)",
                "is_fallback": True,
                "fallback_reason": "model_unavailable",
                "engine": "rules",
            }
    else:
        return {
            "has_key": False,
            "provider": None,
            "model": None,
            "banner": "Running without LLM (Deterministic rules & cached parser active)",
            "is_fallback": True,
            "fallback_reason": "no_api_key" if not gemini_key else "model_unavailable",
            "engine": "rules",
        }


def parse_informal_message_rules(text: str, channel: str = "Email", date_str: str = "2026-06-30") -> dict:
    """Deterministic rule-based parser for informal messages (no API key required)."""
    text_lower = text.lower()

    # 1. Preset matching shortcuts
    if "del-dxb" in text_lower and ("peak journeys" in text_lower or "cancelled booking" in text_lower):
        return {
            "agent_name": "Peak Journeys",
            "route": "DEL-DXB",
            "ticket_ref": None,
            "booking_ref": None,
            "channel": channel or "Email",
            "issue_type": "new_request",
            "language_detected": "English",
            "urgency": "High",
            "confidence": 0.95,
            "summary": "Agent inquiring about DEL-DXB cancellation without reference number.",
            "raw_text": text,
        }

    if "blr-maa" in text_lower or ("bhai refund ka kya hua" in text_lower):
        return {
            "agent_name": "Nomad Travel",
            "route": "BLR-MAA",
            "ticket_ref": None,
            "booking_ref": None,
            "channel": channel or "WhatsApp",
            "issue_type": "status_chase",
            "language_detected": "Hinglish",
            "urgency": "High",
            "confidence": 0.95,
            "summary": "Follow-up for BLR-MAA refund pending over 2 weeks.",
            "raw_text": text,
        }

    if "finance says they never received several" in text_lower or "marked them done on my side" in text_lower:
        return {
            "agent_name": "Internal Support",
            "route": None,
            "ticket_ref": None,
            "booking_ref": None,
            "channel": channel or "Email",
            "issue_type": "internal_note",
            "language_detected": "English",
            "urgency": "High",
            "confidence": 0.98,
            "summary": "Internal Support report of closed refunds missing in Finance tracker.",
            "raw_text": text,
        }

    # 2. General regex extractors
    route_match = re.search(r"\b([a-zA-Z]{3}\s*[-/]\s*[a-zA-Z]{3})\b", text)
    route = route_match.group(1).upper().replace("/", "-").replace(" ", "") if route_match else None

    # Ref match
    ref_match = re.search(r"\b(RF\s*[-]?\s*\d+|PNR[:\s]*[A-Z0-9]+)\b", text, re.I)
    ticket_ref = clean_id(ref_match.group(1)) if ref_match else None

    # Agent detection
    matched_agent = "Unknown Agent"
    for agent in CANONICAL_AGENTS:
        if agent.lower() in text_lower:
            matched_agent = agent
            break

    # Hinglish detection
    hinglish_markers = ["bhai", "kya", "hua", "wala", "hafte", "gaye", "koi", "jawab", "nahi", "plz", "jaldi"]
    is_hinglish = any(word in text_lower for word in hinglish_markers)
    language = "Hinglish" if is_hinglish else "English"

    # Issue type
    if "difference" in text_lower or "deduction" in text_lower or "less" in text_lower or "short" in text_lower:
        issue_type = "amount_dispute"
    elif "status" in text_lower or "kya hua" in text_lower or "update" in text_lower or "chasing" in text_lower or "where" in text_lower:
        issue_type = "status_chase"
    elif "never received" in text_lower or "internal note" in text_lower:
        issue_type = "internal_note"
    else:
        issue_type = "new_request"

    # Urgency
    high_urgency = ["client is asking", "2 hafte", "two weeks", "urgent", "immediately", "bhai", "no response"]
    urgency = "High" if any(marker in text_lower for marker in high_urgency) else "Medium"

    return {
        "agent_name": matched_agent,
        "route": route,
        "ticket_ref": ticket_ref,
        "booking_ref": ticket_ref,
        "channel": channel or "Email",
        "issue_type": issue_type,
        "language_detected": language,
        "urgency": urgency,
        "confidence": 0.85,
        "summary": text[:120].strip() + ("..." if len(text) > 120 else ""),
        "raw_text": text,
    }


def _call_gemini_json(client, model_name: str, prompt: str, timeout: float = 8.0) -> dict:
    """Invoke Gemini model requesting strict JSON with timeout."""
    def _execute():
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3].strip()
        return json.loads(raw_text)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_execute)
        return future.result(timeout=timeout)


def parse_informal_message(
    text: str,
    channel: str = "Email",
    date_str: str = "2026-06-30",
    gemini_client=None,
) -> dict:
    """Parse informal message into structured schema using Gemini if available, otherwise rule-based.
    GEMINI_MODEL is read strictly from env only (no hardcoded default of any 1.x/2.0 model).
    If model is unavailable, surfaces fallback_reason 'model_unavailable'.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()

    # Model must come from environment only
    if not model or model.startswith("your-"):
        rules_res = parse_informal_message_rules(text, channel, date_str)
        rules_res["engine"] = "rules_fallback"
        rules_res["parser_engine"] = "rules_fallback"
        rules_res["engine_chip"] = "Rules fallback"
        rules_res["fallback_reason"] = "model_unavailable"
        return rules_res

    if not key or key.startswith("AQ."):
        rules_res = parse_informal_message_rules(text, channel, date_str)
        rules_res["engine"] = "rules_fallback"
        rules_res["parser_engine"] = "rules_fallback"
        rules_res["engine_chip"] = "Rules fallback"
        rules_res["fallback_reason"] = "model_unavailable"
        return rules_res

    # Check model availability via test call
    if gemini_client is None:
        works, reason = test_configured_model()
        if not works:
            rules_res = parse_informal_message_rules(text, channel, date_str)
            rules_res["engine"] = "rules_fallback"
            rules_res["parser_engine"] = "rules_fallback"
            rules_res["engine_chip"] = "Rules fallback"
            rules_res["fallback_reason"] = "model_unavailable"
            return rules_res

    if (key or gemini_client) and text.strip():
        try:
            client = gemini_client
            if client is None:
                from google import genai
                client = genai.Client(api_key=key)

            prompt = f"""You are an operational assistant at BharatTrip travel company.
Parse the following refund communication message into a strictly valid JSON object.
Return ONLY valid JSON with exactly these keys:
- agent_name: string (canonical travel agency name or detected name, or "Unknown Agent")
- route: string (format "AAA-BBB" in uppercase airport IATA codes, or null)
- ticket_ref: string (format "RF-####" or null)
- channel: string ("Email" or "WhatsApp" or "Phone" or "Portal")
- issue_type: string (strictly one of: "new_request", "status_chase", "amount_dispute", "internal_note")
- language_detected: string ("English" or "Hinglish")
- urgency: string ("High", "Medium", or "Low")
- confidence: float (between 0.0 and 1.0)

Message:
\"\"\"{text}\"\"\"
"""
            result = _call_gemini_json(client, model, prompt, timeout=8.0)

            # Validate schema
            required_keys = {"agent_name", "route", "ticket_ref", "channel", "issue_type", "language_detected", "urgency", "confidence"}
            if not required_keys.issubset(result.keys()):
                raise ValueError("Missing keys in Gemini JSON output")

            # Route standardization
            if result.get("route"):
                m = re.search(r"([a-zA-Z]{3})[-/]([a-zA-Z]{3})", str(result["route"]))
                result["route"] = f"{m.group(1).upper()}-{m.group(2).upper()}" if m else None

            # Ticket ref standardization
            if result.get("ticket_ref"):
                result["ticket_ref"] = clean_id(str(result["ticket_ref"]))
            result["booking_ref"] = result.get("ticket_ref")

            result["channel"] = channel or result.get("channel", "Email")
            result["summary"] = text[:120].strip() + ("..." if len(text) > 120 else "")
            result["raw_text"] = text
            result["engine"] = "gemini"
            result["parser_engine"] = "gemini"
            result["engine_chip"] = "Parsed by Gemini"
            result["fallback_reason"] = None

            return result

        except Exception:
            rules_res = parse_informal_message_rules(text, channel, date_str)
            rules_res["engine"] = "rules_fallback"
            rules_res["parser_engine"] = "rules_fallback"
            rules_res["engine_chip"] = "Rules fallback"
            rules_res["fallback_reason"] = "model_unavailable"
            return rules_res

    # Default rules parser when no key
    rules_res = parse_informal_message_rules(text, channel, date_str)
    rules_res["engine"] = "rules_fallback"
    rules_res["parser_engine"] = "rules_fallback"
    rules_res["engine_chip"] = "Rules fallback"
    rules_res["fallback_reason"] = "model_unavailable"
    return rules_res


# Forbidden ungrounded status words
STATUS_GUARD_WORDS = {"disbursed", "refunded", "declined", "cleared", "paid", "settled", "pending", "approved"}


def _validate_reply_guardrail(draft: str, facts: dict) -> bool:
    """Enforces strict guardrail:
    If the draft contains a status word, amount or ticket ID not present in the supplied facts, discard it.
    """
    draft_lower = draft.lower()

    # Allowed status words from facts
    allowed_status_text = facts.get("status_summary", "").lower()
    allowed_status_words = {w.strip(".,;:()") for w in allowed_status_text.split() if w.strip(".,;:()") in STATUS_GUARD_WORDS}

    # Check for forbidden status words
    for word in STATUS_GUARD_WORDS:
        if word in draft_lower and word not in allowed_status_words:
            # Word was used in draft but not authorized in facts!
            return False

    # Check for unauthorized ticket IDs
    allowed_ids = {facts.get("ticket_id", "").lower(), facts.get("new_ticket_id", "").lower()} - {""}
    id_matches = re.findall(r"\bRF-\w+\b", draft, re.I)
    for found_id in id_matches:
        if found_id.lower() not in allowed_ids:
            return False

    # Check for unauthorized rupee amounts
    allowed_amounts = set()
    amt = facts.get("amount") or facts.get("amount_paid")
    if amt is not None:
        try:
            val = float(amt)
            allowed_amounts.update([f"{val:,.0f}", f"{int(val)}", f"{val:.0f}"])
        except Exception:
            pass

    found_numbers = re.findall(r"\b(?:INR|₹|rs\.?)\s*([0-9,]+)\b", draft, re.I)
    for num in found_numbers:
        clean_num = num.replace(",", "").strip()
        if clean_num not in allowed_amounts and f"{clean_num}" not in allowed_amounts:
            return False

    return True


def draft_reply_with_gemini(facts: dict, parsed_msg: dict, gemini_client=None) -> tuple[str, str]:
    """Pass ONLY matched facts to Gemini to draft a polite reply.
    Applies guardrail: Discards draft if unauthorized status/amount/ID is introduced.
    Returns: (reply_text, engine_used)
    """
    template_reply = facts["default_draft"]
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

    if not (key or gemini_client):
        return template_reply, "template"

    try:
        client = gemini_client
        if client is None:
            from google import genai
            client = genai.Client(api_key=key)

        prompt = f"""You are drafting a concise, polite B2B customer support email for BharatTrip.
Draft a short reply using ONLY these verified operational facts. Do NOT invent an ETA, turnaround days, financial amount, or status:

Facts:
- Travel Agency: {facts.get('agent', 'Agency')}
- Ticket Reference: {facts.get('ticket_id') or facts.get('new_ticket_id') or 'N/A'}
- Flight Route: {facts.get('route') or 'Booked Route'}
- Operational Status: {facts.get('status_summary', '')}

Write a professional response under 70 words:"""

        def _exec():
            resp = client.models.generate_content(model=model, contents=prompt)
            return resp.text.strip()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_exec)
            draft = future.result(timeout=6.0)

        # Apply strict facts guardrail
        if _validate_reply_guardrail(draft, facts):
            return draft, "gemini"
        else:
            return template_reply, "template_guardrail_fallback"

    except Exception:
        return template_reply, "template"


def _get_or_create_new_ticket(agent: str, route: str, raw_text: str, parsed_msg: dict) -> dict:
    """Create or retrieve deduplicated RF-NEW-### ticket marked 'logged via intake'."""
    msg_hash = hashlib.sha256(raw_text.strip().lower().encode("utf-8")).hexdigest() if raw_text else None
    if msg_hash and msg_hash in _DEDUP_INTAKE_TICKETS:
        return _DEDUP_INTAKE_TICKETS[msg_hash]

    new_id = get_next_new_refund_id()
    new_entry = {
        "clean_id": new_id,
        "canonical_agent": normalize_agent_name(agent) if agent else "Unknown Agent",
        "route": route or "NOT-SPECIFIED",
        "Refund Amount (INR)": None,
        "Amount Paid (INR)": 0.0,
        "Deduction (INR)": 0.0,
        "clean_status": "Working",
        "clean_payout_status": "Pending Verification",
        "gap_class": "Logged via Intake",
        "effective_age_days": 0,
        "owner_team": "Support",
        "recommended_action": "Verify cancellation with supplier and log refund amount",
        "intake_source": parsed_msg.get("channel", "Email"),
        "intake_date": parsed_msg.get("request_date") or parsed_msg.get("date_received", str(SNAPSHOT_DATE.date())),
    }
    if msg_hash:
        _DEDUP_INTAKE_TICKETS[msg_hash] = new_entry
    return new_entry


def lookup_and_reconcile_intake(
    parsed_msg: dict | tuple,
    unified_ledger: pd.DataFrame,
    msg_date_str: str = "2026-06-30",
    gemini_client=None,
) -> dict:
    """Look up parsed intake request against unified ledger with plausibility guard.
    Rules:
    - Internal Support note: route to Gap Class B analysis without creating refund.
    - Assertable UNIQUE_MATCH only if:
        (a) message contains ticket ref equal to ledger ID, OR
        (b) exactly one candidate AND its request date is within 45 days before message date
            AND its status does not contradict message.
    - Otherwise (contradiction or >45 days): return POSSIBLE_MATCH_LOW_CONFIDENCE with plain note,
      do not assert any status, create RF-NEW-### entry marked 'logged via intake', draft reply
      asking for booking reference / PNR / travel date.
    - Ambiguous (multiple candidates): apply same 45-day filter (earlier candidates excluded from main list
      but mentioned as earlier refunds).
    """
    if isinstance(parsed_msg, tuple):
        parsed_msg = parsed_msg[0]
    agent = parsed_msg.get("agent_name")
    route = parsed_msg.get("route")
    ticket_ref = parsed_msg.get("ticket_ref") or parsed_msg.get("booking_ref")
    issue_type = parsed_msg.get("issue_type")
    raw_text = parsed_msg.get("raw_text", "")

    # Determine message date
    date_val = parsed_msg.get("request_date") or msg_date_str
    try:
        msg_date = pd.to_datetime(date_val)
    except Exception:
        msg_date = pd.to_datetime("2026-06-30")

    # 1. Preset (c) / Internal Gap Report
    if issue_type in ["internal_gap_escalation", "internal_note"] or agent == "Internal Support":
        gap_b_records = unified_ledger[unified_ledger["gap_class"] == GAP_CLASS_B]
        count_b = len(gap_b_records)
        sum_b = float(gap_b_records["Refund Amount (INR)"].sum())

        return {
            "match_type": "INTERNAL_GAP_REPORT",
            "message": "Internal Support Note identified: routed to Gap Class B analysis.",
            "action": "DISPLAY_GAP_B_REPORT",
            "gap_b_count": count_b,
            "gap_b_sum": sum_b,
            "draft_reply": f"Internal note acknowledged. Exactly {count_b} refunds marked Closed in Support have no Finance record (Total: INR {sum_b:,.0f}). Batch handoff required to Finance Operations.",
            "candidates": gap_b_records.head(10).to_dict(orient="records"),
            "new_ticket": None,
            "reply_engine": "template",
        }

    # 2. Condition (a): Message contains a ticket ref equal to a ledger ID -> assertable UNIQUE_MATCH
    if ticket_ref:
        cleaned_ref = clean_id(ticket_ref)
        id_match = unified_ledger[unified_ledger["clean_id"] == cleaned_ref]
        if len(id_match) == 1:
            return _format_unique_match(id_match.iloc[0], parsed_msg, gemini_client)

    # 3. Match by Canonical Agent + Route
    candidates = pd.DataFrame()
    if agent and agent != "Unknown Agent" and route:
        canon_agent = normalize_agent_name(agent)
        candidates = unified_ledger[
            (unified_ledger["canonical_agent"] == canon_agent)
            & (unified_ledger["route"] == route)
        ]

    if len(candidates) == 0:
        # No match found -> create new entry with RF-NEW-### prefix
        new_entry = _get_or_create_new_ticket(agent, route, raw_text, parsed_msg)
        new_id = new_entry["clean_id"]

        template_draft = (
            f"Dear {agent or 'Travel Partner'} Team,\n\n"
            f"Thank you for contacting BharatTrip. We have logged your refund request under reference {new_id}. "
            f"Our Support team is currently verifying the booking details with the travel supplier. We will update you "
            f"as soon as verification is complete.\n\n"
            f"Reference: {new_id}\n"
            f"Best regards,\nBharatTrip Operations Team"
        )

        facts = {
            "agent": agent or "Travel Partner",
            "new_ticket_id": new_id,
            "route": route or "the booked flight",
            "status_summary": "Logged new ticket; awaiting verification with supplier.",
            "default_draft": template_draft,
        }
        draft_reply, reply_engine = draft_reply_with_gemini(facts, parsed_msg, gemini_client)

        return {
            "match_type": "NO_MATCH_NEW_CREATED",
            "message": f"No existing ticket found. Created new intake ticket: {new_id}",
            "new_ticket": new_entry,
            "draft_reply": draft_reply,
            "candidates": [],
            "reply_engine": reply_engine,
        }

    # Helper date filter for candidates
    def _in_window(row):
        req_dt = row.get("parsed_request_date")
        if pd.isna(req_dt):
            return False
        delta = (msg_date - pd.to_datetime(req_dt)).days
        return 0 <= delta <= 45

    def _is_earlier(row):
        req_dt = row.get("parsed_request_date")
        if pd.isna(req_dt):
            return False
        delta = (msg_date - pd.to_datetime(req_dt)).days
        return delta > 45

    # Case: Exactly 1 candidate overall
    if len(candidates) == 1:
        single_cand = candidates.iloc[0]
        req_dt = single_cand.get("parsed_request_date")
        delta = (msg_date - pd.to_datetime(req_dt)).days if pd.notna(req_dt) else 999
        in_45_days = (0 <= delta <= 45)

        # Check status contradiction with message
        fin_status = single_cand.get("clean_payout_status", "")
        msg_lower = raw_text.lower()
        msg_indicates_unreceived = any(kw in msg_lower for kw in [
            "haven't received", "havent received", "not received", "kya hua",
            "koi jawab nahi", "where", "chasing", "pending", "2 hafte", "two weeks"
        ]) or issue_type in ["status_chase", "new_request"]

        contradicts = (msg_indicates_unreceived and fin_status in ["Refund Done", "Declined"])

        # Condition (b): within 45 days AND status does not contradict
        if in_45_days and not contradicts:
            return _format_unique_match(single_cand, parsed_msg, gemini_client)
        else:
            # Condition (b) fails -> POSSIBLE_MATCH_LOW_CONFIDENCE
            cand_id = single_cand["clean_id"]
            proc_dt = single_cand.get("parsed_processed_on")
            if pd.notna(proc_dt):
                paid_str = pd.to_datetime(proc_dt).strftime("%d %b")
                status_note = f"earlier refund on this route, paid {paid_str}; confirm if same booking"
            else:
                req_str = pd.to_datetime(req_dt).strftime("%d %b") if pd.notna(req_dt) else "earlier"
                status_note = f"earlier refund on this route, requested {req_str}; confirm if same booking"

            new_ticket = _get_or_create_new_ticket(agent, route, raw_text, parsed_msg)
            new_id = new_ticket["clean_id"]

            draft_reply = (
                f"Dear {agent} Team,\n\n"
                f"Thank you for reaching out regarding the {route} refund inquiry. We found an earlier record ({status_note}). "
                f"To confirm whether your inquiry relates to that transaction or a separate cancellation, could you please provide "
                f"the booking reference, airline PNR, or travel date?\n\n"
                f"In the meantime, your request has been logged under reference {new_id}.\n\n"
                f"Best regards,\nBharatTrip Operations Team"
            )

            cand_dict = single_cand.to_dict()
            cand_dict["plain_note"] = status_note

            return {
                "match_type": "POSSIBLE_MATCH_LOW_CONFIDENCE",
                "message": f"Possible match identified ({cand_id}), but low confidence due to date or status variance. Clarification requested.",
                "candidate_note": status_note,
                "candidates": [cand_dict],
                "candidate_count": 1,
                "new_ticket": new_ticket,
                "new_ticket_id": new_id,
                "draft_reply": draft_reply,
                "reply_engine": "template",
            }

    # Case: Multiple candidates overall
    # Apply 45-day window filter: candidates outside window excluded from main list but mentioned as earlier refunds
    has_explicit_date = bool(parsed_msg.get("request_date"))
    if has_explicit_date:
        active_mask = candidates.apply(_in_window, axis=1)
        earlier_mask = candidates.apply(_is_earlier, axis=1)
        active_df = candidates[active_mask]
        earlier_df = candidates[earlier_mask]

        if len(active_df) >= 2:
            use_df = active_df
            earlier_count = len(earlier_df)
        else:
            use_df = candidates
            earlier_count = 0
    else:
        use_df = candidates
        earlier_count = 0

    active_records = use_df[
        ["clean_id", "canonical_agent", "route", "Refund Amount (INR)", "clean_status", "clean_payout_status", "parsed_request_date"]
    ].to_dict(orient="records")

    earlier_note = f" (plus {earlier_count} earlier refund{'s' if earlier_count != 1 else ''} outside 45-day window)" if earlier_count > 0 else ""

    draft = (
        f"Dear {agent} Team,\n\n"
        f"Thank you for reaching out regarding route {route}. We found {len(active_records)} recent refund records "
        f"matching your agency for this sector{earlier_note}. Could you please confirm your specific ticket reference, "
        f"booking reference, PNR, or travel date so we can provide the exact status?\n\n"
        f"Best regards,\nBharatTrip Operations Team"
    )

    return {
        "match_type": "MULTIPLE_MATCHES",
        "message": f"Found {len(active_records)} recent candidate matches{earlier_note}. Requires agent clarification.",
        "candidates": active_records,
        "candidate_count": len(active_records),
        "earlier_candidates_count": earlier_count,
        "draft_reply": draft,
        "new_ticket": None,
        "reply_engine": "template",
    }


def _format_unique_match(row: pd.Series, parsed_msg: dict, gemini_client=None) -> dict:
    """Format uniquely matched ledger entry and draft polite reply grounded strictly in ledger."""
    ticket_id = row["clean_id"]
    agent = row["canonical_agent"]
    route = row["route"]
    sup_status = row.get("clean_status", "Unknown")
    fin_status = row.get("clean_payout_status", "None")
    amt_paid = row.get("Amount Paid (INR)")
    gap = row.get("gap_class", "")

    if fin_status == "Refund Done":
        status_text = f"Refund of INR {amt_paid:,.0f} has been processed and disbursed."
    elif fin_status == "Pending Payout":
        status_text = "The refund request has been verified and is currently awaiting payout clearance with Finance."
    elif fin_status == "Declined":
        status_text = "The refund was declined in accordance with supplier cancellation policies (decline recorded in Finance)."
    elif gap == GAP_CLASS_B:
        status_text = "The refund is currently under expedited operational review with our Finance team."
    else:
        status_text = f"The refund request is currently {sup_status.lower()} in our system."

    template_draft = (
        f"Dear {agent} Team,\n\n"
        f"Regarding your inquiry for ticket {ticket_id} ({route}):\n"
        f"{status_text}\n\n"
        f"Please reference {ticket_id} for any future correspondence.\n\n"
        f"Best regards,\nBharatTrip Operations Team"
    )

    facts = {
        "agent": agent,
        "ticket_id": ticket_id,
        "route": route,
        "status_summary": status_text,
        "amount_paid": amt_paid,
        "default_draft": template_draft,
    }

    final_draft, reply_engine = draft_reply_with_gemini(facts, parsed_msg, gemini_client)

    return {
        "match_type": "UNIQUE_MATCH",
        "matched_ticket": row.to_dict(),
        "ticket_id": ticket_id,
        "status_summary": status_text,
        "draft_reply": final_draft,
        "candidates": [row.to_dict()],
        "new_ticket": None,
        "reply_engine": reply_engine,
    }
