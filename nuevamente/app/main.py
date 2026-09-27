"""Aplicacion FastAPI de NuevaMente.

Punto de entrada de la API REST. Configura la aplicacion con:
- Lifespan para inicializar el grafo LangGraph como singleton al arranque.
- Router de adaptacion bajo el prefijo /api/v1.
- Exception handlers para errores de dominio (NuevaMenteError) y errores genericos.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from nuevamente.app.routers import adaptar_router
from nuevamente.core.exceptions import NuevaMenteError
from nuevamente.pipeline.graph import build_graph

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan del servidor: compila el grafo una vez al arranque.

    El grafo compilado se almacena en app.state.graph y es reutilizado
    por todos los requests. La compilacion se hace aqui (no en cada request)
    para evitar overhead en tiempo de respuesta del endpoint POST.
    """
    logger.info("Arranque de NuevaMente: compilando grafo LangGraph...")
    app.state.graph = build_graph()
    logger.info("Grafo LangGraph compilado y listo.")
    yield
    logger.info("Apagado de NuevaMente.")


app = FastAPI(
    title="NuevaMente API",
    version="1.0.0",
    description=(
        "Sistema de transformacion de documentacion tecnica en paquetes educativos "
        "personalizados. Acepta documentos PDF, Markdown y texto plano y genera "
        "contenido adaptado segun perfil, formato pedagogico y nicho sectorial."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(NuevaMenteError)
async def nuevamente_error_handler(request: Request, exc: NuevaMenteError) -> JSONResponse:
    """Convierte excepciones de dominio en respuestas JSON estandarizadas.

    Todos los errores de dominio retornan JSON con las claves:
    status, codigo y mensaje, con el codigo HTTP correspondiente al tipo de error.
    """
    logger.warning(
        "Error de dominio: codigo=%s mensaje=%s path=%s",
        exc.codigo,
        exc.mensaje,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content={"status": "error", "codigo": exc.codigo, "mensaje": exc.mensaje},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura excepciones no previstas y retorna un error 500 generico.

    Evita que stacktraces internos lleguen al cliente. El error completo
    se registra en los logs para diagnostico.
    """
    logger.exception(
        "Error inesperado en %s: %s",
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "codigo": "error_interno",
            "mensaje": "Error interno del servidor.",
        },
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(adaptar_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Archivos estaticos e interfaz web
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Sirve la interfaz web principal (index.html).

    Retorna el archivo index.html de la SPA. El endpoint se excluye del
    schema OpenAPI para no contaminar la documentacion de la API REST.
    """
    return FileResponse(str(_static_dir / "index.html"))


# Montar directorio de estaticos bajo /static
# IMPORTANTE: debe ir despues de los routers para que /api/v1/* tenga precedencia
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
