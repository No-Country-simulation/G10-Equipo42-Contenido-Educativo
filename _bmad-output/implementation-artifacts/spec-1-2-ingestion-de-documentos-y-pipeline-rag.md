---
title: 'Story 1.2: Ingestion de Documentos y Pipeline RAG'
type: 'feature'
created: '2026-09-25'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '43eb2db'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El pipeline de NuevaMente no puede procesar documentos: no existe logica para extraer texto de PDF/Markdown/TXT, segmentarlo en chunks, generar embeddings con Voyage AI, ni indexar en FAISS. Sin este paso, ningun documento puede ser transformado en contenido educativo.

**Approach:** Implementar el servicio de ingestion (`services/ingestion.py`) que extrae texto segun el tipo de archivo, y el servicio RAG (`services/rag.py`) con su adaptador de infraestructura (`infra/vectorstore.py` e `infra/embeddings.py`) que segmenta, embede e indexa en FAISS con persistencia en disco. El nodo LangGraph `ingest` es un thin wrapper que orquesta ambos servicios y escribe los resultados en el state.

## Boundaries & Constraints

**Always:**
- Usar `RecursiveCharacterTextSplitter` de `langchain_text_splitters` con `chunk_size` y `chunk_overlap` leidos de `Settings`.
- Usar `langchain_voyageai.VoyageAIEmbeddings` con modelo leido de `Settings.embedding_model_name`.
- Persitir indice FAISS en `{faiss_index_dir}/{document_id}/` como `index.faiss` + `index.pkl` usando `FAISS.save_local` / `FAISS.load_local`.
- Si el indice ya existe en disco para ese `document_id`, cargarlo sin re-generar embeddings.
- Metadata de cada chunk: `chunk_index` (int), `parent_heading` (str, puede ser ""), `source` (file_name).
- `section_map` se construye parseando headings Markdown (`#`, `##`, etc.) del texto crudo. Para PDF y TXT, retorna lista vacia.
- Errores de formato no soportado -> `DocumentoNoSoportado`. Archivo vacio/sin texto -> `DocumentoVacio`.
- Respetar regla de dependencia: `services/` puede importar de `infra/` y `core/`, no de `pipeline/` ni `app/`.
- Type hints completos, sin emojis.

**Never:**
- No llamar al LLM en este nodo — la ingestion y el indexado son 100% deterministas (sin IA).
- No implementar logica de retrieval (eso es Story 1.3).
- No modificar `NuevaMenteState` en `pipeline/state.py` — los campos ya existen: `chunks`, `section_map`, `document_id`, `raw_text`, `file_name`.
- No agregar dependencias externas mas alla de las ya declaradas en `pyproject.toml`.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| PDF valido, nuevo | archivo .pdf con texto | `raw_text` extraido, `chunks` con metadata, `section_map`, indice FAISS guardado en disco | — |
| Markdown con headings | archivo .md con `# H1\n## H2` | `section_map` con entradas por heading, chunks con `parent_heading` correcto | — |
| TXT plano | archivo .txt | `raw_text` extraido, `section_map=[]`, chunks con `parent_heading=""` | — |
| PDF ya indexado | `document_id` con indice en disco | indice cargado sin llamar a Voyage AI | — |
| Extension no soportada | archivo .docx | `DocumentoNoSoportado` | llamador retorna HTTP 415 |
| Archivo vacio / sin texto extraible | .pdf sin texto (imagen) | `DocumentoVacio` | llamador retorna HTTP 422 |
| Chunk unico (doc muy corto) | texto de 50 chars | 1 chunk, `section_map` segun formato | — |

</frozen-after-approval>

## Code Map

- `nuevamente/core/exceptions.py` — `DocumentoNoSoportado`, `DocumentoVacio`, `PipelineError` ya definidas. Reutilizar sin cambios.
- `nuevamente/pipeline/state.py` — `NuevaMenteState` ya tiene `raw_text`, `file_name`, `document_id`, `chunks: list[dict]`, `section_map: list[dict]`. Solo lectura aqui.
- `nuevamente/config.py` — `Settings.chunk_size`, `chunk_overlap`, `embedding_model_name`, `voyage_api_key`, `faiss_index_dir`. Instanciar con `Settings()`.
- `nuevamente/infra/embeddings.py` — CREAR: factory `get_embeddings(settings) -> VoyageAIEmbeddings`.
- `nuevamente/infra/vectorstore.py` — CREAR: `save_index(faiss_vs, document_id, settings)` y `load_index(document_id, embeddings, settings) -> FAISS | None`.
- `nuevamente/services/ingestion.py` — CREAR: `extract_text(file_bytes, file_name) -> str` y `build_section_map(raw_text, file_name) -> list[dict]`.
- `nuevamente/services/rag.py` — CREAR: `ingest_document(document_id, raw_text, file_name, settings) -> dict` orquestando chunk+embed+index.
- `nuevamente/pipeline/nodes/ingest.py` — CREAR: nodo LangGraph `ingest_node(state) -> dict` thin wrapper.
- `langchain_text_splitters.RecursiveCharacterTextSplitter` — splitter principal con `add_start_index=True`.
- `langchain_voyageai.VoyageAIEmbeddings` — embeddings con modelo de Settings.
- `langchain_community.vectorstores.FAISS` — `from_documents()`, `save_local()`, `load_local()`.
- `pypdf.PdfReader` — extraccion de texto PDF pagina por pagina.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/infra/embeddings.py` — Crear factory `get_embeddings(settings: Settings) -> VoyageAIEmbeddings`. Inicializar con `voyage_api_key` y `model`. Sin logica adicional.
- [x] `nuevamente/infra/vectorstore.py` — Crear `save_index(faiss_vs: FAISS, document_id: str, settings: Settings) -> None` (crea directorio, llama `save_local`) y `load_index(document_id: str, embeddings, settings: Settings) -> FAISS | None` (retorna `None` si directorio no existe; carga con `allow_dangerous_deserialization=True`).
- [x] `nuevamente/services/ingestion.py` — Crear `extract_text(file_bytes: bytes, file_name: str) -> str` (branch por extension: .pdf via pypdf, .md/.txt decode directo) y `build_section_map(raw_text: str, file_name: str) -> list[dict]` (parsea headings Markdown con regex `^#{1,6} .+`; para no-.md retorna `[]`). Lanzar `DocumentoNoSoportado` si extension desconocida, `DocumentoVacio` si texto vacio tras extraccion.
- [x] `nuevamente/services/rag.py` — Crear `ingest_document(document_id: str, raw_text: str, file_name: str, settings: Settings) -> dict`. Flujo: (1) `load_index` si indice existe -> derivar chunks desde `faiss_vs.docstore._dict.values()`; (2) si no, split con `RecursiveCharacterTextSplitter`, enriquecer metadata con `chunk_index` y `parent_heading`, `FAISS.from_documents`, `save_index`; (3) retornar `{"chunks": [...], "section_map": build_section_map(...)}`).
- [x] `nuevamente/pipeline/nodes/ingest.py` — Crear `ingest_node(state: NuevaMenteState) -> dict`. Extrae `raw_text`, `file_name`, `document_id` del state. Llama `ingest_document`. Retorna dict parcial para merge en state.
- [x] `nuevamente/pipeline/nodes/__init__.py` — Exportar `ingest_node`.

**Acceptance Criteria:**
- Given un archivo .pdf con texto, when `extract_text(bytes, "doc.pdf")` se llama, then retorna string no vacio.
- Given un archivo .md con headings `# Intro\n## Setup`, when `build_section_map(texto, "doc.md")` se llama, then retorna lista con `{"heading": "Intro", "level": 1}` y `{"heading": "Setup", "level": 2}`.
- Given `raw_text` de 5000 chars, when `ingest_document` se llama por primera vez, then el indice se persiste en `data/faiss_indexes/{document_id}/index.faiss` y `index.pkl`.
- Given el mismo `document_id` con indice existente, when `ingest_document` se llama de nuevo, then el indice se carga desde disco (log "cargando indice desde disco").
- Given extension `.docx`, when `extract_text(bytes, "doc.docx")` se llama, then se lanza `DocumentoNoSoportado`.
- Given PDF sin texto extraible, when la extraccion retorna string vacio, then `ingest_document` lanza `DocumentoVacio`.
- Given el nodo `ingest_node` con un state valido, when se ejecuta, then el state resultante tiene `chunks` (list no vacia) y `section_map` (list).

## Implementation Notes

- `FakeEmbeddings(size=1024)` de `langchain_core.embeddings` usados para tests sin credenciales — confirma que el flujo completo chunk→FAISS→persist→load funciona correctamente.
- `FAISS.docstore._dict.values()` funciona correctamente en langchain-community>=0.4 para recuperar `Document` objects del indice cargado.
- Para `.txt` y `.pdf`, `build_section_map` retorna `[]` correctamente (sin headings Markdown).
- `_find_parent_heading` asume que `section_map` esta ordenado por `start_offset` ascendente (garantizado por el parseado secuencial de regex).
- El nodo `ingest_node` instancia `Settings()` internamente — patron simple para este nodo; stories posteriores pueden inyectar settings si necesario.
- Fallback de decodificacion en `_extract_from_text`: utf-8 primero, luego latin-1.

- `RecursiveCharacterTextSplitter`: usar `create_documents([raw_text], metadatas=[{"source": file_name}])`. Luego iterar chunks para enriquecer con `chunk_index` y `parent_heading` usando `start_index` del metadata y el resultado de `build_section_map`.
- Para `parent_heading`: buscar el ultimo heading en `section_map` cuyo `start_offset` sea <= `chunk.metadata["start_index"]`.
- `FAISS.load_local` requiere `allow_dangerous_deserialization=True` — seguro porque el indice fue generado localmente por nosotros mismos.
- El nodo LangGraph retorna dict parcial; LangGraph hace merge automatico con el state actual (patron estandar TypedDict).
- Logging con `logging.getLogger(__name__)`: info al inicio con `document_id` y `file_name`; info al final con conteo de chunks generados o cargados.

## Spec Change Log

## Review Triage Log

- Finding 1: `infra/vectorstore.py` tipo `VoyageAIEmbeddings` demasiado concreto en `load_index` — verdict: `low` — evidence: FAISS.load_local acepta cualquier `Embeddings`; usar base type desacopla el modulo del proveedor concreto. Route: **patch** (aplicado: cambiado a `langchain_core.embeddings.Embeddings`).
- Finding 2: `services/rag.py` importacion de FAISS dentro de `_build_index` — verdict: `low` — evidence: inconsistente con el resto del modulo; importacion tardía sin beneficio. Route: **patch** (aplicado: movida al nivel de modulo).
- Finding 3: `services/rag.py` importacion de `Document` sin uso — verdict: `low` — evidence: `from langchain_core.documents import Document` importado pero nunca usado directamente. Route: **patch** (aplicado: removido).
- Finding 4: `services/ingestion.py` `import os` dentro de funcion `_get_extension` — verdict: `low` — evidence: patron inconsistente con el resto del modulo. Route: **patch** (aplicado: movido al nivel de modulo).
- Finding 5: Doble check `DocumentoVacio` en `ingest_document` y `extract_text` — verdict: `false` — evidence: `ingest_document` puede ser llamada directamente con `raw_text` sin pasar por `extract_text`; el check defensivo es correcto y no redundante.
- Finding 6: Error generico si indice FAISS corrupto en disco — verdict: `low` — rejected: agregar manejo de error especifico requeriria guards adicionales; fuera del alcance de este story (fallo esperado del sistema de archivos).
- Finding 7: `_find_parent_heading` asume `section_map` ordenado — verdict: `false` — evidence: garantizado por `finditer` que recorre el texto en orden ascendente de offset; documentado en Implementation Notes.
- Finding 8: `get_embeddings` se instancia incluso en cache hit — verdict: `false` — evidence: `VoyageAIEmbeddings` no valida credenciales en construccion (solo al llamar a embed_*); la instancia es necesaria para pasar a `load_index` que la usa para reconstruir el retriever FAISS.


## Design Notes

Separacion de responsabilidades:
- `infra/embeddings.py` e `infra/vectorstore.py` encapsulan LangChain/FAISS — si el proveedor cambia, solo estos archivos cambian.
- `services/ingestion.py` es puro Python sin deps de LangChain — mas facil de testear.
- `services/rag.py` orquesta; el nodo LangGraph es un thin adapter que solo conecta el state con el service.

Para derivar chunks de un indice ya cargado:
```python
docs = list(faiss_vs.docstore._dict.values())
chunks = [{"page_content": d.page_content, **d.metadata} for d in docs]
```

## Verification

**Commands:**
- `uv sync` -- expected: sin errores de dependencias
- `uv run python -c "from nuevamente.infra.embeddings import get_embeddings; print('embeddings OK')"` -- expected: imprime "embeddings OK"
- `uv run python -c "from nuevamente.infra.vectorstore import save_index, load_index; print('vectorstore OK')"` -- expected: imprime "vectorstore OK"
- `uv run python -c "from nuevamente.services.ingestion import extract_text, build_section_map; print('ingestion OK')"` -- expected: imprime "ingestion OK"
- `uv run python -c "from nuevamente.services.rag import ingest_document; print('rag OK')"` -- expected: imprime "rag OK"
- `uv run python -c "from nuevamente.pipeline.nodes.ingest import ingest_node; print('node OK')"` -- expected: imprime "node OK"
