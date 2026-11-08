"""Optional "has this password been leaked?" check using Have I Been Pwned.

Privacy (k-anonymity): the password is hashed locally with SHA-1 and **only the
first 5 hex characters of the hash** are sent.  The server returns every hash
suffix that shares that prefix and the comparison happens on this machine, so the
password - and even its full hash - never leaves the computer.

(SHA-1 is required by the HIBP API.  It is used here only for lookup, not to
protect or store anything.)
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from typing import Callable, Optional, Tuple

API_URL = "https://api.pwnedpasswords.com/range/"
USER_AGENT = "password-strength-checker-student-project"


def sha1_prefix_suffix(password: str) -> Tuple[str, str]:
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()  # nosec - API requirement
    return digest[:5], digest[5:]


def count_in_response(body: str, suffix: str) -> int:
    """Find ``suffix`` in the ``SUFFIX:COUNT`` lines returned by the API."""
    for line in body.splitlines():
        candidate, _, count = line.strip().partition(":")
        if candidate.upper() == suffix:
            try:
                return int(count)
            except ValueError:
                return 0
    return 0


def check_pwned(password: str, timeout: float = 5.0,
                opener: Callable = urllib.request.urlopen) -> Optional[int]:
    """Return how many times the password appears in known breaches.

    Returns ``0`` if it was not found and ``None`` if the service could not be reached.
    """
    if not password:
        return 0
    prefix, suffix = sha1_prefix_suffix(password)
    request = urllib.request.Request(
        API_URL + prefix, headers={"User-Agent": USER_AGENT, "Add-Padding": "true"}
    )
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return count_in_response(body, suffix)
