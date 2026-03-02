#!/usr/bin/env python3
"""Compatibility wrapper for environment generation script.

Canonical location: scripts/setup/generate_env.py
"""

from pathlib import Path
import runpy
import sys


def main() -> None:
    script_path = Path(__file__).resolve().parent / "scripts" / "setup" / "generate_env.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Expected script not found: {script_path}")

    # Preserve CLI behavior by executing target script as __main__.
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise
