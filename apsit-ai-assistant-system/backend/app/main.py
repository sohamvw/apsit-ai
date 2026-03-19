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

# ✅ LOAD ENV
load_dotenv()

# 🔥 FORCE REMOVE GOOGLE_API_KEY (CRITICAL FIX)
if "GOOGLE_API_KEY" in os.environ:
    print("⚠️ Removing GOOGLE_API_KEY from environment")
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


def get_gemini():
    global client
    if client is None:
        print("🔗 Connecting to Gemini...")

        print("🔍 ENV DEBUG:")
        print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))
        print("GOOGLE_API_KEY =", os.getenv("GOOGLE_API_KEY"))

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise Exception("❌ GEMINI_API_KEY not found in environment")

        print("✅ Using Gemini key:", api_key[:10], "...")

        client = genai.Client(api_key=api_key)

    return client


@app.get("/health")
def health():
    return {"status": "assistant-running"}


@app.post("/query")
async def query(request: QueryRequest):

    q = request.query
    session_id = request.session_id

    print("\n🔍 Query received:", q)

    # 🌐 Detect language
    lang = detect_lang(q)

    # 🔎 Retrieve context
    contexts, sources = retrieve(q)

    # 🔥 FILTER BAD DATA (IMPORTANT FIX)
    clean_contexts = [
        c for c in contexts
        if "Not Acceptable" not in c and len(c.strip()) > 30
    ]

    combined_context = "\n\n".join(clean_contexts)

    # 🧠 Session memory
    history = get(session_id)

    history_text = ""
    for h in history:
        history_text += f"User: {h['q']}\nAssistant: {h['a']}\n"

    # ⚠️ NO CONTEXT GUARD
    if not combined_context:
        answer = "I could not find this information in APSIT documents."

        add(session_id, {"q": q, "a": answer})

        return {
            "answer": answer,
            "language": lang,
            "sources": [],
            "pdfs": []
        }

    # 🧾 Prompt
    prompt = f"""
You are APSIT Official AI Assistant.

Strict Rules:
- Answer ONLY using the provided context
- Do NOT hallucinate
- If unsure → say "I could not find this information in APSIT documents."
- Keep answer clear and structured

Conversation History:
{history_text}

Context:
{combined_context}

User Question:
{q}
"""

    try:
        gemini = get_gemini()

        response = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = getattr(response, "text", "No response generated.")

    except Exception as e:
        print("❌ Gemini error:", e)
        answer = "AI response failed. Please try again."

    # 💾 Save memory
    add(session_id, {"q": q, "a": answer})

    # 📄 Extract PDFs
    pdf_links = [url for url in sources if url.endswith(".pdf")]

    return {
        "answer": answer,
        "language": lang,
        "sources": sources,
        "pdfs": pdf_links
    }