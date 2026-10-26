---
title: 'Story 1.5: Evaluacion de Fidelidad (Agente Critico/Revisor)'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'dispatch'
baseline_commit: '6492c19d47090ad4d523fc3b898f4b054772713e'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El pipeline tiene el Agente Redactor (Story 1.4) que produce `generated_content`, pero ese contenido queda sin evaluacion de fidelidad. El campo `evaluacion_calidad` en el paquete tiene valores placeholder y no hay ningun nodo que determine si el contenido generado esta suficientemente anclado al documento fuente antes de ensamblarlo.

**Approach:** Implementar el servicio de evaluacion (`services/evaluation.py`) con una funcion `evaluate_fidelity(generated_content, retrieved_chunks, settings)` que usa `llm.with_structured_output(EvaluacionCalidad)` para que el LLM evalue cuantitativamente el anclaje al fuente (score 0.0-1.0) y retorne observaciones concretas. El nodo LangGraph `review_node` es un thin wrapper que lee el state, llama al servicio y escribe `review_result` (dict serializable de `EvaluacionCalidad`) en el state. El conditional edge y el control de retry (max 1) se implementan en Story 1.6; este nodo solo produce la evaluacion.

## Boundaries & Constraints

**Always:**
- Usar `get_llm(settings)` de `infra/llm.py` para instanciar el LLM.
- Usar `llm.with_structured_output(EvaluacionCalidad)` donde `EvaluacionCalidad` ya esta definida en `core/schemas.py`. El resultado es una instancia Pydantic; retornar `.model_dump()` para que sea serializable en NuevaMenteState.
- El prompt del Critico debe incluir: el contenido generado (del `generated_content`) y el contexto del documento fuente (chunks recuperados). Debe instruir al LLM a asignar `anclaje_fuente_score` (0.0-1.0) segun que tan fielmente el contenido cita o refleja el documento, con `observaciones` especificas y accionables cuando el score < 0.7.
- Respetar la regla de dependencia: `services/` importa de `infra/` y `core/`, no de `pipeline/`.
- Type hints completos, sin emojis, logging con `logging.getLogger(__name__)`.
- El campo `review_result` en NuevaMenteState es `dict[str, Any]` — almacenar el resultado como `.model_dump()`.

**Never:**
- No implementar logica de retry ni conditional edge — eso es Story 1.6.
- No modificar `core/schemas.py`, `core/models.py`, `infra/llm.py`, `pipeline/state.py` ni ningun nodo ya existente (ingest, retrieve, draft).
- No agregar dependencias externas mas alla de las ya declaradas en `pyproject.toml`.
- No implementar la logica de ensamblado del paquete educativo final — eso es Story 1.6.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| Primera evaluacion (buen anclaje) | generated_content valido, retrieved_chunks no vacios | review_result dict con anclaje_fuente_score >= 0.7, claridad_pedagogica positiva | -- |
| Evaluacion con anclaje bajo | generated_content con info no respaldada por chunks | review_result con score < 0.7, observaciones especificas y accionables | -- |
| Chunks vacios | retrieved_chunks = [] | review_result con score bajo y observacion indicando falta de contexto fuente | -- |
| generated_content vacio | generated_content = {} | PipelineError con mensaje descriptivo del Critico | caller registra error |
| Fallo del LLM | LLM lanza excepcion | PipelineError con agente="critico" y detalle del error original | -- |

</frozen-after-approval>

## Code Map

- `nuevamente/config.py` -- Settings: llm_model_name, llm_temperature, llm_max_retries. Solo lectura.
- `nuevamente/core/exceptions.py` -- PipelineError(mensaje, *, agente, detalle). Lanzar si generated_content esta vacio o el LLM falla.
- `nuevamente/core/schemas.py` -- EvaluacionCalidad (anclaje_fuente_score: float, claridad_pedagogica: str, observaciones: str). Solo lectura; usarla como schema de with_structured_output.
- `nuevamente/pipeline/state.py` -- NuevaMenteState: leer generated_content, retrieved_chunks; escribir review_result. No modificar.
- `nuevamente/infra/llm.py` -- get_llm(settings) -> BaseChatModel. Reutilizar sin cambios. Patron identico al usado en generation.py.
- `nuevamente/services/evaluation.py` -- CREAR: evaluate_fidelity(generated_content, retrieved_chunks, settings) -> dict[str, Any].
- `nuevamente/pipeline/nodes/review.py` -- CREAR: review_node(state: NuevaMenteState) -> dict thin wrapper.
- `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar export de review_node.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/services/evaluation.py` -- CREAR funcion publica `evaluate_fidelity(generated_content: dict[str, Any], retrieved_chunks: list[dict[str, Any]], settings: Settings) -> dict[str, Any]`. Incluir: validacion de generated_content no vacio (PipelineError si vacio), helper privado `_build_source_text(chunks)` analogo al de generation.py, serializacion del generated_content a texto legible via helper `_serialize_generated_content(generated_content)`, prompt con SystemMessage (rol Critico) y HumanMessage (contenido + fuente), llamada `llm.with_structured_output(EvaluacionCalidad).invoke(messages)`, wrapped en try/except que lanza PipelineError con agente="critico", retorno de `resultado.model_dump()`.
- [x] `nuevamente/pipeline/nodes/review.py` -- CREAR `review_node(state: NuevaMenteState) -> dict[str, Any]`. Extrae generated_content y retrieved_chunks del state, instancia Settings(), llama evaluate_fidelity, retorna `{"review_result": resultado}`. Logging de inicio y fin con document_id y score del resultado.
- [x] `nuevamente/pipeline/nodes/__init__.py` -- ACTUALIZAR: agregar `from nuevamente.pipeline.nodes.review import review_node` y exportar en `__all__`.

**Acceptance Criteria:**
- Given generated_content con estructura valida de un formato pedagogico y retrieved_chunks no vacios, when evaluate_fidelity se llama, then retorna dict deserializable como EvaluacionCalidad con anclaje_fuente_score en [0.0, 1.0], claridad_pedagogica string no vacio, y observaciones string no vacio.
- Given generated_content con informacion no respaldada por los chunks, when evaluate_fidelity se llama, then el score es < 0.7 y las observaciones mencionan las discrepancias especificas.
- Given generated_content = {} (vacio), when evaluate_fidelity se llama, then se lanza PipelineError con mensaje descriptivo.
- Given review_node con state valido que tiene generated_content y retrieved_chunks, when se ejecuta, then el state resultante tiene review_result con keys anclaje_fuente_score, claridad_pedagogica, observaciones.
- Given fallo del LLM durante la evaluacion, when evaluate_fidelity se llama, then se lanza PipelineError con agente="critico" y detalle del error original.
- Given cualquier generated_content valido, when evaluate_fidelity retorna, then `EvaluacionCalidad(**result_dict)` pasa validacion Pydantic sin errores.

## Implementation Notes

- Implementado con patron `llm.with_structured_output(EvaluacionCalidad).invoke(messages).model_dump()` identico al Agente Redactor (Story 1.4, doc langchain/models.mdx).
- `_serialize_generated_content` extrae titulo, introduccion e items del dict `contenido_adaptado` para producir texto legible al LLM. Fallback a `json.dumps` si la estructura es inesperada (robustez frente a formatos futuros).
- El prompt del SystemMessage fija la escala de scoring con puntos de referencia concretos (>= 0.7 = aceptable, < 0.5 = fallo severo) para reducir la varianza del LLM en la asignacion del score.
- Verificaciones completadas: `evaluation OK`, `review OK`, `nodes OK` (imports limpios sin errores). Tests de logica pura (sin LLM) verificados: PipelineError en contenido vacio, serializacion, chunks vacios/reales, validacion Pydantic.

## Spec Change Log

## Review Triage Log

- Finding 1: `resultado.model_dump()` fuera del try/except — verdict: `low` — evidence: si `invoke` devuelve None sin lanzar excepcion, `resultado.model_dump()` lanzaria `AttributeError` sin contexto de agente. Route: **patch** (aplicado: movido dentro del try/except con logging de score incluido).
- Finding 2: chunks como Document objects vs dicts — verdict: `false` — evidence: `retrieved_chunks` en `NuevaMenteState` es `list[dict[str, Any]]`; el pipeline RAG almacena dicts, no Documents. Mismo patron que `_build_context_text` de generation.py.
- Finding 3: `review_node` no valida `generated_content` antes de llamar — verdict: `false` — evidence: `state.get("generated_content", {})` retorna `{}` por default, que hace que `evaluate_fidelity` lance PipelineError con agente="critico" correctamente.
- Finding 4: Prompt como payload unico vs mensajes separados — verdict: `false` — evidence: el codigo usa `[SystemMessage(...), HumanMessage(...)]` explicitamente; el finding describe lo contrario de lo implementado.
- Finding 5: `document_id` anidado en metadata — verdict: `false` — evidence: `NuevaMenteState` (state.py:24) define `document_id: str` al nivel raiz del TypedDict; no esta anidado.
- Finding 6: Sin tests unitarios automaticos — verdict: `defer` — evidence: el proyecto no tiene suite de tests (pre-existente al cambio); la logica pura (PipelineError, serializacion, validacion Pydantic) fue verificada inline. Cerrar con tests formales en una story dedicada.

## Design Notes

Patron de llamada con with_structured_output (mismo patron que generation.py, doc langchain/models.mdx):
```python
from nuevamente.core.schemas import EvaluacionCalidad
llm = get_llm(settings)
structured_llm = llm.with_structured_output(EvaluacionCalidad)
resultado = structured_llm.invoke(messages)  # instancia EvaluacionCalidad
review_result = resultado.model_dump()
```

Estructura del prompt del Critico:
- SystemMessage: rol de Evaluador de Fidelidad; instruir al LLM a asignar anclaje_fuente_score basado en cuantos claims del contenido estan directamente respaldados por el texto fuente. Score >= 0.7 = aceptable; < 0.7 = requiere reintento con observaciones accionables.
- HumanMessage: contenido generado serializado (titulo + items como texto plano via `_serialize_generated_content`) seguido del documento fuente (chunks concatenados via `_build_source_text`). Instruccion de evaluar y proveer observaciones concretas.

`_serialize_generated_content`: intentar extraer `contenido_adaptado.titulo` e iterar sobre `contenido_adaptado.items` convirtiendo cada item a texto plano. Fallback a `json.dumps(generated_content, ensure_ascii=False, indent=2)` si la estructura no es la esperada.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.services.evaluation import evaluate_fidelity; print('evaluation OK')"` -- expected: imprime "evaluation OK"
- `uv run python -c "from nuevamente.pipeline.nodes.review import review_node; print('review OK')"` -- expected: imprime "review OK"
- `uv run python -c "from nuevamente.pipeline.nodes import draft_node, retrieve_node, ingest_node, review_node; print('nodes OK')"` -- expected: imprime "nodes OK"
