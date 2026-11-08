"""Configuration constants for BharatTrip Refund Operations."""
import os
from pathlib import Path
import pandas as pd

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKBOOK_PATH = PROJECT_ROOT / "data" / "BharatTrip_Refund_Data.xlsx"

# Fixed operational snapshot date
SNAPSHOT_DATE = pd.Timestamp("2026-06-30")

# 22 Canonical Agent Names
CANONICAL_AGENTS = [
    "Anand Travels",
    "BlueJet Tours",
    "Coral Voyages",
    "DeccanFly",
    "Global Wings",
    "GoFly Holidays",
    "Himalaya Holidays",
    "Kaveri Tours",
    "Lotus Travel Co",
    "Metro Yatra",
    "Nomad Travel",
    "Orbit Travels",
    "Peak Journeys",
    "Pinnacle Getaways",
    "SafarNama Travel",
    "Skyline Travels",
    "Sunrise Trips",
    "TripHub",
    "Voyage Desk",
    "Wander Agency",
    "Yatri Junction",
    "ZipTrip",
]

# Canonical mapping for casing variants
CANONICAL_AGENT_MAP = {
    agent.lower().replace(" ", ""): agent for agent in CANONICAL_AGENTS
}

# Gap Class Taxonomy
GAP_CLASS_A = "Class A: Unlinked Escalation"
GAP_CLASS_B = "Class B: Support Closed, Finance None"
GAP_CLASS_C = "Class C: Support Closed, Finance Pending"
GAP_CLASS_D = "Class D: Support Closed, Finance Declined"
GAP_CLASS_E = "Class E: Paid with Amount Discrepancy"
GAP_CLASS_H = "Class H: Finance Only (No Support Ticket)"
GAP_CLASS_MATCH = "Matched & Reconciled"
GAP_CLASS_MATCH_MISSING_AMT = "Matched - Support amount missing"

# Escalation Root Causes
ROOT_CAUSE_PAID_MATCHED = "paid and matched"
ROOT_CAUSE_SUPPORT_CLOSED_NO_FINANCE = "Support closed/no Finance"
ROOT_CAUSE_NEVER_LOGGED = "never logged"
ROOT_CAUSE_PAID_AMOUNT_DIFFERS = "paid but amount differs"
ROOT_CAUSE_FINANCE_PENDING_SUPPORT_OPEN = "Finance pending/Support not closed"
ROOT_CAUSE_DECLINED = "declined"
ROOT_CAUSE_SUPPORT_CLOSED_FINANCE_PENDING = "Support closed/Finance pending"
ROOT_CAUSE_FINANCE_ONLY = "Finance-only"

# Inferred approval tier threshold: all approved rows in Finance are above INR 20,000 (smallest approved is INR 20,100; two unapproved refunds sit at exactly INR 20,000)
APPROVAL_THRESHOLD = 20000.0
