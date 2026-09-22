"""Mock CRM: lead creation, escalation, and call summary (Q1 business action).

Persists to a local SQLite file so leads/escalations are inspectable. In
production this would be a CRM API (Salesforce/HubSpot) or a webhook. PII stored
here is deliberately minimal and this DB is gitignored.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

_DB_PATH = "data/crm.sqlite"


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY, created_at TEXT, name TEXT, phone TEXT,
            business_type TEXT, purpose TEXT, revenue_lakh REAL, vintage_months INTEGER,
            credit_band TEXT, eligibility TEXT, status TEXT, raw TEXT
        );
        CREATE TABLE IF NOT EXISTS escalations (
            esc_id TEXT PRIMARY KEY, created_at TEXT, reason TEXT, call_id TEXT, notes TEXT
        );
        """
    )
    c.commit()
    return c


@dataclass
class Lead:
    name: str
    phone: str = ""
    business_type: str = ""
    purpose: str = ""
    revenue_lakh: float | None = None
    vintage_months: int | None = None
    credit_band: str = ""
    eligibility: str = ""
    lead_id: str = field(default_factory=lambda: "lead_" + uuid.uuid4().hex[:10])
    status: str = "new"


def create_lead(lead: Lead) -> dict:
    c = _conn()
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        """INSERT OR REPLACE INTO leads
           (lead_id,created_at,name,phone,business_type,purpose,revenue_lakh,
            vintage_months,credit_band,eligibility,status,raw)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            lead.lead_id, now, lead.name, lead.phone, lead.business_type, lead.purpose,
            lead.revenue_lakh, lead.vintage_months, lead.credit_band, lead.eligibility,
            lead.status, json.dumps(asdict(lead)),
        ),
    )
    c.commit()
    c.close()
    return {"lead_id": lead.lead_id, "status": "created", "created_at": now}


def escalate(reason: str, call_id: str = "", notes: str = "") -> dict:
    c = _conn()
    esc_id = "esc_" + uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO escalations (esc_id,created_at,reason,call_id,notes) VALUES (?,?,?,?,?)",
        (esc_id, now, reason, call_id, notes),
    )
    c.commit()
    c.close()
    return {"escalation_id": esc_id, "status": "queued", "reason": reason}


def call_summary(*, lead_id: str = "", transcript_turns: list[dict] | None = None,
                 eligibility: str = "", outcome: str = "") -> dict:
    """Produce a mock-CRM call summary object."""
    turns = transcript_turns or []
    return {
        "lead_id": lead_id,
        "turn_count": len(turns),
        "eligibility": eligibility,
        "outcome": outcome,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
