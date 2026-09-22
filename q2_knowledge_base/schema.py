"""Knowledge-base record schema and taxonomy.

Mirrors the field example in the assessment:
  record_id, title, content, category, source, version, pii
and adds retrieval-oriented metadata (chunk info, tags, updated date).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# Product / policy taxonomy for business-loan qualification.
TAXONOMY: dict[str, list[str]] = {
    "product": ["term_loan", "working_capital", "line_of_credit", "equipment_finance", "invoice_finance"],
    "policy": ["eligibility", "documentation", "interest_and_fees", "repayment", "privacy_pii"],
    "qualification": ["revenue_rules", "vintage_rules", "credit_score_rules", "collateral_rules"],
    "faq": ["general", "application_process", "disbursal", "prepayment"],
    "objection": ["rate_too_high", "too_much_paperwork", "already_have_loan", "not_sure_need_it", "trust_security"],
    "partnership_benefits": ["branch", "referral"],
}

CATEGORIES = list(TAXONOMY.keys())


@dataclass
class KBRecord:
    record_id: str
    title: str
    content: str
    category: str          # top-level taxonomy key
    subcategory: str       # value within taxonomy[category]
    source: str            # human-readable origin (e.g. "website:/loans/eligibility")
    version: str = "1.0"
    pii: bool = False
    tags: list[str] = field(default_factory=list)
    updated: str = "2026-01-01"   # ISO date, standardized

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KBChunk:
    """A retrievable unit derived from a KBRecord."""
    chunk_id: str
    record_id: str
    title: str
    content: str
    category: str
    subcategory: str
    source: str
    version: str
    pii: bool
    seq: int  # position of this chunk within its record

    def citation(self) -> str:
        return f"{self.record_id} · {self.title} ({self.source}, v{self.version})"
