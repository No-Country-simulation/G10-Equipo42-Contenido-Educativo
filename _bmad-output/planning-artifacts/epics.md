---
stepsCompleted: []
inputDocuments:
  - _bmad-output/planning-artifacts/prd-nuevamente-2026-09-22/prd.md
  - _bmad-output/planning-artifacts/prd-nuevamente-2026-09-22/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-nuevamente-2026-09-22/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-nuevamente-2026-09-22/SOLUTION-DESIGN.md
---

# NuevaMente - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for NuevaMente, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR1:** El sistema debe permitir la carga e ingestión de archivos técnicos en formatos `.pdf`, `.md` (Markdown) y `.txt` (texto sin formato), así como el ingreso directo de texto vía interfaz web.
- **FR2:** El sistema debe normalizar y limpiar el texto extraído eliminando caracteres especiales, encabezados/pies de página repetitivos y saltos de línea anómalos antes de la segmentación.
- **FR3:** El sistema debe segmentar el texto extraído mediante una estrategia con solapamiento configurable (`chunk_size=800`, `chunk_overlap=150` caracteres por defecto) preservando límites de párrafos o secciones.
- **FR4:** El sistema debe generar embeddings exclusivamente mediante el modelo `voyage-multilingual-2` de Voyage AI para todos los chunks con dimensión vectorial fija de 1024d.
- **FR5:** El sistema debe indexar los embeddings en una colección persistente de ChromaDB y recuperar los K fragmentos más relevantes (K=5 por defecto) mediante búsqueda semántica por similitud de coseno en menos de 1.5 segundos.
- **FR6:** El sistema debe recibir obligatoriamente parámetros de adaptación pedagógica:
  - Perfil del Destinatario: Principiante / Transición, Junior / Semi Senior, Líder Técnico / Arquitecto, Gestor / Ejecutivo.
  - Formato Pedagógico: Tutorial / Guía Práctica, Flashcards de Memorización, Quiz Interactivo con Justificaciones, Resumen Ejecutivo (TL;DR), Guion de Clase.
  - Nicho de Aplicación: Fintech, Salud, E-commerce, General.
  - Nivel de Detalle: Didáctico, Técnico, Conciso.
- **FR7:** El sistema debe implementar una capa de abstracción LLM compatible con la API OpenAI Chat Completions (`/v1/chat/completions`) usando Google Gemini Flash por defecto e intercambiable mediante variables de entorno (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`) sin cambios en el código de negocio.
- **FR8:** La salida generada por el LLM debe ajustarse estrictamente al esquema JSON oficial especificado por el Hackathon ONE, validado mediante modelos Pydantic v2 (`status`, `metadatos`, `contenido_adaptado`, `evaluacion_calidad`, `almacenamiento_oci`).
- **FR9:** El sistema debe evaluar automáticamente el contenido generado contra los chunks recuperados emitiendo `anclaje_fuente_score` (0.0 a 1.0) y ejecutar un ciclo de auto-reflexión / reintento (hasta 2 reintentos) si el score es inferior al umbral configurable (0.85 para perfiles técnicos, 0.80 para perfiles ejecutivos).
- **FR10:** El sistema debe persistir el archivo fuente original en el bucket `nuevamente-documentos-origen` y el JSON estructurado generado en `nuevamente-contenidos-educativos` de OCI Object Storage Always Free usando el SDK oficial (`oci`), generando un `objeto_id` único `{formato}-{perfil_slug}-{timestamp}.json` con `status_upload="completado"`.
- **FR11:** El sistema debe proporcionar un modo Mock Local activado mediante `OCI_MOCK=true` que almacena los archivos localmente en `./mock_oci_storage/{bucket_name}/{objeto_id}` emitiendo `status_upload="mock_local"`, garantizando un contrato Pydantic idéntico y determinístico para desarrollo sin conexión.
- **FR12:** La interfaz interactiva en Streamlit debe proveer componentes de carga de archivos (`st.file_uploader`), selectores desplegables para Perfil, Formato, Nicho y Nivel de Detalle, y el botón principal "Generar Contenido Educativo".
- **FR13:** La interfaz Streamlit debe mostrar el avance del pipeline en tiempo real mediante `st.status()` reflejando los 5 sub-pasos secuenciales (Ingestión → Indexación RAG → Generación Didáctica → Evaluación de Fidelidad → Almacenamiento en OCI), indicando reintentos de auto-reflexión con el sufijo `(reintento N/2)` sin retroceder visualmente.
- **FR14:** La interfaz Streamlit debe renderizar interactivamente el material generado según el formato seleccionado:
  - Flashcards interactivas con animación flip (frente / dorso / pista didáctica).
  - Quizzes interactivos con selección de opciones y justificación explicativa inmediata.
  - Tutoriales paso a paso con bloques de código y syntax highlighting.
  - Resúmenes ejecutivos estructurados por puntos clave de alto impacto.
  - Panel lateral con métricas de fidelidad (`anclaje_fuente_score`), tiempo estimado de estudio, confirmación de persistencia OCI y botón de descarga del JSON oficial.

### NonFunctional Requirements

- **NFR1 (Costo Cero en Nube):** Todas las dependencias de nube deben operar estrictamente bajo la capa Always Free de Oracle Cloud Infrastructure (OCI Object Storage: 10 GB y 50,000 llamadas API/mes gratuitas).
- **NFR2 (Stack Tecnológico Fijado):** Python 3.12, Streamlit (>=1.38.0), LangGraph (>=0.2.0), LangChain Core (>=0.3.0), Voyage AI `voyage-multilingual-2` (1024d), ChromaDB (>=0.5.5 local persistente), Google Gemini Flash (1.5/2.0), Pydantic v2 (>=2.8.0), PyPDF (>=4.3.0), OCI SDK (`oci` >=2.130.0).
- **NFR3 (Latencia y Rendimiento):** Tiempo total de procesamiento y generación inferior a 30 segundos por documento promedio (1 a 10 páginas) para flujo nominal sin reintentos; tiempo de consulta vectorial en ChromaDB < 1.5 segundos.
- **NFR4 (Fidelidad Técnica y Calidad RAG):** El 100% de las respuestas generadas en los escenarios de prueba deben alcanzar `anclaje_fuente_score` ≥ 0.85 para perfiles técnicos y ≥ 0.80 para perfiles ejecutivos.
- **NFR5 (Integridad de Contrato):** El 100% de las respuestas exitosas deben validar contra el modelo Pydantic v2 `EducationalContentPackage` sin fallas de serialización/deserialización JSON.
- **NFR6 (Resiliencia y Manejo de Errores):** Captura amigable de excepciones de red y APIs externas sin exponer stack traces en la UI; retries automáticos con retroceso exponencial (`tenacity`) ante rate limits HTTP 429 de Voyage AI o Gemini.
- **NFR7 (Seguridad y Privacidad de Credenciales):** Las credenciales y claves de API (`GEMINI_API_KEY`, `VOYAGE_API_KEY`, credenciales OCI) deben gestionarse exclusivamente mediante variables de entorno (`.env` o `secrets.toml`) y estar excluidas de Git.
- **NFR8 (Portabilidad y Modo Offline):** Modo Mock Local que permite clonar el repositorio y ejecutar la aplicación al 100% de sus capacidades de forma local u offline sin requerir cuenta ni credenciales de Oracle Cloud.

### Additional Requirements

- **Starter Template / Arquitectura Hexagonal:** Aplicación modular limpia basada en Puertos y Adaptadores (`core/`, `domain/`, `services/`, `pipeline/`, `ui/`, `app.py`).
- **ARCH-1 (Orquestación con LangGraph StateGraph - AD-1):** Pipeline implementado como un `StateGraph` de 5 nodos (`ingest`, `retrieve`, `generate`, `evaluate`, `persist`) comunicados mediante el `TypedDict` inmutable `PipelineGraphState`, consumido con `graph.stream()` desde Streamlit.
- **ARCH-2 (Ciclo de Auto-Reflexión y Reintento - AD-2):** Nodo `evaluate` que invoca un auditor LLM a `temperature=0.0`. Arista condicional: si `score < umbral` y `retry_count < 2`, retorna a `generate` inyectando feedback de discrepancia para auto-corrección; de lo contrario transiciona a `persist`.
- **ARCH-3 (Contratos Estrictos Pydantic v2 - AD-3):** Generación mediante `llm.with_structured_output(EducationalContentPackage)`. Ningún nodo ni componente debe manipular diccionarios libres o JSONs sin tipar.
- **ARCH-4 (Aislamiento de Estado en Streamlit - AD-4):** Estado del paquete activo almacenado en `st.session_state["active_package"]`; clientes pesados instanciados con `@st.cache_resource`; los componentes interactivos no deben re-ejecutar el grafo.
- **ARCH-5 (Aislamiento y Caché Semántico por SHA-256 - AD-5):** Colecciones en ChromaDB identificadas por el hash SHA-256 del texto extraído y normalizado (`doc_{sha256[:12]}`). Si la colección existe, se reutiliza el índice de inmediato evitando llamadas redundantes a Voyage AI.
- **ARCH-6 (Puerto de Almacenamiento Dual - AD-6):** Interfaz `StoragePort` con implementaciones intercambiables `OCIObjectStorageAdapter` y `MockLocalStorageAdapter`, seleccionadas automáticamente según presencia de credenciales o `OCI_MOCK=true`.
- **ARCH-7 (Factoría LLM OpenAI-Compatible - AD-7):** Servicio `LLMFactory` que expone el protocolo estándar de OpenAI Chat Completions API (`/v1/chat/completions`), parametrizable vía variables de entorno.
- **ARCH-8 (Convención de Nombres e Invariantes):** PascalCase para modelos y adaptadores, snake_case para archivos y nodos, marcas temporales en ISO-8601 UTC, nombrado determinístico `{formato}-{perfil_slug}-{timestamp}.json`.

### UX Design Requirements

- **UX-DR1 (Layout Principal y Configuración):** Interfaz Streamlit limpia y moderna (`app.py`), con barra lateral (sidebar) para configuración pedagógica y uploader de documentos, y área central para ejecución y visualización de resultados.
- **UX-DR2 (Panel de Progreso Reactivo):** Indicador de progreso con `st.status()` expandible con los 5 sub-pasos secuenciales (Ingestión, Indexación RAG, Generación Didáctica, Evaluación de Fidelidad, Almacenamiento en OCI), mostrando reactivamente `(reintento N/2)` si se activa auto-reflexión sin retroceder visualmente la barra.
- **UX-DR3 (Componente Interactivo de Flashcards):** Baraja interactiva (`ui/views/flashcards.py`) con efecto flip para alternar frente y dorso, botones de navegación anterior/siguiente y pista didáctica colapsable.
- **UX-DR4 (Componente Interactivo de Quizzes):** Cuestionario interactivo (`ui/views/quiz.py`) con opciones seleccionables, revelación inmediata de acierto/error y justificación técnica basada en la fuente original.
- **UX-DR5 (Componente de Visualización de Tutoriales):** Guía práctica (`ui/views/tutorial.py`) estructurada en pasos secuenciales con bloques de código resaltados por sintaxis y notas explicativas.
- **UX-DR6 (Componente de Resumen Ejecutivo):** Formato TL;DR (`ui/views/executive.py`) estructurado en tarjetas de alto impacto (Hallazgo principal, Impacto de negocio, Recomendación de acción).
- **UX-DR7 (Panel de Métricas y Exportación):** Indicadores visuales de calidad (`anclaje_fuente_score`), tiempo estimado de estudio, confirmación de persistencia OCI y botón para descargar el archivo JSON estructurado.

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}
