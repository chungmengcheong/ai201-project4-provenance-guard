# tests/test_app.py
# test_submit_scored is an integration test — requires a valid GROQ_API_KEY in .env

import json

import config
import pytest
from app import app, limiter, log_event

SAMPLE_CONTENT = (
    "Artificial intelligence represents a transformative paradigm shift in modern society. "
    "It is important to note that while the benefits of AI are numerous, it is equally "
    "essential to consider the ethical implications. Furthermore, stakeholders across "
    "various sectors must collaborate to ensure responsible deployment."
)

@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- /submit ---

def test_submit_scored(client):
    response = client.post("/submit", json={
        "content": SAMPLE_CONTENT,
        "creator_id": "test-user-1",
    })
    assert response.status_code == 200
    data = response.get_json()
    print(data)

    assert data["status"] == "scored"
    assert "content_id" in data
    assert data["message"] is None

    assert isinstance(data["confidence_score"], float)
    assert 0.0 <= data["confidence_score"] <= 1.0

    signals = data["signals"]
    assert isinstance(signals["LLM"], float)
    assert isinstance(signals["LLM_reasoning"], str)
    assert len(signals["LLM_reasoning"]) > 0


def test_submit_too_short(client):
    response = client.post("/submit", json={
        "content": "Too short.",
        "creator_id": "test-user-1",
    })
    assert response.status_code == 200
    data = response.get_json()
    print(data)

    assert data["status"] == "error"
    assert "too short" in data["message"].lower()


def test_submit_too_long(client):
    response = client.post("/submit", json={
        "content": "a" * 10001,
        "creator_id": "test-user-1",
    })
    assert response.status_code == 200
    data = response.get_json()
    print(data)

    assert data["status"] == "error"
    assert "too long" in data["message"].lower()


def test_rate_limiter(client):
    for _ in range(config.MAX_SUBMISSIONS_IN_TIME_WINDOW):
        response = client.post("/submit", json={
            "content": SAMPLE_CONTENT,
            "creator_id": "test-user-1",
        })
        assert response.status_code == 200

    response = client.post("/submit", json={
        "content": SAMPLE_CONTENT,
        "creator_id": "test-user-1",
    })
    assert response.status_code == 429


# --- log_event ---

def test_log_event_writes_entry(tmp_path, monkeypatch):
    log_file = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))

    entry = {
        "content_id": "test-123",
        "creator_id": "user-1",
        "status": "scored",
        "confidence_score": 0.75,
    }
    log_event(entry)

    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 1
    logged = json.loads(lines[0])
    assert logged["content_id"] == "test-123"
    assert logged["status"] == "scored"
    assert "timestamp" in logged


def test_log_event_appends(tmp_path, monkeypatch):
    log_file = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))

    log_event({"content_id": "a", "status": "scored"})
    log_event({"content_id": "b", "status": "error"})

    lines = log_file.read_text().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["content_id"] == "a"
    assert json.loads(lines[1])["content_id"] == "b"
