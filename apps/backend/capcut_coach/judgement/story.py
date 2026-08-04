"""Script → story beats: the coverage contract (add-on §8).

The script is not a list of captions to paste onto arbitrary shots — it is a
contract for what the finished video must *cover*. This module parses a script
into ordered beats, classifies each beat's narrative purpose, and — critically —
extracts the **immutable facts** (numbers, prices, offers, CTAs, URLs) that the
planner may never alter or drop, even when it shortens wording (CLAUDE.md rule 7;
add-on §8).

Pure and deterministic; no model required. A VLM (Level B) can later enrich
desired actions/emotions, but the facts are fixed here from the owner's own text.
"""

from __future__ import annotations

import re
import uuid

from .schemas import StoryBeat, StoryPurpose

SECOND_US = 1_000_000

# Signals for immutable facts that must survive verbatim (add-on §8).
_MONEY = re.compile(r"[£$€]\s?\d[\d,]*(?:\.\d+)?|\b\d+(?:\.\d+)?\s?(?:%|percent\b)")
_NUMBER = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
_URL = re.compile(r"\b(?:https?://|www\.)\S+|\b\S+\.(?:com|co|io|shop|store)\b", re.IGNORECASE)
_OFFER = re.compile(r"\b(free|save|off|discount|deal|offer|only|limited|today|book|call|"
                    r"order|shop|sign\s?up|subscribe|dm|link in bio)\b", re.IGNORECASE)

_CTA_WORDS = re.compile(r"\b(book|call|order|shop|buy|sign\s?up|subscribe|dm|visit|"
                        r"click|link in bio|get yours|today)\b", re.IGNORECASE)
_HOOK_WORDS = re.compile(r"\b(imagine|ever|tired of|what if|stop|watch|here'?s|introducing)\b",
                         re.IGNORECASE)
_PROOF_WORDS = re.compile(r"\b(results?|before|after|review|rated|proven|trusted|guarantee)\b",
                          re.IGNORECASE)


def extract_immutable_facts(text: str) -> list[str]:
    """Facts that must be preserved verbatim: money, offers, numbers, URLs."""
    facts: list[str] = []
    for pat in (_MONEY, _URL):
        facts += [m.group(0).strip() for m in pat.finditer(text)]
    facts += [m.group(0).strip() for m in _OFFER.finditer(text)]
    # Bare numbers only when not already captured inside a money/percent match.
    for m in _NUMBER.finditer(text):
        tok = m.group(0)
        if not any(tok in f for f in facts):
            facts.append(tok)
    # De-duplicate, preserve order.
    seen: set[str] = set()
    out: list[str] = []
    for f in facts:
        low = f.lower()
        if low not in seen:
            seen.add(low)
            out.append(f)
    return out


def _classify(line: str, index: int, total: int) -> StoryPurpose:
    if _CTA_WORDS.search(line):
        return "cta"
    if index == 0 and (_HOOK_WORDS.search(line) or total > 1):
        return "hook"
    if _PROOF_WORDS.search(line):
        return "proof"
    if index == total - 1:
        return "payoff"
    return "setup"


def _split_lines(script: str) -> list[str]:
    """One beat per non-empty line; fall back to sentence splitting for prose."""
    lines = [ln.strip() for ln in script.splitlines() if ln.strip()]
    if len(lines) > 1:
        return lines
    # Single block of prose: split into sentences.
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", script.strip()) if s.strip()]


def parse_beats(script: str) -> list[StoryBeat]:
    """Parse a script into ordered story beats with immutable facts marked.

    A beat is *required* when it carries an immutable fact or is a call-to-action —
    those must be covered or explicitly reported missing by Smart Check (§8).
    """
    beats: list[StoryBeat] = []
    lines = _split_lines(script or "")
    total = len(lines)
    for i, line in enumerate(lines):
        facts = extract_immutable_facts(line)
        purpose = _classify(line, i, total)
        required = bool(facts) or purpose == "cta"
        beats.append(StoryBeat(
            id=f"beat_{uuid.uuid4().hex[:12]}",
            source_text=line,
            purpose=purpose,
            required=required,
            caption_text=line,
            immutable_facts=facts,
            min_duration_us=int(1.5 * SECOND_US),
            max_duration_us=int(5.0 * SECOND_US),
            confidence=0.5 if total > 1 else 0.3,  # a lone prose block is lower-confidence
        ))
    return beats


def facts_preserved(original_facts: list[str], shortened_text: str) -> bool:
    """True iff every immutable fact still appears in the shortened caption (§8).

    Case-insensitive substring check — the planner may re-word around a fact but
    must never drop or alter the fact itself.
    """
    hay = shortened_text.lower()
    return all(fact.lower() in hay for fact in original_facts)
