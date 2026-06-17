# DocApp API

## Convenciones

- **Tablas DB**: español (documento, pagina)
- **Código**: inglés (variables, funciones, archivos)
- **Logs/mensajes**: español
- **Rutas API**: inglés (/v1/documents, /v1/pages)
- **Tags API**: español ("Documentos", "Páginas")
- **Requirements**: versiones fijas (==)
- **Endpoint wrapper**: success_response() / error_response()
- **Base image**: python:3.12-slim + netcat-openbsd
- **Entrypoint**: entrypoint.sh (espera DB → inicia uvicorn)

## Arquitectura

Backend monolítico sin capas hexagonales:
- app/routers/ → endpoints
- app/services/ → lógica de negocio
- app/db/ → modelos SQLAlchemy
- app/schemas/ → Pydantic
- app/shared/ → utilerías
- app/config/ → configuración

## Endpoints

GET  /v1/health-check/
GET  /v1/documents/
GET  /v1/documents/{id}
POST /v1/documents/upload-image
POST /v1/documents/upload-pdf
POST /v1/documents/{id}/enhance-all
GET  /v1/pages/{id}
GET  /v1/pages/{id}/status
GET  /v1/pages/{id}/image?type=original|enhanced
POST /v1/pages/{id}/enhance

## Deploy

docker compose up --build -d
