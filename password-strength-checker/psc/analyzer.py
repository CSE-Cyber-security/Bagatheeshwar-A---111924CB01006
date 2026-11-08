"""Core analysis engine.

Pipeline::

    password -> character pool + naive entropy
             -> pattern detectors (patterns.py)
             -> cheapest-path search  => "effective" entropy
             -> score, label, crack times, checklist, suggestions
"""
from __future__ import annotations

import math
import string
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import crack_time, patterns

# Human-readable names of the checklist items (order = display order).
CHECK_LABELS: Dict[str, str] = {
    "length_8": "At least 8 characters",
    "length_12": "At least 12 characters (recommended)",
    "lower": "Contains lowercase letters",
    "upper": "Contains uppercase letters",
    "digit": "Contains digits",
    "symbol": "Contains symbols",
    "not_common": "Not a commonly used password",
    "no_dictionary": "No dictionary words",
    "no_patterns": "No sequences, keyboard walks or repeats",
    "no_dates": "No dates or years",
}

# (upper bound in bits, label); anything above the last bound is "Very Strong".
LEVELS: List[Tuple[float, str]] = [(28, "Very Weak"), (36, "Weak"), (60, "Moderate"), (80, "Strong")]
TOP_LABEL = "Very Strong"
SCORE_FULL_BITS = 80.0  # entropy that earns 100/100
MIN_LENGTH_CAP_BITS = 35.0  # passwords shorter than 8 chars can never be better than "Weak"


@dataclass
class Result:
    """Everything we know about one password."""

    length: int
    charset_size: int
    charsets: List[str]
    naive_bits: float
    effective_bits: float
    score: int
    label: str
    checks: Dict[str, bool] = field(default_factory=dict)
    findings: List[dict] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    crack_times: List[dict] = field(default_factory=list)
    breach_count: Optional[int] = None

    def to_dict(self, include_tokens: bool = False) -> dict:
        """JSON-friendly dict.  Password fragments are left out unless asked for."""
        findings = [
            {k: v for k, v in f.items() if include_tokens or k != "token"} for f in self.findings
        ]
        return {
            "length": self.length,
            "charset_size": self.charset_size,
            "charsets": self.charsets,
            "naive_entropy_bits": round(self.naive_bits, 2),
            "effective_entropy_bits": round(self.effective_bits, 2),
            "score": self.score,
            "label": self.label,
            "checks": self.checks,
            "findings": findings,
            "suggestions": self.suggestions,
            "crack_times": [
                {"scenario": c["description"], "estimate": c["display"]} for c in self.crack_times
            ],
            "breach_count": self.breach_count,
        }


# --------------------------------------------------------------------------
def charset_info(password: str) -> Tuple[List[str], int]:
    """Which character groups are used, and the size of the combined pool."""
    names: List[str] = []
    size = 0
    if any(c in string.ascii_lowercase for c in password):
        names.append("lowercase")
        size += 26
    if any(c in string.ascii_uppercase for c in password):
        names.append("uppercase")
        size += 26
    if any(c in string.digits for c in password):
        names.append("digits")
        size += 10
    if any(c in string.punctuation or c == " " for c in password):
        names.append("symbols")
        size += 33
    if any(not (c in string.ascii_letters or c in string.digits or c in string.punctuation
                or c == " ") for c in password):
        names.append("other/unicode")
        size += 100
    return names, size


def cheapest_path(password: str, matches: List[patterns.Match],
                  per_char_bits: float) -> Tuple[float, List[patterns.Match]]:
    """Dynamic programming: the lowest-entropy way to "spell" the password.

    ``best[i]`` = fewest bits needed to produce the first ``i`` characters, either by
    brute-forcing one more character or by using a pattern match that ends at ``i``.
    """
    n = len(password)
    by_end: Dict[int, List[patterns.Match]] = defaultdict(list)
    for m in matches:
        by_end[m.end].append(m)

    best = [0.0] + [math.inf] * n
    back: List[Optional[patterns.Match]] = [None] * (n + 1)
    for i in range(1, n + 1):
        best[i] = best[i - 1] + per_char_bits
        for m in by_end[i]:
            candidate = best[m.start] + m.bits
            if candidate < best[i]:
                best[i], back[i] = candidate, m

    chosen: List[patterns.Match] = []
    i = n
    while i > 0:
        m = back[i]
        if m is None:
            i -= 1
        else:
            chosen.append(m)
            i = m.start
    chosen.reverse()
    return best[n], chosen


def label_for(bits: float) -> str:
    for upper_bound, name in LEVELS:
        if bits < upper_bound:
            return name
    return TOP_LABEL


def score_for(bits: float) -> int:
    return int(round(min(100.0, max(0.0, bits) / SCORE_FULL_BITS * 100)))


def _suggestions(n: int, flags: Dict[str, bool], kinds: set, is_common: bool,
                 breach_count: Optional[int]) -> List[str]:
    tips: List[str] = []
    if breach_count:
        tips.append(f"This password appears {breach_count:,} times in known data breaches. "
                    "Never use it again, anywhere.")
    if is_common:
        tips.append("This is one of the most commonly used passwords - attackers try these first.")
    if n < 12:
        tips.append("Make it longer: aim for at least 12 characters, ideally 16 or more.")
    if kinds & {"dictionary", "common"} and not is_common:
        tips.append("Avoid dictionary words, even with swaps like @ for a or 0 for o. "
                    "A random passphrase of several unrelated words is a better choice.")
    if kinds & {"sequence", "keyboard"}:
        tips.append("Avoid sequences and keyboard walks such as abc, 1234 or qwerty.")
    if "repeat" in kinds:
        tips.append("Avoid repeated characters or repeated blocks such as aaa or abcabc.")
    if kinds & {"year", "date"}:
        tips.append("Avoid birth years, dates and other numbers that are easy to guess.")
    if n < 16:
        missing = [name for name, key in (("lowercase letters", "lower"), ("uppercase letters", "upper"),
                                          ("digits", "digit"), ("symbols", "symbol")) if not flags[key]]
        if missing:
            tips.append("Mix in " + ", ".join(missing) + ".")
    if not tips:
        tips.append("Looks good! Keep it in a password manager and never reuse it on other sites.")
    return tips


def analyze(password: str, breach_count: Optional[int] = None) -> Result:
    """Analyse ``password``.  ``breach_count`` (from :mod:`psc.breach`) is optional."""
    n = len(password)
    if n == 0:
        return Result(0, 0, [], 0.0, 0.0, 0, "Empty", {k: False for k in CHECK_LABELS},
                      [], ["Type or generate a password to analyse it."],
                      crack_time.estimate_all(0.0), None)

    charsets, pool = charset_info(password)
    per_char = math.log2(pool)
    naive = n * per_char

    matches = patterns.find_matches(password, pool)
    effective, path = cheapest_path(password, matches, per_char)
    effective = min(effective, naive)

    variants = [patterns.lower(password)] + patterns.leet_variants(patterns.lower(password))
    common = patterns.common_passwords()
    is_common = any(v in common for v in variants)

    if n < 8:
        effective = min(effective, MIN_LENGTH_CAP_BITS)

    score = score_for(effective)
    label = label_for(effective)
    if breach_count:  # found in a real-world leak: nothing else matters
        score, label = min(score, 10), "Compromised"

    kinds = {m.kind for m in path}
    flags = {
        "lower": "lowercase" in charsets,
        "upper": "uppercase" in charsets,
        "digit": "digits" in charsets,
        "symbol": any(c in string.punctuation or c == " " or not c.isascii() for c in password),
    }
    checks = {
        "length_8": n >= 8,
        "length_12": n >= 12,
        **flags,
        "not_common": not is_common,
        "no_dictionary": not (kinds & {"dictionary", "common"}),
        "no_patterns": not (kinds & {"sequence", "keyboard", "repeat"}),
        "no_dates": not (kinds & {"year", "date"}),
    }
    findings = [
        {"kind": m.kind, "detail": m.detail, "token": m.token}
        for m in path if m.kind != "separator"
    ]
    return Result(
        length=n,
        charset_size=pool,
        charsets=charsets,
        naive_bits=naive,
        effective_bits=effective,
        score=score,
        label=label,
        checks=checks,
        findings=findings,
        suggestions=_suggestions(n, flags, kinds, is_common, breach_count),
        crack_times=crack_time.estimate_all(effective),
        breach_count=breach_count,
    )
