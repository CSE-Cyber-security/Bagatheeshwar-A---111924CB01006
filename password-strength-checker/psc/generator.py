"""Cryptographically secure password and passphrase generators.

Uses :mod:`secrets` (never :mod:`random`) so the output is unpredictable.
"""
from __future__ import annotations

import math
import secrets
import string
from functools import lru_cache
from typing import List

from .patterns import english_words

SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~"
AMBIGUOUS = set("Il1O0o|")
MAX_LENGTH = 256


def generate_password(length: int = 16, *, lower: bool = True, upper: bool = True,
                      digits: bool = True, symbols: bool = True,
                      avoid_ambiguous: bool = False) -> str:
    """Random password containing at least one character of every selected group."""
    groups: List[str] = []
    for enabled, chars in ((lower, string.ascii_lowercase), (upper, string.ascii_uppercase),
                           (digits, string.digits), (symbols, SYMBOLS)):
        if enabled:
            if avoid_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            groups.append(chars)
    if not groups:
        raise ValueError("Select at least one character group.")
    if length < len(groups):
        raise ValueError(f"Length must be at least {len(groups)} for the selected groups.")
    if length > MAX_LENGTH:
        raise ValueError(f"Length must not exceed {MAX_LENGTH}.")

    everything = "".join(groups)
    chars = [secrets.choice(group) for group in groups]  # guarantee one of each group
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


@lru_cache(maxsize=1)
def passphrase_words() -> List[str]:
    """2,048 common, easy-to-type words (exactly 11 bits of entropy per word)."""
    words = [w for w in english_words() if 4 <= len(w) <= 8 and w.isascii() and w.isalpha()]
    return words[:2048]


def generate_passphrase(words: int = 6, separator: str = "-", capitalize: bool = False,
                        add_number: bool = False) -> str:
    """Several random words, e.g. ``rocket-lemon-train-valley-spoon-grape``."""
    if not 3 <= words <= 20:
        raise ValueError("Use between 3 and 20 words.")
    pool = passphrase_words()
    chosen = [secrets.choice(pool) for _ in range(words)]
    if capitalize:
        chosen = [w.capitalize() for w in chosen]
    phrase = separator.join(chosen)
    if add_number:
        phrase += separator + str(secrets.randbelow(100))
    return phrase


def passphrase_entropy_bits(words: int, add_number: bool = False) -> float:
    """True entropy of :func:`generate_passphrase` output."""
    bits = words * math.log2(len(passphrase_words()))
    return bits + (math.log2(100) if add_number else 0.0)
