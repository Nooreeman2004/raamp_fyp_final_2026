from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class DiagResult:
    name: str
    status: str  # PASS|FAIL|WARN
    reason: str
    details: Optional[Dict[str, Any]] = None

    def line(self) -> str:
        base = f"{self.name:<18} {self.status:<4} - {self.reason}"
        return base


def _ensure_backend_imports() -> None:
    """
    Allows running `python tests/diagnostics/test_x.py` from repo root or raamp-backend.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    backend_root = os.path.abspath(os.path.join(here, "..", ".."))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)


def safe_main(run_fn, name: str) -> int:
    """
    Wrapper to guarantee diagnostics never crash the runner.
    `run_fn` should return a DiagResult.
    """
    _ensure_backend_imports()
    try:
        r: DiagResult = run_fn()
        icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(r.status, "[INFO]")
        print(f"{icon} {r.line()}")
        if r.details:
            for k, v in r.details.items():
                print(f"   - {k}: {v}")
        return 0 if r.status == "PASS" else 1
    except Exception as e:
        # Never expose full trace by default; still keep it available for devs.
        print(f"❌ {name:<18} FAIL - Unhandled exception (diagnostic bug): {type(e).__name__}")
        print("   - reason: This diagnostic script crashed; fix the script (not the data source).")
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            traceback.print_exc()
        return 2

