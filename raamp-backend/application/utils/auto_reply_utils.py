from __future__ import annotations

import hashlib
import re
import unicodedata


def normalize_reply_text(text: str) -> str:
    """
    Normalization spec (plan):
    - Unicode normalize to NFKC
    - Trim
    - Collapse whitespace runs to a single space
    - Lowercase
    """
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    return s


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

