"""
Send a signed test webhook POST to the local Meta webhook endpoint.

This simulates Meta delivering a comment event (Instagram-style by default)
and includes the correct X-Hub-Signature-256 header.

Usage (PowerShell):
  cd raamp-backend
  python scripts/test_meta_webhook_post.py --url http://127.0.0.1:8000/api/meta/webhooks/comments

Requires:
  - FACEBOOK_APP_SECRET in environment (loads from .env if present)
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import requests
from dotenv import load_dotenv


def sign(app_secret: str, raw_body: bytes) -> str:
    digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def instagram_comment_payload(*, ig_business_id: str, comment_id: str, message: str) -> Dict[str, Any]:
    # Shape matches what our extractor expects: object + entry[0].changes[0].value
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return {
        "object": "instagram",
        "entry": [
            {
                "id": ig_business_id,
                "time": now_ts,
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "comment_id": comment_id,
                            "message": message,
                            "created_time": now_ts,
                            "from": {"id": "1234567890"},
                            "media_id": "17895695668004550",
                        },
                    }
                ],
            }
        ],
    }


def facebook_comment_payload(*, page_id: str, comment_id: str, message: str) -> Dict[str, Any]:
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return {
        "object": "page",
        "entry": [
            {
                "id": page_id,
                "time": now_ts,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "comment_id": comment_id,
                            "message": message,
                            "created_time": now_ts,
                            "from": {"id": "1234567890", "name": "Test User"},
                            "post_id": f"{page_id}_999999999999",
                            "verb": "add",
                            "published": 1,
                        },
                    }
                ],
            }
        ],
    }


def main() -> int:
    load_dotenv()

    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000/api/meta/webhooks/comments")
    p.add_argument("--platform", choices=["instagram", "facebook"], default="instagram")
    p.add_argument("--ig-business-id", default=os.getenv("TEST_IG_BUSINESS_ID", "17841400000000000"))
    p.add_argument("--page-id", default=os.getenv("TEST_PAGE_ID", "1067280970047460"))
    p.add_argument("--comment-id", default=f"test_comment_{int(datetime.now(timezone.utc).timestamp())}")
    p.add_argument("--message", default="Hey, what are your hours today?")
    args = p.parse_args()

    secret = (os.getenv("FACEBOOK_APP_SECRET") or "").strip()
    if not secret:
        print("ERROR: FACEBOOK_APP_SECRET is missing in environment/.env", file=sys.stderr)
        return 2

    if args.platform == "instagram":
        payload = instagram_comment_payload(
            ig_business_id=str(args.ig_business_id),
            comment_id=str(args.comment_id),
            message=str(args.message),
        )
    else:
        payload = facebook_comment_payload(
            page_id=str(args.page_id),
            comment_id=str(args.comment_id),
            message=str(args.message),
        )

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = sign(secret, raw)

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "User-Agent": "raamp-test-webhook/1.0",
    }

    print(f"POST {args.url}")
    print(f"X-Hub-Signature-256: {sig[:24]}... (len={len(sig)})")
    r = requests.post(args.url, data=raw, headers=headers, timeout=15)
    print("Status:", r.status_code)
    try:
        print("Body:", r.json())
    except Exception:
        print("Body:", r.text[:500])

    if r.status_code == 200:
        print("OK: webhook endpoint accepted the request.")
        return 0
    print("FAIL: webhook endpoint did not accept the request.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

