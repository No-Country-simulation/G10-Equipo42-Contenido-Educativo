---
title: 'Story 1.3: Retrieval Contextualizado (Agente Investigador RAG)'
type: 'feature'
created: '2026-09-25'
status: 'done'
route: 'dispatch'
baseline_commit: '873e97e5e345fdb958e9deaa02db5f21c118890a'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El pipeline de NuevaMente no puede seleccionar los chunks mas relevantes del indice FAISS segun el perfil, formato y nicho de la solicitud. Sin este paso, el Agente Redactor recibiria todos los chunks del documento (inviable para documentos grandes) o ninguno, lo que impide la generacion de contenido educativo fidelizado al documento fuente.

**Approach:** Implementar el servicio de retrieval (`services/retrieval.py`) con estrategia dual: fast-path cuando el total de tokens en chunks es <= 50K (todos los chunks pasan directamente), y full-coverage para documentos mas grandes (query synthesis via LLM + similarity search en FAISS + piso de cobertura por seccion + chunk budget). El nodo LangGraph `retrieve_node` es un thin wrapper que lee el state y escribe `retrieved_chunks`. La factory de LLM (`infra/llm.py`) encapsula `init_chat_model` para reutilizacion en stories posteriores.

## Boundaries & Constraints

**Always:**
- Usar `init_chat_model` de `langchain.chat_models` con `settings.llm_model_name` para instanciar el LLM (patron actual segun doc LangChain).
- La estrategia se elige comparando `sum(len(c["page_content"]) for c in chunks) / 4` contra `settings.fast_path_token_threshold` (ya en Settings = 50_000).
- Fast-path: retornar todos los chunks sin llamar al LLM ni a FAISS.
- Full-coverage: (1) construir section_map compacto (heading + primera oracion de cada seccion), (2) query synthesis -- 1 llamada al LLM con HumanMessage describiendo perfil/formato/nicho, (3) similarity_search en FAISS con k=settings.retrieval_k por cada query, (4) deduplicar por chunk_index, (5) aplicar piso de cobertura: para cada seccion del section_map sin chunks recuperados, agregar el chunk con menor chunk_index dentro de esa seccion, (6) aplicar chunk budget = settings.retrieval_k * 2 chunks maximos.
- Cargar el indice FAISS con load_index(document_id, embeddings, settings) ya implementado en infra/vectorstore.py. Si el indice no existe, lanzar PipelineError.
- Respetar regla de dependencia: services/ importa de infra/ y core/, no de pipeline/.
- Type hints completos, sin emojis, logging con logging.getLogger(__name__).
- infra/llm.py expone get_llm(settings) -> BaseChatModel usando init_chat_model.

**Never:**
- No reimplementar la logica de carga de indice -- reutilizar infra/vectorstore.load_index.
- No modificar NuevaMenteState en pipeline/state.py -- el campo retrieved_chunks: list[dict[str, Any]] ya existe.
- No agregar dependencias externas mas alla de las ya declaradas en pyproject.toml.
- No implementar logica de generacion de contenido (eso es Story 1.4).
- No modificar services/rag.py ni infra/embeddings.py.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| Doc pequeno (<= 50K tokens aprox) | chunks con total chars <= 200K | retrieved_chunks = todos los chunks, sin llamada LLM ni FAISS | -- |
| Doc grande (> 50K tokens aprox) | chunks con total chars > 200K, section_map no vacio | queries LLM generadas, FAISS consultado, piso de cobertura aplicado, retrieved_chunks <= chunk_budget | -- |
| Doc grande, seccion sin cobertura | Una seccion del section_map sin chunks recuperados por FAISS | El chunk representativo de esa seccion se agrega forzosamente | -- |
| Indice FAISS no encontrado | document_id sin indice en disco | PipelineError con mensaje descriptivo | caller registra error, pipeline falla |
| section_map vacio (PDF/TXT grande) | chunks > 50K tokens, section_map=[] | Full-coverage sin piso de cobertura; queries LLM + FAISS + budget | -- |

</frozen-after-approval>

## Code Map

- `nuevamente/config.py` -- Settings.fast_path_token_threshold (int=50_000), Settings.retrieval_k (int=10), Settings.llm_model_name (str), Settings.llm_temperature, Settings.llm_max_retries. Solo lectura.
- `nuevamente/core/exceptions.py` -- PipelineError ya definida. Lanzar si indice FAISS no existe.
- `nuevamente/pipeline/state.py` -- NuevaMenteState: leer chunks, section_map, document_id, perfil, formato, nicho; escribir retrieved_chunks. No modificar.
- `nuevamente/infra/embeddings.py` -- get_embeddings(settings) -> VoyageAIEmbeddings. Reutilizar sin cambios.
- `nuevamente/infra/vectorstore.py` -- load_index(document_id, embeddings, settings) -> FAISS | None. Reutilizar sin cambios.
- `nuevamente/infra/llm.py` -- CREAR: get_llm(settings: Settings) -> BaseChatModel usando init_chat_model(settings.llm_model_name, temperature=settings.llm_temperature, max_retries=settings.llm_max_retries).
- `nuevamente/services/retrieval.py` -- CREAR: retrieve_chunks(document_id, chunks, section_map, perfil, formato, nicho, settings) -> list[dict].
- `nuevamente/pipeline/nodes/retrieve.py` -- CREAR: retrieve_node(state: NuevaMenteState) -> dict thin wrapper.
- `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar export de retrieve_node.
- `langchain.chat_models.init_chat_model` -- patron actual; acepta formato provider:model como google_genai:gemini-2.0-flash-lite.
- `langchain_core.messages.HumanMessage` -- para construir el prompt de query synthesis.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/infra/llm.py` -- CREAR factory get_llm(settings: Settings) -> BaseChatModel. Usar init_chat_model con settings.llm_model_name, temperature=settings.llm_temperature, max_retries=settings.llm_max_retries. Importar BaseChatModel de langchain_core.language_models.
- [x] `nuevamente/services/retrieval.py` -- CREAR funcion publica retrieve_chunks(document_id: str, chunks: list[dict], section_map: list[dict], perfil: str, formato: str, nicho: str, settings: Settings) -> list[dict]. Incluir: calculo de tokens estimados y decision fast-path/full-coverage; funcion privada _fast_path(chunks) que retorna todos los chunks; funcion privada _full_coverage(document_id, chunks, section_map, perfil, formato, nicho, settings) con query synthesis (1 llamada LLM con HumanMessage), FAISS search, dedup por chunk_index, piso de cobertura y chunk budget.
- [x] `nuevamente/pipeline/nodes/retrieve.py` -- CREAR retrieve_node(state: NuevaMenteState) -> dict[str, Any]. Extrae campos del state, instancia Settings(), llama retrieve_chunks, retorna {"retrieved_chunks": ...}.
- [x] `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar from nuevamente.pipeline.nodes.retrieve import retrieve_node y exportar en __all__.

**Acceptance Criteria:**
- Given chunks con total chars <= 200K, when retrieve_chunks(...) se llama, then retorna todos los chunks sin modificacion y sin llamar al LLM ni a FAISS.
- Given chunks con total chars > 200K e indice FAISS existente, when retrieve_chunks(...) se llama, then el LLM genera queries de synthesis (1 llamada) y FAISS retorna chunks relevantes; el total de retrieved_chunks no supera settings.retrieval_k * 2.
- Given full-coverage con una seccion del section_map sin chunks recuperados, when se aplica el piso de cobertura, then al menos un chunk de esa seccion aparece en retrieved_chunks.
- Given un document_id sin indice FAISS en disco, when retrieve_chunks(...) se llama en full-coverage path, then se lanza PipelineError.
- Given section_map=[] con chunks > 50K tokens, when retrieve_chunks(...) se llama, then ejecuta full-coverage sin piso de cobertura y respeta chunk budget.
- Given el nodo retrieve_node con un state valido que tiene chunks y section_map, when se ejecuta, then el state resultante tiene retrieved_chunks como lista no vacia.

## Implementation Notes

- init_chat_model desde langchain.chat_models es el patron actual recomendado (doc models.mdx). El model name google_genai:gemini-2.0-flash-lite en config.py sigue el formato provider:model que init_chat_model acepta directamente.
- Para query synthesis: construir un HumanMessage con el section_map compacto (heading + primera oracion) y los parametros de personalizacion. Pedir al LLM queries separadas por newlines (sin structured output -- parsing trivial con splitlines()).
- Estimacion de tokens: total_chars / 4 es heuristica conservadora para vocabulario en espanol/ingles.
- Chunk budget = settings.retrieval_k * 2 = 20 chunks por defecto. Aplicar al final como retrieved_sorted[:chunk_budget] ordenado por chunk_index.
- Deduplicacion: usar chunk_index del metadata como clave de set. Mantener orden ascendente.
- Para el piso de cobertura: para cada seccion sin representacion, buscar en chunks el primero (menor chunk_index) cuyo parent_heading coincide con el heading de la seccion.
- El nodo retrieve_node instancia Settings() internamente, igual que ingest_node. Patron consistente.

## Spec Change Log

## Review Triage Log

- Finding 1: `covered_headings` incluye string vacio de chunks sin heading — verdict: `false` — evidence: el guard `if not heading` en `_apply_coverage_floor:323` ya skipea secciones con heading="" antes de chequear la cobertura; el string vacio en `covered_headings` no afecta secciones con heading real. En `build_section_map` los headings extraidos de regex nunca son vacios.
- Finding 2: `doc.metadata.get("chunk_index", -1)` podia insertar entry con key=-1 en retrieved_by_index si un doc de FAISS carecia de chunk_index — verdict: `low` — evidence: ocurre solo con indices construidos externamente (nunca con ingest_node). Route: **patch** (aplicado: cambiado a sentinel None + continue).
- Finding 3: `n_queries = max(3, len(section_map))` sin cap podia generar muchas llamadas FAISS en docs con muchas secciones — verdict: `low` — evidence: con 20 secciones habria 20 queries y 20 llamadas similarity_search, impactando latencia en hardware 1 OCPU. Route: **patch** (aplicado: `min(max(3, len(section_map)), 8)`).
- Finding 4: Sin tests unitarios formales en el repo para los nuevos modulos — verdict: `low` deferred — evidence: el proyecto no tiene directorio tests/ desde Story 1.1 (issue pre-existente). Route: **defer**.


## Design Notes

Separacion de responsabilidades:
- infra/llm.py encapsula init_chat_model -- si el proveedor cambia, solo este archivo cambia. Mismo patron que infra/embeddings.py.
- services/retrieval.py contiene la logica de decision fast-path/full-coverage, query synthesis y piso de cobertura.
- pipeline/nodes/retrieve.py es un thin adapter sin logica de negocio.

Query synthesis prompt (estructura):

```
Eres un asistente de recuperacion de informacion.
Mapa de secciones del documento:
{section_map_compacto}

Genera {n_queries} queries de busqueda semantica para recuperar contenido relevante,
distribuidas por todo el documento, adaptadas para un destinatario "{perfil}"
que quiere aprender en formato "{formato}" sobre el nicho "{nicho}".
Retorna una query por linea, sin numeracion ni prefijos.
```

## Verification

**Commands:**
- `uv run python -c "from nuevamente.infra.llm import get_llm; print('llm OK')"` -- expected: imprime "llm OK"
- `uv run python -c "from nuevamente.services.retrieval import retrieve_chunks; print('retrieval OK')"` -- expected: imprime "retrieval OK"
- `uv run python -c "from nuevamente.pipeline.nodes.retrieve import retrieve_node; print('node OK')"` -- expected: imprime "node OK"
- `uv run python -c "from nuevamente.pipeline.nodes import retrieve_node, ingest_node; print('nodes OK')"` -- expected: imprime "nodes OK"
