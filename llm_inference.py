import os, json, time
from uuid import uuid4
from dotenv import load_dotenv
from openai import OpenAI
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from pydantic import BaseModel
from typing import Optional, List

# ─── config & startup ─────────────────────────────────────────────────────
JSON_PATH = "notes_meta.json"
EMBED_MODEL = "all-MiniLM-L6-v2"
load_dotenv()

# 1) OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


class OpenRouterLLM(LLM, BaseModel):
    client: OpenAI
    system_prompt: str = (
        "You are Jarvis, a helpful assistant. "
        "If the user wants to add or search notes, respond with JSON only: "
        '{"action": "...", "project": "...", "content": "..."}'
    )

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        resp = self.client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=messages,
            temperature=0.0,
        )
        return resp.choices[0].message.content

    @property
    def _llm_type(self) -> str:
        return "openrouter-mistral"


router_llm = OpenRouterLLM(client=client)


# 2) Persistence helpers
def load_notes() -> dict:
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    return json.load(open(JSON_PATH, "r", encoding="utf-8"))


def save_notes(notes: dict):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# 3) Embedding + FAISS index builder
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def build_vectordb() -> FAISS | None:
    raw = load_notes()
    docs = [
        Document(
            page_content=v["content"],
            metadata={
                "id": k,
                "project": v["project"],
                "created_at": v["created_at"],
            },
        )
        for k, v in raw.items()
    ]
    return None if not docs else FAISS.from_documents(docs, embeddings)


vectordb = build_vectordb()
qa = None
if vectordb:
    qa = RetrievalQA.from_chain_type(
        llm=router_llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(search_kwargs={"k": 5}),
    )


# 4) Note‐manipulation helpers
def add_note(project: str, content: str):
    notes = load_notes()
    note_id = str(uuid4())
    notes[note_id] = {
        "project": project,
        "content": content,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_notes(notes)
    # update FAISS
    new_doc = Document(
        page_content=content,
        metadata={
            "id": note_id,
            "project": project,
            "created_at": notes[note_id]["created_at"],
        },
    )
    global vectordb, qa
    if vectordb is None:
        vectordb = FAISS.from_documents([new_doc], embeddings)
        qa = RetrievalQA.from_chain_type(
            llm=router_llm,
            chain_type="stuff",
            retriever=vectordb.as_retriever(search_kwargs={"k": 5}),
        )
    else:
        vectordb.add_documents([new_doc])
    print(f"➡️  Added note to project '{project}': {content}")


def search_notes(query: str, project: str = None):
    if qa is None:
        return "No notes available yet."
    prompt = f'(Project="{proj}")'
    return qa.run(prompt)


# 5) Intent parser
def parse_intent(user_text: str) -> dict:
    raw = router_llm(
        f"""
    You are a helpful assistant.

    Your task is to understand the user's intent and output a JSON object with the following keys:
    - "action": One of "add_note", "search_notes", or "None". Use "None" only if the user's intent is general conversation or unclear.
    - "project": If applicable, extract the topic or subject related to the note or search. Otherwise, set to "None".
    - "content": Should be None, unless if the action is "add_note", on that case, extract the content user message. If the action is "search_notes" or unclear, set to "None".
    - "response": A concise and natural language reply to the user. This should ALWAYS be present and NEVER be null or "None".

    Logic rules:
    - If the user is clearly adding a note, set "action" to "add_note", and fill "project" and "content" based on the message.
    - If the user is clearly searching for notes, set "action" to "search_notes", and extract the "project" being searched. "content" should be "None".
    - If the intent is unclear, or the user is just chatting, set "action", "project", and "content" to "None".
    - If you’re unsure about any field, ask the user for clarification, and set "action", "project", and "content" to "None".

    Always ensure the output is stricly a JSON and includes all four keys, and the "response" must always contain a helpful reply to the user (you should always reply as pair for key "response").

    User: {user_text}
    """
    )
    return json.loads(raw)


# ─── 6) Main loop ──────────────────────────────────────────────────────────
def startup():
    print("Jarvis ready! (type 'quit' to exit)\n")
    while True:
        text = input("You: ").strip()
        if text.lower() in ("quit", "exit"):
            break
        try:
            intent = parse_intent(text)
            print(intent)
            print(intent.get("response"))
        except Exception as e:
            print("⚠️  Could not parse intent:", e)
            continue

        act = intent.get("action")
        proj = intent.get("project")
        cont = intent.get("content")

        if act == "add_note":
            add_note(proj, cont)
        elif act == "search_notes":
            answer = search_notes(cont, project=proj)
            
            print(f"Jarvis:", answer)

startup()

