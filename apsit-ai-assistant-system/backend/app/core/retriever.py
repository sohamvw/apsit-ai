from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

# Load embedding model once
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Connect to Qdrant
qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "apsit_main"


def retrieve(query, limit=5):

    # Encode query
    query_vector = model.encode(query).tolist()

    # Search Qdrant
    results = qdrant.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )

    contexts = []
    sources = []

    for r in results:

        payload = r.payload

        content = payload.get("content", "")
        url = payload.get("url")

        if content:
            contexts.append(content)

        if url and url not in sources:
            sources.append(url)

    return contexts, sources