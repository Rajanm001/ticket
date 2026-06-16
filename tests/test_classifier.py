from app.classifier import TicketClassifier


def test_classifier_refund_category() -> None:
    model = TicketClassifier()
    category, confidence, alternatives = model.predict(
        "Refund not received",
        "I cancelled my subscription but money is not returned.",
    )
    assert category == "Refund"
    assert 0 <= confidence <= 1
    assert len(alternatives) == 2
