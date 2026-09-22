import os
import math
import hashlib
from typing import List
from langchain_core.embeddings import Embeddings
from app.rag.config import rag_settings

class DeterministicLocalEmbeddings(Embeddings):
    """
    Lightweight, deterministic local fallback embeddings.
    Maps text to a normalized 384-dimensional dense float vector using
    multi-hash feature projections and token frequency statistics.
    Enables local vector search and testing without external API keys or heavy GPU weights.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Multi-hash projection
            h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % self.dimension
            h2 = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[h1] += 1.0
            vec[h2] += 0.5

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)

def get_embedding_model() -> Embeddings:
    """
    Returns an embedding model based on environment configuration.
    Priority:
    1. Google Gemini (if GOOGLE_API_KEY / GEMINI_API_KEY is configured and langchain_google_genai is available)
    2. OpenAI (if OPENAI_API_KEY is configured and langchain_openai is available)
    3. Deterministic Local Embeddings (guarantees offline functionality & zero-key execution)
    """
    provider = rag_settings.EMBEDDING_PROVIDER.lower()

    # Check for Google Gemini
    if provider in ["google", "gemini"] or (provider == "auto" and os.getenv("GOOGLE_API_KEY")):
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
            if api_key:
                return GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=api_key
                )
        except Exception:
            pass

    # Check for OpenAI
    if provider == "openai" or (provider == "auto" and os.getenv("OPENAI_API_KEY")):
        try:
            from langchain_openai import OpenAIEmbeddings
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
            if api_key:
                return OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=api_key
                )
        except Exception:
            pass

    # Resilient local fallback
    return DeterministicLocalEmbeddings(dimension=384)
