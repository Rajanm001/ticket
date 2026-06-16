from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_index_serves_web_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>Ticket Triage" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_triage() -> None:
    payload = {
        "ticket_id": "CASE_TEST_1",
        "title": "Refund pending",
        "body": "Refund not received after cancellation.",
    }
    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "category" in body
    assert "draft_reply" in body
