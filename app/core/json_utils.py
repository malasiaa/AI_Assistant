"""Helpers for turning LLM text output into JSON.

LLMs frequently wrap JSON in prose or markdown fences, which makes a plain
``json.loads`` fail. ``extract_json`` is tolerant of that.
"""
import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    """Return the first JSON object found in ``text``.

    Handles bare JSON, ```json fenced``` blocks, and JSON surrounded by
    other text. Raises ``ValueError`` if no JSON object can be decoded.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty text")

    candidates = [text]
    candidates += _FENCE.findall(text)

    decoder = json.JSONDecoder()
    for candidate in candidates:
        start = candidate.find("{")
        while start != -1:
            try:
                obj, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                start = candidate.find("{", start + 1)
                continue
            if isinstance(obj, dict):
                return obj
            start = candidate.find("{", start + 1)

    raise ValueError("no JSON object found")
