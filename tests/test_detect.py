# tests/test_detect.py
# Integration tests — require a valid GROQ_API_KEY in .env

import pytest
from detect import assess_signal_llm, assess_signal_stylometric, detect_signal

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


# --- LLM signal ---

def _assert_llm_shape(result):
    assert isinstance(result, dict)
    assert "confidence_score" in result
    assert "reasoning" in result
    assert "message" in result
    if result["message"] is None:
        assert isinstance(result["confidence_score"], float)
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert isinstance(result["reasoning"], str)


def test_llm_clearly_ai():
    result = assess_signal_llm(CLEARLY_AI)
    print("\n[LLM | clearly AI]\n", result)
    _assert_llm_shape(result)


def test_llm_clearly_human():
    result = assess_signal_llm(CLEARLY_HUMAN)
    print("\n[LLM | clearly human]\n", result)
    _assert_llm_shape(result)


def test_llm_borderline_formal_human():
    result = assess_signal_llm(BORDERLINE_FORMAL_HUMAN)
    print("\n[LLM | borderline: formal human]\n", result)
    _assert_llm_shape(result)


def test_llm_borderline_edited_ai():
    result = assess_signal_llm(BORDERLINE_EDITED_AI)
    print("\n[LLM | borderline: lightly edited AI]\n", result)
    _assert_llm_shape(result)


# --- Stylometric signal ---

def _assert_stylometric_shape(score):
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_stylometric_clearly_ai():
    score = assess_signal_stylometric(CLEARLY_AI)
    print(f"\n[stylometric | clearly AI] score={score:.3f}")
    _assert_stylometric_shape(score)


def test_stylometric_clearly_human():
    score = assess_signal_stylometric(CLEARLY_HUMAN)
    print(f"\n[stylometric | clearly human] score={score:.3f}")
    _assert_stylometric_shape(score)


def test_stylometric_borderline_formal_human():
    score = assess_signal_stylometric(BORDERLINE_FORMAL_HUMAN)
    print(f"\n[stylometric | borderline: formal human] score={score:.3f}")
    _assert_stylometric_shape(score)


def test_stylometric_borderline_edited_ai():
    score = assess_signal_stylometric(BORDERLINE_EDITED_AI)
    print(f"\n[stylometric | borderline: lightly edited AI] score={score:.3f}")
    _assert_stylometric_shape(score)


# --- detect_signal ---

def _assert_detection_shape(result):
    assert isinstance(result, dict)
    assert result["status"] in ("scored", "error")
    assert "confidence_score" in result
    assert "signals" in result
    assert "message" in result
    if result["status"] == "scored":
        assert isinstance(result["confidence_score"], float)
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert isinstance(result["signals"]["LLM"], float)
        assert isinstance(result["signals"]["stylometric"], float)
        assert isinstance(result["signals"]["LLM_reasoning"], str)


@pytest.mark.parametrize("content,label", [
    (CLEARLY_AI, "clearly AI"),
    (CLEARLY_HUMAN, "clearly human"),
    (BORDERLINE_FORMAL_HUMAN, "borderline: formal human"),
    (BORDERLINE_EDITED_AI, "borderline: lightly edited AI"),
])
def test_detect_signal(content, label):
    result = detect_signal(content)
    print(f"\n[detect_signal | {label}]\n", result)
    _assert_detection_shape(result)
