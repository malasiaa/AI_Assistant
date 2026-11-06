import pytest

from app.core.json_utils import extract_json


def test_plain_json():
    assert extract_json('{"action": "add_note", "category": "To do"}') == {
        "action": "add_note",
        "category": "To do",
    }


def test_json_in_markdown_fence():
    text = 'Sure!\n```json\n{"action": "None", "response": "Hello"}\n```\nAnything else?'
    assert extract_json(text)["response"] == "Hello"


def test_json_surrounded_by_prose():
    text = 'Here you go: {"action": "search_notes", "category": "Trips"} - enjoy.'
    assert extract_json(text)["category"] == "Trips"


def test_nested_object():
    text = '{"a": {"b": 1}, "c": 2}'
    assert extract_json(text) == {"a": {"b": 1}, "c": 2}


def test_skips_broken_brace_before_real_json():
    text = 'Note {not json} then {"ok": true}'
    assert extract_json(text) == {"ok": True}


@pytest.mark.parametrize("bad", ["", "   ", "no json here", "[1, 2, 3]", None])
def test_invalid_raises(bad):
    with pytest.raises(ValueError):
        extract_json(bad)
