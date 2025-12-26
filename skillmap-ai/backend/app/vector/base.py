from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class VectorStore(ABC):
    """
    Simple abstraction over a vector database.
    Implementations may use Pinecone, Weaviate, or in-memory storage.
    """

    @abstractmethod
    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, id: str) -> Optional[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def query(
        self, vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Return list of (id, score, metadata) sorted by descending similarity.
        """
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """
    Default in-memory vector backend for local development and testing.
    """

    def __init__(self) -> None:
        self._vectors: Dict[str, np.ndarray] = {}
        self._meta: Dict[str, Dict[str, Any]] = {}

    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        self._vectors[id] = np.array(vector, dtype=float)
        self._meta[id] = metadata or {}

    def fetch(self, id: str) -> Optional[List[float]]:
        v = self._vectors.get(id)
        if v is None:
            return None
        return v.tolist()

    def query(
        self, vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if not self._vectors:
            return []
        q = np.array(vector, dtype=float)
        results: List[Tuple[str, float, Dict[str, Any]]] = []
        for id_, v in self._vectors.items():
            if filter:
                meta = self._meta.get(id_, {})
                if not all(meta.get(k) == v for k, v in filter.items()):
                    continue
            denom = (np.linalg.norm(q) * np.linalg.norm(v)) + 1e-8
            score = float((q @ v) / denom)
            results.append((id_, score, self._meta.get(id_, {})))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


_VECTOR_STORE_SINGLETON: Optional[InMemoryVectorStore] = None


def get_vector_store() -> VectorStore:
    # For MVP we always return the in-memory backend; can be switched via config.
    global _VECTOR_STORE_SINGLETON
    if _VECTOR_STORE_SINGLETON is None:
        _VECTOR_STORE_SINGLETON = InMemoryVectorStore()
    return _VECTOR_STORE_SINGLETON


