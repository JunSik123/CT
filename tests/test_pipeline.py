from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_identify_endpoint_returns_top_match():
    payload = {"color": "white", "shape": "round", "imprint": "AP500"}
    response = client.post("/identify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["top_match"]["pill_id"] == "mfds-0001"
    assert data["confidence"] >= 0.5
    assert any(candidate["pill"]["pill_id"] == "mfds-0001" for candidate in data["candidates"])


def test_get_pill_details_returns_warnings():
    response = client.get("/pills/mfds-0002")
    assert response.status_code == 200
    data = response.json()
    assert data["pill"]["pill_id"] == "mfds-0002"
    assert any("주의" in warning["title"] for warning in data["warnings"])
