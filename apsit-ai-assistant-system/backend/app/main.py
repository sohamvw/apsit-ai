from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.core.retriever import retrieve
from app.multilingual.language_detector import detect_lang
from app.memory.session_memory import add, get

from google import genai
import os

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = None


# -----------------------------
# Request schema for Swagger
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"


# -----------------------------
# Gemini lazy loader
# -----------------------------
def get_gemini():
    global client
    if client is None:
        print("Connecting to Gemini...")
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return client


# -----------------------------
# Health endpoint
# -----------------------------
@app.get("/health")
def health():
    return {"status": "assistant-running"}


# -----------------------------
# Main query endpoint
# -----------------------------
@app.post("/query")
async def query(request: QueryRequest):

    q = request.query
    session_id = request.session_id

    # detect language
    lang = detect_lang(q)

    # retrieve documents
    contexts, sources = retrieve(q)

    combined_context = "\n\n".join(contexts)

    # conversation memory
    history = get(session_id)

    history_text = ""
    for h in history:
        history_text += f"User: {h['q']}\nAssistant: {h['a']}\n"

    prompt = f"""
You are APSIT Official AI Assistant.

Answer ONLY using the provided context.
If the answer is not found in context say:
"I could not find this information in APSIT documents."

Use bullet points when helpful.

Conversation History:
{history_text}

Context:
{combined_context}

User Question:
{q}
"""

    gemini = get_gemini()

    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    answer = response.text

    add(session_id, {"q": q, "a": answer})

    pdf_links = [url for url in sources if url.endswith(".pdf")]

    return {
        "answer": answer,
        "language": lang,
        "sources": sources,
        "pdfs": pdf_links
    }