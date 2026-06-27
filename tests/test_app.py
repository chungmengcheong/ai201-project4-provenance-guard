# tests/test_app.py
# test_submit_scored is an integration test — requires a valid GROQ_API_KEY in .env

import json
import config
import pytest
from app import app, apply_label, get_log, limiter, log_event

CLEARLY_AI = (
    "Artificial intelligence represents a transformative paradigm shift in modern society. "
    "It is important to note that while the benefits of AI are numerous, it is equally "
    "essential to consider the ethical implications. Furthermore, stakeholders across "
    "various sectors must collaborate to ensure responsible deployment."
)
CLEARLY_HUMAN = (
    "ok so i finally tried that new ramen place downtown and honestly? "
    "underwhelming. the broth was fine but they put WAY too much sodium in it and "
    "i was thirsty for like three hours after. my friend got the spicy version and "
    "said it was better. probably won't go back unless someone drags me there"
)
BORDERLINE_FORMAL_HUMAN = (
    "The relationship between monetary policy and asset price inflation has been "
    "extensively studied in the literature. Central banks face a fundamental tension "
    "between their mandate for price stability and the unintended consequences of "
    "prolonged low interest rates on equity and real estate valuations."
)
BORDERLINE_EDITED_AI = (
    "I've been thinking a lot about remote work lately. There are genuine tradeoffs — "
    "flexibility and no commute on one side, isolation and blurred work-life boundaries "
    "on the other. Studies show productivity varies widely by individual and role type."
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

@pytest.mark.parametrize("content", [
    CLEARLY_AI,
    CLEARLY_HUMAN,
    BORDERLINE_FORMAL_HUMAN,
    BORDERLINE_EDITED_AI,
])
def test_submit_scored(client, content):
    response = client.post("/submit", json={
        "text": content,
        "creator_id": "test-user-1",
    })
    assert response.status_code == 200
    data = response.get_json()
    print(f"{content=}\n")
    print(data)
    print("--------------------------------\n")

    assert data["status"] == "scored"
    assert "content_id" in data
    assert data["message"] is None

    assert isinstance(data["confidence_score"], float)
    assert 0.0 <= data["confidence_score"] <= 1.0

    assert isinstance(data["user_friendly_description"], str)
    assert len(data["user_friendly_description"]) > 0

    signals = data["signals"]
    assert isinstance(signals["LLM"], float)
    assert isinstance(signals["LLM_reasoning"], str)
    assert isinstance(signals["stylometric"], float)


def test_submit_too_short(client):
    response = client.post("/submit", json={
        "text": "Too short.",
        "creator_id": "test-user-1",
    })
    assert response.status_code == 200
    data = response.get_json()
    print(data)

    assert data["status"] == "error"
    assert "too short" in data["message"].lower()


def test_submit_too_long(client):
    response = client.post("/submit", json={
        "text": "a" * 10001,
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
            "text": CLEARLY_AI,
            "creator_id": "test-user-1",
        })
        assert response.status_code == 200

    response = client.post("/submit", json={
        "text": CLEARLY_AI,
        "creator_id": "test-user-1",
    })
    assert response.status_code == 429


# --- /appeal ---

USER_REASON = (
    "I wrote this myself from personal experience. "
    "I am a non-native English speaker and my writing style may appear more formal than typical."
)

def test_appeal(client):
    response = client.post("/appeal", json={
        "content_id": "test-content-id",
        "creator_id": "test-user-1",
        "label": "uncertain",
        "confidence_score": 0.50,
        "signals": {"LLM": 0.75, "stylometric": 0.25},
        "creator_reasoning": USER_REASON,
    })
    assert response.status_code == 200
    data = response.get_json()
    print(data)
    assert data["message"] == "Appeal received. Content status updated to 'under review'."

    entry = get_log()[-1]
    assert entry["content_id"] == "test-content-id"
    assert entry["status"] == "under_review"
    assert entry["creator_reasoning"] == USER_REASON
    assert "timestamp" in entry


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


# --- get_log ---

def test_get_log_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "LOG_FILE", str(tmp_path / "nonexistent.jsonl"))
    assert get_log() == []


def test_get_log_returns_entries(tmp_path, monkeypatch):
    log_file = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))

    log_event({"content_id": "a", "status": "scored"})
    log_event({"content_id": "b", "status": "error"})

    entries = get_log()
    assert len(entries) == 2
    assert entries[0]["content_id"] == "a"
    assert entries[1]["content_id"] == "b"


def test_get_log_ignores_blank_lines(tmp_path, monkeypatch):
    log_file = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr(config, "LOG_FILE", str(log_file))

    log_file.write_text('{"content_id": "a"}\n\n{"content_id": "b"}\n')

    entries = get_log()
    assert len(entries) == 2


# --- apply_label ---

def test_apply_label_high_confidence_ai():
    result = apply_label(0.90)
    assert result["label"] == "high-confidence AI"
    result = apply_label(1.0)
    assert result["label"] == "high-confidence AI"


def test_apply_label_uncertain():
    result = apply_label(0.26)
    assert result["label"] == "uncertain"
    result = apply_label(0.60)
    assert result["label"] == "uncertain"
    result = apply_label(0.89)
    assert result["label"] == "uncertain"


def test_apply_label_high_confidence_human():
    result = apply_label(0.0)
    assert result["label"] == "high-confidence human"
    result = apply_label(0.25)
    assert result["label"] == "high-confidence human"


def test_apply_label_returns_description():
    for score in [0.05, 0.50, 0.95]:
        result = apply_label(score)
        assert "label" in result
        assert "user_friendly_description" in result
        assert len(result["user_friendly_description"]) > 0
