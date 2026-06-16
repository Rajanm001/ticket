from __future__ import annotations

# Signal -> weight. Higher weight means a stronger pull toward escalation.
# Weights are calibrated so that genuine outages and compliance/legal exposure
# cross the 0.5 decision boundary on their own, while milder urgency words only
# nudge the score.
RISK_SIGNALS: dict[str, float] = {
    # Outage / availability
    "outage": 0.40,
    "down": 0.30,
    "503": 0.25,
    "not responding": 0.30,
    "critical": 0.25,
    # Legal / compliance exposure
    "legal": 0.40,
    "lawsuit": 0.45,
    "breach": 0.40,
    "gdpr": 0.30,
    "compliance": 0.30,
    "data deletion": 0.20,
    "dpa": 0.20,
    # Customer urgency / sentiment
    "urgent": 0.18,
    "asap": 0.15,
    "angry": 0.18,
    "frustrated": 0.15,
    "cancel my account": 0.25,
    # Repeated contact is a mild escalation signal
    "second time": 0.15,
    "again": 0.08,
}

# Account tier is a real escalation driver: a high-value (enterprise) customer
# with any risk signal is far more likely to be escalated than a free user with
# the same issue. The assignment itself cites "VIP customer + repeated prior
# failures" as an example rationale, so the model must be able to see tier.
TIER_WEIGHTS: dict[str, float] = {
    "enterprise": 0.20,
    "vip": 0.20,
    "pro": 0.05,
    "free": 0.0,
}


class EscalationPredictor:
    """Heuristic escalation scorer.

    Produces a probability plus a rationale that names the exact signals it
    found, so an agent can see *why* a ticket was flagged rather than trusting
    an opaque score. Text signals (outages, legal/compliance exposure, urgency,
    repeated contact) are combined with the customer tier when it is available.
    """

    def predict(
        self,
        title: str,
        body: str,
        customer_tier: str | None = None,
    ) -> tuple[bool, float, str]:
        text = f"{title} {body}".lower()

        matched = [signal for signal in RISK_SIGNALS if signal in text]
        score = 0.10 + sum(RISK_SIGNALS[s] for s in matched)

        reasons = list(matched)
        tier_key = (customer_tier or "").strip().lower()
        tier_weight = TIER_WEIGHTS.get(tier_key, 0.0)
        if tier_weight > 0:
            score += tier_weight
            if tier_key in {"enterprise", "vip"}:
                reasons.append(f"high-value ({tier_key}) account")

        probability = round(min(score, 0.98), 3)
        will_escalate = probability >= 0.5

        if reasons:
            rationale = "Escalation signals detected: " + ", ".join(sorted(reasons))
        else:
            rationale = "No strong escalation signals in the ticket text"

        return will_escalate, probability, rationale

