# app/services/embeddings.py
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-mpnet-base-v2")

def embed(texts: list[str]) -> list[list[float]]:
    return embedding_model.encode(texts).tolist()
