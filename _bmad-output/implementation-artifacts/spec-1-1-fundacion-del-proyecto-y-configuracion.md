---
title: 'Story 1.1: Fundacion del Proyecto y Configuracion'
type: 'feature'
created: '2026-09-25'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '8e586f8bf2a5519ea482ccb23586d6d7bef99417'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El proyecto NuevaMente no tiene codigo. No existe estructura de directorios, modelos de dominio, schemas Pydantic ni configuracion centralizada. Sin esta base, ninguna story posterior puede comenzar.

**Approach:** Inicializar el proyecto Python con la estructura modular definida en la arquitectura (app/, core/, pipeline/, services/, infra/), crear los modelos de dominio (enums), los schemas Pydantic para los 5 formatos pedagogicos, el estado del grafo LangGraph como TypedDict, las excepciones de dominio, y la configuracion centralizada con pydantic-settings. Incluir pyproject.toml con todas las dependencias del proyecto.

## Boundaries & Constraints

**Always:**
- Respetar la regla de dependencia: app -> pipeline -> services -> infra; core es transversal.
- Usar Python 3.12, Pydantic v2, pydantic-settings para config.
- Los enums de Perfil tienen exactamente 4 valores, FormatoPedagogico exactamente 5, Nicho con opciones predefinidas + texto libre.
- NuevaMenteState como TypedDict (no Pydantic, para rendimiento en LangGraph).
- Todos los archivos con type hints completos.
- Estilo profesional: sin emojis en codigo ni en comentarios.

**Never:**
- No implementar logica de pipeline, servicios, API ni nodos en esta story — solo la estructura y los tipos.
- No crear tests en esta story — la verificacion es por import exitoso y validacion de estructura.
- No instalar dependencias innecesarias para esta story (el spec define el pyproject.toml completo para el proyecto, pero solo el subset relevante se usa aqui).

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|-----------------------------------|-----------------|
| Import de core/models.py | `from nuevamente.core.models import Perfil, FormatoPedagogico` | Enums importables sin error | N/A |
| Instanciacion de schema | `FlashcardsPaquete(...)` con datos validos | Instancia Pydantic validada | ValidationError si datos invalidos |
| Config sin .env | Instanciacion de `Settings()` | Valores por defecto funcionales | N/A |
| Config con .env | Variables de entorno seteadas | Settings los lee correctamente | N/A |
| Import cruzado invalido | `from nuevamente.core import ...` en infra/ | Funciona (core es transversal) | N/A |

</frozen-after-approval>

## Code Map

- `nuevamente/` -- Directorio raiz del paquete Python. No existe aun (greenfield).
- `nuevamente/core/models.py` -- Enums: Perfil (4 valores), FormatoPedagogico (5 valores), Nicho (predefinidos + libre).
- `nuevamente/core/schemas.py` -- PaqueteEducativoBase y 5 modelos por formato. Cada uno con estructura de items especifica.
- `nuevamente/core/exceptions.py` -- Excepciones de dominio: DocumentoNoSoportado, DocumentoVacio, PipelineError, etc.
- `nuevamente/pipeline/state.py` -- NuevaMenteState (TypedDict) con campos de input, pipeline, control y output.
- `nuevamente/config.py` -- pydantic-settings: modelo LLM, embeddings, chunking, OCI, rutas FAISS.
- `nuevamente/app/`, `nuevamente/pipeline/nodes/`, `nuevamente/services/`, `nuevamente/infra/` -- Directorios con __init__.py vacios (estructura para stories posteriores).
- `pyproject.toml` -- Dependencias del proyecto, metadata, configuracion de herramientas.
- `.gitignore` -- Actualizar con data/faiss_indexes/, .env, __pycache__, etc.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` -- Crear con metadata del proyecto, dependencias (langchain, langgraph, langchain-google-genai, langchain-voyageai, langchain-community, faiss-cpu, fastapi, uvicorn, pydantic, pydantic-settings, python-multipart, oci, pypdf) y configuracion de herramientas.
- [x] `nuevamente/__init__.py` -- Crear paquete raiz.
- [x] `nuevamente/core/__init__.py` -- Crear paquete core.
- [x] `nuevamente/core/models.py` -- Crear enums Perfil (Principiante, Junior, Senior, LiderTecnico), FormatoPedagogico (Flashcards, QuizInteractivo, TutorialPasoAPaso, ResumenEjecutivo, GuionDeClase), y el modelo para Nicho con validacion (predefinidos: General, Fintech, Salud, Ecommerce + texto libre).
- [x] `nuevamente/core/schemas.py` -- Crear PaqueteEducativoBase con campos comunes (status, metadatos, contenido_adaptado, evaluacion_calidad) y los 5 modelos especificos (FlashcardsPaquete, QuizPaquete, TutorialPaquete, ResumenEjecutivoPaquete, GuionClasePaquete) con items tipados.
- [x] `nuevamente/core/exceptions.py` -- Crear excepciones: DocumentoNoSoportado (415), DocumentoVacio (422), PipelineError (500), ServicioNoDisponible (503).
- [x] `nuevamente/pipeline/__init__.py` -- Crear paquete pipeline.
- [x] `nuevamente/pipeline/state.py` -- Crear NuevaMenteState como TypedDict con todos los campos del state del grafo.
- [x] `nuevamente/pipeline/nodes/__init__.py` -- Crear paquete nodes (vacio, para stories posteriores).
- [x] `nuevamente/services/__init__.py` -- Crear paquete services (vacio).
- [x] `nuevamente/infra/__init__.py` -- Crear paquete infra (vacio).
- [x] `nuevamente/app/__init__.py` -- Crear paquete app (vacio).
- [x] `nuevamente/app/routers/__init__.py` -- Crear paquete routers (vacio).
- [x] `nuevamente/config.py` -- Crear Settings con pydantic-settings: GOOGLE_API_KEY, VOYAGE_API_KEY, LLM_MODEL_NAME, EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP, FAISS_INDEX_DIR, OCI_BUCKET_NAME, OCI_NAMESPACE, OCI_COMPARTMENT_ID, con defaults sensatos.
- [x] `.gitignore` -- Actualizar con entradas para data/faiss_indexes/, .env, __pycache__, dist/, *.egg-info.

**Acceptance Criteria:**
- Given el proyecto inicializado, when se ejecuta `python -c "from nuevamente.core.models import Perfil, FormatoPedagogico"`, then no hay errores de importacion.
- Given el proyecto inicializado, when se ejecuta `python -c "from nuevamente.core.schemas import FlashcardsPaquete, QuizPaquete, TutorialPaquete, ResumenEjecutivoPaquete, GuionClasePaquete"`, then no hay errores de importacion.
- Given el proyecto inicializado, when se ejecuta `python -c "from nuevamente.pipeline.state import NuevaMenteState"`, then no hay errores de importacion.
- Given el proyecto inicializado, when se ejecuta `python -c "from nuevamente.config import Settings; s = Settings()"`, then se crea una instancia con valores por defecto.
- Given los directorios creados, when se revisa la estructura, then existen app/, core/, pipeline/, services/, infra/ con sus __init__.py.

## Implementation Notes

- `langchain-community` version corregida de `>=0.6` a `>=0.4` (la 0.6 no existe; la 1.0.0a1 es pre-release).
- `hatchling.backends` corregido a `hatchling.build` (nombre correcto del build backend).
- Se agrego `FORMATO_A_SCHEMA` dict en schemas.py como utility para mapeo dinamico formato -> modelo Pydantic.
- NuevaMenteState usa `total=False` para permitir campos opcionales al inicio del pipeline.
- Se verifico compatibilidad con la documentacion actualizada de LangChain/LangGraph: `init_chat_model()` con provider prefix `google_genai:` es la API actual recomendada.
## Spec Change Log


## Review Triage Log

- Finding 1: `FORMATO_A_SCHEMA` usa strings hardcodeados en vez del enum — verdict: `low` — evidence: duplica valores de FormatoPedagogico pero son estables; fix es trivial (usar enum.value). Route: **patch**.
- Finding 2: No hay singleton/factory para Settings — verdict: `false` — evidence: pydantic-settings instanciacion directa es el patron estandar; cada story posterior instancia segun necesidad. No hay dano observable.
- Finding 3: total=False hace inputs opcionales en type checking — verdict: `low` — rejected: fix requiere dual TypedDict split que agrega complejidad sin beneficio practico en pipeline secuencial.
- Finding 4: http_status como class variable — verdict: `false` — evidence: patron estandar Python, MRO resuelve correctamente en subclases.
- Finding 5: No hay py.typed marker — verdict: `low` — rejected: NuevaMente es aplicacion standalone, no library. Improbable en uso normal.
- Finding 6: QuizItem.respuesta_correcta sin validacion cruzada — verdict: `low` — rejected: validacion en Pydantic bloquearia outputs LLM aprovechables; la responsabilidad es del agente critico.

## Design Notes

Los schemas Pydantic siguen la jerarquia definida en la arquitectura:

```python
# Estructura simplificada
class MetadatosPedagogicos(BaseModel):
    perfil_aplicado: str
    formato_generado: str
    tiempo_estimado_estudio_minutos: int
    conceptos_clave: list[str]
    prerrequisitos: list[str]

class EvaluacionCalidad(BaseModel):
    anclaje_fuente_score: float  # 0.0-1.0
    claridad_pedagogica: str
    observaciones: str

class PaqueteEducativoBase(BaseModel):
    status: str
    metadatos: MetadatosPedagogicos
    evaluacion_calidad: EvaluacionCalidad

# Cada formato hereda y define su propio contenido_adaptado
class FlashcardItem(BaseModel):
    frente: str
    dorso: str
    pista_didactica: str

class ContenidoAdaptadoFlashcards(BaseModel):
    titulo: str
    introduccion_contextualizada: str
    items: list[FlashcardItem]

class FlashcardsPaquete(PaqueteEducativoBase):
    contenido_adaptado: ContenidoAdaptadoFlashcards
```

Para NuevaMenteState se usa TypedDict simple (sin Annotated reducers) ya que el pipeline es secuencial sin nodos paralelos.

## Verification

**Commands:**
- `uv sync` -- expected: dependencias instaladas sin errores
- `uv run python -c "from nuevamente.core.models import Perfil, FormatoPedagogico; print('models OK')"` -- expected: imprime "models OK"
- `uv run python -c "from nuevamente.core.schemas import FlashcardsPaquete, QuizPaquete, TutorialPaquete, ResumenEjecutivoPaquete, GuionClasePaquete; print('schemas OK')"` -- expected: imprime "schemas OK"
- `uv run python -c "from nuevamente.pipeline.state import NuevaMenteState; print('state OK')"` -- expected: imprime "state OK"
- `uv run python -c "from nuevamente.config import Settings; s = Settings(); print(f'config OK: {s.llm_model_name}')"` -- expected: imprime "config OK: google_genai:gemini-2.0-flash-lite"
