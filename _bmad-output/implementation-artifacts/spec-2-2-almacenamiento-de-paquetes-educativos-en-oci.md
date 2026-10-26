---
title: 'Story 2.2: Almacenamiento de Paquetes Educativos en OCI'
type: 'feature'
created: '2026-09-26'
baseline_commit: '0829216'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-2-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** Los paquetes educativos generados por el pipeline no se persisten en ningún lado; no existe trazabilidad output y no se cumple el requisito del hackathon de almacenar los resultados en OCI (FR-13).

**Approach:** Agregar un método `upload_paquete_educativo` a `StorageService` (ya existente de Story 2.1) y llamarlo en `_run_pipeline` (en `adaptar.py`) justo después de que `graph.invoke` retorna el `educational_package`. El resultado del upload se incluye en el payload de `set_completed`, de modo que GET `/adaptar/{task_id}` lo expone bajo la clave `almacenamiento_oci`.

## Boundaries & Constraints

**Always:**
- El upload a OCI es **best-effort**: si falla, el paquete se entrega al usuario normalmente; `almacenamiento_oci.status_upload` indica `"fallido"` con mensaje descriptivo; el error se loguea en nivel `ERROR`.
- El objeto en OCI se llama `paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json`, donde `timestamp` es el epoch en segundos (`int(time.time())`), `perfil` y `formato` son los valores tal cual vienen del state (slugs ya seguros).
- El JSON del paquete se serializa con `json.dumps(educational_package, ensure_ascii=False)` y se sube como bytes UTF-8.
- Las credenciales OCI se leen exclusivamente desde `~/.oci/config` (igual que Story 2.1). No hardcodear secretos.
- El upload ocurre **síncronamente** dentro de `_run_pipeline` (ya corremos en un thread separado via `asyncio.to_thread`); no necesita `asyncio.to_thread` adicional.
- `TaskStore.set_completed` debe aceptar el campo opcional `almacenamiento_oci: dict` e incluirlo en el resultado almacenado.
- La respuesta de GET `/adaptar/{task_id}` expone `almacenamiento_oci` cuando status es `"completed"`.
- Logging a stdout con `logging.getLogger(__name__)`, sin emojis, estilo profesional. Type hints completos, Python 3.12.
- No modificar `pipeline/state.py`, `pipeline/graph.py`, `core/schemas.py`, `core/models.py`, ni `core/exceptions.py`.

**Never:**
- No agregar el upload como un nuevo nodo dentro del grafo LangGraph; el upload es responsabilidad de la capa de servicio, no del grafo.
- No hacer el upload asíncrono con `asyncio.create_task` (ya estamos en un thread de `asyncio.to_thread`; usarlo anidado causaría errores de event loop).
- No bloquear la entrega del paquete si el upload falla.
- No modificar la estructura del `educational_package` ya generado por el grafo.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| Upload exitoso | `educational_package` válido, credenciales OCI configuradas | Objeto JSON creado en bucket; `almacenamiento_oci = {"status_upload": "ok", "bucket": "<nombre>", "objeto_id": "paquetes/<document_id>_<perfil>_<formato>_<ts>.json"}` | — |
| OCI deshabilitado (`oci_bucket_name` vacío) | Settings sin `OCI_BUCKET_NAME` | `almacenamiento_oci = {"status_upload": "deshabilitado"}` | — |
| Error de red / timeout | OCI no accesible | Paquete entregado normalmente; `almacenamiento_oci = {"status_upload": "fallido", "mensaje": "..."}` ; log ERROR | Excepción capturada en `StorageService` |
| Pipeline fallido (exc en `graph.invoke`) | Error antes de format_output | No se intenta el upload; `task_store.set_failed` como antes; `almacenamiento_oci` no presente | — |

</frozen-after-approval>

## Code Map

- `nuevamente/services/storage.py` — MODIFICAR. Agregar método `upload_paquete_educativo(self, package_dict: dict, document_id: str, perfil: str, formato: str) -> dict[str, str]`. Construye `object_name = f"paquetes/{document_id}_{perfil}_{formato}_{int(time.time())}.json"`, serializa el dict a JSON UTF-8, llama `self._client.upload_object(object_name, data)`. En éxito retorna `{"status_upload": "ok", "bucket": self._client._bucket_name, "objeto_id": object_name}`. En `except Exception` loguea ERROR y retorna `{"status_upload": "fallido", "mensaje": str(e)}`. Si `_enabled` es False retorna `{"status_upload": "deshabilitado"}`. Importar `json` y `time` en el módulo.
- `nuevamente/services/task_store.py` — MODIFICAR. `set_completed(task_id, resultado, almacenamiento_oci=None)`: si `almacenamiento_oci` es no-None, añadirlo al dict de la tarea bajo la clave `"almacenamiento_oci"`.
- `nuevamente/app/routers/adaptar.py` — MODIFICAR. En `_run_pipeline`, después de `resultado = await asyncio.to_thread(graph.invoke, initial_state)`, llamar `oci_result = storage_service.upload_paquete_educativo(resultado["educational_package"], initial_state["document_id"], initial_state["perfil"], initial_state["formato"])`. Luego `task_store.set_completed(task_id, resultado["educational_package"], almacenamiento_oci=oci_result)`. Agregar log INFO con el resultado del upload.
- `nuevamente/infra/oci.py` — Solo lectura. `OCIStorageClient.upload_object` ya soporta `object_name` y `data: bytes`; compatible sin cambios. El `_bucket_name` es accesible como atributo de instancia.
- `nuevamente/pipeline/state.py` — Solo lectura. `oci_upload_status: dict[str, Any]` ya existe pero no lo usamos desde el grafo; el upload ocurre en la capa de servicio.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/services/storage.py` — MODIFICAR: agregar `upload_paquete_educativo(self, package_dict, document_id, perfil, formato) -> dict[str, str]`. Importar `json` y `time` al inicio del módulo. El nombre del objeto sigue el patrón `paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json`. Retorno en éxito: `{"status_upload": "ok", "bucket": self._client._bucket_name, "objeto_id": object_name}`.
- [x] `nuevamente/services/task_store.py` — MODIFICAR: `set_completed` acepta parámetro opcional `almacenamiento_oci: dict | None = None`. Si no es None, incluirlo como clave `"almacenamiento_oci"` en el dict de la tarea.
- [x] `nuevamente/app/routers/adaptar.py` — MODIFICAR: en `_run_pipeline`, después de `graph.invoke`, llamar a `storage_service.upload_paquete_educativo(...)` síncronamente y pasar el resultado a `task_store.set_completed(task_id, ..., almacenamiento_oci=oci_result)`.

**Acceptance Criteria:**
- Given `oci_bucket_name` no configurado, when el pipeline completa, then `almacenamiento_oci.status_upload` es `"deshabilitado"` y el paquete se entrega normalmente.
- Given credenciales OCI válidas y pipeline exitoso, when se completa `graph.invoke`, then el JSON del paquete se sube a OCI y GET `/adaptar/{task_id}` retorna `almacenamiento_oci` con `status_upload: "ok"`, `bucket` y `objeto_id`.
- Given un error de OCI durante el upload, when ocurre la excepción, then el paquete se entrega normalmente, `almacenamiento_oci.status_upload` es `"fallido"` con un `mensaje`, y el error queda en el log.
- Given el pipeline falla antes de completar (`graph.invoke` lanza excepción), when `set_failed` se llama, then `almacenamiento_oci` no está presente en la respuesta.
- Given una respuesta completada con OCI habilitado, when se hace GET `/adaptar/{task_id}`, then el payload incluye `almacenamiento_oci` como objeto anidado con al menos las claves `status_upload`, `bucket` y `objeto_id`.

## Implementation Notes

- `nuevamente/services/storage.py` modificado: imports `json` y `time` agregados. Nuevo método `upload_paquete_educativo` síncrono con el patrón best-effort idéntico a `upload_documento_fuente`. Nombre del objeto: `paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json`. Accede a `self._client._bucket_name` para incluirlo en el retorno de éxito.
- `nuevamente/services/task_store.py` modificado: `set_completed` acepta `almacenamiento_oci: dict[str, Any] | None = None`. Cuando no es None, se añade al dict de la tarea bajo la clave `"almacenamiento_oci"`. El endpoint `consultar_tarea` lo expone automáticamente mediante `{**tarea}`.
- `nuevamente/app/routers/adaptar.py` modificado: `_run_pipeline` llama síncronamente a `storage_service.upload_paquete_educativo(...)` después de `graph.invoke` (ya corremos en un thread separado, no se necesita `asyncio.to_thread` adicional). El resultado se pasa a `set_completed` vía `almacenamiento_oci=oci_result`.
- Verificaciones completadas con `uv run python -c ...`:
  - `paquete deshabilitado OK: {'status_upload': 'deshabilitado'}` ✓
  - `task_store OK: True`, `almacenamiento_oci: {'status_upload': 'ok', 'bucket': 'b', 'objeto_id': 'paquetes/x.json'}` ✓
  - `app imports OK: NuevaMente API` ✓

## Spec Change Log

## Review Triage Log

- Finding BH-1: Slash en object name por el valor de perfil `'Lider Tecnico/Arquitecto'` — verdict: `false` — OCI Object Storage acepta cualquier carácter en el object name; el slash crea un prefijo jerárquico virtual que es el comportamiento estándar de object storage. Los objetos son listables y accesibles normalmente. `perfil` y `formato` son validados contra los enums antes de llegar al upload. Route: rechazado.
- Finding BH-2: JSON serialization failure para tipos no-serializables — verdict: `false` — `educational_package` siempre proviene de `Pydantic.model_dump()` que retorna únicamente tipos Python nativos (str, int, float, list, dict, bool). Verificado con test manual. Route: rechazado.
- Finding BH-3: Falta `logger.exception` vs `logger.error` para stack trace — verdict: `low` — patrón consistente con `upload_documento_fuente` de Story 2.1 y con el resto del proyecto. `logger.error` con el mensaje de excepción es suficiente para diagnóstico operacional. Route: rechazado (patrón del proyecto).
- Finding BH-4: `upload_paquete_educativo` podría propagar excepción a `_run_pipeline` — verdict: `false` — el `assert self._client is not None` está dentro del bloque `try/except Exception` del método; `AssertionError` hereda de `Exception` y sería capturado. El método nunca propaga excepciones al caller. Route: rechazado.
- Finding BH-5: Type annotation `dict[str, Any] | None = None` incorrecto — verdict: `false` — Python 3.12 soporta `X | Y` nativo (PEP 604). El tipo es correcto. Route: rechazado.
- Finding BH-6: Sin tests unitarios permanentes en `tests/` — verdict: `low` — pre-existente desde Epic 1; el proyecto no tiene test suite automatizada y la verificación manual con `uv run python -c` es el patrón establecido. Route: defer.


## Design Notes

El upload ocurre **síncronamente** en `_run_pipeline`, que ya corre en un thread separado (`asyncio.to_thread`). Esto evita problemas de event loop anidado que ocurrirían al intentar crear una nueva corutina dentro de un thread que no tiene event loop propio.

```python
# En _run_pipeline, después de graph.invoke:
resultado = await asyncio.to_thread(graph.invoke, initial_state)
oci_result = storage_service.upload_paquete_educativo(
    resultado["educational_package"],
    initial_state["document_id"],
    initial_state["perfil"],
    initial_state["formato"],
)
task_store.set_completed(task_id, resultado["educational_package"], almacenamiento_oci=oci_result)
```

Notar que `upload_paquete_educativo` es síncrono (no async), lo que es correcto porque ya estamos en un thread.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.services.storage import StorageService; from nuevamente.config import Settings; svc = StorageService(Settings(oci_bucket_name='')); r = svc.upload_paquete_educativo({'status': 'completed'}, 'uuid-test', 'tecnico', 'Flashcards'); print('paquete deshabilitado OK:', r)"` -- expected: `paquete deshabilitado OK: {'status_upload': 'deshabilitado'}`
- `uv run python -c "from nuevamente.services.task_store import TaskStore; ts = TaskStore(); ts.create('t1'); ts.set_completed('t1', {'status': 'completed'}, almacenamiento_oci={'status_upload': 'ok', 'bucket': 'b', 'objeto_id': 'paquetes/x.json'}); r = ts.get('t1'); print('task_store OK:', 'almacenamiento_oci' in r)"` -- expected: `task_store OK: True`
- `uv run python -c "from nuevamente.app.main import app; print('app imports OK:', app.title)"` -- expected: `app imports OK: NuevaMente API`
