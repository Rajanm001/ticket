from __future__ import annotations

import re


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)\d{3,4}[-.\s]?\d{3,4}")
TOKEN_RE = re.compile(r"\b(?:sk|rk|pk|token|api)[-_]?[a-zA-Z0-9]{8,}\b", re.IGNORECASE)


def sanitize_text(text: str) -> str:
    sanitized = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    sanitized = PHONE_RE.sub("[REDACTED_PHONE]", sanitized)
    sanitized = TOKEN_RE.sub("[REDACTED_TOKEN]", sanitized)
    return sanitized
