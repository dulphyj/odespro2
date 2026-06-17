#!/bin/sh
set -e

if [ -f config_prod.json ]; then
    echo "Generando config.json desde config_prod.json..."
    python -c "
import os, re
with open('config_prod.json') as f:
    content = f.read()
with open('config.json', 'w') as f:
    f.write(re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), m.group(0)), content))
"
fi

echo "Esperando PostgreSQL..."
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL iniciado"

echo "Esperando MinIO..."
until nc -z "$MINIO_HOST" "$MINIO_PORT" 2>/dev/null; do
    sleep 1
done
echo "MinIO iniciado"

echo "Iniciando DocApp API..."
exec python -m uvicorn main:app --host 0.0.0.0 --port "$SERVICE_PORT"
