from app.escalation import EscalationPredictor


def test_escalation_high_risk_language() -> None:
    predictor = EscalationPredictor()
    will_escalate, probability, rationale = predictor.predict(
        "Production Down",
        "This is critical and urgent. We are facing a legal breach risk.",
    )
    assert will_escalate is True
    assert probability >= 0.5
    assert rationale
