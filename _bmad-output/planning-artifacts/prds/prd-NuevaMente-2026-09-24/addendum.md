---
title: "NuevaMente — Addendum al PRD"
created: 2026-09-24
updated: 2026-09-24
---

# Addendum: PRD NuevaMente

Este addendum preserva profundidad técnica, decisiones de implementación y material de referencia que informa al PRD pero no pertenece a él.

## Stack Confirmado

| Componente | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.12 | Ecosistema ML/AI maduro, requisito del hackathon |
| Orquestación de agentes | LangGraph | Grafos de decisión con estado, feedback loops, modularidad |
| LLM | Gemini Flash | Balance costo/velocidad/calidad para el volumen del MVP |
| Embeddings | Voyage AI | Calidad de embeddings superior para retrieval semántico |
| Vector Store | FAISS | Consumo de memoria significativamente menor que ChromaDB. Crítico para 1GB RAM |
| Schemas | Pydantic | Tipado estricto, validación de entrada/salida, integración nativa con FastAPI |
| API Framework | FastAPI | Documentación auto-generada, async-ready, typing nativo |
| Persistencia | OCI Object Storage | Requisito obligatorio del hackathon (capa Always Free) |

## Restricciones de Infraestructura

- **OCI Always Free**: 1 GB RAM, 1 OCPU. Única instancia disponible.
- FAISS preferido sobre ChromaDB por consumo de memoria (~10x menor para índices pequeños).
- La instancia puede no ser suficiente para documentos muy grandes — el pipeline debe fallar limpiamente antes de OOM.
- API-first con UI incluida en MVP: interfaz web ligera servida como HTML estático por FastAPI. Framework SPA/avanzado queda para v2.

## El Problema de la Query RAG No-Convencional

NuevaMente NO es un chatbot RAG convencional. No hay "mensaje del usuario" que sirva como query de búsqueda vectorial. El usuario sube un documento + selecciona parámetros.

**Opciones a evaluar en arquitectura:**
1. **Queries sintéticas por sección**: el Agente Investigador analiza la estructura del documento (encabezados, temas) y genera queries temáticas para recuperar chunks relevantes por área.
2. **Retrieval por outline**: primero se genera un outline del documento, luego se recuperan chunks por cada punto del outline.
3. **Full-document para documentos cortos**: si el documento cabe entero en el context window del LLM, se pasa completo sin retrieval. FAISS se usa igualmente para el score de fidelidad.
4. **Namespace/filtro por doc_id**: con la persistencia de índice FAISS en disco local (`save_local`/`load_local`), cada documento puede tener su propio directorio de índice identificado por doc_id.

La opción 1 o 2 son las más probables para el MVP. La 3 es un fast-path para documentos cortos.

## Documentación de Demo y Pruebas

Ubicación: `~/proj/dev_one-nuevamente/documentacion/`

### Python 3.14 Docs (plaintext) — 16 MB
- `tutorial/classes.txt` (922 líneas) — candidato principal: denso, enseñable, contraste fuerte principiante vs avanzado
- `tutorial/datastructures.txt` (717 líneas) — muy práctico, buen contraste por nicho
- `tutorial/errors.txt` (686 líneas) — excepciones, buen ejemplo para tutorial paso a paso

### LangChain Docs (markdown) — 63 MB
- `concepts/*.mdx` — conceptos de alto nivel, buenos para adaptar a diferentes perfiles
- `langgraph/*.mdx` — material denso y reciente

### Escenarios de demo planificados
1. **Mismo documento, distintos perfiles**: `classes.txt` → Flashcards/Principiante vs Resumen Ejecutivo/Líder Técnico.
2. **Mismo documento, distintos formatos**: `datastructures.txt` → Tutorial vs Quiz vs Flashcards, mismo perfil.
3. **Nicho personalizado**: `classes.txt` → perfil Junior, nicho libre "veterinario aprendiendo a programar".

## Checklist de Evaluación del Hackathon (Trazabilidad)

| Requisito | FR/Feature que lo cubre |
|---|---|
| ☐ Ingestión funcional de documentos técnicos (PDF, Markdown o texto) | FR-1, FR-2 |
| ☐ RAG con chunking, embeddings y búsqueda vectorial | FR-3, FR-4, FR-7 |
| ☐ Orquestación con LLM | FR-7, FR-8, FR-9 (LangGraph) |
| ☐ Adaptación comprobada para ≥2 perfiles y ≥2 formatos | FR-5, FR-8, SM-1 |
| ☐ Salida JSON estructurada + interfaz/API operativa | FR-10, FR-11, FR-14 |
| ☐ OCI Object Storage (Always Free) | FR-12, FR-13 |
| ☐ ≥3 ejemplos de ejecución con documentación real | SM-4 (escenarios de demo) |
| ☐ Documentación completa en GitHub con diagrama de arquitectura | Fuera del PRD (documentación) |

## Línea de Tiempo

- **Inicio**: 23 de septiembre de 2026
- **Entrega**: 26 de octubre de 2026 (~33 días)
- **Equipo**: 1 persona (Jesus), desarrollo asistido por IA
- **Estrategia**: MVP obligatorio primero → opcionales incrementales

## Landscape y Contexto Competitivo

NuevaMente se diferencia del estado del arte en RAG educativo (2025-2026) en un punto específico: **transformación, no conversación**. La mayoría de los sistemas RAG en EdTech son chatbots tutores (pregunta-respuesta). NuevaMente transforma un documento entero en un producto educativo nuevo — esto es conceptualmente distinto y técnicamente más exigente.

El agentic RAG con LangGraph (supervisor → especialistas → revisor) está alineado con las mejores prácticas actuales para pipelines de producción de contenido educativo.
