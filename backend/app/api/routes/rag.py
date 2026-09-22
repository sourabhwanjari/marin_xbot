import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import (
    RagQueryRequest,
    RagQueryResponse,
    RagIngestResponse,
    RagStatusResponse
)
from app.rag.config import rag_settings
from app.rag.ingestion import ingestion_pipeline
from app.rag.chain import marine_rag_chain
from app.rag.vectorstore import vector_store_manager

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])

@router.get("/status", response_model=RagStatusResponse)
async def get_rag_status():
    """Returns vector store status, indexed documents, chunk counts, and embedding provider."""
    stats = vector_store_manager.get_stats()
    return RagStatusResponse(
        status="ready" if stats["total_chunks"] > 0 else "unindexed",
        total_documents=stats["total_documents"],
        total_chunks=stats["total_chunks"],
        embedding_provider=rag_settings.EMBEDDING_PROVIDER,
        storage_path=stats["storage_path"],
        documents=stats["documents"],
        is_available=True
    )

@router.post("/ingest", response_model=RagIngestResponse)
async def trigger_ingestion():
    """Scans data/documents/, splits new documents, and indexes them into vector store."""
    try:
        result = ingestion_pipeline.run()
        return RagIngestResponse(
            status=result["status"],
            documents_processed=result["documents_loaded"],
            chunks_created=result["chunks_created"],
            chunks_indexed=result["chunks_indexed"],
            chunks_skipped=result["chunks_skipped"],
            errors=result["errors"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/query", response_model=RagQueryResponse)
async def query_knowledge_base(request: RagQueryRequest):
    """Directly queries the RAG knowledge base for evidence-backed answers and source citations."""
    try:
        res = marine_rag_chain.query(request.question)
        return RagQueryResponse(
            answer=res["answer"],
            sources=res["sources"],
            retrieved_chunks=res["retrieved_chunks"],
            is_rag=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a PDF, DOCX, or TXT document to data/documents/ and runs ingestion."""
    allowed_exts = {".pdf", ".docx", ".txt", ".md"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed types: {sorted(list(allowed_exts))}"
        )

    target_dir = rag_settings.DOCUMENTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file.filename

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed saving uploaded file: {str(e)}")

    # Automatically trigger ingestion for the new file
    ingest_result = ingestion_pipeline.run()

    return {
        "status": "success",
        "file_name": file.filename,
        "size_bytes": target_path.stat().st_size,
        "ingestion": ingest_result
    }
