"""Pattern detection used by the analyzer.

Every detector returns a list of :class:`Match` objects.  A match says
"characters ``start:end`` of the password can be guessed with only ``bits``
bits of effort because they follow a predictable pattern".  The analyzer then
finds the cheapest combination of matches that covers the password.
"""
from __future__ import annotations

import math
import re
import string
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path(__file__).resolve().parent / "data"

MIN_TOKEN_LEN = 4   # shortest substring looked up in the word lists
MAX_TOKEN_LEN = 32  # longest substring looked up in the word lists


@dataclass(frozen=True)
class Match:
    """A predictable chunk of the password."""

    start: int
    end: int  # exclusive
    kind: str  # common | dictionary | sequence | repeat | keyboard | year | date | separator
    bits: float
    token: str
    detail: str = ""

    @property
    def length(self) -> int:
        return self.end - self.start


# --------------------------------------------------------------------------
# Word lists
# --------------------------------------------------------------------------
def _load_ranked(filename: str) -> Dict[str, int]:
    """Load a one-word-per-line file, most popular first, into {word: rank}."""
    ranks: Dict[str, int] = {}
    with (DATA_DIR / filename).open(encoding="utf-8") as handle:
        for line in handle:
            word = line.strip().lower()
            if word and word not in ranks:
                ranks[word] = len(ranks) + 1
    return ranks


@lru_cache(maxsize=1)
def common_passwords() -> Dict[str, int]:
    """Top 10,000 leaked passwords, rank 1 = most common."""
    return _load_ranked("common_passwords.txt")


@lru_cache(maxsize=1)
def english_words() -> Dict[str, int]:
    """Top ~10,000 English words, rank 1 = most frequent."""
    return _load_ranked("words.txt")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
# Characters people commonly swap for letters ("leetspeak").
LEET_MAP = {
    "@": "a", "4": "a", "8": "b", "3": "e", "1": "i", "!": "i",
    "0": "o", "$": "s", "5": "s", "7": "t", "+": "t",
}


def lower(text: str) -> str:
    """Lower-case char by char so the string length never changes."""
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)


def leet_variants(lowered: str) -> List[str]:
    """Return de-leeted versions of a lower-cased string (same length)."""
    plain = "".join(LEET_MAP.get(c, c) for c in lowered)
    alt = "".join("l" if c == "1" else LEET_MAP.get(c, c) for c in lowered)
    out = []
    for variant in (plain, alt):
        if variant != lowered and variant not in out:
            out.append(variant)
    return out


def _case_bits(original: str) -> float:
    """Extra guesses needed because of the capitalisation used."""
    letters = [c for c in original if c.isalpha()]
    if not letters or all(c.islower() for c in letters):
        return 0.0
    if all(c.isupper() for c in letters):
        return 1.0
    if letters[0].isupper() and all(c.islower() for c in letters[1:]):
        return 1.0  # "Password" - by far the most common style
    upper = sum(c.isupper() for c in letters)
    lower_count = len(letters) - upper
    ways = sum(math.comb(len(letters), k) for k in range(1, min(upper, lower_count) + 1))
    return math.log2(ways) if ways > 1 else 1.0


def _char_class(c: str) -> str:
    if c in string.ascii_lowercase:
        return "l"
    if c in string.ascii_uppercase:
        return "u"
    if c in string.digits:
        return "d"
    return "?"


# --------------------------------------------------------------------------
# Detectors
# --------------------------------------------------------------------------
def dictionary_matches(password: str) -> List[Match]:
    """Common passwords and dictionary words, with leetspeak and capitalisation."""
    n = len(password)
    lowered = lower(password)
    variants = [lowered] + leet_variants(lowered)

    if n < MIN_TOKEN_LEN:
        spans: List[Tuple[int, int]] = [(0, n)] if n else []
    else:
        spans = [
            (i, j)
            for i in range(n)
            for j in range(i + MIN_TOKEN_LEN, min(n, i + MAX_TOKEN_LEN) + 1)
        ]

    best: Dict[Tuple[int, int, str], Match] = {}
    for variant in variants:
        for kind, ranks, noun in (
            ("common", common_passwords(), "Common password"),
            ("dictionary", english_words(), "Dictionary word"),
        ):
            for i, j in spans:
                rank = ranks.get(variant[i:j])
                if rank is None:
                    continue
                substitutions = sum(1 for a, b in zip(lowered[i:j], variant[i:j]) if a != b)
                bits = math.log2(rank + 1) + _case_bits(password[i:j]) + substitutions
                detail = noun + (" using predictable substitutions" if substitutions else "")
                match = Match(i, j, kind, bits, password[i:j], detail)
                key = (i, j, kind)
                if key not in best or bits < best[key].bits:
                    best[key] = match
    return list(best.values())


def sequence_matches(password: str) -> List[Match]:
    """Runs such as ``abcd``, ``DCBA`` or ``13579``-style +/-1 steps (``1234``, ``4321``)."""
    out: List[Match] = []
    n = len(password)
    i = 0
    while i < n - 1:
        step = ord(password[i + 1]) - ord(password[i])
        cls = _char_class(password[i])
        if step in (1, -1) and cls != "?" and _char_class(password[i + 1]) == cls:
            j = i + 1
            while (
                j + 1 < n
                and ord(password[j + 1]) - ord(password[j]) == step
                and _char_class(password[j + 1]) == cls
            ):
                j += 1
            length = j - i + 1
            if length >= 3:
                first = password[i]
                if first in "aAzZ019":
                    base = 2.0  # obvious starting points
                elif cls == "d":
                    base = math.log2(10)
                else:
                    base = math.log2(26)
                bits = base + 1.0 + math.log2(length)  # +1 bit for direction
                out.append(Match(i, j + 1, "sequence", bits, password[i : j + 1],
                                 "Sequence of consecutive characters"))
            i = j
        else:
            i += 1
    return out


def repeat_matches(password: str, pool: int) -> List[Match]:
    """``aaaa`` or repeated blocks such as ``abcabcabc``."""
    out: List[Match] = []
    per_char = math.log2(max(pool, 2))
    for found in re.finditer(r"(.+?)\1+", password, re.DOTALL):
        unit = found.group(1)
        count = len(found.group(0)) // len(unit)
        if len(unit) == 1 and count < 3:
            continue  # "aa" is perfectly normal
        bits = len(unit) * per_char + math.log2(count)
        out.append(Match(found.start(), found.end(), "repeat", bits, found.group(0),
                         f"Repeated characters or block ({count}x)"))
    return out


_ROWS = (("1234567890", 0.0), ("qwertyuiop", 0.5), ("asdfghjkl", 0.75), ("zxcvbnm", 1.25))
_POS = {ch: (r, c + off) for r, (row, off) in enumerate(_ROWS) for c, ch in enumerate(row)}
_SHIFTED = dict(zip("!@#$%^&*()", "1234567890"))


def _key(ch: str) -> str:
    ch = ch.lower()
    return _SHIFTED.get(ch, ch)


def _adjacent(a: str, b: str) -> bool:
    """True if two different keys touch each other on a QWERTY keyboard."""
    if a == b or a not in _POS or b not in _POS:
        return False
    (ra, xa), (rb, xb) = _POS[a], _POS[b]
    dy, dx = abs(ra - rb), abs(xa - xb)
    return (dy == 0 and dx == 1) or (dy == 1 and dx < 1)


def keyboard_matches(password: str) -> List[Match]:
    """Keyboard walks such as ``qwerty``, ``asdfgh`` or ``1qaz``."""
    out: List[Match] = []
    n = len(password)
    i = 0
    while i < n - 1:
        j = i
        while j + 1 < n and _adjacent(_key(password[j]), _key(password[j + 1])):
            j += 1
        length = j - i + 1
        if length >= 4:
            bits = math.log2(40) + (length - 1) * 1.6
            out.append(Match(i, j + 1, "keyboard", bits, password[i : j + 1], "Keyboard pattern"))
        i = j if j > i else i + 1
    return out


_YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})([-/. ]?)(\d{1,2})\2(\d{4}|\d{2})(?!\d)")


def date_matches(password: str) -> List[Match]:
    """Years (1900-2099) and dates such as ``25/12/1999`` or ``01011990``."""
    out: List[Match] = []
    for found in _YEAR_RE.finditer(password):
        out.append(Match(found.start(), found.end(), "year", math.log2(130), found.group(0),
                         "Year"))
    for found in _DATE_RE.finditer(password):
        d, sep, m, y = found.group(1), found.group(2), found.group(3), found.group(4)
        d, m = int(d), int(m)
        valid = (1 <= d <= 31 and 1 <= m <= 12) or (1 <= m <= 31 and 1 <= d <= 12)
        if not valid or (sep == "" and len(found.group(0)) < 6):
            continue
        bits = math.log2(31 * 12 * (130 if len(y) == 4 else 100))
        out.append(Match(found.start(), found.end(), "date", bits, found.group(0), "Date"))
    return out


def separator_matches(password: str) -> List[Match]:
    """A lone ``-``, ``_``, ``.`` or space between words is cheap for an attacker to guess."""
    return [
        Match(i, i + 1, "separator", 3.0, c, "Common separator")
        for i, c in enumerate(password)
        if c in "-_. " and 0 < i < len(password) - 1
    ]


def find_matches(password: str, pool: int) -> List[Match]:
    """Run every detector."""
    return (
        dictionary_matches(password)
        + sequence_matches(password)
        + repeat_matches(password, pool)
        + keyboard_matches(password)
        + date_matches(password)
        + separator_matches(password)
    )
