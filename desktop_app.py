import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import health_router
from app.routers.document_router_v1 import router as document_router
from app.routers.page_router_v1 import router as page_router
from app.shared.logger import setup_logger
from app.db.base import Base
from app.db.session import engine
from desktop.scanner_backend import ScannerBackend
from desktop.scanner_router import router as scanner_router

logger = setup_logger()

os.environ["DOCAPP_MODE"] = "desktop"

app = FastAPI(
    title="DocApp Desktop",
    description="DocApp - Escáner de documentos local",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas / verificadas")
    if ScannerBackend.is_available():
        logger.info("Escáner detectado - modo escáner activado")
    scanners = ScannerBackend.list_scanners()
    for s in scanners:
        logger.info(f"  Escáner: {s['name']}")


@app.on_event("shutdown")
def shutdown():
    engine.dispose()


app.include_router(health_router)
app.include_router(document_router)
app.include_router(page_router)
app.include_router(scanner_router)


def _free_port(port: int):
    """Mata proceso anterior si está usando el puerto."""
    import subprocess
    try:
        out = subprocess.check_output(
            f'netstat -ano | findstr ":{port} "', shell=True, text=True
        )
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                subprocess.run(f"taskkill /F /PID {pid} 2>nul", shell=True)
                break
    except Exception:
        pass


def main():
    port = int(os.environ.get("DOCAPP_PORT", 8000))
    _free_port(port)
    logger.info(f"Iniciando DocApp Desktop en http://localhost:{port}")
    logger.info(f"Documentación: http://localhost:{port}/docs")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
