from __future__ import annotations

import time
from typing import Any

from app.classifier import TicketClassifier
from app.data_loader import load_tickets
from app.escalation import EscalationPredictor
from app.evaluator import Evaluator
from app.generator import ReplyGenerator
from app.logging_utils import logger
from app.pii_guard import sanitize_text
from app.rag import Retriever
from app.repository import TriageRepository


class TriageService:
    def __init__(self) -> None:
        self.classifier = TicketClassifier()
        self.escalation = EscalationPredictor()
        self.retriever = Retriever()
        self.generator = ReplyGenerator()
        self.evaluator = Evaluator()
        self.repository = TriageRepository()

    async def triage(
        self,
        ticket_id: str,
        title: str,
        body: str,
        product: str | None = None,
        customer_tier: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()

        clean_title = sanitize_text(title)
        clean_body = sanitize_text(body)
        category, confidence, alternatives = self.classifier.predict(clean_title, clean_body)
        will_escalate, esc_probability, rationale = self.escalation.predict(
            clean_title, clean_body, customer_tier=customer_tier
        )

        query = f"{clean_title}\n{clean_body}"
        retrieved = self.retriever.retrieve(query=query, top_k=5)
        source_payload = [
            {
                "source_id": item.source_id,
                "source_type": item.source_type,
                "score": item.score,
                "snippet": item.snippet,
            }
            for item in retrieved
        ]

        draft_reply = self.generator.generate(
            title=clean_title,
            body=clean_body,
            category=category,
            escalation_probability=esc_probability,
            sources=source_payload,
        )

        self.repository.save_run(
            ticket_id=ticket_id,
            category=category,
            confidence=confidence,
            escalation_probability=esc_probability,
        )

        latency_ms = round((time.perf_counter() - started) * 1000, 2)

        result = {
            "ticket_id": ticket_id,
            "category": category,
            "confidence": confidence,
            "top_alternatives": alternatives,
            "will_escalate": will_escalate,
            "escalation_probability": esc_probability,
            "escalation_rationale": rationale,
            "draft_reply": draft_reply,
            "sources": source_payload,
            "latency_ms": latency_ms,
        }

        # Observability: structured log of the PII-redacted input and the key
        # outputs with their confidences. The full draft is intentionally not
        # logged to keep log volume and any residual PII risk low.
        logger.bind(
            ticket_id=ticket_id,
            product=product,
            customer_tier=customer_tier,
            title=clean_title,
            category=category,
            confidence=confidence,
            will_escalate=will_escalate,
            escalation_probability=esc_probability,
            source_ids=[s["source_id"] for s in source_payload],
            latency_ms=latency_ms,
        ).info("triage")

        return result

    async def evaluate(self) -> dict[str, float]:
        tickets = load_tickets()
        return self.evaluator.evaluate(tickets)
