"""Embedding abstraction layer.

Default provider: Offline deterministic hash-based embeddings (always works).
Real providers (fastembed/HF) used when network access is available.

Why a hash provider exists:
- V1 needs an end-to-end working pipeline (upload → chunk → embed → search).
- HF model downloads are blocked in some sandboxed environments, and the
  free HF Inference API is unreliable.
- This provider produces a deterministic 1024-dim vector from any text so
  the search pipeline can be tested. It is NOT semantically meaningful —
  swap it out by setting EMBEDDING_PROVIDER=fastembed once network is OK.
"""
import hashlib
import math
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single text into a vector."""

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality."""


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic, offline, network-free embedding provider.

    Ponytail: placeholders only — not semantically meaningful.
    Upgrade to FastEmbedProvider when network/HF model access is available.
    """

    DIMENSION = 1024

    def _embed_raw(self, text: str) -> List[float]:
        # Stable hash → 1024 floats in [-1, 1] via SHA-512 expansion.
        # Multiple rounds cover the 1024-dim vector since SHA-512 is 64 bytes.
        chunks_needed = self.DIMENSION // 64 + 1
        digest = b""
        for i in range(chunks_needed):
            digest += hashlib.sha512(f"{i}:".encode("utf-8") + text.encode("utf-8")).digest()
        vec = []
        for i in range(self.DIMENSION):
            byte = digest[i]
            # Map byte 0-255 → -1..1, then normalise by sqrt(dim) for stable magnitudes
            vec.append((byte / 127.5) - 1.0)
        # L2-normalise so cosine distance is well-defined
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, text: str) -> List[float]:
        return self._embed_raw(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_raw(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self.DIMENSION


class FastEmbedProvider(EmbeddingProvider):
    """Local fastembed embedding provider (real, semantically meaningful).

    Use when network is available — requires downloading the model on first run.
    """

    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    DIMENSION = 1024

    def __init__(self) -> None:
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=self.MODEL_NAME)

    def embed(self, text: str) -> List[float]:
        return list(next(self._model.embed([text])))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [list(e) for e in self._model.embed(texts)]

    @property
    def dimension(self) -> int:
        return self.DIMENSION


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider.

    Set EMBEDDING_PROVIDER=fastembed to use the real semantic model.
    Default: hash provider (offline, deterministic placeholder).
    """
    name = os.getenv("EMBEDDING_PROVIDER", "hash").lower()
    if name == "fastembed":
        return FastEmbedProvider()
    return HashEmbeddingProvider()