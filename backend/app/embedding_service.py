# app/embedding_service.py

from sentence_transformers import SentenceTransformer

# Load once at startup
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embedding(text: str):
    if not text:
        return None

    # Optional safety truncate
    text = text[:8000]

    vector = model.encode(text)
    return vector.tolist()
