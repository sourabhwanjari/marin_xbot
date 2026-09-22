from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        problem_statement=settings.ORCA_CONTEXT,
        version=settings.VERSION,
        is_demo=settings.IS_DEMO
    )
