from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

# =========================
# 🔥 LOAD MODEL ONCE (CRITICAL FIX)
# =========================
print("🧠 Loading embedding model...")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(
    MODEL_NAME,
    use_auth_token=os.getenv("HF_TOKEN")  # optional but recommended
)

print("✅ Model loaded")

qdrant = None

COLLECTION = "apsit_final"


# =========================
# 🔌 QDRANT CONNECTION
# =========================
def get_qdrant():
    global qdrant
    if qdrant is None:
        print("🔌 Connecting to Qdrant...")
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            check_compatibility=False
        )
    return qdrant


# =========================
# 🔍 RETRIEVE
# =========================
def retrieve(query, limit=5):

    try:
        print(f"\n🔍 Query: {query}")

        client = get_qdrant()

        # 🔥 Encode query (NO RELOAD NOW)
        query_vector = model.encode(query).tolist()

        results = client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=limit
        ).points

        contexts = []
        sources = []

        print("📄 Retrieved chunks:")

        for r in results:
            payload = r.payload or {}

            text = payload.get("content", "")
            source = payload.get("url")

            if text and len(text) > 30:
                contexts.append(text)
                print(" -", text[:120])

            if source and source not in sources:
                sources.append(source)

        print(f"✅ Retrieved {len(contexts)} chunks\n")

        return contexts, sources

    except Exception as e:
        print("❌ Retriever error:", e)
        return [], []