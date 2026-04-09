"""
Run all Trend diagnostics
------------------------
Runs each diagnostic in sequence and prints a final summary table.

Each diagnostic is standalone and can be run individually.
This runner aggregates PASS/FAIL/WARN into a final "X/Y returning real data" line.
"""

from __future__ import annotations

from typing import List

# Ensure repo root is on sys.path before importing local diagnostics.
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from _diag_utils import DiagResult


def _icon(status: str) -> str:
    return {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[INFO]")


def main() -> int:
    results: List[DiagResult] = []

    # Import lazily so a broken file doesn't crash the whole runner.
    from test_pytrends import run as run_pytrends
    from test_google_news_rss import run as run_rss
    from test_serp_api import run as run_serp
    from test_trend_signal_db import run as run_db
    from test_llm_suggestions import run as run_llm

    checks = [
        run_pytrends,
        run_rss,
        run_serp,
        run_db,
        run_llm,
    ]

    for fn in checks:
        try:
            r = fn()
        except Exception as e:
            r = DiagResult(name=getattr(fn, "__name__", "unknown"), status="FAIL", reason=f"Diagnostic crashed: {type(e).__name__}")
        results.append(r)

    print("\n=== Trend Diagnostics Summary ===")
    for r in results:
        print(f"{_icon(r.status)} {r.line()}")

    # "Real data" sources are those that PASS.
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    print()
    print(f"{passed}/{total} sources are returning real data")

    # Exit code 0 only if all PASS.
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

