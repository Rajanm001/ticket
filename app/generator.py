from __future__ import annotations

from app.config import settings
from app.logging_utils import logger

# A few categories typically need a specific identifier from the customer.
PLACEHOLDER_BY_CATEGORY = {
    "Billing": "<invoice_id>",
    "Refund": "<order_id>",
    "API Keys": "<key_id>",
    "Data Export": "<account_id>",
    "Account Access": "<account_email>",
    "Password Reset": "<account_email>",
}


def _sources_block(sources: list[dict]) -> str:
    if not sources:
        return "Sources: none found"
    lines = [
        f"- {s['source_id']} ({s['source_type']}, relevance {s['score']:.2f})"
        for s in sources[:4]
    ]
    return "Sources:\n" + "\n".join(lines)


class ReplyGenerator:
    """Produce a grounded first-reply draft.

    Design choice: the default path is a deterministic, retrieval-grounded
    template. It only states next steps that are backed by retrieved snippets
    and always lists the source IDs it relied on, which keeps hallucinations
    near zero. An optional local LLM (Ollama) can rephrase the same grounded
    facts when USE_OLLAMA=true; if it is unavailable we fall back automatically.
    """

    def generate(
        self,
        title: str,
        body: str,
        category: str,
        escalation_probability: float,
        sources: list[dict],
    ) -> str:
        top_score = max((s.get("score", 0.0) for s in sources), default=0.0)
        low_confidence = top_score < settings.low_confidence_threshold

        draft = self._grounded_template(
            category=category,
            escalation_probability=escalation_probability,
            sources=sources,
            low_confidence=low_confidence,
        )

        if settings.use_ollama:
            llm_draft = self._try_ollama(title, body, category, sources, draft)
            if llm_draft:
                return llm_draft
        return draft

    def _grounded_template(
        self,
        category: str,
        escalation_probability: float,
        sources: list[dict],
        low_confidence: bool,
    ) -> str:
        # Low-confidence guardrail: ask for clarification instead of inventing steps.
        if low_confidence or not sources:
            placeholder = PLACEHOLDER_BY_CATEGORY.get(category, "<account_email>")
            return (
                "Hi, thanks for reaching out. I want to make sure I solve this correctly "
                "on the first try. I could not find a confident match in our resolved cases "
                f"for this request, so could you share a few details (for example {placeholder} "
                "and the date the issue started)? "
                "Once I have those I will follow our documented process and confirm the next steps. "
                "Sources: none with sufficient confidence"
            )

        primary = sources[0]
        placeholder = PLACEHOLDER_BY_CATEGORY.get(category)
        ask = (
            f" If you can share {placeholder}, I can action this immediately."
            if placeholder
            else ""
        )
        priority_line = (
            " I have flagged this for priority handling given the urgency signals on the account."
            if escalation_probability >= 0.5
            else ""
        )

        return (
            f"Hi, thanks for contacting support about your {category.lower()} request. "
            f"I have reviewed similar resolved cases and our policy guidance, and here is how we can proceed. "
            f"Based on case {primary['source_id']}, the typical resolution is: {primary['snippet']} "
            f"I will apply the same documented steps to your account and keep you updated until it is closed."
            f"{ask}{priority_line}\n\n"
            f"{_sources_block(sources)}"
        )

    def _try_ollama(
        self,
        title: str,
        body: str,
        category: str,
        sources: list[dict],
        grounded_draft: str,
    ) -> str | None:
        """Optional enhancement. Returns None on any failure (graceful fallback)."""
        try:
            import httpx

            context = _sources_block(sources)
            prompt = (
                "You are a customer support agent. Rewrite the grounded draft below into a "
                "warm, professional reply of 3-6 sentences. Do not add any facts, policies, or "
                "steps that are not present in the draft or the sources. Keep the Sources list.\n\n"
                f"Category: {category}\nTicket: {title} - {body}\n\n"
                f"Grounded draft:\n{grounded_draft}\n\nContext:\n{context}\n"
            )
            resp = httpx.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
                timeout=settings.ollama_timeout_s,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            return text or None
        except Exception as exc:  # noqa: BLE001 - any failure must fall back safely
            logger.warning(f"Ollama unavailable, using grounded template: {exc}")
            return None


