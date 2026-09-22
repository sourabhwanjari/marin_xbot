import os
from pathlib import Path
from pydantic import BaseModel

class RagSettings(BaseModel):
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    DOCUMENTS_DIR: Path = Path(os.getenv("DOCUMENTS_DIR", str(PROJECT_ROOT / "data" / "documents")))
    VECTOR_DB_PATH: Path = Path(os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "storage" / "chroma")))
    
    # Text chunking configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    
    # Retrieval configuration
    TOP_K: int = int(os.getenv("TOP_K", "4"))
    SCORE_THRESHOLD: float = float(os.getenv("SCORE_THRESHOLD", "0.2"))
    
    # Provider configuration
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "auto")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

rag_settings = RagSettings()
