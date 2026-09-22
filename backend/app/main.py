from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, marine, chat, rag, agent, data_sources

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"{settings.SUBTITLE} — Built for {settings.ORCA_CONTEXT}",
    version="1.4.0-phase4",
    docs_url="/docs",
    redoc_url="/redoc"
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
        "phase": "Phase 4 - Real Marine Data Integration + Geo-spatial Intelligence Active",
        "docs": "/docs",
        "health": "/api/health",
        "agent_status": "/api/agent/status",
        "rag_status": "/api/rag/status",
        "data_sources_status": "/api/data-sources/status"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
