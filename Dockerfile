FROM python:3.12-slim

# Configuraciones de entorno
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Dependencias base del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar gestor de dependencias uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Usuario sin privilegios root por buenas prácticas de seguridad
RUN useradd -m -u 1000 appuser

# Directorio de trabajo y directorios de persistencia local
WORKDIR /home/appuser/app
RUN mkdir -p data/faiss_indexes data/storage && chown -R appuser:appuser /home/appuser

USER appuser
ENV HOME=/home/appuser \
    PATH="/home/appuser/.local/bin:$PATH"

# Instalar dependencias del proyecto
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Copiar codigo fuente y recursos
COPY --chown=appuser:appuser nuevamente ./nuevamente
COPY --chown=appuser:appuser docs ./docs

# Puerto de escucha
EXPOSE 8000

# Iniciar servidor Uvicorn con resolucion dinamica de puerto
CMD ["sh", "-c", "uv run uvicorn nuevamente.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
