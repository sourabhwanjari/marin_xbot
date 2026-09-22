import hashlib
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.config import rag_settings

def get_text_splitter(
    chunk_size: int = rag_settings.CHUNK_SIZE,
    chunk_overlap: int = rag_settings.CHUNK_OVERLAP
) -> RecursiveCharacterTextSplitter:
    """
    Returns a configured RecursiveCharacterTextSplitter with marine document separators.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        length_function=len,
        is_separator_regex=False
    )

def split_documents(
    documents: List[Document],
    chunk_size: int = rag_settings.CHUNK_SIZE,
    chunk_overlap: int = rag_settings.CHUNK_OVERLAP
) -> List[Document]:
    """
    Splits documents into manageable chunks while preserving and enriching metadata.
    Adds a deterministic chunk_id based on file name, page, and chunk index.
    """
    splitter = get_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)

    enriched_chunks: List[Document] = []
    for idx, chunk in enumerate(chunks):
        file_name = chunk.metadata.get("file_name", "unknown")
        page = chunk.metadata.get("page", 1)

        # Generate deterministic chunk hash
        content_hash = hashlib.sha256(chunk.page_content.encode("utf-8")).hexdigest()[:12]
        chunk_id = f"{file_name}_p{page}_c{idx}_{content_hash}"

        # Preserve and assign metadata
        chunk.metadata["chunk_id"] = chunk_id
        chunk.metadata["chunk_index"] = idx
        chunk.metadata["chunk_size"] = len(chunk.page_content)

        enriched_chunks.append(chunk)

    return enriched_chunks
