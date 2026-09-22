import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.documents import Document
from app.rag.config import rag_settings
from app.rag.loaders import load_document, UnsupportedDocumentError
from app.rag.splitter import split_documents
from app.rag.vectorstore import vector_store_manager

logger = logging.getLogger("marinex.rag.ingestion")

def clean_text(text: str) -> str:
    """
    Cleans and normalizes extracted document text.
    Removes excessive whitespace and null bytes while preserving paragraph breaks.
    """
    text = text.replace("\x00", "")
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    # Collapse multiple blank lines into double newline
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")
    return cleaned.strip()

class IngestionPipeline:
    """
    Scans document directory, extracts and cleans text, splits into chunks,
    and updates vector store with duplicate prevention.
    """
    def __init__(self, documents_dir: Path = rag_settings.DOCUMENTS_DIR):
        self.documents_dir = Path(documents_dir)

    def run(self) -> Dict[str, Any]:
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        files = [p for p in self.documents_dir.iterdir() if p.is_file() and p.name != "README.md"]

        logger.info(f"[INGESTION] Found {len(files)} potential documents in {self.documents_dir}")

        documents_found = len(files)
        documents_loaded = 0
        all_raw_docs: List[Document] = []
        errors: List[Dict[str, str]] = []

        # 1. Load and clean each document
        for file_path in files:
            try:
                raw_docs = load_document(file_path)
                for doc in raw_docs:
                    doc.page_content = clean_text(doc.page_content)
                    doc.metadata["date_added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                all_raw_docs.extend(raw_docs)
                documents_loaded += 1
                logger.info(f"[INGESTION] Document loaded: {file_path.name} ({len(raw_docs)} pages/sections)")
            except UnsupportedDocumentError as e:
                logger.warning(f"[INGESTION WARNING] Skipping unsupported file {file_path.name}: {e}")
                errors.append({"file": file_path.name, "error": str(e)})
            except Exception as e:
                logger.error(f"[INGESTION ERROR] Error loading {file_path.name}: {e}")
                errors.append({"file": file_path.name, "error": str(e)})

        # 2. Split documents into chunks
        chunks = split_documents(all_raw_docs)
        logger.info(f"[CHUNKING] Created {len(chunks)} chunks from {documents_loaded} documents")

        # 3. Add to vector store (with duplicate prevention)
        store_result = vector_store_manager.add_documents(chunks)
        chunks_added = store_result.get("added", 0)
        chunks_skipped = store_result.get("skipped", 0)

        logger.info(f"[EMBEDDING] Vector store updated: {chunks_added} chunks added, {chunks_skipped} skipped duplicates.")

        return {
            "status": "success",
            "documents_found": documents_found,
            "documents_loaded": documents_loaded,
            "chunks_created": len(chunks),
            "chunks_indexed": chunks_added,
            "chunks_skipped": chunks_skipped,
            "errors": errors,
            "storage_path": str(rag_settings.VECTOR_DB_PATH)
        }

ingestion_pipeline = IngestionPipeline()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stats = ingestion_pipeline.run()
    print("Ingestion Result:", stats)
