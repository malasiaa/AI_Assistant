from fastapi import APIRouter, Body
from app.services import nlp_parser, notes_service, calendar_service

router = APIRouter()

@router.post("/")
def handle_action(user_input: str = Body(...)):
    parsed = nlp_parser.parse_user_input(user_input)
    intent = parsed["intent"]

    if intent == "create_note":
        return notes_service.create_note(parsed["content"])
    elif intent == "set_reminder":
        return calendar_service.set_reminder(parsed["content"])
    else:
        return {"message": "Sorry, I didn’t understand that."}
