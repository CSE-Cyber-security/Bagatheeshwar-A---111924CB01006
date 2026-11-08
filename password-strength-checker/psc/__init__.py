"""Password Strength Checker - a pattern-aware password analyzer.

Public API::

    from psc import analyze
    result = analyze("correct horse battery staple")
    print(result.label, result.score)
"""

__version__ = "1.0.0"

from .analyzer import Result, analyze  # noqa: E402  (after __version__ on purpose)

__all__ = ["analyze", "Result", "__version__"]
