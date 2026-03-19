from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

model = None
qdrant = None

COLLECTION = "apsit_final"


# =========================
# 🔧 LOAD MODEL
# =========================
def get_model():
    global model
    if model is None:
        print("🔄 Loading embedding model...")
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("✅ Embedding dimension:", model.get_sentence_embedding_dimension())
    return model


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

        model = get_model()
        client = get_qdrant()

        # 🔥 Encode query
        query_vector = model.encode(query).tolist()

        # 🔥 SEARCH
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

            # ✅ FIXED KEYS (MATCH INGESTION)
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