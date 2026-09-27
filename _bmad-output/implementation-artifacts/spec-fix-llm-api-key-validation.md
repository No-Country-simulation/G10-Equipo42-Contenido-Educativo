---
title: 'Fix LLM API Key Validation'
type: 'bugfix'
created: '2026-09-27'
status: 'done'
baseline_commit: '8275a54ef04964ec17b2c82e9132c0eaf3cc9775'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Al invocar el pipeline RAG desde la API o UI (`POST /api/v1/adaptar`), la inicialización de `ChatGoogleGenerativeAI` falla con `ValidationError: API key required for Gemini Developer API` debido a que `Settings` no exporta las API keys a `os.environ` y `get_llm()` no pasa `api_key` explícitamente a `init_chat_model()`.

**Approach:** Inyectar `api_key=settings.google_api_key` en `kwargs` dentro de `get_llm()` cuando esté configurada, sincronizar `GOOGLE_API_KEY`, `GEMINI_API_KEY` y `VOYAGE_API_KEY` en `os.environ` mediante `model_post_init()` en `Settings`, y añadir tests unitarios para verificar la instanciación y sincronización de entorno.

## Boundaries & Constraints

**Always:**
- `get_llm` debe admitir tanto claves pasadas explícitamente como variables de entorno existentes (usando `os.environ.setdefault` para no sobreescribir valores de entorno preexistentes si ya fueron inyectados por el sistema host).
- La inicialización de `ChatGoogleGenerativeAI` no debe romperse cuando `google_api_key` esté configurada en `.env` o en `Settings`.
- Mantener compatibilidad total con la suite de tests existente (`pytest` al 100%).

**Never:**
- No sobreescribir variables de entorno de forma destructiva si ya están configuradas en el entorno del proceso (usar `setdefault`).
- No hardcodear API keys en el código fuente ni alterar la firma pública de `get_llm(settings: Settings)`.
- No alterar otros proveedores o parámetros de generación existentes sin necesidad.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| get_llm con google_api_key en Settings | `Settings(google_api_key="test-key")` | Retorna instancia de `BaseChatModel` (`ChatGoogleGenerativeAI`) configurada con la API key | N/A |
| Settings exporta GOOGLE_API_KEY y VOYAGE_API_KEY | `Settings(google_api_key="gkey", voyage_api_key="vkey")` | `os.environ["GOOGLE_API_KEY"] == "gkey"`, `os.environ["VOYAGE_API_KEY"] == "vkey"` | N/A |
| Settings no sobreescribe variables existentes | `os.environ["GOOGLE_API_KEY"] = "original"` y `Settings(google_api_key="nuevo")` | `os.environ["GOOGLE_API_KEY"] == "original"` | N/A |
| get_llm sin api_key cuando GOOGLE_API_KEY en os.environ | `Settings(google_api_key="")` con `GOOGLE_API_KEY` en `os.environ` | `get_llm` se inicializa usando la variable de entorno | N/A |

</frozen-after-approval>

## Code Map

- `nuevamente/config.py` -- Añadir hook `model_post_init(self, __context: Any)` en `Settings` para poblar `os.environ` vía `setdefault` con `GOOGLE_API_KEY`, `GEMINI_API_KEY` y `VOYAGE_API_KEY`.
- `nuevamente/infra/llm.py` -- Modificar `get_llm(settings: Settings)` para inyectar `kwargs["api_key"] = settings.google_api_key` antes de invocar `init_chat_model()`.
- `tests/test_llm.py` -- Nuevo archivo de pruebas unitarias que valida `get_llm` y el hook `model_post_init` de `Settings`.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/infra/llm.py` -- Inyectar `kwargs["api_key"]` en `get_llm` cuando `settings.google_api_key` tenga valor no vacío.
- [x] `nuevamente/config.py` -- Implementar `model_post_init(self, __context: Any)` en `Settings` con `os.environ.setdefault` para `GOOGLE_API_KEY`, `GEMINI_API_KEY` y `VOYAGE_API_KEY`.
- [x] `tests/test_llm.py` -- Crear tests unitarios para verificar la instanciación de `get_llm`, el pasaje de `api_key` y la sincronización de variables de entorno de `Settings`.

**Acceptance Criteria:**
- Given una instancia de `Settings` con `google_api_key="test-key"`, when se invoca `get_llm(settings)`, then se retorna exitosamente una instancia de `BaseChatModel` sin lanzar `ValidationError`.
- Given variables de API key presentes en `Settings`, when se inicializa `Settings`, then las variables `GOOGLE_API_KEY` y `VOYAGE_API_KEY` quedan accesibles en `os.environ`.
- Given una variable `GOOGLE_API_KEY` ya presente en el entorno, when se inicializa `Settings`, then el valor original de `os.environ` se preserva intacto.

## Implementation Notes

- Modificado `nuevamente/infra/llm.py`: se preparan `kwargs` con `temperature` y `max_retries`, y se añade `kwargs["api_key"] = settings.google_api_key` cuando `settings.google_api_key` no está vacío.
- Modificado `nuevamente/config.py`: implementado hook `model_post_init` en `Settings` que utiliza `os.environ.setdefault` para `GOOGLE_API_KEY`, `GEMINI_API_KEY` y `VOYAGE_API_KEY`.
- Creado `tests/test_llm.py`: 4 pruebas unitarias que cubren todas las combinaciones de la matriz de E/S.
- Verificación ejecutada: `uv run pytest` pasa al 100% (18/18 pruebas superadas).

## Spec Change Log

## Review Triage Log

- Finding BH-1: Posible paso de string con solo espacios en `google_api_key` — verdict: `low` — En uso normal y variables de entorno no se configuran espacios en blanco aislados; no justifica complejidad adicional.
- Finding BH-2: Preexistencia de `GEMINI_API_KEY` en entorno — verdict: `false` — `setdefault` respeta explícitamente cualquier valor previo sin sobreescribir.
- Finding EC-1: Fallback a variables de entorno cuando `google_api_key` es vacío en `Settings` — verdict: `false` — Comportamiento intencional y cubierto por `test_get_llm_instantiation_with_environ_key`.
- Finding EC-2: No inyectar valores vacíos en `os.environ` — verdict: `false` — La condición `if self.google_api_key:` previene inyecciones vacías.
- Finding VG-1: Sin tests de integración endpoint-to-LLM para `POST /api/v1/adaptar` — verdict: `low` / defer — Patrón preexistente en el proyecto; la suite unitaria cubre completamente la interfaz `get_llm` y `Settings`.

## Verification

**Commands:**
- `uv run pytest tests/test_llm.py` -- expected: todos los tests nuevos pasan exitosamente.
- `uv run pytest` -- expected: 100% de la suite de tests (incluyendo `test_storage.py` y `test_llm.py`) pasa exitosamente.
