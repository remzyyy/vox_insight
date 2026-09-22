"""Data collection & cleaning utilities (Q2).

Covers the assessment's cleaning requirements:
  - website extraction & document parsing (HTML -> text)
  - remove nav/headers/footers/repeated/irrelevant content
  - handle extraction failures & flag obvious source errors
  - remove duplicate / near-duplicate content
  - standardize headings, dates, terminology
  - identify & protect PII

Extraction of live URLs is optional (needs network); the build pipeline ships
with local sample sources so the KB is reproducible offline.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from shared.logging_utils import get_logger
from shared.pii import scan_and_redact

log = get_logger("q2.cleaning")

# Boilerplate lines to strip from scraped pages (nav/footer/cookie banners).
_BOILERPLATE = [
    re.compile(r"^\s*(home|about us|contact|careers|login|sign up|menu)\s*$", re.I),
    re.compile(r"cookie", re.I),
    re.compile(r"all rights reserved", re.I),
    re.compile(r"^\s*(privacy policy|terms of service)\s*$", re.I),
    re.compile(r"follow us on", re.I),
]

# Terminology standardization: map inconsistent variants to canonical terms.
_TERM_MAP = {
    r"\bworking capital loan\b": "working capital",
    r"\bWC loan\b": "working capital",
    r"\bROI\b": "interest rate",
    r"\brate of interest\b": "interest rate",
    r"\bEMI['\u2019]?s?\b": "EMI",
    r"\bpre[- ]?payment\b": "prepayment",
    r"\bturn ?over\b": "annual revenue",
}


@dataclass
class CleanResult:
    text: str
    had_pii: bool
    pii_types: list[str]
    warnings: list[str]


def html_to_text(html: str) -> str:
    """Extract readable text from HTML, dropping nav/script/style/footer."""
    try:
        from bs4 import BeautifulSoup
    except Exception:
        # Fallback: naive tag strip if bs4 missing.
        return re.sub(r"<[^>]+>", " ", html)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "form", "aside"]):
        tag.decompose()
    text = soup.get_text("\n")
    return text


def _standardize_dates(text: str) -> str:
    # DD/MM/YYYY or DD-MM-YYYY -> YYYY-MM-DD (best-effort, assumes day-first).
    def repl(m):
        d, mo, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{int(mo):02d}-{int(d):02d}"

    return re.sub(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", repl, text)


def _standardize_terms(text: str) -> str:
    for pat, canonical in _TERM_MAP.items():
        text = re.sub(pat, canonical, text, flags=re.I)
    # Collapse redundant parentheticals left by standardization, e.g.
    # "working capital (working capital)" -> "working capital".
    text = re.sub(r"\b(\w[\w ]*?)\s*\(\1\)", r"\1", text, flags=re.I)
    return text


def clean_text(raw: str, *, redact_pii: bool = True) -> CleanResult:
    warnings: list[str] = []
    if not raw or not raw.strip():
        warnings.append("empty_or_failed_extraction")
        return CleanResult("", False, [], warnings)

    lines = [ln.strip() for ln in raw.splitlines()]
    kept: list[str] = []
    seen: set[str] = set()
    for ln in lines:
        if not ln:
            continue
        if any(p.search(ln) for p in _BOILERPLATE):
            continue
        # Drop exact duplicate lines (repeated sections).
        key = ln.lower()
        if key in seen:
            continue
        seen.add(key)
        kept.append(ln)

    text = "\n".join(kept)
    text = _standardize_dates(text)
    text = _standardize_terms(text)
    # Collapse excess whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # Flag obvious source errors.
    if re.search(r"\b(lorem ipsum|404 not found|page not found|undefined)\b", text, re.I):
        warnings.append("suspected_source_error")

    had_pii, pii_types = False, []
    if redact_pii:
        res = scan_and_redact(text)
        text = res.redacted_text
        had_pii = res.has_pii
        pii_types = res.found_types

    return CleanResult(text=text, had_pii=had_pii, pii_types=pii_types, warnings=warnings)


def content_fingerprint(text: str) -> str:
    """Normalized fingerprint for exact-duplicate detection."""
    norm = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha1(norm.encode()).hexdigest()


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


NEAR_DUP_THRESHOLD = 0.85


def dedupe_records(records: list) -> list:
    """Remove exact and near-duplicate records.

    Exact duplicates are caught by normalized fingerprint. Near-duplicates
    (e.g. a mirror page that only differs by nav/footer) are caught by
    Jaccard token-set similarity above NEAR_DUP_THRESHOLD.
    """
    seen_fp: set[str] = set()
    kept: list = []
    kept_tokens: list[set[str]] = []
    for r in records:
        fp = content_fingerprint(r.content)
        if fp in seen_fp:
            log.info("Dropping exact-duplicate record %s", r.record_id)
            continue
        toks = _token_set(r.content)
        if any(_jaccard(toks, kt) >= NEAR_DUP_THRESHOLD for kt in kept_tokens):
            log.info("Dropping near-duplicate record %s", r.record_id)
            continue
        seen_fp.add(fp)
        kept.append(r)
        kept_tokens.append(toks)
    return kept
