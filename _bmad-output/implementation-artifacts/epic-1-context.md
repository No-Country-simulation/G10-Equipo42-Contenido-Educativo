# Epic 1 Context: Pipeline de Transformacion de Documentos

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

El usuario puede enviar un documento tecnico via API y recibir un paquete educativo JSON estructurado, adaptado a su perfil, formato pedagogico y nicho, con evaluacion de fidelidad al documento fuente. Este epic constituye el nucleo completo del sistema: ingestion, RAG, multi-agente con LangGraph, structured output via Pydantic, y API REST funcional. Cubre los requisitos obligatorios 1-5 del hackathon.

## Stories

- Story 1.1: Fundacion del Proyecto y Configuracion
- Story 1.2: Ingestion de Documentos y Pipeline RAG
- Story 1.3: Retrieval Contextualizado (Agente Investigador RAG)
- Story 1.4: Generacion de Contenido Adaptado (Agente Redactor Pedagogico)
- Story 1.5: Evaluacion de Fidelidad (Agente Critico/Revisor)
- Story 1.6: Ensamblado del Paquete Educativo y Grafo LangGraph
- Story 1.7: API REST y Endpoint de Adaptacion

## Requirements & Constraints

### Funcionales

- Aceptar documentos PDF, Markdown (.md) y texto plano (.txt). Retornar HTTP 415 para formatos no soportados, HTTP 422 si el archivo esta vacio o no se puede extraer texto.
- Extraer contenido textual independientemente del formato de entrada.
- Segmentar texto en chunks semanticos con chunking recursivo por caracteres con overlap configurable. Cada chunk incluye metadata (posicion, encabezado padre).
- Generar embeddings con Voyage AI y almacenarlos en FAISS (index.faiss + index.pkl en disco local). Busqueda por similitud con k configurable.
- Tres parametros de personalizacion validados con Pydantic: perfil_destinatario (4 opciones enum), formato_salida (5 opciones enum), nicho_sector (texto libre o predefinido).
- Patron asincrono: POST retorna 202 + task_id, GET para polling de status. Pipeline ejecuta en background.
- Estrategia RAG dual: fast-path (doc <= 50K tokens, todos los chunks) vs full-coverage (section map + query synthesis + stratified retrieval con piso de cobertura).
- Redactor genera contenido con `llm.with_structured_output()` usando Gemini 3.5 Flash Lite. 5 formatos pedagogicos diferenciados.
- Critico evalua fidelidad (anclaje_fuente_score 0.0-1.0). Loop de correccion con max 1 reintento si score < 0.7.
- Paquete educativo JSON con secciones: status, metadatos, contenido_adaptado, evaluacion_calidad. Schema validado con Pydantic.
- Cada formato tiene subestructura definida: Flashcards (frente/dorso/pista), Quiz (pregunta/opciones/respuesta/justificacion), Tutorial (paso/titulo/explicacion/ejemplo), Resumen Ejecutivo (seccion/contenido/implicacion), Guion de Clase (fase/contenido/duracion/notas).
- Endpoint POST /api/v1/adaptar (multipart/form-data). Documentacion OpenAPI auto-generada en /docs.
- Errores retornan JSON con status "error", codigo y mensaje descriptivo en espanol.

### No Funcionales

- Hardware: 1GB RAM + 1 OCPU (OCI Always Free). No exceder ~800MB RSS. Concurrencia 1.
- Tiempo de respuesta end-to-end < 2 minutos para documentos de hasta 1000 lineas.
- Costo $0: todo dentro de Always Free OCI + tiers gratuitos de Gemini 3.5 Flash Lite y Voyage AI.
- Logging a stdout/stderr con contexto suficiente para diagnosticar fallos.
- Modulos separados con config externalizada, type hints completos (Python 3.12), Pydantic para schemas.
- Estilo profesional: sin abuso de emojis, el proyecto debe verse profesional.

## Technical Decisions

### Estructura del Proyecto

Layout modular con regla de dependencia unidireccional: `app/` -> `pipeline/` -> `services/` -> `infra/`; `core/` es transversal (importado por todos, no importa a nadie).

```
nuevamente/
├── app/              # FastAPI: main.py, routers/adaptar.py, static/
├── core/             # Dominio puro: schemas.py, models.py, exceptions.py
├── pipeline/         # LangGraph: graph.py, state.py, nodes/
├── services/         # Logica de negocio: ingestion.py, rag.py, generation.py, storage.py
├── infra/            # Adaptadores: embeddings.py, vectorstore.py, llm.py, oci.py
├── config.py         # pydantic-settings centralizado
data/faiss_indexes/   # Indices por documento (gitignored)
```

### Estado del Grafo LangGraph

`NuevaMenteState(TypedDict)` con campos inmutables (input: document_id, raw_text, file_name, perfil, formato, nicho), intermedios (chunks, section_map, retrieved_chunks, generated_content), control de flujo (review_result, retry_count) y output (educational_package, oci_upload_status).

### Grafo de Procesamiento

Lineal con un conditional edge: START -> ingest -> retrieve -> draft -> review -> format_output -> END. Review puede retornar a draft si score < 0.7 y retry < 1.

### Stack

- Python 3.12, LangGraph 1.2.x, Gemini 3.5 Flash Lite, Voyage AI (voyage-4), FAISS (faiss-cpu), Pydantic v2, FastAPI, pydantic-settings, Uvicorn, OCI SDK.

### Configuracion Centralizada

`config.py` usa pydantic-settings para cargar variables de entorno: modelo LLM, modelo embeddings, parametros de chunking (tamano, overlap), credenciales OCI, rutas de indices FAISS.

## Cross-Story Dependencies

- Story 1.1 es prerequisito de todas las demas: establece la estructura, modelos de dominio, schemas y configuracion.
- Story 1.2 (ingestion + RAG indexing) es prerequisito de Story 1.3 (retrieval).
- Story 1.3 alimenta a Story 1.4 (redactor) con retrieved_chunks.
- Story 1.4 alimenta a Story 1.5 (critico) con generated_content.
- Story 1.6 integra todos los nodos en el grafo LangGraph.
- Story 1.7 expone el pipeline como API REST.
