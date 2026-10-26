---
title: 'Story 3.1: Upload de Documentos y Configuración de Parámetros'
type: 'feature'
created: '2026-09-26'
baseline_commit: '9af912d'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** NuevaMente no tiene interfaz de usuario — el sistema sólo es accesible vía herramientas API externas (curl, Swagger), lo que excluye a usuarios no técnicos y no cumple el requisito del hackathon de interfaz interactiva.

**Approach:** Crear la interfaz web base (`app/static/index.html` + CSS + JS) servida por FastAPI via `StaticFiles`, con area de upload de documentos (drag-and-drop + click), controles de parámetros (Perfil, Formato, Nicho), selección de documentos ya procesados desde OCI, y endpoint `GET /api/v1/historial` que lista paquetes anteriores. La historia implementa el formulario de entrada completo; el ciclo de generación y los renderers de formato se implementan en Story 3.2.

## Boundaries & Constraints

**Always:**
- HTML/CSS/JS vanilla — sin frameworks JS (React, Vue, etc.) ni CSS frameworks (Tailwind). Renderización client-side pura.
- Los archivos estáticos van en `nuevamente/app/static/`. FastAPI los monta via `StaticFiles`. La URL raíz `/` retorna `index.html`.
- Perfil: 4 opciones fijas (Principiante, Junior, Senior, Lider Tecnico/Arquitecto). Formato: 5 opciones fijas. Nicho: 4 predefinidos + campo texto libre. Las opciones deben coincidir exactamente con los valores de los enums de `core/models.py`.
- Los tres parámetros son obligatorios; el botón de lanzar generación queda deshabilitado hasta que se completen documento + 3 parámetros. Validación client-side con indicación visual de campos faltantes.
- Upload acepta exclusivamente PDF, .md y .txt (misma restricción que el backend). Validación client-side por extensión.
- El endpoint `GET /api/v1/historial` retorna `{"generaciones": [...]}` — si OCI está deshabilitado o lista vacía, retorna lista vacía sin error.
- `OCIStorageClient` se extiende con `list_objects(prefix)` — propaga excepciones al caller (`StorageService`), que las captura con best-effort (retorna lista vacía en error).
- Logging sin emojis, type hints completos, Python 3.12. No modificar `core/`, `pipeline/`, `services/ingestion.py`, `services/generation.py`, `services/rag.py`.

**Never:**
- No usar SSR ni templates Jinja2 para la UI. La interfaz es 100% estática.
- No agregar autenticación ni estado de sesión.
- No implementar los renderers de formato (Flashcards, Quiz, etc.) — eso es Story 3.2.
- No implementar la carga de paquetes por historial (get_object desde OCI) — eso es Story 3.3.
- No bloquear el servidor si OCI no está disponible al listar el historial.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------| 
| Usuario sube PDF válido | Archivo .pdf seleccionado | Nombre del archivo mostrado, botón habilitado si params completos | — |
| Archivo de tipo no soportado | Archivo .docx o .xlsx | Archivo rechazado con mensaje indicativo, sin enviar al backend | Validación client-side |
| Parámetros incompletos al lanzar | Documento cargado pero sin perfil/formato | Botón deshabilitado, campos faltantes resaltados visualmente | — |
| GET /historial con OCI habilitado | OCI accesible, prefijo "paquetes/" con objetos | Lista de generaciones con nombre documento, perfil, formato, fecha | — |
| GET /historial con OCI deshabilitado | `oci_bucket_name` vacío | `{"generaciones": []}` sin error | — |
| GET /historial con OCI con error | OCI configurado pero no accesible | `{"generaciones": []}` + log ERROR | Excepción capturada en StorageService |

</frozen-after-approval>

## Code Map

- `nuevamente/app/main.py` — MODIFICAR. Agregar montaje de `StaticFiles` y endpoint GET `/` que retorna `FileResponse("nuevamente/app/static/index.html")`. Importar `StaticFiles` de `starlette.staticfiles`, `FileResponse` de `fastapi.responses`.
- `nuevamente/app/static/index.html` — CREAR. HTML base de la SPA: layout con sidebar izquierda (historial) y área principal (upload + parámetros + botón). Carga `style.css` y `app.js`.
- `nuevamente/app/static/style.css` — CREAR. Sistema de diseño completo: dark mode, variables CSS, tipografía (Google Fonts: Inter), colores curados, animaciones de micro-interacción, responsive layout.
- `nuevamente/app/static/app.js` — CREAR. Lógica client-side: drag-and-drop upload, validación de formulario, envío `POST /api/v1/adaptar`, polling `GET /api/v1/adaptar/{task_id}`, carga de historial desde `GET /api/v1/historial`. Story 3.2 extenderá este archivo con los renderers.
- `nuevamente/app/routers/adaptar.py` — MODIFICAR. Agregar endpoint `GET /historial` que llama a `storage_service.list_paquetes()` y retorna `{"generaciones": [...]}`.
- `nuevamente/services/storage.py` — MODIFICAR. Agregar método `list_paquetes() -> list[dict]` con best-effort: si deshabilitado, retorna `[]`; si error OCI, loguea y retorna `[]`. Construye metadata de cada item parseando el nombre del objeto `paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json`.
- `nuevamente/infra/oci.py` — MODIFICAR. Agregar `list_objects(prefix: str, limit: int = 100) -> list[str]`: llama `self._client.list_objects(namespace, bucket, prefix=prefix, limit=limit)` y retorna lista de `object_name`. Propaga excepciones.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/infra/oci.py` — AGREGAR método `list_objects(prefix, limit=100) -> list[str]`: usa `self._client.list_objects(namespace_name=self._namespace, bucket_name=self._bucket_name, prefix=prefix, limit=limit)` y retorna `[obj.name for obj in response.data.objects]`.
- [x] `nuevamente/services/storage.py` — AGREGAR método `list_paquetes() -> list[dict]`: si `_enabled` es False, retorna `[]`. Llama `self._client.list_objects("paquetes/")`. Parsea cada `object_name` con regex o split para extraer `document_id`, `perfil`, `formato`, `timestamp`. Retorna lista de dicts con claves `objeto_id`, `perfil`, `formato`, `fecha_epoch`, `fecha_iso`. En `except Exception` loguea ERROR y retorna `[]`.
- [x] `nuevamente/app/routers/adaptar.py` — AGREGAR endpoint `GET /historial`: llama `storage_service.list_paquetes()` y retorna `JSONResponse({"generaciones": result})`.
- [x] `nuevamente/app/main.py` — MODIFICAR: agregar `app.mount("/static", StaticFiles(directory=static_dir), name="static")` y `@app.get("/") async def root() -> FileResponse` que retorna el `index.html`. Calcular `static_dir` como `Path(__file__).parent / "static"`.
- [x] `nuevamente/app/static/style.css` — CREAR: sistema de diseño completo con dark mode, variables CSS (colores, tipografía, espaciado), animaciones, layout sidebar+main, componentes (upload-zone, form-controls, button-primary, spinner).
- [x] `nuevamente/app/static/index.html` — CREAR: estructura HTML5 semántica. Layout: `<aside>` (historial) + `<main>` (upload, parámetros, botón). Carga Inter desde Google Fonts, `style.css` y `app.js`.
- [x] `nuevamente/app/static/app.js` — CREAR: módulo JS con funciones para drag-and-drop, validación de form, envío `POST /api/v1/adaptar` con `FormData`, polling, carga de historial y render de lista de generaciones. Estructura modular con funciones nombradas (sin código suelto salvo el `DOMContentLoaded`).

**Acceptance Criteria:**
- Given la aplicación FastAPI iniciada, when accedo a la URL raíz `/` en el navegador, then recibo el `index.html` con status 200 y la interfaz web es visible con área de upload y controles de parámetros.
- Given la interfaz cargada, when arrastro o selecciono un archivo PDF/md/txt, then el nombre del archivo aparece en la UI con feedback visual de confirmación.
- Given un archivo .docx seleccionado, when el usuario intenta cargarlo, then la interfaz rechaza el archivo con un mensaje indicativo sin enviarlo al backend.
- Given la interfaz con un documento cargado y los tres parámetros completos, when el usuario hace click en "Generar", then se envía POST /api/v1/adaptar con los datos correctos (multipart/form-data con `archivo`, `perfil_destinatario`, `formato_salida`, `nicho_sector`).
- Given algún parámetro obligatorio sin completar, when el usuario intenta lanzar la generación, then el botón está deshabilitado o muestra indicación visual de campos faltantes.
- Given `GET /api/v1/historial` con OCI deshabilitado, when se llama al endpoint, then retorna `{"generaciones": []}` con status 200.
- Given documentos previamente procesados existentes en OCI, when la interfaz carga, then la barra lateral muestra la lista de generaciones anteriores con perfil, formato y fecha.

## Implementation Notes

- `nuevamente/infra/oci.py`: Agregado `list_objects(prefix, limit=100)`. Usa `self._client.list_objects()` del SDK OCI y retorna `[obj.name for obj in response.data.objects]`. Propaga excepciones al caller.
- `nuevamente/services/storage.py`: Agregado `list_paquetes()` con best-effort. Parsea `object_name` con `rsplit("_", 3)` para extraer los 4 componentes. Ordena por `fecha_epoch` descendente. Importa `datetime` a nivel de módulo.
- `nuevamente/app/routers/adaptar.py`: Agregado `GET /historial` → `listar_historial()`. Delega en `storage_service.list_paquetes()`.
- `nuevamente/app/main.py`: Importados `Path`, `FileResponse`, `StaticFiles`. Endpoint `GET /` con `include_in_schema=False`. `StaticFiles` montado en `/static` después del router.
- `nuevamente/app/static/style.css`: Sistema de diseño con fondo `#0f0f1a`, acento violeta-azul, Inter via Google Fonts, glassmorphism en cards, animaciones de progreso indeterminado y fadeIn.
- `nuevamente/app/static/index.html`: HTML5 semántico con `<aside>` (historial) y `<main>` (upload + parámetros + botón + paneles de estado). IDs únicos para todos los elementos interactivos.
- `nuevamente/app/static/app.js`: Módulo `'use strict'` con funciones nombradas. `escapeHtml()` en todos los renders de datos del servidor para prevenir XSS. Polling con `setInterval` / `clearInterval`. La función `showResult()` es un placeholder que Story 3.2 reemplazará con renderers por formato.
- Verificaciones ejecutadas y exitosas:
  - `list_objects OK: True` ✓
  - `list_paquetes deshabilitado OK: True` ✓
  - `static exists: True` ✓
  - `GET /api/v1/historial` → 200 `{"generaciones": []}` ✓
  - `GET /` → 200 `text/html` ✓
- Nota de diseño: el endpoint `GET /` usa `include_in_schema=False` para no contaminar la documentación OpenAPI. `StaticFiles` va después del router para que `/api/v1/*` tenga precedencia.

## Spec Change Log

## Review Triage Log

- Finding BH-1: `rsplit("_", 3)` frágil si perfil/formato tienen underscore — verdict: `low` — Los enums actuales (`Perfil`, `FormatoPedagogico`) no contienen underscores. El riesgo es teórico para valores futuros. Route: defer.
- Finding BH-2: `clearFile()` no llama `hideFileError()` — verdict: `low` — Verificado: `clearFile()` en `app.js` no invoca `hideFileError()`. Si el usuario selecciona un archivo inválido (error visible) y luego limpia con el botón ✕, el panel de error queda visible con el formulario vacío. Route: patch.
- Finding BH-3: Clase `error` prematura en selects vacíos al seleccionar archivo — verdict: `low` — Verificado: `handleFileSelected()` llama `updateGenerateButton()` que aplica `classList.toggle('error', !selectPerfil.value)`. Si el usuario sube un archivo antes de completar los selects, los campos vacíos se marcan en rojo antes de que intente enviar. Confuso UX. Route: patch.
- Finding BH-4: `selectNicho.classList.toggle('error')` cuando nicho es `'__custom__'` — verdict: `false` — Cuando `selectNicho.value === '__custom__'`, el código toma el branch `if (selectNicho.value === '__custom__') { inputNichoCustom.classList.toggle('error', !nichoVal) }`, nunca el `else`. La clase error no se añade incorrectamente al select.
- Finding BH-5: `StaticFiles` falla si el directorio no existe — verdict: `false` — Comportamiento fail-fast deseable. Los archivos estáticos son parte del commit y siempre deben estar presentes. No es un defecto.
- Finding BH-6: Polling sin timeout máximo — verdict: `low` — rechazado. El fix requeriría agregar un contador de intentos, un botón de cancelar o un timeout configurable — complejidad que supera la gravedad para un MVP. El usuario puede recargar la página.
- Finding EC-1: `int(ts_str)` con timestamp no-entero — verdict: `false` — El `except Exception` dentro del loop de parsing captura `ValueError` y lo loguea como WARNING, omitiendo el objeto. Cubierto correctamente.
- Finding VG-1: No hay test del endpoint `/historial` con OCI habilitado — verdict: `low` — Pre-existente: el proyecto no tiene suite de tests automatizados. El patrón establecido es verificación manual. Route: defer.


## Design Notes

El diseño de `index.html`/`style.css`/`app.js` debe ser **profesional y moderno**: dark mode con fondo `#0f0f1a` (deep navy), acento principal en gradiente violeta-azul (`#7c3aed` → `#2563eb`), tipografía Inter (Google Fonts), glassmorphism en cards, animaciones suaves (transition 200-300ms).

El área de upload debe ser visualmente prominente con borde punteado animado y cambio de estado al arrastrar (drag-over). Los selects de parámetros deben tener estilo custom (no el browser default). El botón de "Generar" tiene gradiente y efecto hover/active.

Parsing de `object_name` para extraer metadata del historial:
```
# Formato: paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json
# Ejemplo: paquetes/abc-123-def_Principiante_Flashcards_1727000000.json
# Split por "_" desde el final: timestamp=-1, formato=-2, perfil=-3, document_id=todo lo anterior
parts = object_name.replace("paquetes/", "").replace(".json", "").rsplit("_", 3)
# parts = [document_id, perfil, formato, timestamp]
```
Nota: `perfil` puede contener espacios o "/" (e.g. "Lider Tecnico/Arquitecto") — pero al subir el paquete en Story 2.2 se usa el valor tal cual. El parsing debe usar `rsplit("_", 3)` para tomar los últimos 3 underscores como separadores, dejando el document_id (UUID sin underscores) como primera parte.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.app.main import app; routes = [r.path for r in app.routes]; print('routes OK:', '/' in routes and '/historial' not in routes)"` — expected: `routes OK: True` (el /historial está bajo el router /api/v1)
- `uv run python -c "from nuevamente.infra.oci import OCIStorageClient; print('list_objects OK:', hasattr(OCIStorageClient, 'list_objects'))"` — expected: `list_objects OK: True`
- `uv run python -c "from nuevamente.services.storage import StorageService; from nuevamente.config import Settings; svc = StorageService(Settings(oci_bucket_name='')); r = svc.list_paquetes(); print('list_paquetes deshabilitado OK:', r == [])"` — expected: `list_paquetes deshabilitado OK: True`
- `uv run python -c "from pathlib import Path; p = Path('nuevamente/app/static'); print('static exists:', p.exists() and (p/'index.html').exists() and (p/'style.css').exists() and (p/'app.js').exists())"` — expected: `static exists: True`

**Manual checks (if no CLI):**
- Abrir `http://localhost:8000` en el navegador: debe mostrar la interfaz con sidebar de historial, área de upload y formulario de parámetros.
- Arrastrar un PDF: debe mostrar el nombre del archivo y habilitar el botón si los demás params están completos.
- Intentar con un .docx: debe rechazarlo con mensaje de error client-side.
