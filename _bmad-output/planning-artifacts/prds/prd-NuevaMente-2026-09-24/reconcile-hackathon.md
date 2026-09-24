# Reconciliación: Definición del Hackathon ONE G10 (hackaton-42.pdf)

**Input:** `/home/lucky_tv/proj/dev_one-nuevamente/hackaton-42.pdf`

## Veredicto: ✅ Cubierto — todos los requisitos obligatorios trazados

## Checklist de Requisitos Mínimos del Hackathon

| Requisito (textual del PDF) | Capturado en PRD | FR/SM |
|---|---|---|
| ☐ Ingestión funcional de documentos técnicos (PDF, Markdown o texto) | ✅ | FR-1, FR-2 |
| ☐ RAG con chunking, embeddings y búsqueda vectorial en Vector Store | ✅ | FR-3, FR-4, FR-7 |
| ☐ Orquestación con LLM (Gemini, OpenAI, Claude o equivalente) | ✅ | FR-7, FR-8, FR-9 (Gemini Flash + LangGraph) |
| ☐ Adaptación comprobada para ≥2 perfiles y ≥2 formatos | ✅ | FR-5, FR-8 (5 formatos, 4 perfiles), SM-1 |
| ☐ Salida JSON estructurada + interfaz/API operativa | ✅ | FR-10, FR-11, FR-14 (API) + FR-16-20 (UI) |
| ☐ OCI Object Storage (Always Free) para persistencia | ✅ | FR-12, FR-13 |
| ☐ ≥3 ejemplos de ejecución con documentaciones reales | ✅ | SM-4, Addendum (escenarios de demo) |
| ☐ Documentación completa en GitHub con diagrama arquitectura | ✅ | §6.1 En Alcance (último bullet) |

## Entregables del Hackathon

| Entregable | Capturado | Nota |
|---|---|---|
| 1. IA Generativa, RAG & Agentes (notebooks/módulos) | ✅ | §4.1-4.3 features completas |
| 2. Back-End, Automatización & Interfaz | ✅ | §4.6 API + §4.7 UI |
| 3. OCI Always Free (Object Storage obligatorio) | ✅ | §4.5 |
| 4. Documentación & Demostración | ✅ | §6.1, Addendum escenarios |

## Diferenciales opcionales del Hackathon

| Diferencial | En PRD | Estado |
|---|---|---|
| Despliegue en OCI Compute | §6.2 (fuera MVP) | Opcional, deseable |
| Sistema multi-agente con LangGraph | §4.3, FR-7/8/9 | ✅ En MVP |
| Quizzes con evaluación en tiempo real | §6.2 (fuera MVP) | Opcional, deseable |
| Soporte multimodal | §6.2 (fuera MVP) | v2+ |
| Exportación multiformato | §6.2 (fuera MVP) | Opcional, deseable |

## Gaps encontrados

1. **El hackathon sugiere Streamlit o Gradio.** El PRD optó por HTML estático servido por FastAPI. Esto es válido — el PDF dice "Streamlit, Gradio, FastAPI, Flask o equivalente" — pero vale notar que no es la opción sugerida por defecto. No es un gap sino una decisión deliberada (bajo consumo de recursos).

2. **Directrices técnicas — Docling no mencionada.** El hackathon no menciona Docling, pero el proyecto de referencia `raggraph` lo usa. El PRD dice "[ASSUMPTION: Se usa PyPDF o equivalente]". La herramienta de extracción específica se resuelve en implementación. No es gap.

3. **Formato de ejemplo del hackathon incluye `nivel_detalle`.** El JSON de ejemplo del PDF incluye un campo `nivel_detalle: "Didactico"` que el PRD no captura como parámetro separado — está implícito en el Perfil del Destinatario. Decisión legítima de simplificación.
