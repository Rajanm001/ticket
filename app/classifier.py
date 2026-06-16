from __future__ import annotations

from collections import Counter

from app.constants import CATEGORIES


# Weighted keyword lexicon per category. Multi-word phrases are scored higher
# because they are more discriminative than single tokens.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Billing": ["invoice", "billed", "billing", "charge", "charged", "overcharged", "payment"],
    "Refund": ["refund", "money back", "reimburse", "chargeback", "cancelled subscription"],
    "Password Reset": ["reset password", "forgot password", "password reset", "reset link", "otp"],
    "Account Access": ["locked", "can't log in", "cannot log in", "account access", "login", "sign in"],
    "Subscription": ["subscription", "plan", "upgrade", "downgrade", "renewal", "renew"],
    "API Keys": ["api key", "api keys", "token", "secret key", "key rotation", "rotate key"],
    "Bug Report": ["bug", "crash", "crashes", "error", "exception", "broken", "not working"],
    "Feature Request": ["feature request", "please add", "would be great", "enhancement", "support for"],
    "Outage": ["down", "outage", "503", "unavailable", "not responding", "incident"],
    "Compliance": ["gdpr", "compliance", "audit", "data deletion", "privacy", "dpa"],
    "Data Export": ["export", "download data", "csv export", "data export", "backup"],
    "Other": [],
}


class TicketClassifier:
    """Deterministic keyword classifier.

    Returns the most likely category, a normalised confidence in [0, 1], and the
    two next-best alternative categories. Designed as a transparent, debuggable
    baseline that is cheap to run and easy to audit (no model weights to drift).
    """

    def predict(self, title: str, body: str) -> tuple[str, float, list[str]]:
        text = f"{title} {body}".lower()
        scores: Counter[str] = Counter()

        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    # Phrases (with a space) are more specific -> higher weight.
                    scores[category] += 2 if " " in kw else 1

        if not scores:
            return "Other", 0.30, ["Bug Report", "Account Access"]

        ranked = scores.most_common()
        top_category, top_score = ranked[0]
        total = sum(scores.values())
        confidence = round(min(0.99, top_score / total + 0.10), 3)

        alternatives = [name for name, _ in ranked[1:3]]
        for fallback in ("Other", "Bug Report", "Account Access"):
            if len(alternatives) >= 2:
                break
            if fallback != top_category and fallback not in alternatives:
                alternatives.append(fallback)

        return top_category, confidence, alternatives


