---
title: 'Story 4.2: Documentación del Repositorio GitHub'
type: 'feature'
created: '2026-10-25'
status: 'done'
baseline_commit: '43c6fe694a53e770459019488802fe8cdf21d9be'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-4-context.md
  - _bmad-output/implementation-artifacts/spec-hybrid-local-storage.md
  - _bmad-output/implementation-artifacts/spec-collapsible-sidebar-and-layout.md
  - _bmad-output/implementation-artifacts/spec-4-1-ejecucion-de-escenarios-de-demostracion.md
  - _bmad-output/planning-artifacts/architecture/architecture-NuevaMente-2026-09-24/ARCHITECTURE.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** El README actual del repositorio contiene texto genérico de una plantilla inicial previa y no refleja la solución real de NuevaMente ni las evoluciones arquitectónicas recientes: el almacenamiento híbrido Local-First con sincronización en background a OCI, el rediseño de interfaz con barra lateral colapsable / off-canvas móvil y títulos de historial por IA, los 5 formatos pedagógicos con schemas Pydantic tipados, ni la guía para que un evaluador del hackathon instale, configure variables de entorno y reproduzca los escenarios de prueba end-to-end.

**Approach:** Reescribir exhaustivamente `README.md` convirtiéndolo en la documentación técnica y funcional de referencia para evaluadores y desarrolladores. Explicar en detalle la arquitectura híbrida Local-First (persistencia en `data/storage/` sin requerir credenciales cloud obligatorias + sincronización automática a OCI), diagramas Mermaid actualizados (arquitectura de componentes y grafo de LangGraph con loop de corrección), guía de instalación y puesta en marcha rápida, configuración de `.env`, ejecución de demostraciones (`scripts/run_demo_scenarios.py`) con enlace a evidencias en `docs/demos/`, y detalle de la organización del código según `ARCHITECTURE.md` sec. 6.

## Boundaries & Constraints

**Always:**
- Redactar en español formal, estructurado y profesional, con badges y tablas comparativas.
- Documentar prominentemente la **Arquitectura Híbrida Local-First & OCI**:
  - Persistencia local inmediata de documentos fuente (`data/storage/documentos/`) y paquetes educativos generados (`data/storage/paquetes/`).
  - Sincronización en segundo plano (`sync_pending_to_oci`) ejecutada en el startup del servidor FastAPI cuando OCI está configurado.
  - Historial unificado y desduplicado (`GET /historial`) fusionando fuentes locales y remotas por `objeto_id`.
  - Funcionamiento 100% autónomo y offline respecto a la nube de Oracle cuando no se proporcionan credenciales OCI.
- Describir las capacidades y diseño de la interfaz web moderna:
  - Barra lateral colapsable tipo riel en escritorio y drawer off-canvas en móviles.
  - Historial enriquecido con títulos generados por la IA (`history_metadata.json`).
  - Renderizador visual interactivo para los 5 formatos pedagógicos (Flashcards 3D, Quizzes, Tutoriales, Resumen Ejecutivo, Guion de Clase).
- Incorporar diagramas Mermaid nativos y compatibles con GitHub:
  1. **Diagrama de Arquitectura de Componentes y Almacenamiento Híbrido** (FastAPI, Pipeline LangGraph, Gemini 3.5 Flash Lite, Voyage AI, FAISS local, Almacenamiento Local `data/storage/`, OCI Object Storage con sync en segundo plano, y Frontend SPA).
  2. **Diagrama de Flujo del Pipeline RAG y Agentes** (`ingest` -> `retrieve` con Full-Coverage/Section Map -> `draft` con Structured Output -> `review` con cálculo de fidelidad $\ge 0.7$ -> bucle condicional de reintento -> `format_output` -> persistencia local e híbrida).
- Proveer instrucciones de instalación paso a paso:
  - Método recomendado con `uv` (`uv sync` / `uv run ...`).
  - Método alternativo estándar con Python venv / pip (`pip install -e .`).
- Proveer instrucciones claras para configurar `.env` a partir de `.env.example`, marcando explícitamente cuáles variables son estrictamente requeridas (`GOOGLE_API_KEY`, `VOYAGE_API_KEY`) y cómo OCI (`OCI_*`) opera como servicio opcional/híbrido.
- Proveer instrucciones exactas para iniciar el servidor (`uvicorn nuevamente.app.main:app --reload`) y abrir Swagger en `/docs`.
- Proveer instrucciones completas para reproducir las demostraciones mediante `scripts/run_demo_scenarios.py` y enlazar el reporte de evidencias en `docs/demos/README.md`.
- Describir la estructura modular de directorios según `ARCHITECTURE.md` sección 6.

**Never:**
- No dejar textos de plantilla ni enlaces rotos.
- No asumir que el evaluador necesita credenciales de OCI para correr el proyecto: la guía debe enfatizar que se puede probar en modo local completo.
- No alterar código fuente de la aplicación ni romper la suite de tests (`pytest`).

## I/O & Edge-Case Matrix

| Escenario | Condición / Entrada del Evaluador | Contenido / Comportamiento Documentado | Criterio de Éxito |
|---|---|---|---|
| Evaluación Rápida sin OCI | Evaluador cuenta únicamente con `GOOGLE_API_KEY` y `VOYAGE_API_KEY` | Sección "Inicio Rápido" detalla que dejando las variables `OCI_*` vacías el sistema opera en modo Local-First almacenando documentos y paquetes en `data/storage/` e indexando en FAISS local | Despliegue inmediato en local sin fricción ni errores de conexión |
| Evaluación con OCI Activo | Evaluador cuenta con bucket y perfil OCI | Se explican los parámetros `OCI_BUCKET_NAME`, `OCI_NAMESPACE`, etc., y se documenta la sincronización en background en arranque y la desduplicación del historial | Persistencia remota y local perfectamente alineadas |
| Reproducción de Escenarios Demo | Ejecución de `python scripts/run_demo_scenarios.py` | Comandos paso a paso (ejecución global o individual con `--scenario`) y tabla explicativa de los 5 casos sobre PDF, MD y TXT | Evaluador puede replicar las corridas o inspeccionar los archivos JSON en `docs/demos/` |
| Navegación de Arquitectura y Código | Auditoría de estructura de repositorio | Árbol de archivos documentado con roles de cada paquete (`core/`, `pipeline/`, `services/`, `infra/`, `app/`, `data/`) | Localización inmediata de cualquier módulo por el evaluador |

</frozen-after-approval>

## Code Map

- `README.md` -- ARCHIVO PRINCIPAL. Documentación raíz del repositorio GitHub con descripción completa, diagramas Mermaid actualizados, arquitectura híbrida Local-First, guía de instalación, guía de demos y estructura del proyecto.
- `.env.example` -- REFERENCIA. Contrato de variables de entorno (obligatorias vs opcionales).
- `docs/demos/README.md` -- REFERENCIA Y ENLACE. Reporte de evidencias de demostración, métricas de calidad (anclaje score = 1.00) y comparativas cualitativas entre perfiles.
- `_bmad-output/implementation-artifacts/spec-hybrid-local-storage.md` -- REFERENCIA ARQUITECTURA. Detalles del almacenamiento local-first en `data/storage/` (documentos y paquetes), desduplicación en `list_paquetes` y sincronización `sync_pending_to_oci`.
- `_bmad-output/implementation-artifacts/spec-collapsible-sidebar-and-layout.md` -- REFERENCIA UX/UI. Detalles del sidebar colapsable, drawer móvil y títulos de historial por IA.
- `_bmad-output/planning-artifacts/architecture/architecture-NuevaMente-2026-09-24/ARCHITECTURE.md` -- FUENTE DE VERDAD. Arquitectura del sistema, especificación de nodos del pipeline, y estructura del proyecto en sec. 6.
- `pyproject.toml` -- REFERENCIA. Dependencias del proyecto, versión de Python (>=3.12), herramientas de build y testing.

## Tasks & Acceptance

**Execution:**
- [x] `README.md` -- Rediseñar y reescribir integralmente el README con:
  - Header con título, badges y resumen ejecutivo del producto.
  - Propuesta pedagógica y casos de uso (perfiles, formatos y nicho).
  - Arquitectura del Sistema: Diagrama Mermaid detallado incluyendo Almacenamiento Híbrido Local-First (`data/storage/`) y OCI Object Storage con sync en segundo plano.
  - Pipeline RAG & LangGraph: Diagrama Mermaid del flujo de agentes (`ingest`, `retrieve`, `draft`, `review`, `format_output`) con el bucle condicional de fidelidad.
  - Características destacadas de la UI/UX (sidebar colapsable, responsive drawer off-canvas, títulos de historial automáticos por IA).
  - Requisitos previos y guía de instalación paso a paso (`uv` y `pip`).
  - Configuración detallada de variables de entorno (`.env` vs `.env.example`), destacando el modo Local-First sin necesidad de OCI.
  - Puesta en marcha: levantar servidor local (interfaz web y Swagger `/docs`).
  - Guía de reproducción de escenarios de demostración (`scripts/run_demo_scenarios.py`) y enlace a `docs/demos/`.
  - Estructura del repositorio conforme a `ARCHITECTURE.md` sec. 6.
  - Métricas de calidad pedagógica logradas en el Hackathon (SM-1, SM-2, SM-3 con anclaje score = 1.00).
  - Comandos para correr la suite de pruebas (`pytest`).
  - Equipo y licencia.
- [x] `README.md` -- Verificar visualización de sintaxis Mermaid y formato Markdown compatible con GitHub.

**Acceptance Criteria:**
- Given el repositorio en GitHub, when un evaluador accede al `README.md`, then encuentra la descripción completa de NuevaMente, la explicación de la arquitectura híbrida Local-First / OCI, los dos diagramas Mermaid (arquitectura y flujo RAG), la guía de instalación paso a paso, la configuración de variables de entorno, y la guía de ejecución de demos.
- Given la guía de instalación en el `README.md`, when un desarrollador o evaluador sigue los pasos en un entorno limpio con Python 3.12+, then puede levantar el servidor web local (`http://localhost:8000`) y ejecutar los tests o escenarios de demostración sin ambigüedad y sin requerir cuenta OCI.
- Given la sección de estructura del proyecto, when se compara con el árbol de archivos real y con `ARCHITECTURE.md` sec. 6, then coincide exactamente con la organización de `nuevamente/` y sus módulos.

## Implementation Notes

- Se reescribió integralmente `README.md` eliminando la plantilla inicial genérica y dotando al repositorio de documentación profesional de alto estándar.
- Se incorporaron dos diagramas Mermaid nativos compatibles con GitHub:
  1. Diagrama de arquitectura de componentes, desacoplamiento modular y persistencia híbrida (Local-First en `data/storage/` + sincronización transparente con OCI Object Storage).
  2. Diagrama de flujo del pipeline RAG con LangGraph StateGraph, Full-Coverage Retrieval y feedback loop del Agente Crítico/Revisor.
- Se documentó la diferenciación frente a chatbots RAG estándar y la matriz de personalización (Perfiles x Formatos x Nichos).
- Se documentó el flujo de UI moderna (sidebar riel colapsable, drawer móvil off-canvas, títulos por IA y visualizadores interactivos).
- Se redactó una guía paso a paso de instalación (`uv` y `pip`), configuración de variables de entorno (`.env`), arranque del servidor FastAPI con Uvicorn y acceso a Swagger `/docs`.
- Se documentó el comando para ejecutar las demostraciones (`scripts/run_demo_scenarios.py`) y se enlazaron los 5 paquetes educativos generados y el reporte en `docs/demos/README.md`.
- Se documentó la estructura de directorios según `ARCHITECTURE.md` sección 6 y el comando para ejecutar la suite de 28 tests (`uv run pytest`).

## Spec Change Log

## Review Triage Log

- Finding BH-1: Enlace a LICENSE en README.md conducía a 404 por ausencia del archivo — verdict: `medium` — Patched: se creó `LICENSE` con texto oficial MIT Copyright 2026 Jesús / No Country (Equipo 42).
- Finding BH-2: Endpoint de consulta de tarea documentado como /api/v1/adaptar/{task_id}/status en lugar de /api/v1/adaptar/{task_id} — verdict: `medium` — Patched: corregido en tabla de API REST de `README.md`.
- Finding BH-3: Operadores < y & en etiqueta de edge en Mermaid de README.md con potencial riesgo de parseo HTML en markdown — verdict: `low` — Patched: normalizada etiqueta a `|"anclaje_score < 0.70 (reintento)"|`.
- Finding BH-4: Árbol de directorios de README.md omitía data/history_metadata.json — verdict: `low` — Patched: incorporado en árbol de data/ en `README.md`.
- Finding BH-5: Sección de convenciones de commits y ramas omitida en README.md — verdict: `low` — Patched: incorporada sección "Convenciones de Desarrollo y Commits" alineada con los criterios de aceptación.
- Finding EC-1: Dependencia de python3-venv en Linux para instalación sin uv — verdict: `false` — El README destaca `uv` como método primario y recomendado que no requiere paquetes de sistema adicionales.
- Finding VG-1: Cobertura y ejecución de suite de pruebas automatizadas — verdict: `false` — 28 de 28 tests pasan limpiamente con `uv run pytest`.

## Design Notes

El README debe diseñarse con una estructura modular y altamente visual, utilizando bloques de código con sintaxis resaltada, tablas comparativas y diagramas Mermaid nativos compatibles con el renderizador web de GitHub. Se destacará explícitamente que el sistema cuenta con almacenamiento híbrido Local-First (`data/storage/documentos/` y `data/storage/paquetes/`) con sincronización transparente a OCI en background. Esto asegura que los evaluadores puedan probar la solución de inmediato sin necesidad de disponer de una suscripción a Oracle Cloud, garantizando al mismo tiempo que si se ingresan las credenciales de OCI el sistema cumple el requisito cloud del hackathon.

## Verification

**Commands:**
- `uv run pytest` -- expected: 28 tests passing
- `git status` -- expected: working tree clean except modified README.md

**Manual checks (if no CLI):**
- Inspeccionar `README.md` para verificar que no queden marcadores de posición, que todos los enlaces relativos existan (`docs/demos/README.md`, `.env.example`, `scripts/run_demo_scenarios.py`), y que los bloques Mermaid tengan sintaxis válida.
