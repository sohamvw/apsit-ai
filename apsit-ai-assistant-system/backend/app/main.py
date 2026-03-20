from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.core.retriever import retrieve
from app.multilingual.language_detector import detect_lang
from app.memory.session_memory import add, get

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = None


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    language: Optional[str] = "auto"


def get_gemini():
    global client
    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY missing")

        client = genai.Client(api_key=api_key)

    return client


@app.get("/health")
def health():
    return {"status": "assistant-running"}


@app.post("/query")
async def query(request: QueryRequest):

    q = request.query
    session_id = request.session_id

    # =========================
    # 🌐 LANGUAGE CONTROL
    # =========================
    if request.language and request.language != "auto":
        lang = request.language
    else:
        lang = detect_lang(q)

    if lang == "mr":
        lang_instruction = "Answer strictly in Marathi. Do NOT use English."
    elif lang == "hi":
        lang_instruction = "Answer strictly in Hindi. Do NOT use English."
    elif lang == "en":
        lang_instruction = "Answer strictly in English."
    else:
        lang_instruction = "Answer in the same language as the question."

    # =========================
    # 🔎 RETRIEVE
    # =========================
    try:
        contexts, sources = retrieve(q)
    except Exception:
        return {
            "answer": "System busy. Try again.",
            "language": "en",
            "sources": [],
            "pdfs": [],
            "images": []
        }

    clean_contexts = [c for c in contexts if len(c.strip()) > 30]
    combined_context = "\n\n".join(clean_contexts)

    history = get(session_id)
    history_text = "\n".join(
        [f"User: {h['q']}\nAssistant: {h['a']}" for h in history]
    )

    if not combined_context:
        answer = "I could not find this information in APSIT documents."
        add(session_id, {"q": q, "a": answer})

        return {
            "answer": answer,
            "language": lang,
            "sources": [],
            "pdfs": [],
            "images": []
        }

    # =========================
    # 🧾 PROMPT (UPDATED)
    # =========================
    prompt = f"""
You are APSIT Official AI Assistant.

Rules:
- Answer only from context
- Do not hallucinate
- Use simple language
- Format using bullet points
- Add short intro
- Remove symbols like ** or *
- Do NOT mix languages

{lang_instruction}

Context:
{combined_context}

Question:
{q}
"""

    try:
        gemini = get_gemini()

        response = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = getattr(response, "text", "No response generated.")

    except Exception:
        answer = "AI response failed."

    add(session_id, {"q": q, "a": answer})

    pdf_links = [u for u in sources if u.endswith(".pdf")]
    image_links = [u for u in sources if u.endswith((".jpg", ".png", ".jpeg"))]

    return {
        "answer": answer,
        "language": lang,
        "sources": sources,
        "pdfs": pdf_links,
        "images": image_links
    }