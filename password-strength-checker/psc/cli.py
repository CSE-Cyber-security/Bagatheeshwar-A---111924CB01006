"""Command-line interface.

Examples::

    python main.py check                   # hidden prompt (recommended)
    python main.py check --online          # also run the breach check
    python main.py generate -l 20
    python main.py passphrase -w 6 --capitalize
    python main.py batch passwords.txt     # audit a list, passwords are never echoed
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from typing import List, Optional

from . import __version__, analyzer, breach, generator

LABEL_COLORS = {
    "Very Weak": "31;1", "Weak": "31", "Moderate": "33", "Strong": "32",
    "Very Strong": "32;1", "Compromised": "31;1", "Empty": "90",
}


class Style:
    """Colours/box characters that degrade gracefully on old terminals."""

    def __init__(self, stream=None):
        stream = stream or sys.stdout
        if os.name == "nt":
            os.system("")  # switches on ANSI escape handling in recent Windows consoles
        self.color = bool(getattr(stream, "isatty", lambda: False)()) and "NO_COLOR" not in os.environ
        try:
            "█░✔✘•─".encode(getattr(stream, "encoding", None) or "ascii")
            self.fancy = True
        except (UnicodeEncodeError, LookupError):
            self.fancy = False
        self.full, self.empty = ("█", "░") if self.fancy else ("#", "-")
        self.ok, self.bad = ("✔", "✘") if self.fancy else ("[x]", "[ ]")
        self.bullet = "•" if self.fancy else "-"
        self.rule = "─" if self.fancy else "-"

    def paint(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def bar(self, score: int, width: int = 24) -> str:
        filled = round(width * score / 100)
        return self.full * filled + self.empty * (width - filled)


def format_report(result: analyzer.Result, style: Style, show_tokens: bool = True) -> str:
    s = style
    lines = [s.paint("Password Strength Report", "1"), s.rule * 26]
    if result.length == 0:
        lines.append("No password entered.")
        return "\n".join(lines)

    colour = LABEL_COLORS.get(result.label, "0")
    lines += [
        f"Strength : {s.paint(result.label, colour)}  [{s.paint(s.bar(result.score), colour)}] {result.score}/100",
        f"Length   : {result.length} characters",
        f"Charsets : {', '.join(result.charsets) or 'none'} (pool of {result.charset_size})",
        f"Entropy  : {result.naive_bits:.1f} bits naive -> {result.effective_bits:.1f} bits after pattern analysis",
    ]
    if result.breach_count is not None:
        if result.breach_count:
            lines.append("Breaches : " + s.paint(f"found {result.breach_count:,} times in known leaks!", "31;1"))
        else:
            lines.append("Breaches : " + s.paint("not found in known leaks", "32"))

    lines += ["", "Estimated time to crack (average case):"]
    lines += [f"  {c['description']:<56}{c['display']}" for c in result.crack_times]

    lines += ["", "Checks:"]
    for key, passed in result.checks.items():
        mark = s.paint(s.ok, "32") if passed else s.paint(s.bad, "31")
        lines.append(f"  {mark} {analyzer.CHECK_LABELS[key]}")

    if result.findings:
        lines += ["", "Predictable patterns found:"]
        for f in result.findings:
            extra = f"  ({f['token']})" if show_tokens and f["token"] else ""
            lines.append(f"  {s.bullet} {f['detail']}{extra}")

    lines += ["", "Suggestions:"] + [f"  {s.bullet} {tip}" for tip in result.suggestions]
    return "\n".join(lines)


def _read_password(prompt: str = "Enter password (hidden): ") -> str:
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    return sys.stdin.readline().rstrip("\r\n")


# --------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    if args.password is not None:
        password = args.password
        if not args.json:
            print("Tip: passwords typed on the command line can end up in your shell history. "
                  "Omit the argument to get a hidden prompt.", file=sys.stderr)
    else:
        password = _read_password()

    count: Optional[int] = None
    if args.online:
        count = breach.check_pwned(password)
        if count is None:
            print("Note: breach check unavailable (could not reach the service).", file=sys.stderr)

    result = analyzer.analyze(password, breach_count=count)
    if args.json:
        print(json.dumps(result.to_dict(include_tokens=False), indent=2, ensure_ascii=False))
    else:
        print(format_report(result, Style()))
    return 1 if result.score < args.min_score else 0


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        for _ in range(args.count):
            pw = generator.generate_password(
                args.length, lower=not args.no_lower, upper=not args.no_upper,
                digits=not args.no_digits, symbols=not args.no_symbols,
                avoid_ambiguous=args.avoid_ambiguous)
            result = analyzer.analyze(pw)
            print(f"{pw}   [{result.label}, {result.effective_bits:.0f} bits]")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


def cmd_passphrase(args: argparse.Namespace) -> int:
    try:
        for _ in range(args.count):
            phrase = generator.generate_passphrase(
                args.words, args.separator, args.capitalize, args.add_number)
            bits = generator.passphrase_entropy_bits(args.words, args.add_number)
            print(f"{phrase}   [{bits:.0f} bits of true entropy]")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    try:
        with open(args.file, encoding="utf-8") as handle:
            passwords = [line.rstrip("\r\n") for line in handle if line.strip()]
    except OSError as exc:
        print(f"Error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    results = [analyzer.analyze(pw) for pw in passwords]
    if args.json:
        rows = [{"line": i, **r.to_dict(include_tokens=False)} for i, r in enumerate(results, 1)]
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        style = Style()
        print(f"{'#':>4}  {'Length':>6}  {'Score':>5}  {'Entropy':>8}  Strength")
        for i, r in enumerate(results, 1):
            label = style.paint(r.label, LABEL_COLORS.get(r.label, "0"))
            print(f"{i:>4}  {r.length:>6}  {r.score:>5}  {r.effective_bits:>6.1f} b  {label}")
        weak = sum(1 for r in results if r.score < args.min_score)
        print(f"\n{len(results)} passwords checked, {weak} below the minimum score of {args.min_score}.")
        print("(Passwords are never printed. Row numbers match the lines in your file.)")
    return 1 if any(r.score < args.min_score for r in results) else 0


def cmd_gui(_: argparse.Namespace) -> int:
    try:
        from .gui import launch
        launch()
    except Exception as exc:  # tkinter missing or no display available
        print(f"Cannot start the GUI ({exc}). Use the command-line mode instead: python main.py check",
              file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="password-strength-checker",
        description="Pattern-aware password strength checker, generator and auditor.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("check", help="analyse one password (default command)")
    p.add_argument("password", nargs="?", help="omit to be prompted with hidden input")
    p.add_argument("--online", action="store_true",
                   help="also query Have I Been Pwned (sends only a 5-character hash prefix)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--min-score", type=int, default=0, metavar="N",
                   help="exit with status 1 if the score is below N (useful in scripts)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("generate", help="generate secure random passwords")
    p.add_argument("-l", "--length", type=int, default=16)
    p.add_argument("-n", "--count", type=int, default=1)
    p.add_argument("--no-lower", action="store_true")
    p.add_argument("--no-upper", action="store_true")
    p.add_argument("--no-digits", action="store_true")
    p.add_argument("--no-symbols", action="store_true")
    p.add_argument("--avoid-ambiguous", action="store_true", help="skip look-alikes such as l, 1, I, O, 0")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("passphrase", help="generate random word passphrases")
    p.add_argument("-w", "--words", type=int, default=6)
    p.add_argument("-n", "--count", type=int, default=1)
    p.add_argument("-s", "--separator", default="-")
    p.add_argument("--capitalize", action="store_true")
    p.add_argument("--add-number", action="store_true")
    p.set_defaults(func=cmd_passphrase)

    p = sub.add_parser("batch", help="audit a file with one password per line")
    p.add_argument("file")
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-score", type=int, default=50, metavar="N")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("gui", help="open the desktop window")
    p.set_defaults(func=cmd_gui)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["check"]
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().print_help()
        return 2
    return args.func(args)
