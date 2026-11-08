#!/usr/bin/env python3
"""Password Strength Checker - entry point.

    python main.py                 open the desktop window (falls back to the terminal)
    python main.py check           check a password in the terminal (hidden input)
    python main.py generate        generate a secure password
    python main.py passphrase      generate a passphrase
    python main.py batch FILE      audit a file of passwords
    python main.py -h              all options
"""
import sys

from psc.cli import main as cli_main


def run() -> int:
    if len(sys.argv) > 1:
        return cli_main()
    try:
        from psc.gui import launch
        launch()
        return 0
    except Exception as exc:  # tkinter not installed, or no display (SSH, containers)
        print(f"GUI unavailable ({exc}); switching to terminal mode.\n", file=sys.stderr)
        return cli_main(["check"])


if __name__ == "__main__":
    raise SystemExit(run())
