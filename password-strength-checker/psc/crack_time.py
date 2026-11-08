"""Turn an entropy estimate into human-readable "time to crack" figures."""
from __future__ import annotations

from typing import Dict, List

# key -> (description, guesses per second)
SCENARIOS: Dict[str, tuple] = {
    "online_throttled": ("Online attack, rate-limited (100 guesses/hour)", 100 / 3600),
    "online_unthrottled": ("Online attack, no limit (10 guesses/second)", 10.0),
    "offline_slow_hash": ("Offline, slow hash such as bcrypt (10 thousand/second)", 1e4),
    "offline_fast_hash": ("Offline, fast hash on GPUs (10 billion/second)", 1e10),
}

_MAX_BITS = 1000  # keeps 2**bits inside float range


def average_guesses(bits: float) -> float:
    """On average an attacker finds the password after trying half the space."""
    return 2.0 ** (min(max(bits, 0.0), _MAX_BITS) - 1)


def seconds_to_crack(bits: float, guesses_per_second: float) -> float:
    return average_guesses(bits) / guesses_per_second


def _fmt(value: float, unit: str) -> str:
    whole = int(round(value))
    return f"{whole} {unit}{'' if whole == 1 else 's'}"


def humanize(seconds: float) -> str:
    """1.5e9 -> '48 years', 3e20 -> '9 trillion years' ..."""
    if seconds < 1:
        return "instantly"
    if seconds < 60:
        return _fmt(seconds, "second")
    minutes = seconds / 60
    if minutes < 60:
        return _fmt(minutes, "minute")
    hours = minutes / 60
    if hours < 24:
        return _fmt(hours, "hour")
    days = hours / 24
    if days < 30:
        return _fmt(days, "day")
    months = days / 30.44
    if months < 12:
        return _fmt(months, "month")
    years = days / 365.25
    if years < 1000:
        return _fmt(years, "year")
    for scale, name in ((1e15, "quadrillion"), (1e12, "trillion"), (1e9, "billion"),
                        (1e6, "million"), (1e3, "thousand")):
        if years >= scale:
            if years >= 1e18:
                break
            return f"{years / scale:,.0f} {name} years"
    return "practically forever"


def estimate_all(bits: float) -> List[dict]:
    """One entry per attack scenario."""
    estimates = []
    for key, (description, rate) in SCENARIOS.items():
        secs = seconds_to_crack(bits, rate)
        estimates.append(
            {"key": key, "description": description, "seconds": secs, "display": humanize(secs)}
        )
    return estimates
