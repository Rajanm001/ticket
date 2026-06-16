"""Unit and integration tests for the triage pipeline.

Everything here runs fully offline: no network calls and no model downloads.
The retriever is built on TF-IDF over the local dataset, so each component is
deterministic and fast.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.classifier import TicketClassifier
from app.constants import CATEGORIES
from app.data_loader import load_faqs, load_tickets
from app.escalation import EscalationPredictor
from app.evaluator import Evaluator
from app.generator import ReplyGenerator
from app.pii_guard import sanitize_text
from app.rag import RetrievalItem, Retriever
from app.service import TriageService


class TestClassifier:
    def setup_method(self) -> None:
        self.model = TicketClassifier()

    def test_refund(self) -> None:
        category, confidence, alternatives = self.model.predict(
            "Refund not received",
            "I cancelled my subscription but the refund has not arrived.",
        )
        assert category == "Refund"
        assert 0.0 <= confidence <= 1.0
        assert len(alternatives) == 2
        assert all(a in CATEGORIES for a in alternatives)

    def test_password_reset(self) -> None:
        category, _, _ = self.model.predict(
            "Cannot log in",
            "I forgot my password and need a password reset link.",
        )
        assert category in {"Password Reset", "Account Access"}

    def test_outage(self) -> None:
        category, _, _ = self.model.predict(
            "Service is down",
            "The production endpoint is returning 503 errors during an outage.",
        )
        assert category == "Outage"

    def test_unknown_defaults_to_known_category(self) -> None:
        category, confidence, alternatives = self.model.predict(
            "Hello",
            "Just saying hi with no clear intent.",
        )
        assert category in CATEGORIES
        assert 0.0 <= confidence <= 1.0
        assert len(alternatives) == 2


class TestEscalation:
    def setup_method(self) -> None:
        self.model = EscalationPredictor()

    def test_high_risk(self) -> None:
        will_escalate, probability, rationale = self.model.predict(
            "Production down",
            "The system is down and returning 503 errors. This is urgent.",
        )
        assert will_escalate is True
        assert probability >= 0.5
        assert rationale

    def test_low_risk(self) -> None:
        will_escalate, probability, rationale = self.model.predict(
            "Feature question",
            "How do I rename a project in the dashboard?",
        )
        assert will_escalate is False
        assert 0.0 <= probability <= 1.0
        assert rationale

    def test_enterprise_tier_raises_probability(self) -> None:
        base = self.model.predict("Compliance", "We need a GDPR data deletion confirmation.")
        with_tier = self.model.predict(
            "Compliance",
            "We need a GDPR data deletion confirmation.",
            customer_tier="enterprise",
        )
        assert with_tier[1] > base[1]
        assert "enterprise" in with_tier[2]


class TestRetriever:
    def setup_method(self) -> None:
        self.retriever = Retriever()

    def test_returns_ranked_items(self) -> None:
        results = self.retriever.retrieve("refund not received", top_k=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        for item in results:
            assert isinstance(item, RetrievalItem)
            assert 0.0 <= item.score <= 1.0
            assert item.source_id

    def test_scores_descending(self) -> None:
        results = self.retriever.retrieve("password reset email link")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestGenerator:
    def setup_method(self) -> None:
        self.generator = ReplyGenerator()

    def test_grounded_reply_cites_source(self) -> None:
        sources = [
            {
                "source_id": "CASE_001",
                "source_type": "ticket",
                "score": 0.6,
                "snippet": "Refund was processed to the original payment method.",
            }
        ]
        reply = self.generator.generate(
            title="Refund request",
            body="I need a refund for my last order.",
            category="Refund",
            escalation_probability=0.1,
            sources=sources,
        )
        assert "CASE_001" in reply
        assert "Sources:" in reply

    def test_low_confidence_asks_for_clarification(self) -> None:
        reply = self.generator.generate(
            title="Help",
            body="Something is wrong.",
            category="Refund",
            escalation_probability=0.0,
            sources=[],
        )
        assert "<order_id>" in reply


class TestPiiGuard:
    def test_redacts_contact_details(self) -> None:
        cleaned = sanitize_text("Email me at jane@example.com or call 555-123-4567.")
        assert "jane@example.com" not in cleaned
        assert "555-123-4567" not in cleaned
        assert "[REDACTED" in cleaned


class TestData:
    def test_tickets_loaded(self) -> None:
        tickets = load_tickets()
        assert 150 <= len(tickets) <= 400
        sample = tickets[0]
        for field in ("ticket_id", "title", "body", "category", "resolution", "escalated"):
            assert field in sample

    def test_faqs_loaded(self) -> None:
        faqs = load_faqs()
        assert 10 <= len(faqs) <= 20


class TestEvaluator:
    def test_metrics_in_valid_ranges(self) -> None:
        metrics = Evaluator().evaluate(load_tickets())
        for key in (
            "routing_accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "groundedness",
        ):
            assert 0.0 <= metrics[key] <= 1.0
        assert metrics["sample_size"] > 0


class TestIntegration:
    def test_full_triage_flow(self) -> None:
        service = TriageService()
        result = asyncio.run(
            service.triage(
                ticket_id="TEST_1",
                title="Refund not received",
                body="I cancelled my plan but the refund has not arrived. This is urgent.",
            )
        )
        assert result["ticket_id"] == "TEST_1"
        assert result["category"] in CATEGORIES
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["will_escalate"], bool)
        assert 0.0 <= result["escalation_probability"] <= 1.0
        assert result["draft_reply"]
        assert isinstance(result["sources"], list)


class TestCli:
    def test_cli_outputs_valid_json(self, capsys) -> None:
        from app import cli

        exit_code = cli.main(
            ["--title", "Refund not received", "--body", "I cancelled but no refund arrived."]
        )
        assert exit_code == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["category"] in CATEGORIES
        assert "draft_reply" in data
        assert "will_escalate" in data


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
