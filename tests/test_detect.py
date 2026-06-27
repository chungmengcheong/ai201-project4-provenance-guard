# tests/test_detect.py
# Integration tests — require a valid GROQ_API_KEY in .env

import pytest
from detect import assess_signal_llm

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


def _assert_shape(result):
    """Assert the response matches the assess_signal_llm() output contract."""
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
    print("\n[clearly AI]\n", result)
    _assert_shape(result)


def test_llm_clearly_human():
    result = assess_signal_llm(CLEARLY_HUMAN)
    print("\n[clearly human]\n", result)
    _assert_shape(result)


def test_llm_borderline_formal_human():
    result = assess_signal_llm(BORDERLINE_FORMAL_HUMAN)
    print("\n[borderline: formal human]\n", result)
    _assert_shape(result)


def test_llm_borderline_edited_ai():
    result = assess_signal_llm(BORDERLINE_EDITED_AI)
    print("\n[borderline: lightly edited AI]\n", result)
    _assert_shape(result)
