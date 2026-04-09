"""
Diagnostics: LLM availability (OpenAI)
-------------------------------------
Checks whether the LLM client is configured and can return valid JSON.

Why this matters:
- Content suggestions and some explanations rely on LLM output.
- We fail closed now (503) rather than returning templated suggestions; this test tells you if LLM is actually reachable.

Notes:
- This script makes a *minimal* paid API call if OPENAI_API_KEY is set.
- It prints only a tiny sanitized sample response.
"""

from __future__ import annotations

import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv

from _diag_utils import DiagResult, safe_main


async def _run_async() -> DiagResult:
    load_dotenv()

    details: Dict[str, Any] = {"timestamp_utc": datetime.utcnow().isoformat() + "Z"}

    try:
        from infrastructure.clients.llm_client import LLMClient

        client = LLMClient()
        if not getattr(client, "client", None):
            return DiagResult(
                name="LLM",
                status="FAIL",
                reason="OPENAI_API_KEY not configured",
                details=details,
            )

        system = "Return valid JSON with keys: ok, echo."
        user = "Respond with {\"ok\": true, \"echo\": \"ping\"}."
        res = await client.generate_structured_json(system, user, max_retries=0)

        if not isinstance(res, dict):
            return DiagResult(name="LLM", status="FAIL", reason="Non-JSON response", details=details)

        if res.get("ok") is not True:
            return DiagResult(name="LLM", status="FAIL", reason="Unexpected JSON shape/content", details={**details, "sample": res})

        details["sample"] = {"ok": res.get("ok"), "echo": res.get("echo")}
        details["model"] = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o")

        return DiagResult(name="LLM", status="PASS", reason="LLM returned valid structured JSON", details=details)

    except Exception as e:
        # Do not expose internal/provider errors unless debugging.
        if os.getenv("DIAG_DEBUG", "").lower() in ("1", "true", "yes"):
            details["error"] = str(e)
        return DiagResult(name="LLM", status="FAIL", reason="LLM call failed", details=details)


def run() -> DiagResult:
    return asyncio.run(_run_async())


if __name__ == "__main__":
    raise SystemExit(safe_main(run, "LLM"))

