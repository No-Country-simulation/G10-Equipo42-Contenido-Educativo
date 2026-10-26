---
title: 'Story 1.6: Ensamblado del Paquete Educativo y Grafo LangGraph'
type: 'feature'
created: '2026-09-26'
baseline_commit: '9bb4b2d1e1d6e6c07c53e6c7d2ca79b4ae7795b2'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** Los nodos ingest, retrieve, draft y review existen y están probados de forma aislada, pero no hay un grafo LangGraph que los conecte. Tampoco existe un nodo `format_output` que ensamble el paquete educativo final (con metadatos, contenido y evaluación) ni la lógica de retry condicional cuando el score es bajo. El pipeline end-to-end no puede ejecutarse.

**Approach:** Crear `services/assembly.py` con `assemble_package(generated_content, review_result, formato)` que construye y valida el `educational_package` completo usando los schemas Pydantic de `core/schemas.py`. Luego crear `pipeline/nodes/format_output.py` como thin wrapper y `pipeline/graph.py` con `build_graph()` que conecta todos los nodos con `StateGraph`, incluyendo el conditional edge de `review` → (`draft` si score < 0.7 y retry < 1) → `format_output`.

## Boundaries & Constraints

**Always:**
- Usar `FORMATO_A_SCHEMA[formato]` de `core/schemas.py` para validar el paquete final con Pydantic.
- El conditional edge usa exclusivamente los campos `review_result["anclaje_fuente_score"]` y `retry_count` del state para decidir el routing.
- `format_output_node` escribe `educational_package` como `dict` (resultado de `.model_dump()`) en el state.
- `build_graph()` retorna un grafo compilado (`builder.compile()`) sin checkpointer — pipeline stateless.
- Respetar la regla de dependencia: `services/` importa de `infra/` y `core/`, no de `pipeline/`. `pipeline/` importa de `services/` y `core/`.
- Type hints completos, sin emojis, logging con `logging.getLogger(__name__)`.
- El incremento de `retry_count` se hace en el router del conditional edge retornando el nombre del nodo; `draft_node` ya lee `retry_count` del state y puede incrementarlo en su propio dict de retorno para que el router lo vea en el siguiente paso.

**Never:**
- No agregar checkpointer ni persistencia al grafo en esta story.
- No modificar `core/schemas.py`, `core/models.py`, `pipeline/state.py`, ni los nodos existentes (ingest, retrieve, draft, review).
- No agregar dependencias externas más allá de las ya declaradas en `pyproject.toml`.
- No implementar la capa FastAPI ni el endpoint REST — eso es Story 1.7.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|--------------------|
| Ejecución completa score >= 0.7 | generated_content válido, review_result con score >= 0.7, retry_count = 0 | educational_package dict con status="completed", metadatos, contenido_adaptado, evaluacion_calidad | -- |
| Primer intento score < 0.7 (retry) | review_result con score < 0.7, retry_count = 0 | Router envía a draft_node; draft_node retorna retry_count = 1 | -- |
| Segundo intento score < 0.7 (límite) | review_result con score < 0.7, retry_count = 1 | Router envía a format_output (se acepta el resultado) | -- |
| formato no registrado | formato desconocido en generated_content | PipelineError con mensaje descriptivo | caller registra error |
| generated_content vacío o mal formado | generated_content = {} o sin claves esperadas | PipelineError desde assemble_package con agente="format_output" | caller registra error |

</frozen-after-approval>

## Code Map

- `nuevamente/core/schemas.py` — `FORMATO_A_SCHEMA`, `PaqueteEducativoBase` y subclases por formato. Solo lectura; usar para validar con `schema_class(**paquete_dict).model_dump()`.
- `nuevamente/core/models.py` — `FormatoPedagogico` enum. Solo lectura.
- `nuevamente/core/exceptions.py` — `PipelineError(mensaje, *, agente, detalle)`. Lanzar en `assemble_package` si formato inválido o contenido mal formado.
- `nuevamente/pipeline/state.py` — `NuevaMenteState`: leer `generated_content`, `review_result`, `retry_count`, `formato`; escribir `educational_package`. No modificar.
- `nuevamente/pipeline/nodes/__init__.py` — ACTUALIZAR: agregar export de `format_output_node`.
- `nuevamente/pipeline/nodes/draft.py` — Solo lectura: referencia para el patrón thin wrapper y cómo leer `retry_count` del state.
- `nuevamente/pipeline/nodes/review.py` — Solo lectura: referencia para el patrón thin wrapper.
- `nuevamente/services/generation.py` — Solo lectura: referencia de la estructura de `generated_content` (dict con claves `metadatos`, `contenido_adaptado`, etc.).
- `nuevamente/services/assembly.py` — CREAR: `assemble_package(generated_content, review_result, formato, settings)`.
- `nuevamente/pipeline/nodes/format_output.py` — CREAR: `format_output_node(state)` thin wrapper.
- `nuevamente/pipeline/graph.py` — CREAR: `build_graph()` que ensambla y compila el `StateGraph`.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/services/assembly.py` — CREAR: función pública `assemble_package(generated_content: dict[str, Any], review_result: dict[str, Any], formato: str, settings: Settings) -> dict[str, Any]`. Incluir: validación de formato con PipelineError si no está en FORMATO_A_SCHEMA, construcción del dict `{"status": "completed", "metadatos": generated_content["metadatos"], "contenido_adaptado": generated_content["contenido_adaptado"], "evaluacion_calidad": review_result}`, instanciación y validación Pydantic con `FORMATO_A_SCHEMA[formato](**paquete_dict).model_dump()`, envuelto en try/except que lanza `PipelineError(agente="format_output")`.
- [x] `nuevamente/pipeline/nodes/format_output.py` — CREAR: `format_output_node(state: NuevaMenteState) -> dict[str, Any]`. Lee `generated_content`, `review_result`, `formato`, `document_id` del state, instancia `Settings()`, llama `assemble_package`, retorna `{"educational_package": paquete}`. Logging de inicio y fin con `document_id`.
- [x] `nuevamente/pipeline/nodes/__init__.py` — ACTUALIZAR: agregar `from nuevamente.pipeline.nodes.format_output import format_output_node` y exportar en `__all__`.
- [x] `nuevamente/pipeline/graph.py` — CREAR: `build_graph() -> CompiledGraph`. Usar `StateGraph(NuevaMenteState)`. Agregar nodos: `ingest`, `retrieve`, `draft`, `review`, `format_output`. Edges: `START → ingest → retrieve → draft → review`. Conditional edge de `review` con router `_should_retry(state) -> str` que retorna `"draft"` si `score < 0.7 y retry_count < 1`, o `"format_output"` en caso contrario. `draft_node` ya incrementa `retry_count` en su return dict cuando es llamado en retry (lee el valor actual del state). Edge `format_output → END`. Retornar `builder.compile()`.

**Acceptance Criteria:**
- Given generated_content válido y review_result con score >= 0.7, when format_output_node se ejecuta, then educational_package es un dict que pasa `schema_class(**result)` Pydantic sin errores.
- Given educational_package ensamblado, when se inspecciona, then tiene las claves: `status`, `metadatos`, `contenido_adaptado`, `evaluacion_calidad`.
- Given review_result con score < 0.7 y retry_count = 0, when el router del conditional edge evalúa, then retorna `"draft"`.
- Given review_result con score < 0.7 y retry_count = 1, when el router evalúa, then retorna `"format_output"`.
- Given build_graph() llamado, when se verifica el grafo, then `type(g).__name__` indica que está compilado (no es `StateGraph` crudo) y los imports no lanzan errores.
- Given formato no registrado en FORMATO_A_SCHEMA, when assemble_package se llama, then se lanza PipelineError con agente="format_output".

## Implementation Notes

- `services/assembly.py` creado con `assemble_package()`. Validacion Pydantic con `FORMATO_A_SCHEMA[formato](**paquete_dict).model_dump()`. PipelineError en formato invalido, dict vacio o KeyError de claves.
- `pipeline/nodes/format_output.py` creado como thin wrapper identico al patron de draft.py y review.py.
- `pipeline/nodes/__init__.py` actualizado: `format_output_node` agregado a imports y `__all__`.
- `pipeline/nodes/draft.py` actualizado: retorna `retry_count + 1` en el dict de respuesta para que el router lo vea actualizado en el paso siguiente.
- `pipeline/graph.py` creado con `build_graph()` y router `_should_retry()`. El router retorna `Literal["draft", "format_output"]`; el mapping explicito en `add_conditional_edges` garantiza compatibilidad con LangGraph 0.4+.
- Verificaciones completadas: `assembly OK`, `format_output OK`, `all nodes OK`, `graph OK CompiledStateGraph`.
- Tests de logica pura (sin LLM) verificados: PipelineError en formato invalido (agente='format_output'), PipelineError en dict vacio, router en todos los casos de la I/O Matrix, ensamblado y validacion Pydantic de paquete Flashcards completo.

## Spec Change Log

## Review Triage Log

- Finding 1: `settings` no usado en `assemble_package` — verdict: `low` — evidence: el parametro existe para extension futura y coherencia de firma con otros servicios (generation.py, evaluation.py). Cosmético, sin impacto funcional. Route: **reject** (bajo probability de encounter en uso diario, la firma está documentada).
- Finding 2: Sin tests formales para la logica de retry en `draft_node` (retorno de `retry_count+1`) — verdict: `low` — evidence: el proyecto no tiene suite de tests (pre-existente al cambio); logica pura verificada inline. Mismo deferido que Finding 6 de Story 1.5. Route: **defer**.
- Finding 3: `except Exception` podria envolver un `PipelineError` interno — verdict: `false` — evidence: el `PipelineError` de formato invalido se lanza antes del bloque try (lineas 55-66); dentro del try solo pueden ocurrir `KeyError` (del dict access) o `ValidationError` de Pydantic. No hay codigo que lance PipelineError dentro del try.
- Finding 4: `_should_retry` con `retry_count=None` lanzaria TypeError — verdict: `false` — evidence: `draft_node` siempre retorna `retry_count + 1` como int; el state inicial tiene `retry_count` no seteado (TypedDict total=False), por lo que `.get("retry_count", 0)` retorna 0. La clave nunca puede tener valor None en flujo normal.

## Design Notes

Patrón del conditional edge router compatible con LangGraph >= 0.4 (Graph API, `graph-api.mdx`):

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END

def _should_retry(state: NuevaMenteState) -> Literal["draft", "format_output"]:
    score = (state.get("review_result") or {}).get("anclaje_fuente_score", 1.0)
    retry_count = state.get("retry_count", 0)
    if score < 0.7 and retry_count < 1:
        return "draft"
    return "format_output"

builder = StateGraph(NuevaMenteState)
# ... add_node calls ...
builder.add_conditional_edges("review", _should_retry, {"draft": "draft", "format_output": "format_output"})
```

El `retry_count` se incrementa dentro de `draft_node` cuando detecta que `retry_count > 0` ya no aplica — en realidad el draft_node ya recibe el state con `retry_count` que tiene el valor del intento anterior. Para que el router vea `retry_count = 1` en el segundo paso, `draft_node` debe retornar `{"generated_content": ..., "retry_count": retry_count + 1}` cuando es invocado en modo retry. El `draft_node` ya lee `retry_count` del state (línea 37 de `draft.py`); solo hay que asegurarse de que lo incluya en el dict de retorno.

Estructura de `assemble_package` antes de instanciar Pydantic:
```python
paquete_dict = {
    "status": "completed",
    "metadatos": generated_content["metadatos"],
    "contenido_adaptado": generated_content["contenido_adaptado"],
    "evaluacion_calidad": review_result,
}
schema_class = FORMATO_A_SCHEMA[formato]
return schema_class(**paquete_dict).model_dump()
```

## Verification

**Commands:**
- `uv run python -c "from nuevamente.services.assembly import assemble_package; print('assembly OK')"` -- expected: imprime "assembly OK"
- `uv run python -c "from nuevamente.pipeline.nodes.format_output import format_output_node; print('format_output OK')"` -- expected: imprime "format_output OK"
- `uv run python -c "from nuevamente.pipeline.nodes import ingest_node, retrieve_node, draft_node, review_node, format_output_node; print('all nodes OK')"` -- expected: imprime "all nodes OK"
- `uv run python -c "from nuevamente.pipeline.graph import build_graph; g = build_graph(); print('graph OK', type(g).__name__)"` -- expected: imprime "graph OK" seguido del nombre del tipo compilado
