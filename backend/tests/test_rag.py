import os
import shutil
import pytest
from pathlib import Path
from langchain_core.documents import Document

from app.rag.loaders import load_txt, load_document, UnsupportedDocumentError
from app.rag.splitter import split_documents, get_text_splitter
from app.rag.embeddings import DeterministicLocalEmbeddings, get_embedding_model
from app.rag.vectorstore import MarineVectorStore, vector_store_manager
from app.rag.retriever import MarineRetriever
from app.rag.chain import MarineRagChain
from app.rag.ingestion import ingestion_pipeline
from app.services.query_router import QueryRouter, QueryIntent
from fastapi.testclient import TestClient
from app.main import app

TEST_STORAGE_DIR = Path("./tests/test_storage_chroma")

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_storage():
    """Ensure demo documents are ingested for tests and clean up temporary test storage."""
    ingestion_pipeline.run()
    yield
    if TEST_STORAGE_DIR.exists():
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)

# 1. Test Document Loader & Error Handling
def test_document_loader():
    test_file = Path("./tests/sample_doc.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Marine safety guideline: Avoid fishing in waves higher than 2 meters.", encoding="utf-8")

    try:
        docs = load_txt(test_file)
        assert len(docs) == 1
        assert "waves higher than 2 meters" in docs[0].page_content
        assert docs[0].metadata["file_name"] == "sample_doc.txt"
        assert docs[0].metadata["doc_type"] == "txt"

        # Universal loader test
        docs2 = load_document(test_file)
        assert len(docs2) == 1

        # Unsupported format test
        with pytest.raises(UnsupportedDocumentError):
            load_document(Path("test.unsupported_ext"))

    finally:
        if test_file.exists():
            test_file.unlink()

# 2. Test Text Splitter & Metadata Preservation
def test_text_splitter_and_metadata():
    long_text = "Section 1: Coastal Navigation.\n\n" + ("VHF Channel 16 is reserved for distress. " * 30)
    raw_doc = Document(
        page_content=long_text,
        metadata={"file_name": "rules.txt", "page": 1, "doc_type": "txt"}
    )

    chunks = split_documents([raw_doc], chunk_size=200, chunk_overlap=30)
    assert len(chunks) > 1
    for chunk in chunks:
        assert "chunk_id" in chunk.metadata
        assert "file_name" in chunk.metadata
        assert chunk.metadata["file_name"] == "rules.txt"
        assert chunk.metadata["page"] == 1
        assert len(chunk.page_content) <= 300

# 3. Test Vector Store & Duplicate Prevention
def test_vectorstore_and_deduplication():
    vstore = MarineVectorStore(persist_directory=TEST_STORAGE_DIR)
    embedder = DeterministicLocalEmbeddings()

    doc1 = Document(
        page_content="High wave warning: artisanal boats should not venture beyond 15 NM.",
        metadata={"chunk_id": "test_chunk_01", "file_name": "alert.txt", "page": 1, "doc_type": "txt"}
    )
    doc2 = Document(
        page_content="Potential fishing zones show high chlorophyll and SST fronts.",
        metadata={"chunk_id": "test_chunk_02", "file_name": "pfz.txt", "page": 1, "doc_type": "txt"}
    )

    # First insertion
    res1 = vstore.add_documents([doc1, doc2], embedding_model=embedder)
    assert res1["added"] == 2
    assert res1["skipped"] == 0

    # Duplicate insertion
    res2 = vstore.add_documents([doc1], embedding_model=embedder)
    assert res2["added"] == 0
    assert res2["skipped"] == 1

    stats = vstore.get_stats()
    assert stats["total_chunks"] >= 2
    assert stats["total_documents"] >= 2

# 4. Test Retriever & Source Attribution
def test_retriever():
    vstore = MarineVectorStore(persist_directory=TEST_STORAGE_DIR)
    retriever = MarineRetriever(top_k=2)

    # Search for wave warning
    results = vstore.similarity_search_with_score("high wave warning artisanal boats", k=1)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "artisanal boats" in top_doc.page_content

    sources = retriever.format_sources([top_doc])
    assert len(sources) == 1
    assert sources[0]["file"] == "alert.txt"
    assert sources[0]["page"] == 1

# 5. Test RAG Chain Synthesis
def test_rag_chain():
    chain = MarineRagChain()
    response = chain.query("What should artisanal boats do in high waves?")

    assert "answer" in response
    assert len(response["answer"]) > 10
    assert "sources" in response
    assert response["is_rag"] is True
    assert response["retrieved_chunks"] >= 1

# 6. Test Query Router (Classification & Routing)
def test_query_router():
    router = QueryRouter()

    # Knowledge query
    intent_k = router.classify_intent("What do the safety guidelines say about high wave conditions?")
    assert intent_k == QueryIntent.KNOWLEDGE_BASE

    # Live telemetry query
    intent_l = router.classify_intent("What is the current wave height and SST right now?")
    assert intent_l == QueryIntent.LIVE_MARINE_DATA

    # Mixed query
    intent_m = router.classify_intent("What do the regulations say about today's current wave height?")
    assert intent_m == QueryIntent.MIXED

# 7. Test FastAPI Endpoints (RAG & Chat)
def test_api_endpoints():
    client = TestClient(app)

    # RAG status
    r_status = client.get("/api/rag/status")
    assert r_status.status_code == 200
    data_status = r_status.json()
    assert "total_chunks" in data_status
    assert "embedding_provider" in data_status

    # RAG query endpoint
    r_query = client.post("/api/rag/query", json={"question": "What are the rules for artisanal boats in high waves?"})
    assert r_query.status_code == 200
    data_query = r_query.json()
    assert "answer" in data_query
    assert "sources" in data_query
    assert data_query["is_rag"] is True

    # Main Chat endpoint (auto-routed to RAG)
    r_chat = client.post("/api/chat", json={"message": "What do the safety guidelines say about high waves?"})
    assert r_chat.status_code == 200
    data_chat = r_chat.json()
    assert data_chat["is_rag"] is True
    assert len(data_chat["sources"]) > 0

    # Main Chat endpoint (live mock query)
    r_live = client.post("/api/chat", json={"message": "Where is the nearest Potential Fishing Zone?"})
    assert r_live.status_code == 200
    data_live = r_live.json()
    assert data_live["is_rag"] is False
