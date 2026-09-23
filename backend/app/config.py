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
    ALLOWED_ORIGINS: list[str] = (
        [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
        if os.getenv("CORS_ORIGINS")
        else [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://marin-xbot.vercel.app",
        ]
    )
    CORS_ORIGIN_REGEX: str = r"^https://.*\.vercel\.app$"
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", os.getenv("LLM_API_KEY", ""))
    LLM_API_KEY: str = os.getenv("GOOGLE_API_KEY", os.getenv("LLM_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/marinex_db")

    # IMD Settings
    IMD_ENABLED: bool = os.getenv("IMD_ENABLED", "false").lower() in ("true", "1", "yes")
    IMD_API_KEY: str = os.getenv("IMD_API_KEY", "")
    IMD_BASE_URL: str = os.getenv("IMD_BASE_URL", "")

    # INCOIS Settings
    INCOIS_ENABLED: bool = os.getenv("INCOIS_ENABLED", "false").lower() in ("true", "1", "yes")
    INCOIS_API_KEY: str = os.getenv("INCOIS_API_KEY", "")
    INCOIS_BASE_URL: str = os.getenv("INCOIS_BASE_URL", "")

    # MOSDAC Settings
    MOSDAC_ENABLED: bool = os.getenv("MOSDAC_ENABLED", "false").lower() in ("true", "1", "yes")
    MOSDAC_USERNAME: str = os.getenv("MOSDAC_USERNAME", "")
    MOSDAC_PASSWORD: str = os.getenv("MOSDAC_PASSWORD", "")
    MOSDAC_DATASET_ID: str = os.getenv("MOSDAC_DATASET_ID", "OS3_SST_L3")
    MOSDAC_BASE_URL: str = os.getenv("MOSDAC_BASE_URL", "https://api.mosdac.gov.in")

    # PostGIS Settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGIS_ENABLED: bool = os.getenv("POSTGIS_ENABLED", "false").lower() in ("true", "1", "yes")

settings = Settings()
