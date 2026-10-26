# Epic 2 Context: Persistencia en OCI Object Storage

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Integrar OCI Object Storage (Always Free) como capa de persistencia para los documentos fuente y los paquetes educativos generados. Esto cubre el requisito obligatorio del hackathon (OCI), y aporta trazabilidad entre input y output. Los uploads son **best-effort**: nunca bloquean el flujo principal ni la respuesta al usuario.

## Stories

- Story 2.1: Almacenamiento de Documentos Fuente en OCI
- Story 2.2: Almacenamiento de Paquetes Educativos en OCI

## Requirements & Constraints

- Los uploads a OCI son best-effort: si fallan por timeout, error de red u otro motivo, el pipeline continúa normalmente y el error se loguea con contexto suficiente.
- El cliente OCI se configura exclusivamente mediante variables de entorno / `~/.oci/config`; las credenciales nunca se hardcodean.
- Variables de configuración ya disponibles en `nuevamente/config.py` (Settings): `oci_bucket_name`, `oci_namespace`, `oci_compartment_id`, `oci_config_file`, `oci_config_profile`.
- La dependencia `oci` (SDK oficial, ~2.187.x) debe estar declarada en `pyproject.toml`.
- El SDK OCI es síncrono; debe envolverse en `asyncio.to_thread` si se llama desde contexto async.
- Los objetos se identifican con el `document_id` (UUID) para garantizar unicidad y trazabilidad.

## Technical Decisions

- **Estructura de archivos prevista en la arquitectura:**
  - `nuevamente/infra/oci.py` — cliente OCI Object Storage (init, upload, list, download).
  - `nuevamente/services/storage.py` — lógica de negocio de persistencia (best-effort wrapper).
- **Integración con el pipeline:** el upload del documento fuente ocurre en `app/routers/adaptar.py` justo antes de lanzar el pipeline (o dentro del pipeline en un nodo dedicado si así lo decide el implementador). La arquitectura muestra el upload como "fire-and-forget" desde la API (`API->OCI: Upload (fire-and-forget)`).
- **Estado en `NuevaMenteState`:** ya existe el campo `oci_upload_status: dict` en el state del grafo (pipeline/state.py) para registrar el resultado del upload.
- **Identificación de objetos:** usar `document_id` (UUID de la tarea) como nombre base del objeto en OCI; agregar extensión/sufijo apropiado (`{document_id}.pdf`, `{document_id}.txt`, etc.).
- **Patron de dependencias:** `services/storage.py` → `infra/oci.py` → SDK `oci`. El router puede importar directamente `storage.py`.

## Cross-Story Dependencies

- Story 2.1 (documentos fuente) debe completarse antes de Story 2.2 para tener el cliente OCI (`infra/oci.py`) y el wrapper best-effort (`services/storage.py`) reutilizables.
- Story 3.3 (Historial) depende de que los paquetes estén almacenados en OCI con metadatos listables (Story 2.2).
