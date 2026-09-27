"""Router de adaptacion de documentos.

Expone dos endpoints:
- POST /adaptar: recibe un documento y parametros de personalizacion,
  lanza el pipeline en background y retorna 202 + task_id.
- GET /adaptar/{task_id}: retorna el estado actual de la tarea y,
  cuando esta completada, el paquete educativo generado.

El pipeline se ejecuta via asyncio.to_thread(graph.invoke, state) ya que
todos los nodos del grafo LangGraph son sincronos. Esto libera el event loop
de FastAPI durante la ejecucion del pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from nuevamente.config import Settings
from nuevamente.core.models import FormatoPedagogico, Perfil
from nuevamente.services.ingestion import extract_text
from nuevamente.services.storage import storage_service
from nuevamente.services.task_store import task_store

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuracion de limites
_settings = Settings()
_MAX_FILE_SIZE_BYTES: int = _settings.nm_max_file_size_mb * 1024 * 1024  # 0 = sin limite

# Valores validos para los enums de personalizacion
_PERFILES_VALIDOS = {p.value for p in Perfil}
_FORMATOS_VALIDOS = {f.value for f in FormatoPedagogico}


def _register_background_task(request: Request, task: asyncio.Task) -> None:
    """Registra una tarea asyncio en app.state para evitar recoleccion prematura por el GC.

    Agrega la tarea al set app.state._background_tasks. Cuando la tarea termina,
    se remueve automaticamente del set via callback, manteniendo el conjunto compacto.

    Args:
        request: Request de FastAPI para acceder a app.state.
        task: Tarea asyncio a retener.
    """
    if not hasattr(request.app.state, "_background_tasks"):
        request.app.state._background_tasks: set[asyncio.Task] = set()
    request.app.state._background_tasks.add(task)
    task.add_done_callback(request.app.state._background_tasks.discard)


# ---------------------------------------------------------------------------
# Funcion de background
# ---------------------------------------------------------------------------


async def _run_pipeline(graph: Any, task_id: str, initial_state: dict[str, Any]) -> None:
    """Ejecuta el grafo LangGraph en un thread separado para no bloquear el event loop.

    Actualiza el task_store con el estado de la ejecucion: processing al inicio,
    completed con el paquete educativo al finalizar, o failed con el mensaje de
    error si ocurre una excepcion.

    Args:
        graph: CompiledStateGraph retornado por build_graph().
        task_id: Identificador unico de la tarea.
        initial_state: Estado inicial del grafo con los campos de input.
    """
    logger.info("Pipeline iniciado: task_id=%s documento=%s", task_id, initial_state.get("file_name"))
    task_store.set_processing(task_id)
    try:
        resultado = await asyncio.to_thread(graph.invoke, initial_state)
        paquete = resultado["educational_package"]
        oci_result = storage_service.upload_paquete_educativo(
            paquete,
            initial_state["document_id"],
            initial_state["perfil"],
            initial_state["formato"],
        )
        logger.info(
            "Upload paquete educativo OCI: task_id=%s status=%s",
            task_id,
            oci_result.get("status"),
        )
        task_store.set_completed(task_id, paquete, almacenamiento_oci=oci_result)
        logger.info("Pipeline completado: task_id=%s", task_id)
    except Exception as exc:
        mensaje = str(exc)
        logger.error("Pipeline fallido: task_id=%s error=%s", task_id, mensaje)
        task_store.set_failed(task_id, mensaje)



# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/adaptar", status_code=202)
async def adaptar(
    request: Request,
    archivo: UploadFile,
    perfil_destinatario: str = Form(...),
    formato_salida: str = Form(...),
    nicho_sector: str = Form(...),
) -> JSONResponse:
    """Inicia la adaptacion de un documento tecnico en un paquete educativo.

    Acepta el documento en formato PDF, Markdown (.md) o texto plano (.txt)
    junto con tres parametros de personalizacion. El procesamiento ocurre en
    background; la respuesta inmediata es un 202 Accepted con el task_id para
    hacer polling del resultado via GET /adaptar/{task_id}.

    Args:
        request: Request de FastAPI (para acceder a app.state.graph).
        archivo: Archivo a procesar (PDF, .md o .txt).
        perfil_destinatario: Perfil del destinatario del contenido educativo.
        formato_salida: Formato pedagogico de salida.
        nicho_sector: Nicho o sector de aplicacion (texto libre o predefinido).

    Returns:
        JSONResponse con status 202, task_id y status "pending".

    Raises:
        HTTPException 422: Si perfil o formato no son valores de enum validos.
        DocumentoNoSoportado: Si la extension del archivo no esta soportada (HTTP 415).
        DocumentoVacio: Si el archivo no contiene texto extraible (HTTP 422).
    """
    # Validar enum de perfil
    if perfil_destinatario not in _PERFILES_VALIDOS:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "codigo": "parametro_invalido",
                "mensaje": (
                    f"perfil_destinatario '{perfil_destinatario}' no es valido. "
                    f"Valores aceptados: {sorted(_PERFILES_VALIDOS)}"
                ),
            },
        )

    # Validar enum de formato
    if formato_salida not in _FORMATOS_VALIDOS:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "codigo": "parametro_invalido",
                "mensaje": (
                    f"formato_salida '{formato_salida}' no es valido. "
                    f"Valores aceptados: {sorted(_FORMATOS_VALIDOS)}"
                ),
            },
        )

    # Validar tamano del archivo antes de leerlo en memoria (item 1 retro epic 1)
    if _MAX_FILE_SIZE_BYTES > 0 and archivo.size is not None and archivo.size > _MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "codigo": "archivo_demasiado_grande",
                "mensaje": (
                    f"El archivo excede el tamano maximo permitido de "
                    f"{_settings.nm_max_file_size_mb} MB "
                    f"({archivo.size} bytes recibidos)."
                ),
            },
        )

    # Leer bytes del archivo y extraer texto (puede lanzar DocumentoNoSoportado / DocumentoVacio)
    file_bytes = await archivo.read()

    # Validacion de tamano post-lectura como segunda defensa (cuando size no viene en el header)
    if _MAX_FILE_SIZE_BYTES > 0 and len(file_bytes) > _MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "codigo": "archivo_demasiado_grande",
                "mensaje": (
                    f"El archivo excede el tamano maximo permitido de "
                    f"{_settings.nm_max_file_size_mb} MB "
                    f"({len(file_bytes)} bytes recibidos)."
                ),
            },
        )
    file_name = archivo.filename or "documento"
    raw_text = extract_text(file_bytes, file_name)  # propaga excepciones de dominio

    # Generar identificador unico para la tarea
    task_id = str(uuid.uuid4())
    document_id = task_id  # reutilizamos task_id como document_id del pipeline

    # Estado inicial del grafo
    initial_state: dict[str, Any] = {
        "document_id": document_id,
        "raw_text": raw_text,
        "file_name": file_name,
        "perfil": perfil_destinatario,
        "formato": formato_salida,
        "nicho": nicho_sector,
    }

    # Subir documento fuente a OCI en background (best-effort, no bloquea)
    # La referencia se retiene en app.state._background_tasks para evitar GC prematuro (item 2 retro epic 1)
    oci_task = asyncio.create_task(
        storage_service.upload_documento_fuente_async(file_bytes, file_name, document_id)
    )
    _register_background_task(request, oci_task)
    logger.info(
        "Documento fuente encolado para upload OCI: task_id=%s objeto=documentos/%s%s",
        task_id,
        document_id,
        Path(file_name).suffix,
    )

    # Registrar tarea y lanzar pipeline en background
    task_store.create(task_id)
    pipeline_task = asyncio.create_task(
        _run_pipeline(request.app.state.graph, task_id, initial_state)
    )
    _register_background_task(request, pipeline_task)

    logger.info(
        "Tarea creada: task_id=%s archivo=%s perfil=%s formato=%s",
        task_id,
        file_name,
        perfil_destinatario,
        formato_salida,
    )

    return JSONResponse(
        status_code=202,
        content={"task_id": task_id, "status": "pending"},
    )


@router.get("/adaptar/{task_id}")
async def consultar_tarea(task_id: str) -> JSONResponse:
    """Consulta el estado de una tarea de adaptacion.

    Retorna el estado actual de la tarea y, cuando esta completada,
    el paquete educativo generado. Si la tarea fallo, retorna el
    mensaje de error.

    Args:
        task_id: Identificador de la tarea retornado por POST /adaptar.

    Returns:
        JSONResponse con status 200 y el estado de la tarea, o 404 si no existe.
    """
    tarea = task_store.get(task_id)

    if tarea is None:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "codigo": "tarea_no_encontrada",
                "mensaje": f"No existe ninguna tarea con id '{task_id}'.",
            },
        )

    return JSONResponse(
        status_code=200,
        content={"task_id": task_id, **tarea},
    )
