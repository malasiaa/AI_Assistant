import tempfile, os, time, logging
from logging.handlers import RotatingFileHandler
import shutil
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper


from app.core.llm_inference import (
        list_of_actions,
        list_of_categories,
        parse_intent,  # This function takes (text, actions_list, categories_list)
        add_note,      # This function takes (category, content)
        search_notes   # This function takes (category)
    )

#%% Logger
# python logger
logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)

# Rotate after 5 MB, keep 3 backups
handler = RotatingFileHandler(r"app\api\logs\api.log", maxBytes=5*1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

logger.addHandler(handler)

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
    
#%%% logging middleware    
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    
    # Read request body (optional—only if small!)
    body = await request.body()
    body_text = body.decode('utf-8') if body else ""

    response = await call_next(request)
    duration = (time.time() - start) * 1000

    # Grab intent if set
    intent = getattr(request.state, "intent", None)
    intent_text = repr(intent) if intent is not None else "–"

    # Log in one line
    logger.info(
        f"{request.client.host} | "
        f"{request.method} {request.url.path} | "
        f"status={response.status_code} | "
        f"dur={duration:.1f}ms | "
        f"req_bod={body_text!r} | "
        f"intent={intent_text}"
    )
    return response
    
#%% Endpoints
@app.post("/chat")
def chat(user_input: UserInput, request: Request):
    
    # parse intent
    intent = parse_intent(user_input.text, list_of_actions, list_of_categories)
    
    # make it available to middleware
    request.state.intent = intent
    
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

# Load to ram once on startup
model = whisper.load_model("base")  

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save the uploaded webm to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        # Directly transcribe the .webm
        result = model.transcribe(tmp_path)
        return {"text": result["text"]}
    finally:
        # Clean up
        os.remove(tmp_path)