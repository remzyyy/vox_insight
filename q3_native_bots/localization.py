"""Localization data model shared by the Philippines and Indonesia bots (Q3).

The point of Q3 is *localization, not translation*: natural code-switching,
local finance terminology, culturally appropriate politeness/register, and
fallback that stays in the customer's language. This module defines the schema;
the two market modules provide the actual content.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TermEntry:
    """A local finance term with when/how to use it."""
    term: str
    meaning_en: str
    usage_note: str


@dataclass
class LocalizationExample:
    """Evidence of adaptation vs literal translation."""
    situation: str
    literal_translation: str   # what a naive translator would say (rejected)
    localized: str             # what the bot actually says (natural)
    why: str                   # the localization reasoning


@dataclass
class ScriptedTurn:
    intent: str
    bot: str                   # bot line (localized, may code-switch)
    notes: str = ""


@dataclass
class FAQ:
    question: str
    answer: str


@dataclass
class Objection:
    trigger: str
    response: str


@dataclass
class BotConfig:
    market: str                # "philippines" | "indonesia"
    sector: str
    languages: list[str]
    register_notes: str
    asr: dict
    tts: dict
    terminology: list[TermEntry]
    greeting: str
    flow: list[ScriptedTurn]
    faqs: list[FAQ]
    objections: list[Objection]
    localization_examples: list[LocalizationExample]
    fallback_line: str         # stays in-language; no unexpected English switch
    escalation_line: str
    accent_notes: str = ""     # Indonesia regional accent handling
    code_switching_notes: str = ""
    known_gaps: list[str] = field(default_factory=list)
