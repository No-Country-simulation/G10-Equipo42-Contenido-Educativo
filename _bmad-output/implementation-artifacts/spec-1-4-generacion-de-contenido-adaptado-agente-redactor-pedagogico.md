---
title: 'Story 1.4: Generacion de Contenido Adaptado (Agente Redactor Pedagogico)'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'dispatch'
baseline_commit: 'a2c7618'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El pipeline de NuevaMente tiene el retrieval contextualizado implementado (Story 1.3), pero carece del nodo que transforma esos chunks recuperados en contenido educativo estructurado. Sin este agente, el estado `retrieved_chunks` en NuevaMenteState queda sin consumir y no puede generarse ningun paquete educativo.

**Approach:** Implementar el servicio de generacion (`services/generation.py`) con una funcion `generate_content(retrieved_chunks, perfil, formato, nicho, review_result, settings)` que usa `llm.with_structured_output(PaqueteSchema)` para producir directamente una instancia Pydantic del schema correspondiente al formato solicitado. El nodo LangGraph `draft_node` es un thin wrapper que lee el state, llama al servicio y escribe `generated_content` en el state. La seleccion del schema Pydantic correcto se hace via el dict `FORMATO_A_SCHEMA` ya existente en `core/schemas.py`.

## Boundaries & Constraints

**Always:**
- Usar `get_llm(settings)` de `infra/llm.py` para instanciar el LLM.
- Usar `llm.with_structured_output(SchemaClass)` donde `SchemaClass` es el modelo Pydantic seleccionado via `FORMATO_A_SCHEMA[formato]`. El resultado es una instancia Pydantic directamente.
- El prompt de generacion debe incluir: perfil, formato, nicho, y el contexto de chunks como texto concatenado. Si `review_result` no es None (reintento), incluir el feedback del Critico en el prompt.
- Respetar la regla de dependencia: `services/` importa de `infra/` y `core/`, no de `pipeline/`.
- Type hints completos, sin emojis, logging con `logging.getLogger(__name__)`.
- El campo `generated_content` en NuevaMenteState es `dict[str, Any]` -- almacenar el resultado Pydantic como `.model_dump()` para ser serializable.

**Never:**
- No implementar logica de evaluacion de fidelidad (eso es Story 1.5).
- No modificar `core/schemas.py`, `core/models.py`, `infra/llm.py`, `pipeline/state.py` ni ningun nodo ya existente.
- No agregar dependencias externas mas alla de las ya declaradas en `pyproject.toml`.
- No implementar logica de retry directamente en el servicio -- el control de retry lo gestiona el grafo LangGraph (Story 1.6); el servicio solo acepta `review_result` como contexto opcional.
- No agregar `evaluacion_calidad` real al output del Redactor -- ese campo lo completa el Critico (Story 1.5); usar valores placeholder si el schema lo requiere.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|--------------------|
| Primera generacion (sin reintento) | retrieved_chunks no vacio, review_result=None | dict con estructura del PaqueteSchema del formato, metadatos completos | -- |
| Reintento con feedback del Critico | retrieved_chunks, review_result con observaciones y score | El prompt incluye el feedback; el output refleja mayor anclaje a la fuente | -- |
| Formato "Flashcards" | perfil="Principiante", formato="Flashcards" | dict FlashcardsPaquete con items frente/dorso/pista_didactica | -- |
| Formato "Resumen Ejecutivo" | perfil="Lider Tecnico/Arquitecto", formato="Resumen Ejecutivo" | dict ResumenEjecutivoPaquete con items seccion/contenido/implicacion | -- |
| Nicho texto libre | nicho="veterinario aprendiendo a programar" | El contenido incorpora ese contexto en ejemplos y lenguaje | -- |
| Formato desconocido | formato no en FORMATO_A_SCHEMA | PipelineError con mensaje descriptivo | caller registra error |

</frozen-after-approval>

## Code Map

- `nuevamente/config.py` -- Settings: llm_model_name, llm_temperature, llm_max_retries. Solo lectura.
- `nuevamente/core/exceptions.py` -- PipelineError ya definida. Lanzar si formato no esta en FORMATO_A_SCHEMA.
- `nuevamente/core/schemas.py` -- FORMATO_A_SCHEMA dict y todos los schemas Pydantic. Solo lectura.
- `nuevamente/core/models.py` -- FormatoPedagogico, Perfil. Solo lectura.
- `nuevamente/pipeline/state.py` -- NuevaMenteState: leer retrieved_chunks, perfil, formato, nicho, review_result, retry_count; escribir generated_content. No modificar.
- `nuevamente/infra/llm.py` -- get_llm(settings) -> BaseChatModel. Reutilizar sin cambios.
- `nuevamente/services/generation.py` -- CREAR: generate_content(...) -> dict[str, Any].
- `nuevamente/pipeline/nodes/draft.py` -- CREAR: draft_node(state: NuevaMenteState) -> dict thin wrapper.
- `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar export de draft_node.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/services/generation.py` -- CREAR funcion publica `generate_content(retrieved_chunks: list[dict], perfil: str, formato: str, nicho: str, review_result: dict | None, settings: Settings) -> dict[str, Any]`. Incluir: seleccion del schema via FORMATO_A_SCHEMA[formato] (PipelineError si no existe), construccion del contexto de chunks, construccion del prompt con SystemMessage y HumanMessage, feedback opcional del Critico si review_result no es None, llamada `llm.with_structured_output(schema_class).invoke(messages)`, retorno de `resultado.model_dump()`.
- [x] `nuevamente/pipeline/nodes/draft.py` -- CREAR `draft_node(state: NuevaMenteState) -> dict[str, Any]`. Extrae campos del state, instancia Settings(), llama generate_content, retorna `{"generated_content": resultado}`.
- [x] `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar `from nuevamente.pipeline.nodes.draft import draft_node` y exportar en `__all__`.

**Acceptance Criteria:**
- Given retrieved_chunks no vacio, perfil="Principiante", formato="Flashcards", nicho="General", review_result=None, when generate_content(...) se llama, then retorna un dict deserializable como FlashcardsPaquete con items que contienen frente, dorso, pista_didactica.
- Given perfil="Lider Tecnico/Arquitecto", formato="Resumen Ejecutivo", when generate_content con el mismo documento fuente, then el contenido generado es linguistica y estructuralmente diferente al de un Principiante.
- Given review_result con observaciones (reintento), when generate_content se llama, then el prompt incluye el feedback del Critico.
- Given nicho="veterinario aprendiendo a programar", when generate_content se llama, then el contenido incorpora ese contexto.
- Given formato no en FORMATO_A_SCHEMA, when generate_content se llama, then se lanza PipelineError con mensaje descriptivo.
- Given draft_node con state valido que tiene retrieved_chunks, perfil, formato, nicho, when se ejecuta, then el state resultante tiene generated_content como dict no vacio con estructura valida del formato solicitado.
- Given cualquier combinacion valida de perfil/formato/nicho, when generate_content se llama, then `SchemaClass(**result_dict)` pasa validacion Pydantic sin errores.

## Implementation Notes

- Implementado con patron `llm.with_structured_output(schema_class).invoke(messages).model_dump()` segun doc LangChain langchain/models.mdx. El resultado es una instancia Pydantic que se serializa con `.model_dump()` para almacenarse en NuevaMenteState como `dict[str, Any]`.
- Dicts de instrucciones por perfil (`_INSTRUCCIONES_POR_PERFIL`) y por formato (`_INSTRUCCIONES_POR_FORMATO`) permiten personalizar el SystemMessage sin logica condicional compleja en la funcion principal.
- El placeholder de `evaluacion_calidad` es gestionado por el schema Pydantic de `PaqueteEducativoBase` (campo requerido). El Agente Critico (Story 1.5) sobreescribira esos valores en `format_output`. Esto es correcto: con `with_structured_output` el LLM generara valores para ese campo; Story 1.5 los reemplazara con la evaluacion real.
- `_build_context_text` incluye el `parent_heading` de cada chunk como prefijo de seccion para dar contexto estructural al LLM.
- Verificacion completada: `generation OK`, `draft OK`, `nodes OK` (imports limpios sin errores).

## Spec Change Log

## Review Triage Log

- Finding 1: Falta de normalizacion de casing en formato al consultar FORMATO_A_SCHEMA — verdict: `false` — evidence: el campo `formato` llega al nodo desde NuevaMenteState ya validado por Pydantic (FormatoPedagogico enum) en la capa API; nunca tiene casing incorrecto cuando viene del pipeline normal.
- Finding 2: Inyeccion de review_result sin sanitizacion — verdict: `false` — evidence: review_result proviene del Agente Critico del mismo pipeline (no de input externo); inyectarlo en el prompt del reintento es el comportamiento intencional del loop de correccion.
- Finding 3: Sin try/except alrededor de structured_llm.invoke — verdict: `low` — evidence: un fallo de OutputParserException propagaria sin contexto de cual formato/perfil fallo. Route: **patch** (aplicado: wrapped con PipelineError descriptivo).
- Finding 4: Context length sin verificar en retrieved_docs — verdict: `false` — evidence: Story 1.3 ya aplica chunk_budget = retrieval_k * 2 = 20 chunks antes de escribir retrieved_chunks en el state; el Redactor recibe un conjunto ya acotado.
- Finding 5: Temperatura no configurable para structured output — verdict: `false` — evidence: settings.llm_temperature se pasa a get_llm(settings) en infra/llm.py; la temperatura ya es configurable via Settings.
- Finding 6: Logging insuficiente — verdict: `false` — evidence: generate_content y draft_node loguean inicio y fin con perfil/formato/nicho/chunks count; suficiente para NFR-4. LangSmith excluido de v1.
- Finding 7: Validacion de evaluacion_calidad placeholder — verdict: `false` — evidence: no hay placeholder manual; with_structured_output obliga al LLM a producir todos los campos del schema incluyendo evaluacion_calidad; Story 1.5 sobreescribe esos valores en format_output con la evaluacion real.


## Design Notes

Patron de llamada con with_structured_output (doc langchain/models.mdx):
```python
schema_class = FORMATO_A_SCHEMA[formato]  # e.g. FlashcardsPaquete
llm = get_llm(settings)
structured_llm = llm.with_structured_output(schema_class)
result = structured_llm.invoke(messages)  # instancia Pydantic
generated_content = result.model_dump()
```

Estructura del prompt:
- SystemMessage: rol de Redactor Pedagogico especializado, instrucciones de lenguaje segun perfil (Principiante: analogias y sin jerga; Lider Tecnico: profundidad tecnica y implicaciones estrategicas), adaptacion al nicho.
- HumanMessage: contexto de chunks concatenados como texto plano (page_content de cada chunk), instruccion de generar el paquete en el formato indicado.
- Si review_result no es None: anadir al HumanMessage el feedback del Critico (score + observaciones) con instruccion explicita de mejorar fidelidad al documento fuente.

El schema Pydantic seleccionado tiene `evaluacion_calidad: EvaluacionCalidad` como campo requerido. Inicializar con placeholder (score=0.0, claridad_pedagogica="pendiente de evaluacion", observaciones="evaluacion pendiente por Agente Critico"). Story 1.5 sobreescribira este campo en el paquete final ensamblado.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.services.generation import generate_content; print('generation OK')"` -- expected: imprime "generation OK"
- `uv run python -c "from nuevamente.pipeline.nodes.draft import draft_node; print('draft OK')"` -- expected: imprime "draft OK"
- `uv run python -c "from nuevamente.pipeline.nodes import draft_node, retrieve_node, ingest_node; print('nodes OK')"` -- expected: imprime "nodes OK"
