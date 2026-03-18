import os
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from uuid import uuid4
from pypdf import PdfReader
from urls import URLS
from tqdm import tqdm
import tempfile

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "apsit_test"

print("🔄 Loading embedding model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# ✅ Recreate collection
print("⚡ Creating Qdrant collection...")
qdrant.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)


def fetch_html(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()

        return soup.get_text(separator=" ", strip=True)

    except Exception as e:
        print(f"❌ HTML error: {url} -> {e}")
        return ""


def fetch_pdf(url):
    try:
        res = requests.get(url, timeout=15)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(res.content)
            reader = PdfReader(f.name)

            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

        return text

    except Exception as e:
        print(f"❌ PDF error: {url} -> {e}")
        return ""


def chunk_text(text, size=400):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i + size])


def process_url(url):
    print(f"\n🌐 Processing: {url}")

    if url.endswith(".pdf"):
        text = fetch_pdf(url)
        doc_type = "pdf"
    else:
        text = fetch_html(url)
        doc_type = "html"

    chunks = list(chunk_text(text))

    points = []

    for chunk in chunks:
        vector = model.encode(chunk).tolist()

        points.append({
            "id": str(uuid4()),
            "vector": vector,
            "payload": {
                "text": chunk,
                "source": url,
                "type": doc_type
            }
        })

    return points


def ingest():
    all_points = []

    for url in tqdm(URLS):
        points = process_url(url)
        all_points.extend(points)

        # ✅ Batch upload (important)
        if len(all_points) > 500:
            qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=all_points
            )
            all_points = []

    if all_points:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=all_points
        )

    print("\n✅ INGESTION COMPLETE")


if __name__ == "__main__":
    ingest()