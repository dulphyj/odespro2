FROM madnight/docker-alpine-tesseract:latest AS tesseract

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=tesseract /usr/bin/tesseract /usr/bin/tesseract
COPY --from=tesseract /usr/share/tessdata /usr/share/tessdata

ENV TESSDATA_PREFIX=/usr/share/tessdata

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
