import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from app.rag.config import rag_settings
from app.rag.vectorstore import vector_store_manager

logger = logging.getLogger("marinex.rag.retriever")

class MarineRetriever:
    """
    Retrieves relevant marine document chunks with metadata and source citations.
    """
    def __init__(self, top_k: int = rag_settings.TOP_K):
        self.top_k = top_k

    def retrieve(self, query: str, top_k: int = None) -> List[Document]:
        k = top_k or self.top_k
        logger.info(f"[RETRIEVAL] Searching for query: '{query[:60]}...' with top_k={k}")

        try:
            results_with_score = vector_store_manager.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"[RETRIEVAL ERROR] Vector search failed: {e}")
            return []

        docs: List[Document] = []
        for doc, score in results_with_score:
            doc.metadata["similarity_score"] = round(float(score), 4)
            docs.append(doc)

        logger.info(f"[RETRIEVAL] Retrieved {len(docs)} documents.")
        return docs

    def format_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Extracts clean, non-duplicate source citations from retrieved documents.
        """
        seen = set()
        sources: List[Dict[str, Any]] = []

        for doc in documents:
            file_name = doc.metadata.get("file_name", "Unknown document")
            page = doc.metadata.get("page", 1)
            key = (file_name, page)

            if key not in seen:
                seen.add(key)
                sources.append({
                    "file": file_name,
                    "page": page,
                    "doc_type": doc.metadata.get("doc_type", "unknown"),
                    "chunk_id": doc.metadata.get("chunk_id")
                })

        return sources

marine_retriever = MarineRetriever()
