
- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-retrieval-contextualizado-agente-investigador-rag.md`
  summary: Agregar tests unitarios formales para infra/llm.py, services/retrieval.py y pipeline/nodes/retrieve.py
  evidence: El proyecto no tiene directorio tests/ desde Story 1.1; issue pre-existente no causado por este story. Un directorio tests/ con pytest cubriria el fast-path, el full-coverage con mocks, el piso de cobertura y el PipelineError.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-evaluacion-de-fidelidad-agente-critico-revisor.md`
  summary: Agregar tests unitarios para services/evaluation.py (evaluate_fidelity y helpers)
  evidence: El proyecto no tiene suite de tests propios; la logica pura de _serialize_generated_content y _build_source_text fue verificada inline pero carece de cobertura automatica. Pre-existente al cambio; deberia cerrarse en una story de calidad.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-ensamblado-del-paquete-educativo-y-grafo-langgraph.md`
  summary: Agregar tests formales para la logica de retry en draft_node (retorno de retry_count+1) y para el router _should_retry del grafo LangGraph.
  evidence: El proyecto no tiene suite de tests (pre-existente al cambio); la logica fue verificada inline pero no queda cubierta por un test automatico registrado. Mismo patron que Finding 6 de Story 1.5.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-7-api-rest-y-endpoint-de-adaptacion.md`
  summary: Sin validación de tamaño máximo de archivo en el endpoint POST /api/v1/adaptar
  evidence: El epic-1-context.md establece el límite de hardware (1GB RAM, OCPU 1), y el objetivo de <2min para hasta 1000 líneas, pero no especifica un límite explícito de bytes en el upload. Un archivo muy grande podría saturar la RAM antes de que el pipeline lo procese. La validación debería hacerse antes de leer los bytes completos (usando archivo.size o leyendo en chunks).
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-almacenamiento-de-documentos-fuente-en-oci.md`
  summary: Sin test automatizado para StorageService.upload_documento_fuente y su integración en POST /adaptar
  evidence: El proyecto no tiene suite de tests (pre-existente al cambio); la verificación es manual con uv run python -c ..., patrón establecido desde Epic 1. Si upload_documento_fuente_async se eliminara del handler, nada fallaría automáticamente. Debería cerrarse en una story de calidad con pytest.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-2-almacenamiento-de-paquetes-educativos-en-oci.md`
  summary: Sin tests unitarios permanentes para upload_paquete_educativo y su integración en _run_pipeline
  evidence: El proyecto no tiene suite de tests (pre-existente al cambio); la verificación es manual con uv run python -c ..., patrón establecido desde Epic 1. Debería cerrarse en una story de calidad con pytest y mocks del SDK OCI.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-upload-de-documentos-y-configuracion-de-parametros.md`
  summary: Parsing de object_name con rsplit es frágil si futuros enums incluyen underscore en perfil o formato
  evidence: BH-1 — Los enums actuales (Perfil, FormatoPedagogico) no contienen underscores, así que no hay defecto hoy. Si en el futuro se agrega un valor como "Lider_Tecnico", el rsplit("_", 3) producirá una lista con más de 4 partes y el objeto será omitido silenciosamente. Mitigación: cambiar el nombre del objeto en OCI para usar un separador alternativo (e.g. "|") o incluir un índice fijo.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-upload-de-documentos-y-configuracion-de-parametros.md`
  summary: Sin test automatizado para GET /historial con OCI habilitado (con objetos reales en bucket)
  evidence: VG-1 — Solo se verificó el caso OCI deshabilitado (retorna lista vacía). El caso con OCI habilitado requiere un bucket real o mocks del SDK que el proyecto aún no tiene. Pre-existente al cambio; mismo patrón que Epics 1 y 2.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-generacion-con-feedback-de-progreso-y-visualizacion-de-resul.md`
  summary: Agregar ARIA live region para anunciar feedback de selección en Quiz Interactivo a usuarios de lector de pantalla
  evidence: BH-4 — Los botones de opción del Quiz no tienen `aria-live="polite"` ni actualización de `aria-disabled`/`aria-pressed` al ser seleccionados. El feedback visual (colores correcto/incorrecto + justificación) no es perceptible sin visión. Cosmético para MVP; debería cerrarse en una story de accesibilidad.
- source_spec: `_bmad-output/implementation-artifacts/spec-3-2-generacion-con-feedback-de-progreso-y-visualizacion-de-resul.md`
  summary: Sin tests automatizados para los renderers de formato pedagógico (renderFlashcards, renderQuiz, etc.)
  evidence: VG-1 — Patrón pre-existente del proyecto (verificación manual). Los renderers son funciones puras que retornan HTML; serían fáciles de cubrir con pruebas de snapshot en Jest o similar. Debería cerrarse en una story de calidad con suite de tests JS.
