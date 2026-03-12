from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.retriever import retrieve
from app.multilingual.language_detector import detect_lang
from app.memory.session_memory import add, get

from google import genai

import os

# Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "assistant-running"}


@app.post("/query")
async def query(request: Request):

    body = await request.json()

    q = body["query"]
    session_id = body.get("session_id", "default")

    # detect language
    lang = detect_lang(q)

    # retrieve documents
    contexts, sources = retrieve(q)

    combined_context = "\n\n".join(contexts)

    # get conversation memory
    history = get(session_id)

    history_text = ""

    for h in history:
        history_text += f"User: {h['q']}\nAssistant: {h['a']}\n"

    # RAG prompt
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

    # Gemini response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    answer = response.text

    # store memory
    add(session_id, {"q": q, "a": answer})

    # detect pdf links
    pdf_links = [url for url in sources if url.endswith(".pdf")]

    return {
        "answer": answer,
        "language": lang,
        "sources": sources,
        "pdfs": pdf_links
    }