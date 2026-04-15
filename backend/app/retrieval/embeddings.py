"""Local text embedding helpers."""

from __future__ import annotations

import hashlib
import math
import re


class HashEmbeddingFunction:
    """Deterministic, dependency-light embeddings for local retrieval."""

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in input]

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        for index, token in enumerate(tokens):
            self._add_token(vector, token, 1.0)
            if index + 1 < len(tokens):
                self._add_token(vector, f"{token}:{tokens[index + 1]}", 0.5)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _add_token(self, vector: list[float], token: str, weight: float) -> None:
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % self.dimensions
        vector[index] += weight


DEFAULT_EMBEDDING_DIMENSIONS = 256

