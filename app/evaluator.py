from __future__ import annotations

import re
from typing import Any

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from app.classifier import TicketClassifier
from app.config import settings
from app.escalation import EscalationPredictor
from app.generator import ReplyGenerator
from app.rag import Retriever

_WORD_RE = re.compile(r"[a-z0-9]+")
# Effort model constants for the TTFR proxy (defensible laptop-agent estimates).
_READ_WPM = 200.0   # words an agent reads per minute
_WRITE_WPM = 25.0   # words an agent writes per minute
_TYPICAL_REPLY_WORDS = 60.0
_EDIT_FRACTION = 0.25  # fraction of a reply an agent re-types when editing a draft


def _content_words(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


class Evaluator:
    """Computes the KPIs requested in the assignment on the loaded dataset."""

    def __init__(self) -> None:
        self.classifier = TicketClassifier()
        self.escalation = EscalationPredictor()
        self.retriever = Retriever()
        self.generator = ReplyGenerator()

    def evaluate(self, tickets: list[dict[str, Any]], groundedness_sample: int = 60) -> dict[str, float]:
        if not tickets:
            return {
                "routing_accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "roc_auc": 0.0,
                "groundedness": 0.0,
                "ttfr_minutes_saved": 0.0,
                "cost_per_100_tickets_usd": 0.0,
                "sample_size": 0,
            }

        y_true_cat: list[str] = []
        y_pred_cat: list[str] = []
        y_true_esc: list[int] = []
        y_pred_esc: list[int] = []
        y_prob_esc: list[float] = []

        for ticket in tickets:
            title = str(ticket.get("title", ""))
            body = str(ticket.get("body", ""))
            tier = ticket.get("customer_tier")
            pred_cat, _, _ = self.classifier.predict(title, body)
            _, prob, _ = self.escalation.predict(title, body, customer_tier=tier)

            y_true_cat.append(str(ticket.get("category", "Other")))
            y_pred_cat.append(pred_cat)
            y_true_esc.append(int(ticket.get("escalated", 0)))
            y_pred_esc.append(1 if prob >= 0.5 else 0)
            y_prob_esc.append(prob)

        routing_accuracy = float(accuracy_score(y_true_cat, y_pred_cat))
        precision = float(precision_score(y_true_esc, y_pred_esc, zero_division=0))
        recall = float(recall_score(y_true_esc, y_pred_esc, zero_division=0))
        f1 = float(f1_score(y_true_esc, y_pred_esc, zero_division=0))
        try:
            roc_auc = float(roc_auc_score(y_true_esc, y_prob_esc))
        except ValueError:
            roc_auc = 0.0

        groundedness = self._groundedness(tickets[:groundedness_sample])
        ttfr = self._ttfr_minutes_saved(tickets)
        cost = self._cost_per_100_tickets(tickets[:groundedness_sample])

        return {
            "routing_accuracy": round(routing_accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "groundedness": round(groundedness, 4),
            "ttfr_minutes_saved": round(ttfr, 3),
            "cost_per_100_tickets_usd": round(cost, 4),
            "sample_size": len(tickets),
        }

    def _groundedness(self, tickets: list[dict[str, Any]]) -> float:
        """Fraction of a draft's claim words that are supported by retrieved sources.

        A clarification ask (made when retrieval confidence is low) makes no
        factual claims and therefore counts as fully grounded.
        """
        if not tickets:
            return 0.0

        scores: list[float] = []
        for ticket in tickets:
            title = str(ticket.get("title", ""))
            body = str(ticket.get("body", ""))
            category, _, _ = self.classifier.predict(title, body)
            _, prob, _ = self.escalation.predict(title, body, customer_tier=ticket.get("customer_tier"))
            sources = [s.__dict__ for s in self.retriever.retrieve(f"{title} {body}")]
            draft = self.generator.generate(title, body, category, prob, sources)

            claim, _, _ = draft.partition("Sources:")
            top_score = max((s.get("score", 0.0) for s in sources), default=0.0)
            if not sources or top_score < settings.low_confidence_threshold:
                scores.append(1.0)  # asked for clarification, no unsupported claims
                continue

            support_words = set()
            for s in sources:
                support_words |= _content_words(str(s.get("snippet", "")))
            claim_words = _content_words(claim) - _BOILERPLATE_WORDS
            if not claim_words:
                scores.append(1.0)
                continue
            overlap = len(claim_words & support_words) / len(claim_words)
            scores.append(overlap)

        return sum(scores) / len(scores)

    def _ttfr_minutes_saved(self, tickets: list[dict[str, Any]]) -> float:
        total = 0.0
        for ticket in tickets:
            read_words = len(str(ticket.get("body", "")).split())
            read_time = read_words / _READ_WPM
            manual = read_time + _TYPICAL_REPLY_WORDS / _WRITE_WPM
            assisted = read_time + (_TYPICAL_REPLY_WORDS * _EDIT_FRACTION) / _WRITE_WPM
            total += manual - assisted
        return total / len(tickets) if tickets else 0.0

    def _cost_per_100_tickets(self, tickets: list[dict[str, Any]]) -> float:
        """Estimated USD per 100 tickets.

        The default deterministic path makes no paid API calls, so cost is 0.
        If a priced model is configured via COST_PER_1K_* env vars, we estimate
        from approximate token counts (about words / 0.75).
        """
        if settings.cost_per_1k_input_tokens == 0 and settings.cost_per_1k_output_tokens == 0:
            return 0.0

        per_ticket = 0.0
        for ticket in tickets:
            in_tokens = len(str(ticket.get("body", "")).split()) / 0.75 + 120  # prompt overhead
            out_tokens = _TYPICAL_REPLY_WORDS / 0.75
            per_ticket += (
                in_tokens / 1000 * settings.cost_per_1k_input_tokens
                + out_tokens / 1000 * settings.cost_per_1k_output_tokens
            )
        avg = per_ticket / len(tickets) if tickets else 0.0
        return avg * 100


# Words from our reply scaffolding that should not count as factual claims.
_BOILERPLATE_WORDS = _content_words(
    "hi thanks for contacting support about your request i have reviewed similar resolved "
    "cases and our policy guidance here is how we can proceed based on case the typical "
    "resolution is i will apply the same documented steps to your account and keep you "
    "updated until it is closed if you can share immediately flagged for priority handling "
    "given the urgency signals on the reaching out want to make sure solve this correctly "
    "first try could not find confident match could share few details for example date "
    "started once have those follow process confirm next none with sufficient confidence"
)

