---
title: 'Story 4.1: Ejecución de Escenarios de Demostración'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_commit: 'b0b58f08522fa663eb07ed36501d96188a8fbd32'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Los evaluadores del hackathon requieren verificar que NuevaMente funciona end-to-end con documentación técnica real, validando la ingesta de los 3 tipos de archivos soportados (PDF, MD, TXT), la diferenciación por perfil, la versatilidad de los 5 formatos pedagógicos y la contextualización por nicho, con scores de anclaje a la fuente $\ge 0.7$ y evidencia reproducible.

**Approach:** Incorporar en el proyecto tres documentos técnicos reales (PDF de OCI VCN, Markdown de LangChain vs LangGraph, y TXT de clases en Python 3.14). Implementar un script de ejecución reproducible `scripts/run_demo_scenarios.py` que invoque el pipeline asíncrono o ejecute las solicitudes de demo, valide los paquetes generados contra los schemas Pydantic, persista los resultados localmente y en `docs/demos/`, y verifique que los criterios de calidad pedagógica se cumplan.

## Boundaries & Constraints

**Always:**
- Utilizar documentación real:
  - PDF: `Visión general OCI VCN.pdf` (arquitectura de red en OCI).
  - Markdown: `langchain_vs_langgraph.md` (comparativa conceptual moderna).
  - TXT: `classes.txt` (tutorial oficial de Programación Orientada a Objetos en Python 3.14).
- Cubrir los 5 formatos pedagógicos a lo largo de las demostraciones: Flashcards, Quiz Interactivo, Tutorial Paso a Paso, Resumen Ejecutivo y Guion de Clase.
- Cubrir perfiles contrastantes (Principiante vs Líder Técnico/Arquitecto, Senior, Junior).
- Cubrir al menos un caso con nicho personalizado (ej. *"veterinario aprendiendo a programar"*).
- Todo paquete generado debe ser válido según `nuevamente/core/schemas.py` y tener `anclaje_fuente_score >= 0.7`.
- Los paquetes generados deben persistirse tanto en el storage híbrido local (`data/storage/paquetes/`) como quedar archivados en `docs/demos/` para inspección directa por parte de evaluadores.

**Never:**
- No alterar la lógica de negocio de los agentes ni relajar las validaciones de Pydantic.
- No depender de rutas absolutas externas en los scripts reproducibles; los documentos de demo deben residir dentro del repositorio (`docs/demo-docs/`).
- No requerir pasos manuales no documentados para que un evaluador reproduzca la ejecución.

## I/O & Edge-Case Matrix

| Escenario | Input / Parámetros | Comportamiento Esperado | Criterio de Éxito / Manejo |
|-----------|-------------------|-------------------------|----------------------------|
| Escenario 1A: Python Classes (Principiante) | `classes.txt`, Perfil: Principiante, Formato: Flashcards, Nicho: General | Genera flashcards con lenguaje accesible, analogías simples y conceptos elementales de OOP | Schema `PaqueteFlashcards` válido, anclaje $\ge 0.7$ |
| Escenario 1B: Python Classes (Líder Técnico) | `classes.txt`, Perfil: Líder Técnico, Formato: Resumen Ejecutivo, Nicho: General | Genera resumen ejecutivo analizando modelo de ejecución, dynamic typing, implicaciones de diseño | Lenguaje técnico avanzado, schema `PaqueteResumenEjecutivo` válido, anclaje $\ge 0.7$ |
| Escenario 2A: LangChain vs LangGraph (Tutorial) | `langchain_vs_langgraph.md`, Perfil: Senior, Formato: Tutorial Paso a Paso, Nicho: General | Genera tutorial estructurado por pasos para elegir entre framework vs runtime | Schema `PaqueteTutorial` válido, anclaje $\ge 0.7$ |
| Escenario 2B: LangChain vs LangGraph (Quiz) | `langchain_vs_langgraph.md`, Perfil: Senior, Formato: Quiz Interactivo, Nicho: General | Genera preguntas de opción múltiple con justificaciones técnicas ancladas al documento | Schema `PaqueteQuiz` válido, anclaje $\ge 0.7$ |
| Escenario 3: OCI VCN PDF (Nicho Libre) | `Visión general OCI VCN.pdf`, Perfil: Junior, Formato: Guion de Clase, Nicho: "veterinario aprendiendo a programar" | Extrae texto del PDF (PyPDF), genera guion pedagógico con fases temporales y analogías contextualizadas | Schema `PaqueteGuionClase` válido, anclaje $\ge 0.7$ |

</frozen-after-approval>

## Code Map

- `docs/demo-docs/` -- NUEVO DIRECTORIO. Aloja copias de los 3 documentos fuente para reproducibilidad autónoma:
  - `docs/demo-docs/classes.txt`
  - `docs/demo-docs/langchain_vs_langgraph.md`
  - `docs/demo-docs/vision_general_oci_vcn.pdf`
- `scripts/run_demo_scenarios.py` -- NUEVO SCRIPT. Automatiza la ejecución de los escenarios mediante el pipeline de NuevaMente o cliente HTTP, valida los resultados contra los modelos de `nuevamente.core.schemas`, y exporta las evidencias a `docs/demos/`.
- `docs/demos/` -- NUEVO DIRECTORIO. Almacena los paquetes educativos JSON generados, un reporte Markdown comparativo de los resultados y métricas de calidad.
- `tests/test_demo_scenarios.py` -- NUEVO TEST. Suite de pruebas que verifica la integridad estructural de los paquetes generados en las demos, asegurando que el score de anclaje sea $\ge 0.7$ y que los schemas sean válidos.
- `nuevamente/pipeline/graph.py` y `nuevamente/services/rag.py` -- REUTILIZAR SIN MODIFICAR. El pipeline existente ejecuta la ingesta, vectorización FAISS, agentes redactor/crítico y validación.

## Tasks & Acceptance

**Execution:**
- [x] `docs/demo-docs/` -- Copiar e incorporar los 3 documentos técnicos reales al repositorio.
- [x] `scripts/run_demo_scenarios.py` -- Crear script de ejecución de demostraciones que ejecute los 5 escenarios, verifique Pydantic schemas y guarde los JSON en `docs/demos/` y en storage local.
- [x] `docs/demos/README.md` -- Documentar los escenarios ejecutados, comandos de reproducción, contraste cualitativo entre perfiles y tabla de métricas (scores de anclaje y tiempos).
- [x] `tests/test_demo_scenarios.py` -- Crear test suite que valide programáticamente los artefactos de demo generados contra `PaqueteEducativo` Pydantic models y verifique `anclaje_fuente_score >= 0.7`.

**Acceptance Criteria:**
- Given el sistema NuevaMente en local con API keys configuradas, when se ejecuta `python scripts/run_demo_scenarios.py`, then se ejecutan los 5 escenarios sobre los 3 documentos sin errores.
- Given los paquetes generados, when se comparan Escenario 1A (Principiante) y 1B (Líder Técnico), then el vocabulario, tono y nivel de abstracción reflejan clara diferenciación pedagógica (SM-1).
- Given los 5 paquetes educativos generados, when se validan contra sus respectivos schemas Pydantic (`PaqueteFlashcards`, `PaqueteResumenEjecutivo`, `PaqueteTutorial`, `PaqueteQuiz`, `PaqueteGuionClase`), then el 100% de los paquetes es válido (SM-2).
- Given la evaluación de calidad de cada paquete, when se inspecciona `anclaje_fuente_score`, then todos los paquetes tienen un score $\ge 0.7$ (SM-3).
- Given los artefactos de demostración, when un evaluador inspecciona `docs/demos/`, then encuentra los archivos JSON y el `README.md` con las evidencias listas para la presentación.

## Implementation Notes

- Se copiaron los tres documentos reales desde `/home/lucky_tv/Projects/dev_one-nuevamente/documentacion/` hacia `docs/demo-docs/`: `classes.txt`, `langchain_vs_langgraph.md` y `vision_general_oci_vcn.pdf`.
- Se implementó `scripts/run_demo_scenarios.py` para ejecutar de forma secuencial y desacoplada los 5 escenarios utilizando el pipeline de LangGraph y `StorageService` para el almacenamiento híbrido.
- Se ejecutaron los 5 escenarios de demostración:
  1. Escenario 1A (classes.txt, Principiante, Flashcards) -> 8 items, anclaje 1.00.
  2. Escenario 1B (classes.txt, Líder Técnico, Resumen Ejecutivo) -> 5 items, anclaje 1.00.
  3. Escenario 2A (langchain_vs_langgraph.md, Senior, Tutorial Paso a Paso) -> 4 items, anclaje 1.00.
  4. Escenario 2B (langchain_vs_langgraph.md, Senior, Quiz Interactivo) -> 4 items, anclaje 1.00.
  5. Escenario 3 (vision_general_oci_vcn.pdf, Junior, Guion de Clase, Nicho: veterinario) -> 4 items, anclaje 1.00.
- Se generaron los 5 paquetes en `docs/demos/` y el reporte consolidado en `docs/demos/README.md`.
- Se crearon 5 tests en `tests/test_demo_scenarios.py` que comprueban la extracción de los documentos, la validación Pydantic estricta (`FORMATO_A_SCHEMA`) y la diferenciación semántica y de perfiles. Los 5 tests pasaron (y 28 tests totales en la suite).

## Spec Change Log

## Review Triage Log

- Finding BH-1: SyntaxWarning por escape sequence `\ge` en `generate_demos_readme` — verdict: `low` — En Python 3.12, secuencias de escape no reconocidas en f-strings lanzan advertencia. Patched: se escapó a `\\ge` en `scripts/run_demo_scenarios.py`.
- Finding BH-2: Invocación directa del pipeline en `run_scenario` sin reintentos explícitos en runner — verdict: `false` — El pipeline ya maneja resiliencia con `Settings.llm_max_retries = 6` en el cliente LLM y loop de corrección en el grafo LangGraph (`_should_retry`).
- Finding EC-1: Manejo de credenciales faltantes en `run_demo_scenarios.py` — verdict: `false` — El script valida tempranamente `google_api_key` y `voyage_api_key`, abortando con mensaje explicativo en español antes de procesar.
- Finding EC-2: Carga de JSONs corruptos en `test_demo_scenarios.py` — verdict: `false` — El test valida la presencia de `formato_generado` en `FORMATO_A_SCHEMA` y delega a `model_validate`, capturando cualquier discrepancia estructural.
- Finding VG-1: Validación programática de los 5 schemas y anclaje >= 0.7 — verdict: `false` — Cubierto completamente por `tests/test_demo_scenarios.py` (5 tests específicos, 100% pasados).

## Design Notes

El script `run_demo_scenarios.py` puede importar directamente el pipeline (`crear_pipeline()`) o invocar la app FastAPI via `httpx.AsyncClient(transport=ASGITransport(app=app))`. Invocar el pipeline directamente con `invoke()` o `ainvoke()` es especialmente limpio y robusto porque no depende de puertos de red ni procesos demonio, interactuando con los servicios de storage FAISS y almacenamiento local de manera nativa.
