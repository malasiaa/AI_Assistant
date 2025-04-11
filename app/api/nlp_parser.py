def parse_user_input(text: str) -> dict:
    # Example result: {"intent": "create_note", "entities": {...}}
    # This is where you'll call Mistral or similar
    return {
        "intent": "create_note" if "note" in text else "set_reminder",
        "content": text
    }
