from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return model


qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "apsit_main"


def retrieve(query, limit=5):

    model = get_model()

    query_vector = model.encode(query).tolist()

    results = qdrant.search(
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