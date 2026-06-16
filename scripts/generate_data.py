from __future__ import annotations

import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.constants import CATEGORIES

random.seed(42)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# Several phrasings per category so the corpus is varied (better retrieval and a
# more honest classifier evaluation than a single templated sentence).
BODY_TEMPLATES: dict[str, list[str]] = {
    "Billing": [
        "I was billed incorrectly for last month and need an invoice correction.",
        "My invoice shows a charge I do not recognise. Please review the billing.",
        "I was overcharged on my latest payment and want it adjusted.",
    ],
    "Refund": [
        "I cancelled my subscription but the refund is still not received.",
        "Please process a refund for my last order, the product did not work.",
        "I want my money back for a duplicate charge on my card.",
    ],
    "Password Reset": [
        "The password reset link expired and I cannot log in.",
        "I forgot my password and the reset email never arrives.",
        "Password reset is failing with an invalid OTP message.",
    ],
    "Account Access": [
        "My account is locked after multiple failed login attempts.",
        "I cannot log in even with the correct credentials.",
        "I am unable to sign in and need help restoring account access.",
    ],
    "Subscription": [
        "Please downgrade my plan from enterprise to pro.",
        "I want to upgrade my subscription to the higher tier.",
        "My plan renewal went through but the new features are missing.",
    ],
    "API Keys": [
        "My API key stopped working after the latest rotation.",
        "I need to rotate my API keys and revoke the old secret key.",
        "The API token returns unauthorized after I regenerated it.",
    ],
    "Bug Report": [
        "The dashboard crashes when I upload a CSV file.",
        "I hit an error and the app is broken on the reports page.",
        "There is a bug causing an exception when I save settings.",
    ],
    "Feature Request": [
        "Please add bulk export support for reports.",
        "It would be great to have a dark mode feature.",
        "Feature request: support for scheduled email digests.",
    ],
    "Outage": [
        "Production endpoint is down and returning 503 errors. This is urgent.",
        "Your service outage is blocking our whole team, this is critical.",
        "The API is not responding and our production app is down.",
    ],
    "Compliance": [
        "Need GDPR data deletion confirmation for compliance reasons.",
        "We require a signed DPA and a privacy audit for compliance.",
        "Please confirm GDPR compliance and provide the data processing agreement.",
    ],
    "Data Export": [
        "How can I export all account data in CSV?",
        "I need a full data export and backup of my account.",
        "Please help me download my data export from settings.",
    ],
    "Other": [
        "I need help understanding your product options.",
        "I have a general question about how the platform works.",
        "Can you point me to documentation for getting started?",
    ],
}

RESOLUTIONS: dict[str, str] = {
    "Billing": "Reviewed the invoice, corrected the billing error, and adjusted the charge.",
    "Refund": "Validated the refund and processed it to the original payment method within 5 business days.",
    "Password Reset": "Issued a fresh secure reset link, verified OTP, and confirmed restored access.",
    "Account Access": "Verified identity and unlocked the account after the lockout window.",
    "Subscription": "Applied the plan change effective from the next billing cycle.",
    "API Keys": "Generated a replacement key, revoked the old key, and confirmed authentication works.",
    "Bug Report": "Reproduced the bug, deployed a hotfix, and enabled monitoring on the page.",
    "Feature Request": "Logged the feature request and shared it with the product team for review.",
    "Outage": "Mitigated the incident, restored service, and shared an RCA with affected customers.",
    "Compliance": "Processed the compliance request and updated the audit trail and DPA records.",
    "Data Export": "Generated the export package in CSV and shared it securely from account settings.",
    "Other": "Provided guided support and clear next-action steps for the customer.",
}

TIERS = ["free", "pro", "enterprise"]
PRODUCTS = ["web", "mobile", "api"]


def _is_escalated(category: str, body: str, tier: str, repeat: bool) -> int:
    """Escalation reflects real-world signals so the heuristic can be evaluated
    honestly: urgent outages, legal/compliance exposure, and repeated failures
    on high-value accounts are the drivers."""
    text = body.lower()
    risk = 0.0
    if category == "Outage" or "503" in text or "down" in text:
        risk += 0.5
    if category == "Compliance" or "gdpr" in text or "legal" in text:
        risk += 0.4
    if "urgent" in text or "critical" in text:
        risk += 0.2
    if tier == "enterprise":
        risk += 0.15
    if repeat:
        risk += 0.15
    return 1 if risk >= 0.5 else 0


def make_tickets(n: int = 300) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        category = CATEGORIES[(i - 1) % len(CATEGORIES)]
        body = random.choice(BODY_TEMPLATES[category])
        tier = random.choice(TIERS)
        repeat = random.random() > 0.8
        if repeat:
            body = body + " This is the second time I am reporting this."

        escalated = _is_escalated(category, body, tier, repeat)
        # A little label noise keeps precision/recall realistic rather than perfect.
        if random.random() > 0.95:
            escalated = 1 - escalated

        rows.append(
            {
                "ticket_id": f"CASE_{i:03d}",
                "title": f"{category}: {body.split('.')[0][:60]}",
                "body": body,
                "category": category,
                "customer_tier": tier,
                "product": random.choice(PRODUCTS),
                "resolution": RESOLUTIONS[category],
                "escalated": escalated,
            }
        )
    return rows


def make_faq(n: int = 15) -> list[dict]:
    faqs = [
        {"id": "FAQ_01", "title": "Refund Policy", "content": "Refunds are processed within 5 business days to the original payment method."},
        {"id": "FAQ_02", "title": "Billing Cycles", "content": "Billing renews automatically unless cancelled before the renewal date."},
        {"id": "FAQ_03", "title": "Password Reset", "content": "Use the password reset link and verify the OTP to restore account access."},
        {"id": "FAQ_04", "title": "Account Lockout", "content": "Accounts are temporarily locked after repeated failed logins and unlock after verification."},
        {"id": "FAQ_05", "title": "Plan Changes", "content": "Upgrades are immediate and downgrades apply on the next billing cycle."},
        {"id": "FAQ_06", "title": "API Key Rotation", "content": "Rotate API keys regularly, revoke old keys, and store secrets in a secure vault."},
        {"id": "FAQ_07", "title": "Incident Handling", "content": "Critical incidents and outages are handled by on-call support with status updates."},
        {"id": "FAQ_08", "title": "Feature Requests", "content": "Feature requests are reviewed quarterly by the product team."},
        {"id": "FAQ_09", "title": "GDPR Requests", "content": "GDPR deletion and export requests are completed within the required legal timelines."},
        {"id": "FAQ_10", "title": "Data Export", "content": "Data export is available in CSV and JSON from account settings."},
        {"id": "FAQ_11", "title": "SLA", "content": "Enterprise plans include a 99.9% uptime SLA and priority support."},
        {"id": "FAQ_12", "title": "Response Time", "content": "Support responds within 24 hours on business days."},
        {"id": "FAQ_13", "title": "Security", "content": "Never share API keys in support messages or public channels."},
        {"id": "FAQ_14", "title": "Escalation", "content": "Tickets with legal risk, compliance exposure, or outages are escalated immediately."},
        {"id": "FAQ_15", "title": "Verification", "content": "Ownership verification is mandatory for account-level actions."},
    ]
    return faqs[:n]


def main() -> None:
    tickets = make_tickets(300)
    faqs = make_faq(15)

    with (DATA_DIR / "tickets.json").open("w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=True, indent=2)

    with (DATA_DIR / "faq.json").open("w", encoding="utf-8") as f:
        json.dump(faqs, f, ensure_ascii=True, indent=2)

    escalated = sum(t["escalated"] for t in tickets)
    print(f"Generated {len(tickets)} tickets ({escalated} escalated) and {len(faqs)} FAQs in {DATA_DIR}")


if __name__ == "__main__":
    main()

