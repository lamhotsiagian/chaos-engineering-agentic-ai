"""
Models: Vector Embeddings Provider.

Supports local embedding generation via Ollama (`nomic-embed-text`)
or deterministic mock embeddings for unit and chaos test environments.
"""

import math
import hashlib
from typing import List


class BaseEmbeddingClient:
    """Abstract interface for generating vector embeddings."""

    def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        return [self.embed_text(d) for d in docs]


class MockEmbeddingClient(BaseEmbeddingClient):
    """
    Deterministic pseudo-embedding generator using MD5 hashing.
    Generates 64-dimensional normalized vectors for reproducible test queries.
    """

    def __init__(self, dimension: int = 64):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        raw_hash = hashlib.md5(text.encode("utf-8")).digest()
        # Expand hash to desired dimension
        vector = []
        for i in range(self.dimension):
            byte_val = raw_hash[i % len(raw_hash)]
            vector.append(float(byte_val - 128) / 128.0)

        # L2 normalize
        magnitude = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / magnitude for v in vector]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two normalized vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    mag_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return dot / (mag_a * mag_b)
