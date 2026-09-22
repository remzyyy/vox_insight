"""PII detection and redaction used by the KB cleaner (Q2) and logs.

Regex-based detection is intentionally conservative: it aims to *flag* records
that contain PII so they can be redacted before indexing, rather than to be a
perfect classifier. Detected spans are replaced with typed placeholders so the
surrounding context is preserved for retrieval.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Order matters: more specific patterns first.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    # Phone: optional +CC, then 10 digits possibly split into 5-5 / 3-3-4 / etc.
    ("PHONE", re.compile(
        r"(?<!\d)(?:\+?\d{1,3}[ -]?)?(?:\(?\d{2,5}\)?[ -]?)\d{3,5}(?:[ -]?\d{3,5})?(?!\d)"
    )),
    # National IDs (generic long digit runs already covered by CC; keep SSN-like)
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),  # Indian PAN, illustrative
]


@dataclass
class PIIResult:
    has_pii: bool
    redacted_text: str
    found_types: list[str]


def scan_and_redact(text: str) -> PIIResult:
    found: list[str] = []
    redacted = text
    for label, pattern in _PATTERNS:
        def _repl(m, label=label):
            found.append(label)
            return f"[{label}_REDACTED]"

        redacted = pattern.sub(_repl, redacted)
    # De-dup while preserving order
    ordered = list(dict.fromkeys(found))
    return PIIResult(has_pii=bool(ordered), redacted_text=redacted, found_types=ordered)


def contains_pii(text: str) -> bool:
    return scan_and_redact(text).has_pii
