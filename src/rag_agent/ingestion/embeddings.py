from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    vector = _model.encode(
        text,
        normalize_embeddings=True,
    )

    return vector.tolist()