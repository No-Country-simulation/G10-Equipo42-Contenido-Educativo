# Epic 4 Context: Escenarios de Demostración y Documentación

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Permitir que los evaluadores del hackathon verifiquen el funcionamiento end-to-end de NuevaMente mediante la ejecución reproducible de al menos 3 escenarios con documentación real técnica (PDF, MD, TXT), garantizando un repositorio ordenado, documentado (README, diagramas, guía de instalación) y con evidencias de calidad pedagógica y anclaje a la fuente. Cubre los requisitos obligatorios de evaluación del hackathon (requisitos 7 y 8).

## Stories

- Story 4.1: Ejecución de Escenarios de Demostración
- Story 4.2: Documentación del Repositorio GitHub

## Requirements & Constraints

- El sistema debe procesar documentos reales en los 3 formatos soportados: PDF, Markdown (.md) y Texto plano (.txt).
- Se deben cubrir variaciones significativas en los tres parámetros de adaptación:
  - Mismo documento con diferentes perfiles de destinatario (demostrando diferenciación de complejidad y enfoque).
  - Mismo documento con diferentes formatos pedagógicos (Flashcards, Quiz, Tutorial, Resumen Ejecutivo, Guion de Clase).
  - Nicho sectorial personalizado (demostrando contextualización por vocabulario y analogías).
- Criterios de calidad verificables:
  - Diferenciación lingüística y estructural evidente entre perfiles (SM-1).
  - Salida JSON 100% válida contra los schemas Pydantic definidos en `core/schemas.py` (SM-2).
  - `anclaje_fuente_score` $\ge 0.7$ en todos los escenarios (SM-3).
- Resiliencia y almacenamiento:
  - Los paquetes generados deben quedar registrados localmente y en OCI Object Storage (best-effort), siendo consultables desde el historial.
  - Las evidencias de ejecución (documentos fuente, parámetros y outputs generados) deben quedar archivadas en el repositorio para su reproducción inmediata.

## Technical Decisions

- **Fuentes de documentación de prueba:**
  - PDF: Documento técnico real de infraestructura (ej. `Visión general OCI VCN.pdf`).
  - Markdown: Documentación técnica conceptual moderna (ej. `langchain_vs_langgraph.md` o `langgraph_memory.md`).
  - TXT: Documentación oficial de Python 3.14 (ej. `tutorial/classes.txt` o `tutorial/datastructures.txt`).
- **Scripts de automatización/reproducción:**
  - Disponibilizar un script CLI o endpoint de ejecución de demos que permita reproducir las llamadas sin necesidad de carga manual si el evaluador lo prefiere, o ejecutables vía API/web.
  - Guardar los paquetes educativos resultantes en una carpeta estructurada de demos o fixtures para inspección directa sin costo de tokens para el evaluador.

## Cross-Story Dependencies

- Story 4.1 genera las corridas de demo, valida los outputs JSON y recopila las métricas/evidencias.
- Story 4.2 utiliza las evidencias y escenarios validados en Story 4.1 para incorporarlos en el `README.md` junto con los diagramas de arquitectura y la guía de instalación.
