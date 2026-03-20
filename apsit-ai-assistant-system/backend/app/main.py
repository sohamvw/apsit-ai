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

# 🔥 REMOVE GOOGLE_API_KEY CONFLICT
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
    language: Optional[str] = "auto"   # ✅ FIXED


# =========================
# 🔗 GEMINI
# =========================
def get_gemini():
    global client
    if client is None:
        print("🔗 Connecting to Gemini...")

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise Exception("❌ GEMINI_API_KEY not found")

        print("✅ Gemini connected")

        client = genai.Client(api_key=api_key)

    return client


@app.get("/health")
def health():
    return {"status": "assistant-running"}


@app.on_event("startup")
def startup():
    print("🚀 Backend started successfully")


# =========================
# 🚀 MAIN QUERY
# =========================
@app.post("/query")
async def query(request: QueryRequest):

    q = request.query
    session_id = request.session_id

    print("\n🔍 Query received:", q)

    # 🌐 LANGUAGE LOGIC (FIXED)
    if request.language and request.language != "auto":
        lang = request.language
    else:
        lang = detect_lang(q)

    # 🔎 RETRIEVE (SAFE)
    try:
        contexts, sources = retrieve(q)
    except Exception as e:
        print("❌ Retrieval failed:", e)
        return {
            "answer": "System is busy. Try again.",
            "language": "en",
            "sources": [],
            "pdfs": []
        }

    # 🔥 CLEAN CONTEXT
    clean_contexts = [
        c for c in contexts
        if "Not Acceptable" not in c and len(c.strip()) > 30
    ]

    combined_context = "\n\n".join(clean_contexts)

    # 🧠 MEMORY
    history = get(session_id)

    history_text = ""
    for h in history:
        history_text += f"User: {h['q']}\nAssistant: {h['a']}\n"

    # ❌ NO DATA CASE
    if not combined_context:
        answer = "I could not find this information in APSIT documents."

        add(session_id, {"q": q, "a": answer})

        return {
            "answer": answer,
            "language": lang,
            "sources": [],
            "pdfs": []
        }

    # 🧾 PROMPT
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

    # 🤖 GEMINI
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

    # 💾 SAVE MEMORY
    add(session_id, {"q": q, "a": answer})

    # 📄 PDFs
    pdf_links = [url for url in sources if url.endswith(".pdf")]

    return {
        "answer": answer,
        "language": lang,
        "sources": sources,
        "pdfs": pdf_links
    }