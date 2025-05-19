from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.llm_inference import (
        list_of_actions,
        list_of_categories,
        parse_intent,  # This function takes (text, actions_list, categories_list)
        add_note,      # This function takes (category, content)
        search_notes   # This function takes (category)
    )

# import all your code as is here...
# (just remove the command-line input loop)

app = FastAPI()

# CORS (so frontend can access it locally)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str

@app.post("/chat")
def chat(user_input: UserInput):
    intent = parse_intent(user_input.text, list_of_actions, list_of_categories)

    action = intent.get("action")
    category = intent.get("category")
    content = intent.get("content")
    response = intent.get("response")

    # Act on parsed intent
    result = None
    if action == "add_note":
        add_note(category, content)
    elif action == "search_notes":
        result = search_notes(category=category)

    return {
        "response": response,
        "result": result
    }
