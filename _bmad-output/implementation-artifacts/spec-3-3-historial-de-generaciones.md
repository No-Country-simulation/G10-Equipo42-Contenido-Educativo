---
title: 'Story 3.3: Historial de Generaciones'
type: 'feature'
created: '2026-09-27'
baseline_commit: '7093665'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** Los items del historial en la barra lateral son solo informativos — al hacer click no ocurre nada; no existe el endpoint de descarga de paquetes ni el método OCI de lectura de objetos.

**Approach:** Agregar `get_object()` en `OCIStorageClient`, `get_paquete()` en `StorageService`, un endpoint `GET /api/v1/historial/{objeto_id_encoded}` en el router, y el handler de click en `renderHistorial()` que llame al endpoint y reutilice el dispatcher `showResult()` de Story 3.2 para visualizar el paquete.

## Boundaries & Constraints

**Always:**
- El endpoint de descarga recibe el `objeto_id` URL-encodificado y lo decodifica en Python con `urllib.parse.unquote`.
- `get_object()` en OCI retorna los bytes crudos del objeto; `StorageService.get_paquete()` lo parsea como JSON y retorna el dict, o `None` si falla.
- El endpoint retorna `{"resultado": <paquete_dict>}` para que el JS pueda pasar `{resultado: ...}` directamente a `showResult()`, reutilizando el dispatcher y los cinco renderers de Story 3.2 sin modificarlos.
- `escapeHtml()` y `escapeAttr()` en todo texto proveniente del servidor al inyectarlo en el DOM.
- Si OCI está deshabilitado o el objeto no existe, el endpoint retorna HTTP 404 con `{"detail": "Paquete no encontrado."}`.
- `get_object()` es sincróno (SDK OCI); llamarlo con `asyncio.to_thread` en el endpoint.
- Best-effort: los errores de red/OCI se loguean y el endpoint retorna 404 — no propagan al usuario como 500.

**Never:**
- No modificar `showResult()` ni los renderers (Flashcards, Quiz, Tutorial, Resumen, Guión) de Story 3.2.
- No agregar base de datos ni estado en memoria para el historial; solo OCI.
- No modificar `index.html` — la estructura del sidebar ya existe.
- No agregar dependencias Python externas.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| Click en item del historial, OCI habilitado | `objeto_id` válido en OCI | Paquete se carga y renderiza con el renderer del formato correcto | — |
| Click en item del historial, objeto no existe | `objeto_id` en OCI pero archivo borrado | HTTP 404; JS muestra error en panel de error con botón reintentar | — |
| OCI deshabilitado | Click en cualquier item | HTTP 404; JS muestra mensaje de error | — |
| `objeto_id` con slashes (`paquetes/abc_...json`) | URL-encoded como `%2F` en la URL | Decodificado correctamente con `unquote`; objeto encontrado | — |
| Historial vacío al cargar | OCI sin paquetes o deshabilitado | Sidebar muestra estado vacío con mensaje indicativo (ya implementado) | — |

</frozen-after-approval>

## Code Map

- `nuevamente/infra/oci.py` — MODIFICAR. Agregar `get_object(object_name: str) -> bytes` que llama a `self._client.get_object(...)` y retorna `response.data.content`. Sin captura de excepciones (propaga al llamante como los otros métodos).
- `nuevamente/services/storage.py` — MODIFICAR. Agregar `get_paquete(objeto_id: str) -> dict | None` síncrono: llama a `self._client.get_object(objeto_id)`, parsea JSON y retorna el dict. Si `_enabled` es False retorna `None`. Si lanza excepción: loguea ERROR y retorna `None`.
- `nuevamente/app/routers/adaptar.py` — MODIFICAR. Agregar `GET /historial/{objeto_id_encoded}`: decodifica `objeto_id_encoded` con `urllib.parse.unquote`, llama `await asyncio.to_thread(storage_service.get_paquete, objeto_id)`, retorna `{"resultado": paquete}` o 404. Importar `asyncio` y `urllib.parse` si no están. El endpoint ya usa `storage_service` como módulo-nivel.
- `nuevamente/app/static/app.js` — MODIFICAR. En `renderHistorial()`: registrar handler de click (event delegation sobre `sidebarList`) para `.hist-item`. Al click: leer `data-objeto-id`, llamar `loadPaqueteFromHistorial(objetoId)`. Implementar `loadPaqueteFromHistorial(objetoId)`: muestra panel de progreso, llama `GET /api/v1/historial/{encodeURIComponent(objetoId)}`, en éxito llama `showResult({resultado: data.resultado, status: 'completed'})`, en error muestra panel de error.
- `nuevamente/app/static/app.js` línea 878 — eliminar el comentario `// Nota: la carga del paquete completo desde OCI es responsabilidad de Story 3.3.` tras la implementación.
- `nuevamente/app/routers/adaptar.py` líneas 280–302 — el endpoint `GET /historial` ya existe y no se modifica, solo se agrega el nuevo endpoint de detalle inmediatamente debajo.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/infra/oci.py` — AGREGAR `get_object(self, object_name: str) -> bytes`: llama `self._client.get_object(namespace_name=self._namespace, bucket_name=self._bucket_name, object_name=object_name)` y retorna `response.data.content`. Agregar log DEBUG con namespace, bucket y object_name.
- [x] `nuevamente/services/storage.py` — AGREGAR `get_paquete(self, objeto_id: str) -> dict | None`: best-effort síncrono. Si no `_enabled`, retorna `None`. Llama `self._client.get_object(objeto_id)`, decodifica los bytes como UTF-8, parsea JSON y retorna el dict. En cualquier excepción: loguea ERROR con `objeto_id` y el error, retorna `None`.
- [x] `nuevamente/app/routers/adaptar.py` — AGREGAR `GET /historial/{objeto_id_encoded}` después del endpoint `GET /historial` existente: decodifica el path param con `urllib.parse.unquote`, llama `await asyncio.to_thread(storage_service.get_paquete, objeto_id)`, si el resultado es `None` retorna `JSONResponse(status_code=404, content={"detail": "Paquete no encontrado."})`, si no retorna `JSONResponse(status_code=200, content={"resultado": paquete})`.
- [x] `nuevamente/app/static/app.js` — AGREGAR event delegation en `renderHistorial()` (o en la inicialización): sobre `sidebarList`, listener `click` y `keydown` (Enter/Space) que detecta `.hist-item` como target o ancestor. Leer `dataset.objetoId` del elemento. Llamar `loadPaqueteFromHistorial(objetoId)`.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `loadPaqueteFromHistorial(objetoId)`: mostrar `progressPanel` con mensaje "Cargando paquete desde historial..."; hacer `fetch(`${API_BASE}/historial/${encodeURIComponent(objetoId)}`)`. En éxito (200): llamar `hideProgress()`, `showResult({ status: 'completed', resultado: data.resultado })`. En fallo (404 u otro): llamar `hideProgress()`, `showErrorPanel('No se pudo cargar el paquete del historial.')`.

**Acceptance Criteria:**
- Given paquetes persistidos en OCI, when el usuario carga la interfaz, then la barra lateral muestra la lista de generaciones con formato, perfil y fecha.
- Given un item en la lista del historial, when el usuario hace click en él, then aparece el panel de progreso mientras se descarga el paquete y luego se renderiza en el área principal usando el renderer del formato correspondiente (Flashcards, Quiz, Tutorial, Resumen o Guión).
- Given OCI deshabilitado o el objeto eliminado, when el usuario hace click en un item del historial, then se muestra el panel de error con un mensaje descriptivo en español.
- Given no existen generaciones anteriores, when la barra lateral carga, then muestra el estado vacío con mensaje indicativo (comportamiento preexistente validado).
- Given cualquier item del historial es accesible por teclado (tabindex="0" ya en el HTML), when el usuario presiona Enter o Espacio sobre el item, then se dispara la misma carga que con el click.

## Implementation Notes

- `infra/oci.py`: Agregado `get_object()` al final de `OCIStorageClient`. Patrón consistente con `upload_object()` y `list_objects()` — sin captura de excepciones, propaga al llamante.
- `services/storage.py`: Agregado `get_paquete()` best-effort con `_enabled` guard. Parseo: `json.loads(bytes.decode('utf-8'))`. Todos los errores retornan `None` con log ERROR.
- `routers/adaptar.py`: Endpoint `GET /historial/{objeto_id_encoded:path}` usa `:path` para soportar slashes en el object name. `urllib.parse.unquote` en Python lado servidor. `asyncio.to_thread` preserva el patrón async del proyecto. `None` → 404.
- `app.js`: `initHistorialInteractivity()` registra event delegation sobre `sidebarList` (elemento estático capturado en `DOMContentLoaded`). Patrón idéntico a `initQuizInteractivity()`. `loadPaqueteFromHistorial()` llama `stopPolling()` primero (fix BH-1), luego usa `encodeURIComponent` para el `objeto_id`, llama `showResult({status: 'completed', resultado: data.resultado})` reutilizando el dispatcher de Story 3.2 sin modificaciones.
- Verificación: `uv run python -c "from nuevamente.app.main import app; print('app ok')"` → `app ok` ✓

## Spec Change Log

## Review Triage Log

- Finding BH-1: Polling activo sobrevive al click en historial — verdict: `medium` — `loadPaqueteFromHistorial` no llamaba `stopPolling()`. Si el usuario hace click en historial durante un polling activo, el intervalo sigue corriendo y `showResult/showErrorPanel` del polling sobreescribe el resultado del historial. Patched: se agregó `stopPolling()` como primera línea de `loadPaqueteFromHistorial`.
- Finding BH-2: `response.data.content` incorrecto en OCI — verdict: `false` — En el base_client del SDK OCI (línea 790), para `response_type="stream"`, `deserialized_data = response` donde `response` es el objeto `requests.Response`. `.content` es la propiedad estándar de `requests.Response` que lee el cuerpo completo como `bytes`. Correcto.
- Finding BH-3: Path traversal via `objeto_id` arbitrario — verdict: `false` — OCI maneja aislamiento por namespace+bucket configurado. El acceso queda confinado al bucket de la aplicación. No hay traversal entre buckets.
- Finding EC-1: `data.resultado` undefined en `showResult` — verdict: `false` — `showResult` tiene `const resultado = data.resultado || {}` en la primera línea. Si `data.resultado` es undefined, `resultado = {}`. Todos los accesos posteriores usan `|| {}` y `|| []`. No hay NPE.
- Finding EC-4: Doble-click concurrente en dos items distintos — verdict: `low` — Dos fetches paralelos, el último sobreescribe la UI. Impacto cosmético; requeriría estado adicional para cerrar. Rechazado: poco probable en uso real y fix excede una corrección directa.
- Finding VG-1: Sin tests automatizados para nuevos endpoints Python — verdict: `low` / defer — Patrón pre-existente del proyecto (VG-1 defer en Story 3.2). `get_paquete()`, `get_object()` y el endpoint no tienen tests unitarios.

## Design Notes

**Delegación a `showResult()`:** El endpoint retorna `{"resultado": <paquete>}`. El JS llama `showResult({ status: 'completed', resultado: data.resultado })`. `showResult` ya extrae `resultado`, detecta el formato y despacha al renderer correcto. No hay duplicación de lógica.

**Encoding del `objeto_id`:** Los object names tienen el formato `paquetes/{uuid}_{perfil}_{formato}_{ts}.json`. La barra (`/`) se URL-encode como `%2F`. FastAPI con un path param normal (`/{objeto_id_encoded}`) captura solo hasta el primer `/`; usar `path` type: `@router.get("/historial/{objeto_id_encoded:path}")` para soportar slashes anidados.

**Event delegation para hist-items:** Los items del historial son generados dinámicamente por `renderHistorial()`. Registrar el listener sobre el contenedor estático `sidebarList` (ya capturado en `DOMContentLoaded`) usando event delegation, como se hace en `initQuizInteractivity()` para quiz y flashcard.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.app.main import app; print('app ok')"` — expected: `app ok`

**Manual checks:**
- Iniciar con `uv run uvicorn nuevamente.app.main:app --reload` y abrir `http://localhost:8000`.
- Generar un paquete (cualquier formato); verificar que 2 segundos después el historial se recarga y muestra el nuevo item.
- Click en el item del historial: el paquete se renderiza en el área principal con el renderer correcto.
- Con OCI deshabilitado (`OCI_BUCKET_NAME` vacío): la sidebar muestra "Sin generaciones aún" y el endpoint `GET /api/v1/historial` retorna `{"generaciones": []}`.
