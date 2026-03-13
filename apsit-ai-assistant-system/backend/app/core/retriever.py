from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

model = None
qdrant = None

COLLECTION = "apsit_main"


def get_model():
    global model
    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return model


def get_qdrant():
    global qdrant
    if qdrant is None:
        print("Connecting to Qdrant...")
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
    return qdrant


def retrieve(query, limit=5):

    model = get_model()
    client = get_qdrant()

    query_vector = model.encode(query).tolist()

    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=limit
    )

    contexts = []
    sources = []

    for r in results:
        payload = r.payload

        contexts.append(payload.get("content", ""))

        url = payload.get("url")
        if url and url not in sources:
            sources.append(url)

    return contexts, sources