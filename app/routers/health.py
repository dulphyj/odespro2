from fastapi import APIRouter

health_router = APIRouter(prefix="/v1/health-check", tags=["Revisión Microservicio"])


@health_router.get("/")
async def health():
    return {"api": "up", "service": "DocApp API"}
