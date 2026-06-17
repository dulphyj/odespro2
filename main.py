from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import health_router
from app.routers.document_router_v1 import router as document_router
from app.routers.page_router_v1 import router as page_router
from app.shared.logger import setup_logger
from app.db.base import Base
from app.db.session import engine

logger = setup_logger()

app = FastAPI(
    title="DocApp API",
    description="API para subir imágenes/PDF y mejorar imágenes mediante procesamiento digital",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(document_router)
app.include_router(page_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tablas creadas / verificadas")
