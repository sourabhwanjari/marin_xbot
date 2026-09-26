from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, marine, chat, rag, agent, data_sources
from app.data_ingestion.scheduler.jobs import ingestion_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch scheduled marine public web ingestion tasks
    ingestion_scheduler.start()
    yield
    # Shutdown: Stop scheduled ingestion tasks
    ingestion_scheduler.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"{settings.SUBTITLE} — Built for {settings.ORCA_CONTEXT}",
    version="1.5.0-phase5b",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(marine.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)
app.include_router(rag.router, prefix=settings.API_PREFIX)
app.include_router(agent.router, prefix=settings.API_PREFIX)
app.include_router(data_sources.router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "subtitle": settings.SUBTITLE,
        "problem_statement": settings.ORCA_CONTEXT,
        "phase": "Phase 5B - Official Public Marine Web Ingestion Active",
        "docs": "/docs",
        "health": "/api/health",
        "agent_status": "/api/agent/status",
        "rag_status": "/api/rag/status",
        "gateway_status": "/api/marine/gateway/status",
        "ingestion_status": "/api/marine/ingestion/status",
        "providers_status": "/api/marine/providers/status"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
