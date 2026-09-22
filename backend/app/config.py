import os
from pathlib import Path
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    # Search for .env in current directory, backend root, or project root
    for env_path in [
        Path(".env"),
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]:
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
            break
except ImportError:
    pass

class Settings(BaseModel):
    PROJECT_NAME: str = "MARINEX AI"
    SUBTITLE: str = "AI-Powered Marine Intelligence & Decision Support"
    ORCA_CONTEXT: str = "ORCA: Marine EcOsystem Reasoning with Collaborative Agents"
    VERSION: str = "1.0.0-phase1"
    API_PREFIX: str = "/api"
    IS_DEMO: bool = True
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    
    # Placeholders for future services (no actual secrets in Phase 1)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/marinex_db")
    MOSDAC_USERNAME: str = os.getenv("MOSDAC_USERNAME", "")
    MOSDAC_PASSWORD: str = os.getenv("MOSDAC_PASSWORD", "")

settings = Settings()
