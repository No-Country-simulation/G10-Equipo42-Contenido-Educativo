---
title: "NuevaMente — Addendum al Product Brief"
created: 2026-09-23
updated: 2026-09-23
---

# Addendum: NuevaMente

## Restricciones de Infraestructura

- **OCI Always Free**: 1 GB RAM, 1 OCPU. Es la única instancia disponible del equipo en el tier gratuito.
- Toda decisión tecnológica debe pasar por este filtro de recursos.
- FAISS preferido sobre ChromaDB por consumo de memoria significativamente menor.
- Explorar si hay alternativas aún más ligeras que FAISS.

## Decisión Arquitectónica: API-First

- Construir primero la API REST (FastAPI) en lugar de una UI Streamlit/Gradio.
- La UI se decide después, priorizando bajo consumo de recursos y estética.
- Esto desacopla la lógica de negocio de la presentación.

## Problema Identificado: Estrategia de Query en RAG

El flujo de NuevaMente NO es un chatbot RAG convencional. No hay un "mensaje del usuario" que sirva como query de búsqueda vectorial. El usuario sube un documento + selecciona parámetros (perfil, formato, nicho). ¿Cómo se construye la query de retrieval?

**Análisis a resolver en arquitectura:**
- Opciones: RAG por documento (namespace/filtro por doc_id), queries sintéticas generadas por el LLM, chunking semántico con metadata enriquecida.
- Ver sección de Discovery en el brief para la resolución.

## Scope Incremental

- **Obligatorios primero**: Pipeline RAG funcional, adaptación multi-perfil/multi-formato, OCI Object Storage, salida JSON, interfaz operativa, 3 ejemplos de ejecución, documentación GitHub.
- **Opcionales a considerar**: quizzes con evaluación en tiempo real, despliegue OCI Compute, soporte multimodal, exportación multiformato.
- **Confirmado para MVP**: LangGraph multi-agente (Investigador RAG → Redactor Pedagógico → Crítico/Revisor).

## Línea de Tiempo

- **Inicio**: 23 de septiembre de 2026
- **Entrega**: 26 de octubre de 2026 (~33 días)
- **Equipo**: 1 persona (Jesus), desarrollo asistido por IA
- **Estrategia**: MVP obligatorio primero → opcionales incrementales

## Documentación para Demo y Pruebas

Ubicación: `~/proj/dev_one-nuevamente/documentacion/`

### Python 3.14 Docs (plaintext) — 16 MB
- `tutorial/classes.txt` (922 líneas) — excelente candidato: denso, enseñable, contraste fuerte principiante vs avanzado
- `tutorial/datastructures.txt` (717 líneas) — muy práctico, buen contraste por nicho
- `tutorial/errors.txt` (686 líneas) — excepciones, buen ejemplo para tutorial paso a paso
- `library/asyncio*.txt` (~8500 líneas total) — material extremadamente denso, ideal para mostrar adaptación a ejecutivo vs senior

### LangChain Docs (markdown) — 63 MB
- `concepts/*.mdx` — conceptos de alto nivel, buenos para adaptar a diferentes perfiles
- `langgraph/*.mdx` — material denso y reciente, ideal para demostrar que el sistema no depende de conocimiento previo del LLM

### Notas sobre la estrategia de demo
- El usuario propone permitir input libre en "nicho" además de opciones predeterminadas
- Compatible con apuntes propios del usuario (no solo documentación técnica formal)
- Considerar: ¿un archivo individual denso o compuesto de varios? → resolver durante implementación
