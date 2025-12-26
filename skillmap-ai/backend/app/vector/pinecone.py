from typing import Any, Dict, List, Optional, Tuple

from .base import VectorStore


class PineconeVectorStore(VectorStore):
    """
    Placeholder for a Pinecone-backed implementation.
    For the MVP we keep this unimplemented; configure InMemoryVectorStore instead.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Pinecone backend not configured for this deployment.")

    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        raise NotImplementedError

    def fetch(self, id: str) -> Optional[List[float]]:
        raise NotImplementedError

    def query(
        self, vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        raise NotImplementedError


