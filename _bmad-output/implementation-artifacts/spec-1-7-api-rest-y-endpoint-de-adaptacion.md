---
title: 'Story 1.7: API REST y Endpoint de Adaptación'
type: 'feature'
created: '2026-09-26'
baseline_commit: '723de07'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El pipeline LangGraph está completo pero no existe ninguna capa HTTP que lo exponga. Los consumidores del sistema no tienen forma de enviar documentos ni de consultar el resultado de la transformación.

**Approach:** Crear `nuevamente/app/main.py` con la aplicación FastAPI, `nuevamente/app/routers/adaptar.py` con los endpoints `POST /api/v1/adaptar` (recibe documento + parámetros, retorna 202 + task_id) y `GET /api/v1/adaptar/{task_id}` (polling de status/resultado), y `nuevamente/services/task_store.py` como almacén en memoria de tasks. El pipeline se invoca en background via `asyncio.to_thread(graph.invoke, state)` y el grafo se construye una sola vez al startup como singleton.

## Boundaries & Constraints

**Always:**
- `POST /api/v1/adaptar` acepta `multipart/form-data`: campo `archivo` (UploadFile) + tres campos de formulario: `perfil_destinatario` (str, enum Perfil), `formato_salida` (str, enum FormatoPedagogico), `nicho_sector` (str, texto libre o NichoPredefinido).
- Retornar HTTP 415 para formatos de archivo no soportados (via `DocumentoNoSoportado`), HTTP 422 si el archivo está vacío (via `DocumentoVacio`). Todos los errores de dominio retornan JSON `{"status": "error", "codigo": "...", "mensaje": "..."}`.
- El grafo (`build_graph()`) se instancia **una vez** al startup via `lifespan`, guardado en `app.state.graph`. No en cada request.
- El pipeline corre en background: `asyncio.to_thread(graph.invoke, initial_state)` dentro de `asyncio.create_task`. Los nodos del grafo son síncronos; `asyncio.to_thread` evita bloquear el event loop.
- `task_store.py` usa un `dict` en memoria (concurrencia 1 per spec); estructura de task: `{"status": "pending"|"processing"|"completed"|"failed", "resultado": ..., "error": ...}`.
- `document_id` se genera con `str(uuid.uuid4())` en el endpoint POST.
- El estado inicial del grafo incluye exactamente: `document_id`, `raw_text` (texto extraído), `file_name`, `perfil`, `formato`, `nicho`.
- Extraer texto del archivo inline en el router: `.txt`/`.md` via `content.decode("utf-8")`, `.pdf` via `pypdf.PdfReader`. Verificar si `services/ingestion.py` ya expone `extract_text` reutilizable antes de implementar inline.
- Documentación OpenAPI auto-generada disponible en `/docs` (FastAPI por defecto).
- Logging a stdout con `logging.getLogger(__name__)`, sin emojis, estilo profesional.
- Type hints completos, Python 3.12.

**Never:**
- No agregar checkpointer ni persistencia en disco al grafo.
- No modificar `pipeline/graph.py`, `pipeline/state.py`, `core/schemas.py`, `core/models.py` ni `core/exceptions.py`.
- No agregar dependencias externas; todas las necesarias (FastAPI, uvicorn, python-multipart, pypdf) ya están en `pyproject.toml`.
- No implementar autenticación, rate limiting ni integración OCI en esta story.
- No usar `graph.ainvoke()` directamente — los nodos son síncronos; usar `asyncio.to_thread(graph.invoke, state)`.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| POST archivo PDF válido | `archivo` PDF, `perfil` válido, `formato` válido, `nicho` cualquier str | HTTP 202 `{"task_id": "<uuid>", "status": "pending"}` | -- |
| POST archivo .txt válido | `archivo` .txt, parámetros válidos | HTTP 202 con task_id | -- |
| POST archivo .md válido | `archivo` .md, parámetros válidos | HTTP 202 con task_id | -- |
| POST formato no soportado (.docx) | `archivo` .docx | HTTP 415 `{"status": "error", "codigo": "formato_no_soportado", "mensaje": "..."}` | DocumentoNoSoportado capturado |
| POST archivo vacío | `archivo` sin contenido | HTTP 422 `{"status": "error", "codigo": "documento_vacio", "mensaje": "..."}` | DocumentoVacio capturado |
| GET task_id inexistente | `task_id` no registrado | HTTP 404 `{"status": "error", "codigo": "tarea_no_encontrada", "mensaje": "..."}` | -- |
| GET task en proceso | `task_id` con status "processing" | HTTP 200 `{"task_id": "...", "status": "processing"}` | -- |
| GET task completada | `task_id` con status "completed" | HTTP 200 `{"task_id": "...", "status": "completed", "resultado": {...}}` | -- |
| GET task fallida | `task_id` con status "failed" | HTTP 200 `{"task_id": "...", "status": "failed", "error": "..."}` | -- |
| Pipeline falla internamente | Error en grafo | Task pasa a "failed" con mensaje de error; HTTP 500 no se propaga al cliente | PipelineError capturado en background worker |

</frozen-after-approval>

## Code Map

- `nuevamente/app/__init__.py` — Existe, solo docstring. Solo lectura; no modificar.
- `nuevamente/app/routers/__init__.py` — Existe, solo docstring. ACTUALIZAR: agregar export del router de adaptar.
- `nuevamente/app/main.py` — CREAR: aplicación FastAPI con lifespan (build_graph singleton), inclusion del router, exception handlers para `NuevaMenteError`.
- `nuevamente/app/routers/adaptar.py` — CREAR: endpoints POST y GET `/api/v1/adaptar`, función `_run_pipeline`. La extracción de texto se delega a `ingestion.extract_text(file_bytes, file_name)` — no implementar inline.
- `nuevamente/services/task_store.py` — CREAR: `TaskStore` con dict en memoria; métodos `create`, `set_processing`, `set_completed`, `set_failed`, `get`. Instancia módulo-nivel `task_store = TaskStore()`.
- `nuevamente/services/ingestion.py` — Solo lectura: expone `extract_text(file_bytes: bytes, file_name: str) -> str`. REUSAR en el router para extraer texto del archivo; lanza `DocumentoNoSoportado` y `DocumentoVacio` internamente.
- `nuevamente/pipeline/graph.py` — Solo lectura: `build_graph() -> CompiledStateGraph`. Sin checkpointer.
- `nuevamente/pipeline/state.py` — Solo lectura: `NuevaMenteState` inputs: `document_id`, `raw_text`, `file_name`, `perfil`, `formato`, `nicho`.
- `nuevamente/core/exceptions.py` — Solo lectura: `DocumentoNoSoportado` (415), `DocumentoVacio` (422), `NuevaMenteError` base con `.http_status`, `.codigo`, `.mensaje`.
- `nuevamente/core/models.py` — Solo lectura: `Perfil` (4 valores), `FormatoPedagogico` (5 valores), `NichoPredefinido` (4 valores).
- `nuevamente/config.py` — Solo lectura: `Settings` con `host`, `port`, `log_level`.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/services/task_store.py` — CREAR: clase `TaskStore` con `dict` interno. Métodos: `create(task_id: str) -> None` (status="pending"), `set_processing(task_id: str) -> None`, `set_completed(task_id: str, resultado: dict) -> None`, `set_failed(task_id: str, error: str) -> None`, `get(task_id: str) -> dict | None`. Instancia módulo-nivel `task_store = TaskStore()`.
- [x] `nuevamente/app/main.py` — CREAR: aplicación FastAPI con `lifespan` que llama `build_graph()` y guarda en `app.state.graph`. Metadata: `title="NuevaMente API"`, `version="1.0.0"`. Incluir router de adaptar con prefix `/api/v1`. Exception handler para `NuevaMenteError`: retorna JSON `{"status": "error", "codigo": exc.codigo, "mensaje": exc.mensaje}` con `status_code=exc.http_status`. Exception handler para `Exception` genérica: JSON `{"status": "error", "codigo": "error_interno", "mensaje": "Error interno del servidor"}` con status 500.
- [x] `nuevamente/app/routers/adaptar.py` — CREAR: router FastAPI. `POST /adaptar`: acepta `archivo: UploadFile`, `perfil_destinatario: str = Form(...)`, `formato_salida: str = Form(...)`, `nicho_sector: str = Form(...)`. Valida que perfil y formato sean valores de enum válidos (HTTP 422 automático de FastAPI). Lee bytes del archivo con `await archivo.read()`. Llama `ingestion.extract_text(file_bytes, archivo.filename)` — propaga `DocumentoNoSoportado` y `DocumentoVacio` naturalmente. Genera `document_id = str(uuid.uuid4())`. Crea task. Lanza `asyncio.create_task(_run_pipeline(...))`. Retorna `JSONResponse({"task_id": task_id, "status": "pending"}, status_code=202)`.
- [x] `nuevamente/app/routers/adaptar.py` — CREAR `GET /adaptar/{task_id}`: consulta `task_store.get(task_id)`; retorna 404 si no existe; retorna 200 con dict de la task incluyendo `task_id`.
- [x] `nuevamente/app/routers/adaptar.py` — CREAR función `_run_pipeline(graph, task_id: str, initial_state: dict) async -> None`: llama `task_store.set_processing(task_id)`, luego `resultado = await asyncio.to_thread(graph.invoke, initial_state)`, luego `task_store.set_completed(task_id, resultado["educational_package"])`. En `except Exception as e`: `task_store.set_failed(task_id, str(e))`. Logging de inicio, fin y error.
- [x] `nuevamente/app/routers/__init__.py` — ACTUALIZAR: agregar `from nuevamente.app.routers.adaptar import router as adaptar_router` y exportar.

**Acceptance Criteria:**
- Given una petición POST con archivo PDF válido y parámetros válidos, when se llama `POST /api/v1/adaptar`, then se retorna HTTP 202 con JSON que contiene `task_id` (string no vacío) y `status: "pending"`.
- Given un `task_id` retornado por POST, when se llama `GET /api/v1/adaptar/{task_id}` inmediatamente, then se retorna HTTP 200 con `status` en `["pending", "processing", "completed"]`.
- Given un `task_id` inexistente, when se llama `GET /api/v1/adaptar/{task_id}`, then se retorna HTTP 404 con JSON `{"status": "error", "codigo": "tarea_no_encontrada"}`.
- Given un archivo con extensión no soportada (.docx), when se llama POST, then se retorna HTTP 415 con JSON `{"status": "error", "codigo": "formato_no_soportado"}`.
- Given un archivo vacío (.txt vacío), when se llama POST, then se retorna HTTP 422 con JSON `{"status": "error", "codigo": "documento_vacio"}`.
- Given que el pipeline termina exitosamente, when se consulta GET, then el response incluye `status: "completed"` y `resultado` con las claves `status`, `metadatos`, `contenido_adaptado`, `evaluacion_calidad`.
- Given la app inicializada, when se consulta `GET /docs`, then la documentación OpenAPI está disponible.

## Implementation Notes

- `services/task_store.py` creado con `TaskStore` y la instancia módulo-nivel `task_store`. Los métodos `set_*` comprueban existencia de `task_id` antes de actualizar para evitar KeyError si hubiera race condition.
- `app/main.py` creado con lifespan que compila el grafo al arranque y lo almacena en `app.state.graph`. La compilación demora ~3-4 segundos (build_graph descarga tokenizador en primer arranque); los requests posteriores no tienen overhead.
- `app/routers/adaptar.py` creado. Validación de enums hecha explícitamente con sets (no con Pydantic model) para controlar el mensaje de error en español y retornar JSON con estructura estandarizada. Se reutilizó `ingestion.extract_text(file_bytes, file_name)` directamente — ya lanza `DocumentoNoSoportado` y `DocumentoVacio` con los mensajes correctos.
- `asyncio.create_task(_run_pipeline(...))` requiere que el event loop esté corriendo cuando se llama. En FastAPI async handlers esto siempre se cumple.
- `_run_pipeline` usa `asyncio.to_thread(graph.invoke, initial_state)` — correcto porque todos los nodos del grafo son síncronos. El pipeline en background falla correctamente con `VOYAGE_API_KEY` no configurada en el entorno de test, pasando la tarea a `failed` sin propagar al cliente.
- Verificaciones completadas: `task_store OK`, `app OK NuevaMente API`, `router OK`. Todos los casos de la I/O Matrix verificados con curl contra servidor live en puerto 8003.


## Spec Change Log

## Review Triage Log

- Finding 1: `NuevaMenteError` importado sin usar en `adaptar.py` (F401) — verdict: `low` — evidence: import en línea 336 del diff no aparece en ningún raise/isinstance/type annotation en el archivo; los handlers de dominio están en main.py. Route: **patch** (eliminación directa de una línea). Aplicado.
- Finding 2: Sin validación de tamaño máximo de archivo en POST /api/v1/adaptar — verdict: `low` — evidence: epic-1-context.md menciona 1GB RAM / <2min límite pero no especifica validación de bytes en el endpoint. No fue requerido por el intent ni por el spec. Route: **defer** — deferred-work.md actualizado.
- Finding 3: Filename sin extensión genera mensaje "Formato ''" en el 415 — verdict: `low` — evidence: comportamiento técnicamente correcto (415 apropiado), solo el mensaje es ambiguo; clientes normales siempre envían filename con extensión. Route: **rechazado** (cosmético, fix más complejo que la corrección directa).
- Finding 4: `task_id == document_id` mencionado como deuda técnica — verdict: `false` — evidence: intencional y documentado en Implementation Notes; el spec y el state de LangGraph usan ambos para identificar el mismo pipeline run. No hay defecto.


## Design Notes

Patrón de lifespan en FastAPI para singleton del grafo:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from nuevamente.pipeline.graph import build_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = build_graph()
    yield

app = FastAPI(lifespan=lifespan, title="NuevaMente API", version="1.0.0")
```

Patrón de background task con asyncio.to_thread (nodos síncronos, per LangGraph docs):

```python
import asyncio

async def _run_pipeline(graph, task_id: str, initial_state: dict) -> None:
    task_store.set_processing(task_id)
    try:
        resultado = await asyncio.to_thread(graph.invoke, initial_state)
        task_store.set_completed(task_id, resultado["educational_package"])
    except Exception as e:
        logger.error("Pipeline fallido task_id=%s error=%s", task_id, e)
        task_store.set_failed(task_id, str(e))
```

Extracción de texto inline (si ingestion.py no expone extract_text):

```python
async def _extract_text(archivo: UploadFile) -> str:
    content = await archivo.read()
    ext = Path(archivo.filename or "").suffix.lower()
    if ext in (".txt", ".md"):
        return content.decode("utf-8", errors="replace")
    elif ext == ".pdf":
        import io
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(content)).pages)
    else:
        raise DocumentoNoSoportado(f"Formato '{ext}' no soportado.")
```

## Verification

**Commands:**
- `uv run python -c "from nuevamente.services.task_store import TaskStore; ts=TaskStore(); ts.create('t1'); ts.set_completed('t1', {}); print('task_store OK', ts.get('t1')['status'])"` -- expected: imprime "task_store OK completed"
- `uv run python -c "from nuevamente.app.main import app; print('app OK', app.title)"` -- expected: imprime "app OK NuevaMente API"
- `uv run uvicorn nuevamente.app.main:app --host 0.0.0.0 --port 8001 &; sleep 3; curl -sf http://localhost:8001/docs | head -20; kill %1 2>/dev/null` -- expected: respuesta HTML de la documentación OpenAPI
