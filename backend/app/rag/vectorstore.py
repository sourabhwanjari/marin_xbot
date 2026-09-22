import os
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from app.rag.config import rag_settings
from app.rag.embeddings import get_embedding_model

logger = logging.getLogger("marinex.rag.vectorstore")

METADATA_FILE = "indexed_chunks_registry.json"

class MarineVectorStore:
    """
    Manages local vector storage using Chroma with duplicate prevention
    and metadata persistence.
    """
    def __init__(self, persist_directory: Path = rag_settings.VECTOR_DB_PATH):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.persist_directory / METADATA_FILE
        self._load_registry()
        self._chroma = None

    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry: Dict[str, Any] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load vector store registry: {e}")
                self.registry = {"chunks": {}, "documents": {}}
        else:
            self.registry = {"chunks": {}, "documents": {}}

    def _save_registry(self):
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist vector store registry: {e}")

    def get_chroma(self, embedding_model: Optional[Embeddings] = None):
        """Initializes or returns existing Chroma instance."""
        if self._chroma is None:
            embedder = embedding_model or get_embedding_model()
            from langchain_community.vectorstores import Chroma
            self._chroma = Chroma(
                collection_name="marinex_knowledge_base",
                embedding_function=embedder,
                persist_directory=str(self.persist_directory)
            )
        return self._chroma

    def add_documents(self, documents: List[Document], embedding_model: Optional[Embeddings] = None) -> Dict[str, int]:
        """
        Adds document chunks to vector store with duplicate prevention.
        Only chunks not already present in registry are embedded and indexed.
        """
        chroma = self.get_chroma(embedding_model)
        new_docs: List[Document] = []
        new_ids: List[str] = []

        for doc in documents:
            chunk_id = doc.metadata.get("chunk_id")
            if not chunk_id or chunk_id not in self.registry["chunks"]:
                new_docs.append(doc)
                if chunk_id:
                    new_ids.append(chunk_id)

        if not new_docs:
            logger.info("All documents are already indexed. No new chunks added.")
            return {"added": 0, "skipped": len(documents)}

        # Add to Chroma
        if new_ids and len(new_ids) == len(new_docs):
            chroma.add_documents(documents=new_docs, ids=new_ids)
        else:
            chroma.add_documents(documents=new_docs)

        # Update registry
        for doc in new_docs:
            cid = doc.metadata.get("chunk_id", str(len(self.registry["chunks"])))
            fname = doc.metadata.get("file_name", "unknown")
            self.registry["chunks"][cid] = {
                "file_name": fname,
                "page": doc.metadata.get("page", 1),
                "doc_type": doc.metadata.get("doc_type", "unknown"),
                "chunk_size": len(doc.page_content)
            }
            if fname not in self.registry["documents"]:
                self.registry["documents"][fname] = {
                    "file_name": fname,
                    "doc_type": doc.metadata.get("doc_type", "unknown"),
                    "total_chunks": 0,
                    "date_added": doc.metadata.get("date_added")
                }
            self.registry["documents"][fname]["total_chunks"] += 1

        self._save_registry()
        logger.info(f"Successfully added {len(new_docs)} new chunks to vector store.")
        return {"added": len(new_docs), "skipped": len(documents) - len(new_docs)}

    def similarity_search_with_score(
        self,
        query: str,
        k: int = rag_settings.TOP_K,
        embedding_model: Optional[Embeddings] = None
    ) -> List[Tuple[Document, float]]:
        """
        Searches Chroma for top-k matching chunks with similarity distance scores.
        """
        chroma = self.get_chroma(embedding_model)
        return chroma.similarity_search_with_score(query, k=k)

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on currently indexed documents and chunks."""
        return {
            "total_documents": len(self.registry["documents"]),
            "total_chunks": len(self.registry["chunks"]),
            "documents": list(self.registry["documents"].values()),
            "storage_path": str(self.persist_directory)
        }

vector_store_manager = MarineVectorStore()
