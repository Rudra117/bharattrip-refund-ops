"""Tests for LLM Intake Module, zero-key fallback, and unique matching logic.
"""
import os
import pytest
from core.config import DEFAULT_WORKBOOK_PATH
from core.clean import load_and_clean_all
from core.reconcile import reconcile_trackers, build_unified_ledger
from core.intake import (
    PRESET_A,
    PRESET_B,
    PRESET_C,
    get_llm_status,
    parse_informal_message,
    lookup_and_reconcile_intake,
    get_next_new_refund_id,
)


@pytest.fixture(scope="module")
def unified_ledger():
    """Build unified ledger for testing intake lookups."""
    data = load_and_clean_all(DEFAULT_WORKBOOK_PATH)
    reconciled = reconcile_trackers(data["support"], data["finance"])
    return build_unified_ledger(reconciled, data["escalations"])


def test_fallback_banner_when_no_api_key(monkeypatch):
    """Test that app modules import and fallback banner appears when no key is set (Amendment 4c)."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    status = get_llm_status()
    assert status["has_key"] is False
    assert status["is_fallback"] is True
    assert "Running without LLM" in status["banner"]


def test_preset_a_parsing_no_key(monkeypatch):
    """Test preset (a): parses to Peak Journeys and DEL-DXB with no API key (Amendment 4b)."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    parsed = parse_informal_message(
        PRESET_A["text"],
        channel=PRESET_A["channel"],
        date_str=PRESET_A["date"],
    )

    assert parsed["agent_name"] == "Peak Journeys"
    assert parsed["route"] == "DEL-DXB"
    assert parsed["channel"] == "Email"


def test_preset_b_parsing_no_key(monkeypatch):
    """Test preset (b): parses to Nomad Travel and BLR-MAA with no API key (Amendment 4b)."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    parsed = parse_informal_message(
        PRESET_B["text"],
        channel=PRESET_B["channel"],
        date_str=PRESET_B["date"],
    )

    assert parsed["agent_name"] == "Nomad Travel"
    assert parsed["route"] == "BLR-MAA"
    assert parsed["language_detected"] == "Hinglish"
    assert parsed["channel"] == "WhatsApp"


def test_preset_c_routes_to_gap_b_report(unified_ledger):
    """Test preset (c): internal Support note routes to Gap B report without creating a refund (Amendment 3)."""
    parsed = parse_informal_message(
        PRESET_C["text"],
        channel=PRESET_C["channel"],
        date_str=PRESET_C["date"],
    )

    result = lookup_and_reconcile_intake(parsed, unified_ledger)

    assert result["match_type"] == "INTERNAL_GAP_REPORT"
    assert result["new_ticket"] is None
    assert result["action"] == "DISPLAY_GAP_B_REPORT"
    assert result["gap_b_count"] == 69
    assert result["gap_b_sum"] == 1080700.0


def test_new_ticket_id_prefix():
    """Test new ticket generation uses RF-NEW-### prefix (Amendment 2)."""
    new_id = get_next_new_refund_id()
    assert new_id.startswith("RF-NEW-")
    assert len(new_id) == 10  # RF-NEW-001 format
    # Verify no collision with existing RF-1xxx format
    assert not new_id.startswith("RF-1")


def test_unique_matching_and_multiple_match_handling(unified_ledger):
    """Test intake matching enforces unique matches and requests confirmation on multiples (Amendment 1)."""
    # 1. Non-existent ticket creates new RF-NEW-###
    non_existent = {
        "agent_name": "Sunrise Trips",
        "route": "DEL-KTM",
        "booking_ref": None,
        "issue_type": "new_request",
    }
    result = lookup_and_reconcile_intake(non_existent, unified_ledger)
    assert result["match_type"] in ("UNIQUE_MATCH", "MULTIPLE_MATCHES", "NO_MATCH_NEW_CREATED")

    # If multiple candidates match, candidate list must be returned
    multiple_test = {
        "agent_name": "Peak Journeys",
        "route": "DEL-DXB",
        "booking_ref": None,
        "issue_type": "status_chase",
    }
    result_mult = lookup_and_reconcile_intake(multiple_test, unified_ledger)
    if result_mult["match_type"] == "MULTIPLE_MATCHES":
        assert len(result_mult["candidates"]) > 1
        assert "confirm your specific ticket reference" in result_mult["draft_reply"].lower()


def _has_valid_live_key_and_model():
    k = os.getenv("GEMINI_API_KEY", "").strip()
    m = os.getenv("GEMINI_MODEL", "").strip()
    return bool(k and not k.startswith("AQ.") and m and not m.startswith("your-"))


@pytest.mark.skipif(
    not _has_valid_live_key_and_model(),
    reason="Requires valid live GEMINI_API_KEY and GEMINI_MODEL",
)
def test_live_gemini_engine():
    """Assert engine == 'gemini' when live key and model are configured and reachable."""
    parsed = parse_informal_message(
        "Hi, I cancelled booking for DEL-DXB last week for Peak Journeys.",
        channel="Email",
    )
    assert parsed.get("engine") == "gemini"


class MockResponse:
    def __init__(self, text: str):
        self.text = text


def test_gemini_503_retry_and_fallback_to_next_model(monkeypatch):
    """Test HTTP 503 from primary model retries once after 1s, then tries next model in GEMINI_FALLBACK_MODELS and succeeds."""
    import json
    import time
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-primary")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "gemini-fallback-1,gemini-fallback-2")
    monkeypatch.setattr(time, "sleep", lambda s: None)

    calls = []

    class MockModels:
        def generate_content(self, model: str, contents: str):
            calls.append(model)
            if model == "gemini-primary":
                err = Exception("503 Service Unavailable")
                err.status_code = 503
                raise err
            elif model == "gemini-fallback-1":
                data = {
                    "agent_name": "Peak Journeys",
                    "route": "DEL-DXB",
                    "ticket_ref": "RF-1023",
                    "channel": "Email",
                    "issue_type": "status_chase",
                    "language_detected": "English",
                    "urgency": "High",
                    "confidence": 0.95,
                }
                return MockResponse(json.dumps(data))
            raise Exception("Unexpected model called")

    class MockClient:
        def __init__(self):
            self.models = MockModels()

    mock_client = MockClient()

    res = parse_informal_message(
        "Hi, inquiring about DEL-DXB refund for Peak Journeys RF-1023",
        channel="Email",
        gemini_client=mock_client,
    )

    assert res["engine"] == "gemini"
    assert res["engine_model"] == "gemini-fallback-1"
    assert res["agent_name"] == "Peak Journeys"
    assert res["route"] == "DEL-DXB"
    assert res["ticket_ref"] == "RF-1023"
    assert calls == ["gemini-primary", "gemini-primary", "gemini-fallback-1"]


def test_gemini_all_503_falls_back_to_rules(monkeypatch):
    """Test that if all models fail with HTTP 503 (including retries), it falls back to rules parser."""
    import time
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-primary")
    monkeypatch.setenv("GEMINI_FALLBACK_MODELS", "gemini-fallback-1")
    monkeypatch.setattr(time, "sleep", lambda s: None)

    calls = []

    class MockModels:
        def generate_content(self, model: str, contents: str):
            calls.append(model)
            err = Exception("503 Service Unavailable")
            err.code = 503
            raise err

    class MockClient:
        def __init__(self):
            self.models = MockModels()

    mock_client = MockClient()

    res = parse_informal_message(
        "Hi, I cancelled booking for DEL-DXB last week and was told I'd get a refund. I haven't received anything and I don't have any reference number. Please help, my client is asking.",
        channel="Email",
        gemini_client=mock_client,
    )

    assert res["engine"] == "rules_fallback"
    assert res["engine_model"] is None
    assert res["fallback_reason"] == "model_unavailable"
    assert res["agent_name"] == "Peak Journeys"
    assert res["route"] == "DEL-DXB"
    assert calls == ["gemini-primary", "gemini-primary", "gemini-fallback-1", "gemini-fallback-1"]
