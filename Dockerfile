FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --default-timeout=120 uvicorn
RUN pip install --no-cache-dir --default-timeout=120 fastapi
RUN pip install --no-cache-dir --default-timeout=120 sqlalchemy[asyncio]
RUN pip install --no-cache-dir --default-timeout=120 asyncpg
RUN pip install --no-cache-dir --default-timeout=120 python-multipart
RUN pip install --no-cache-dir --default-timeout=120 pydantic
RUN pip install --no-cache-dir --default-timeout=120 pydantic-settings
RUN pip install --no-cache-dir --default-timeout=120 minio
RUN pip install --no-cache-dir --default-timeout=120 PyMuPDF
RUN pip install --no-cache-dir --default-timeout=120 Pillow
RUN pip install --no-cache-dir --default-timeout=120 numpy

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
