import json
from groq import Groq
import config

_client = Groq(api_key=config.GROQ_API_KEY)

SCORE_MAP = {
    "clearly_ai":    0.95,
    "likely_ai":     0.75,
    "uncertain":     0.50,
    "likely_human":  0.25,
    "clearly_human": 0.05,
}

_PROMPT_TEMPLATE = """\
Classify the following content on the likelihood that it is written by AI.

Respond in JSON only — no other text:
{{
    "score_map": one of ["clearly_ai", "likely_ai", "uncertain", "likely_human", "clearly_human"],
    "reasoning": "1 to 2 lines of text explaining your assessment"
}}

Writing that shows several of the following stylistic tendencies is more likely to be AI:
- Contrastive Rhetorical Framing, e.g. "This isn't about revenue. It's about survival."
- Asking and Answering Rhetorical Questions, e.g., "What changed? The math did."
- Excessive use of dashes, bullets, and headings
- Triplet Framing, e.g., "Fast, cheap, and out of control."
- The Inspirational Pivot, e.g., "This isn't just about AI. It's about humanity."
- Universal Authority Without Source, e.g., "Studies show storytelling is more memorable."
- Quotes with incorrect attribution, e.g., "'AI is the new electricity,' said Musk."

## Content
{content}"""


def assess_signal_llm(content: str) -> dict:
    """Call the LLM to assess whether content is AI-generated.

    Returns:
        {
            "confidence_score": float (0.0–1.0),
            "reasoning": str,
            "message": str | None
        }
    """
    prompt = _PROMPT_TEMPLATE.format(content=content)

    try:
        response = _client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        if not raw:
            raise ValueError("LLM returned empty content")
        parsed = json.loads(raw)
    except Exception as e:
        return {
            "confidence_score": None,
            "reasoning": None,
            "message": f"LLM call failed: {e}",
        }

    score_map_key = parsed.get("score_map")
    reasoning = parsed.get("reasoning")

    if score_map_key not in SCORE_MAP:
        return {
            "confidence_score": None,
            "reasoning": reasoning,
            "message": f"Unexpected score_map value: '{score_map_key}'",
        }

    return {
        "confidence_score": SCORE_MAP[score_map_key],
        "reasoning": reasoning,
        "message": None,
    }
