---
title: 'Hybrid Local-First Storage & OCI Sync'
type: 'feature'
created: '2026-10-25'
status: 'completed'
baseline_commit: '92b30f922122914f6c56b5205e75c2ecb081b509'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-2-context.md
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** 
1. **Pérdida de acceso a la cuenta OCI:** El sistema actual delega exclusivamente en OCI Object Storage la persistencia de los documentos fuente y paquetes educativos. Al no contar con credenciales OCI activas (o estar la cuenta suspendida/inaccesible), el servicio se deshabilita (`_enabled = False`), impidiendo que el usuario guarde su historial de adaptaciones, dejando la barra lateral vacía (`GET /historial` retorna lista vacía) y deshabilitando la consulta de generaciones previas (`GET /historial/{id}` retorna 404).
2. **Requisito de conservación de OCI:** No se debe suprimir la integración con OCI. El sistema debe ser un diseño híbrido: si las variables de OCI están configuradas en `.env` y operativas, deben funcionar tal como se implementó en la Épica 2.
3. **Persistencia Local Completa:** En ausencia de conexión a OCI, el sistema debe persistir en disco local tanto el documento fuente original subido (`documentos/`) como el paquete educativo JSON (`paquetes/`), manteniendo la misma convención de nombres y claves.
4. **Sincronización Transparente y Sin Duplicados:** Si en el futuro se restauran las credenciales OCI en el `.env`, el sistema debe subir a OCI todo el historial local acumulado de forma automática en segundo plano. La consulta del historial (`GET /historial`) debe fusionar los registros locales y remotos deduplicando por identificador de objeto, de modo que ningún elemento aparezca repetido y la experiencia del usuario sea continua.

**Approach:** 
1. **Estructura Local Espejada (`data/storage/`):**
   - Configurar una ruta base local `local_storage_dir` (por defecto `data/storage`) en `Settings`.
   - Replicar la jerarquía de prefijos de OCI:
     - `data/storage/documentos/<document_id>.<extension>`
     - `data/storage/paquetes/<document_id>_<perfil>_<formato>_<timestamp>.json`
   - Mantener el identificador canónico `objeto_id` idéntico al de OCI (ej. `paquetes/...json` y `documentos/...`).
   - Agregar `data/storage/` a `.gitignore` para evitar versionar documentos de usuario o JSONs generados.
2. **Almacenamiento Local-First con Best-Effort OCI:**
   - `upload_documento_fuente`: Escribe inmediatamente los bytes en `data/storage/documentos/`. Si OCI está habilitado, envía además el objeto a OCI de forma segura.
   - `upload_paquete_educativo`: Guarda el archivo JSON en `data/storage/paquetes/` con codificación UTF-8, y persiste el título en `data/history_metadata.json`. Si OCI está habilitado, realiza el upload hacia el bucket de OCI.
   - Si OCI está deshabilitado o falla, la operación retorna exitosa en virtud de la persistencia local garantizada (`status: "ok"`).
3. **Listado de Historial Unificado y Desduplicado (`list_paquetes`):**
   - Escanear los paquetes disponibles en el directorio local `data/storage/paquetes/`.
   - Si OCI está habilitado, obtener el listado remoto de OCI.
   - Combinar ambos conjuntos en un diccionario indexado por `objeto_id`.
   - Como el nombre del archivo contiene `<document_id>_<perfil>_<formato>_<timestamp>.json`, el `objeto_id` es único e inmutable en el tiempo. Si un paquete existe tanto en disco local como en OCI, se unifica en una única entrada (cero duplicados).
   - Incorporar el título generado por la IA desde `history_metadata.json` (o del propio contenido) y ordenar cronológicamente de más reciente a más antiguo.
4. **Descarga Optimizada (`get_paquete`):**
   - Intentar leer primero desde disco local `data/storage/{objeto_id}` (<1ms, sin latencia de red).
   - Si no existe localmente pero OCI está habilitado, descargarlo desde OCI y guardar una copia local en caché para lecturas futuras.
5. **Sincronización en Segundo Plano hacia OCI (`sync_pending_to_oci`):**
   - Al iniciar la aplicación (en el evento `lifespan` de FastAPI) o al detectarse OCI disponible, verificar los archivos locales que no existen en OCI.
   - Subir los documentos y paquetes pendientes a OCI en background sin bloquear la respuesta de la API ni la interfaz web.

## Boundaries & Constraints

**Always:**
- Mantener 100% intacta la compatibilidad con el frontend (`app.js`, `index.html`, `style.css`). El cliente web no requiere modificaciones.
- Mantener intacto el contrato de los endpoints: `POST /adaptar`, `GET /adaptar/{task_id}`, `GET /historial`, y `GET /historial/{objeto_id_encoded:path}`.
- Conservar la clase `OCIStorageClient` en `nuevamente/infra/oci.py` sin alteraciones destructivas.
- Ignorar `data/storage/` en `.gitignore`.
- Asegurar que la creación de directorios sea idempotente (`mkdir(parents=True, exist_ok=True)`).
- Desduplicar el historial estrictamente por la clave canónica `objeto_id`.
- Soportar codificación UTF-8 estricta sin escape ASCII (`ensure_ascii=False`) para tildes y caracteres en español.

**Never:**
- No eliminar el código de OCI ni desestimar su configuración futura.
- No permitir que un fallo de red o credenciales inválidas en OCI interrumpa la persistencia local o el flujo de generación.
- No generar elementos duplicados en la respuesta de `GET /historial`.
- No realizar operaciones de I/O de disco bloqueantes directamente sobre el event loop principal de FastAPI en rutas críticas (usar `asyncio.to_thread` donde proceda).

## I/O & Edge-Case Matrix

| Escenario | Entrada / Estado | Salida / Comportamiento Esperado | Manejo de Excepción / Fallback |
| :--- | :--- | :--- | :--- |
| **Generación sin OCI** (estado actual) | Documento subido + parámetros; `OCI_BUCKET_NAME` vacío o no configurado. | Documento fuente guardado en `data/storage/documentos/`. Paquete guardado en `data/storage/paquetes/`. Retorna `status: "ok"` y `objeto_id`. | Si hay error de disco local (permisos/espacio), loguea en nivel ERROR y reporta fallo controlado. |
| **Generación con OCI habilitado** | Variables OCI presentes y válidas en `.env`. | Documento y paquete se guardan en local y se suben exitosamente a OCI. | Si OCI falla por timeout o error 5xx, el paquete queda preservado en local y se agenda para sincronización posterior. |
| **Listar historial solo local** | `GET /historial`; OCI deshabilitado. | Retorna lista de generaciones leyendo `data/storage/paquetes/` con metadatos y títulos. | Si el directorio local aún no existe, retorna lista vacía `{"generaciones": []}` sin lanzar error. |
| **Listar historial híbrido (Local + OCI)** | `GET /historial`; OCI activo con paquetes remotos y locales. | Retorna la unión de paquetes locales y remotos desduplicados por `objeto_id`. Orden descendente por `fecha_epoch`. | Paquetes presentes en ambas ubicaciones aparecen exactamente 1 vez. |
| **Descarga de paquete presente en local** | `GET /historial/{objeto_id}` | Lee directamente desde `data/storage/{objeto_id}` y retorna JSON 200 inmediatamente. | Evita llamadas de red innecesarias a OCI. |
| **Descarga de paquete presente solo en OCI** | `GET /historial/{objeto_id}` no encontrado en disco local, pero OCI habilitado. | Descarga el objeto desde OCI, lo guarda localmente en `data/storage/{objeto_id}` y lo entrega en JSON 200. | Si tampoco existe en OCI, retorna HTTP 404 con mensaje claro. |
| **Sincronización en arranque** | Servidor inicia con credenciales OCI válidas y archivos pendientes en `data/storage/`. | Tarea de fondo compara e inicia subida de documentos y paquetes locales no presentes en el bucket. | Errores de red individuales se registran en log sin abortar la aplicación ni interrumpir las peticiones entrantes. |
| **Parsing de nombres de archivo no estándar** | Archivo ajeno o temporal en `data/storage/paquetes/`. | Se ignora el archivo con advertencia en log sin afectar el resto del listado. | Robustez de regex/splitting ante formatos inválidos. |

</frozen-after-approval>

## Code Map

- `.gitignore`
  - Añadir regla `data/storage/` para que los documentos y paquetes locales nunca se commiteen al repositorio.

- `nuevamente/config.py`
  - Añadir campo `local_storage_dir: Path = Path("data/storage")` en `Settings` con valor por defecto.

- `nuevamente/services/storage.py`
  - Incorporar soporte para persistencia local:
    - Métodos para asegurar la existencia de directorios (`documentos/` y `paquetes/`).
    - Métodos locales `_save_local_documento` y `_save_local_paquete`.
    - Métodos locales `_list_local_paquetes` y `_get_local_paquete`.
  - Actualizar `upload_documento_fuente`:
    - Guardar siempre localmente primero.
    - Si OCI está activo, subir a OCI.
    - Retornar siempre `status: "ok"` si al menos la persistencia local tuvo éxito.
  - Actualizar `upload_paquete_educativo`:
    - Guardar localmente en `data/storage/paquetes/`.
    - Actualizar `history_metadata.json` con el título.
    - Si OCI está activo, subir a OCI.
    - Retornar `status: "ok"` con `objeto_id`.
  - Actualizar `list_paquetes`:
    - Leer lista local y lista OCI (si está activo).
    - Unificar en un `dict` por `objeto_id` para garantizar **cero duplicados**.
    - Ordenar por `fecha_epoch` descendente.
  - Actualizar `get_paquete`:
    - Buscar en local primero.
    - Si no está, buscar en OCI y cachear localmente.
  - Implementar `sync_pending_to_oci`:
    - Revisar archivos locales y subirlos a OCI si aún no están en el bucket.

- `nuevamente/app/main.py`
  - En el `lifespan` del servidor, si OCI está habilitado, lanzar `sync_pending_to_oci` en segundo plano con `asyncio.create_task`.

- `nuevamente/app/routers/adaptar.py`
  - Mantener endpoints intactos; verificar que la respuesta de `upload_paquete_educativo` refleje el almacenamiento local/híbrido.

- `tests/test_storage.py`
  - Actualizar y ampliar la suite de tests:
    - Test de guardado y lectura local cuando OCI está deshabilitado.
    - Test de desduplicación de paquetes presentes en local y en OCI.
    - Test de fallback local a OCI.
    - Test de sincronización `sync_pending_to_oci`.

## Tasks & Acceptance

**Execution:**
- [x] `.gitignore` -- Agregar `data/storage/` a los patrones ignorados.
- [x] `nuevamente/config.py` -- Agregar configuración de `local_storage_dir`.
- [x] `nuevamente/services/storage.py` -- Implementar persistencia local, unión desduplicada en `list_paquetes`, lectura local-first en `get_paquete` y sincronización en background `sync_pending_to_oci`.
- [x] `nuevamente/app/main.py` -- Añadir trigger de sincronización en background en el startup del servidor.
- [x] `tests/test_storage.py` -- Agregar pruebas unitarias automatizadas con pytest para el comportamiento local-only, híbrido y sincronización.

**Verification:**
1. Con OCI deshabilitado (`.env` sin credenciales OCI o bucket vacío):
   - Subir un documento y generar una adaptación pedagógica.
   - Verificar que el archivo original se almacena en `data/storage/documentos/<id>.<ext>`.
   - Verificar que el paquete educativo se almacena en `data/storage/paquetes/<id>_<perfil>_<formato>_<timestamp>.json`.
   - Verificar que la barra lateral (`GET /historial`) muestra inmediatamente la nueva generación con su título de IA, perfil, formato y fecha.
   - Hacer clic en el ítem del historial: debe cargarse y visualizarse correctamente desde el archivo local sin errores.
2. Comportamiento híbrido y desduplicación:
   - Crear un mock con paquetes en disco local y los mismos paquetes en OCI más otros adicionales.
   - Verificar que `list_paquetes()` devuelve la lista sin ningún elemento repetido.
3. Sincronización hacia OCI:
   - Ejecutar `sync_pending_to_oci` con OCI activo y verificar que los archivos locales no presentes en OCI se suben al bucket.
4. Ejecutar la suite de tests completa:
   - `uv run pytest tests/` pasando al 100%.
