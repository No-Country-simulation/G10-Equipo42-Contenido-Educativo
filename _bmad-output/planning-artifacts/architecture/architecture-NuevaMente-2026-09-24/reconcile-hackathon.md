# Reconciliación: Definición del Hackathon ONE G10 (hackaton-42.pdf)

**Input:** `/home/lucky_tv/proj/dev_one-nuevamente/hackaton-42.pdf`

## Veredicto: ✅ Cubierto — todos los requisitos obligatorios trazados, diferenciales clave incluidos

## Requisitos Mínimos del Hackathon

| Requisito (del PDF) | Trazado en Spine | AD / Componente |
|---|---|---|
| ☐ Ingestión funcional de documentos técnicos (PDF, Markdown o texto) | ✅ | AD-1, AD-5 → `services/ingestion.py` |
| ☐ RAG con chunking, embeddings y búsqueda vectorial en Vector Store | ✅ | AD-3, AD-8 → FAISS + Voyage AI + stratified retrieval |
| ☐ Orquestación con LLM | ✅ | AD-2 → LangGraph grafo determinista, Gemini 3.5 Flash Lite |
| ☐ Adaptación comprobada para ≥2 perfiles y ≥2 formatos | ✅ | AD-6 → 4 perfiles, 5 formatos con modelos Pydantic separados |
| ☐ Salida JSON estructurada + interfaz/API operativa | ✅ | AD-6 (structured output), AD-7 (API), AD-11 (UI) |
| ☐ OCI Object Storage (Always Free) | ✅ | AD-9 → fire-and-forget con dos prefijos |
| ☐ ≥3 ejemplos de ejecución con documentaciones reales | ✅ | Addendum PRD: 3 escenarios con Python 3.14 docs |
| ☐ Documentación completa en GitHub con diagrama de arquitectura | ✅ | ARCHITECTURE.md con diagramas Mermaid |

## Entregables del Hackathon

| Entregable | Trazado | Nota |
|---|---|---|
| 1. IA Generativa, RAG & Agentes | ✅ | AD-2, AD-3, AD-6 — pipeline completo |
| 2. Back-End, Automatización & Interfaz | ✅ | AD-5, AD-7, AD-11 — FastAPI + UI |
| 3. OCI Always Free (Object Storage obligatorio) | ✅ | AD-9, AD-11 |
| 4. Documentación & Demostración | ✅ | ARCHITECTURE.md |

## Diferenciales del Hackathon en la Arquitectura

| Diferencial | En arquitectura | Estado |
|---|---|---|
| Sistema Multi-Agente con LangGraph | AD-2 (grafo con 3 agentes) | ✅ En MVP |
| Despliegue en OCI Compute | AD-11 (Uvicorn + systemd) | ✅ En MVP |
| Quizzes con evaluación en tiempo real | Diferido (fuera MVP) | Opcional |
| Soporte multimodal | Diferido (v2+) | Opcional |
| Exportación multiformato | Diferido (fuera MVP) | Opcional |

## Directrices Técnicas

| Directriz del Hackathon | Cumplimiento |
|---|---|
| LLM: Gemini, OpenAI, Claude o equivalente | ✅ Gemini 3.5 Flash Lite |
| RAG: LangChain + PyPDF + ChromaDB/FAISS | ✅ LangChain + FAISS (mejor para 1GB RAM) |
| Structured outputs con Pydantic | ✅ AD-6 (with_structured_output) |
| Interfaz: Streamlit, Gradio, FastAPI, Flask | ✅ FastAPI con UI estática |
| OCI Object Storage obligatorio | ✅ AD-9 |

## Gaps encontrados

Ninguno.
