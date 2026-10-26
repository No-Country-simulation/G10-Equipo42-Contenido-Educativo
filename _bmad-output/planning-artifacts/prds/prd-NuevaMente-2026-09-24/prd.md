---
title: "NuevaMente — Sistema Inteligente de Adaptación y Generación de Contenido Educativo"
status: final
created: 2026-09-24
updated: 2026-09-24
---

# PRD: NuevaMente

## 0. Propósito del Documento

Este PRD define los requisitos funcionales y no funcionales de NuevaMente para su primera versión (MVP), orientada al Hackathon ONE G10 (Oracle Next Education & Alura) y al portfolio profesional de su creador. Está dirigido al propio desarrollador (Jesus) como guía de implementación, y a los evaluadores del hackathon como referencia de alcance y criterio técnico.

El vocabulario técnico del dominio se ancla en el **Glosario (§3)**. Los requisitos funcionales se agrupan por feature con IDs estables (FR-1 a FR-N). Las asunciones inferidas se marcan con `[ASSUMPTION]` inline y se indexan en §9. El documento se complementa con un **addendum** que preserva decisiones arquitectónicas, restricciones de infraestructura y material de profundidad técnica que excede el alcance de un PRD.

**Inputs existentes:** Product Brief NuevaMente (2026-09-23), Addendum al Brief, Definición del Hackathon ONE G10 (hackaton-42.pdf).

## 1. Visión

NuevaMente transforma documentación técnica densa en contenido educativo personalizado. No es un chatbot que responde preguntas — es un sistema de transformación que recibe un documento completo y produce un paquete educativo estructurado, adaptado al perfil del destinatario, al formato pedagógico elegido y al contexto de aplicación del usuario.

El mismo manual de Python que un principiante necesita como flashcards para memorizar conceptos, un líder técnico lo necesita como resumen ejecutivo para una decisión de arquitectura. NuevaMente automatiza esa adaptación — que hoy consume semanas de trabajo de especialistas — mediante un pipeline de RAG integrado con LLMs y orquestación multi-agente. Cada afirmación del contenido generado se ancla en el documento fuente, con un score de fidelidad que hace explícita y medible la distancia respecto al original.

El proyecto nace con dos propósitos honestos: ser una herramienta que su propio creador usaría para estudiar, y ser una pieza de portfolio que demuestre competencia de punta a punta en IA Generativa, RAG, orquestación de agentes y Oracle Cloud Infrastructure.

## 2. Usuario Objetivo

### 2.1 Jobs To Be Done

- **Aprender de documentación densa sin ahogarse en ella.** Un estudiante, profesional en transición o desarrollador junior tiene documentación rica que necesita dominar, pero el formato y nivel del material original le queda lejos de su punto de partida.
- **Producir material educativo sin ser diseñador instruccional.** Un profesor o líder técnico necesita generar quizzes, flashcards o tutoriales a partir de documentación existente, sin invertir semanas en adaptación manual.
- **Obtener una vista ejecutiva de contenido técnico.** Un gestor o ejecutivo no técnico necesita entender el qué y el por qué de un documento técnico sin leer 30 páginas de especificación.
- **Contextualizar el aprendizaje a mi realidad.** El usuario quiere que el contenido hable su idioma profesional — fintech, salud, e-commerce, o lo que sea — no en abstracto.

### 2.2 No-Usuarios (v1)

- Equipos que necesitan adaptación multilingüe (el sistema opera sólo en español en v1).
- Organizaciones que requieren multi-tenancy, autenticación, o control de acceso.
- Usuarios que esperan una experiencia de chatbot conversacional — NuevaMente no tiene campo de chat.

### 2.3 Journeys de Usuario Clave

- **UJ-1. Carla genera flashcards para su examen de Python.**
  - **Persona + contexto:** Carla, estudiante de informática en transición de carrera, tiene un examen sobre clases en Python en 3 días.
  - **Entry state:** Tiene descargado el archivo `classes.txt` (922 líneas) de la documentación oficial de Python 3.14.
  - **Path:** Abre la interfaz web, sube el archivo, selecciona perfil "Principiante", formato "Flashcards", nicho "General". Lanza la generación.
  - **Climax:** La interfaz muestra las flashcards renderizadas con frente/dorso/pista didáctica, conceptos clave, prerrequisitos y tiempo estimado de estudio (8 min). El `anclaje_fuente_score` muestra 0.95.
  - **Resolution:** Visualiza y estudia las flashcards directamente en la interfaz. Puede descargar el JSON para importar a Anki u otros sistemas.
  - **Edge case:** Si el documento es demasiado extenso para procesar de una vez, el sistema retorna un error descriptivo indicando la limitación.

- **UJ-2. Roberto necesita un resumen ejecutivo de VCN para su director.**
  - **Persona + contexto:** Roberto, líder técnico en una empresa fintech, necesita explicar qué es una VCN de OCI a su director no técnico para aprobar presupuesto.
  - **Entry state:** Tiene la documentación de VCN en formato Markdown.
  - **Path:** Abre la interfaz web, sube el documento, selecciona perfil "Gestor/Ejecutivo No Técnico", formato "Resumen Ejecutivo", nicho "Fintech". Lanza la generación.
  - **Climax:** La interfaz renderiza el resumen ejecutivo con lenguaje de negocio, contextualizado a fintech, con conceptos clave y sin jerga técnica innecesaria.
  - **Resolution:** Comparte el resumen con su director. La conversación de presupuesto avanza sin necesidad de una reunión técnica de 2 horas.

- **UJ-3. Profesora Marta genera un quiz para sus alumnos.**
  - **Persona + contexto:** Marta, profesora de programación en un bootcamp, necesita evaluar comprensión de estructuras de datos.
  - **Entry state:** Tiene el capítulo `datastructures.txt` de Python 3.14.
  - **Path:** Abre la interfaz web, sube el documento, selecciona perfil "Principiante", formato "Quiz Interactivo", nicho "General". Lanza la generación.
  - **Climax:** La interfaz muestra el quiz interactivo: Marta puede ver las preguntas renderizadas con opciones, respuesta correcta y justificación anclada al documento fuente.
  - **Resolution:** Usa el quiz directamente en su próxima clase. Puede re-seleccionarlo desde el historial de la barra lateral si necesita volver a consultarlo.

## 3. Glosario

- **Documento Fuente** — Archivo técnico (PDF, Markdown o texto plano) subido por el usuario como input del sistema. Es la única fuente de verdad para la generación de contenido.
- **Paquete Educativo** — Salida JSON estructurada que contiene el contenido adaptado, metadatos pedagógicos y evaluación de fidelidad. Producto final de cada solicitud.
- **Perfil del Destinatario** — Nivel de conocimiento del receptor del contenido: Principiante, Desarrollador Junior/Semi Senior, Líder Técnico/Arquitecto, o Gestor/Ejecutivo No Técnico.
- **Formato Pedagógico** — Estructura de presentación del contenido adaptado: Tutorial Paso a Paso, Flashcards, Quiz Interactivo, Resumen Ejecutivo, o Guión de Clase.
- **Nicho/Contexto** — Dominio profesional que personaliza el lenguaje y los ejemplos: opciones predefinidas (Fintech, Salud, E-commerce, General) más texto libre.
- **Pipeline RAG** — Flujo de procesamiento que segmenta el Documento Fuente en chunks, genera embeddings vectoriales, los indexa, y los recupera para anclar la generación del LLM en el contenido original.
- **Chunk** — Fragmento semántico del Documento Fuente, resultado de la segmentación. Unidad mínima de indexación y retrieval.
- **Embedding** — Representación vectorial densa de un Chunk, generada por el modelo de embeddings (Voyage AI). Permite búsqueda por similitud semántica.
- **Vector Store** — Índice FAISS que almacena los Embeddings y permite búsqueda vectorial eficiente. Se persiste en disco local (`index.faiss` + `index.pkl`).
- **Anclaje a Fuente (Score)** — Métrica numérica (0.0-1.0) que mide cuánto del contenido generado está respaldado por el Documento Fuente. `[ASSUMPTION: MVP calcula el score mediante autoevaluación del LLM (heurística prompt-based); un método basado en comparación de embeddings se considera diferencial para v2.]`
- **Agente** — Nodo especializado dentro del grafo LangGraph que ejecuta una tarea específica del pipeline (investigación, redacción, revisión).
- **Agente Investigador RAG** — Agente que consulta el Vector Store para recuperar los Chunks relevantes según la solicitud.
- **Agente Redactor Pedagógico** — Agente que transforma los Chunks recuperados en contenido adaptado al Perfil, Formato y Nicho.
- **Agente Crítico/Revisor** — Agente que evalúa el contenido generado contra el Documento Fuente, calcula el Anclaje a Fuente y sugiere correcciones.
- **OCI Object Storage** — Servicio de almacenamiento de objetos de Oracle Cloud Infrastructure, capa Always Free. Persiste Documentos Fuente y Paquetes Educativos.

## 4. Features

### 4.1 Ingestión y Procesamiento de Documentos

**Descripción:** El sistema acepta un Documento Fuente en formato PDF, Markdown o texto plano, extrae su contenido textual, lo segmenta en Chunks semánticos, genera Embeddings vectoriales para cada Chunk mediante Voyage AI, y los indexa en un Vector Store FAISS. El índice se persiste en disco local para reutilización. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-1: Aceptación de documentos

El sistema puede recibir un Documento Fuente en formato PDF, Markdown (.md) o texto plano (.txt) a través de la API REST.

**Consecuencias (testeables):**
- El sistema acepta archivos con extensiones `.pdf`, `.md`, `.txt`.
- El sistema retorna HTTP 415 (Unsupported Media Type) para formatos no soportados.
- El sistema retorna HTTP 422 con mensaje descriptivo si el archivo está vacío o no se puede extraer texto.

#### FR-2: Extracción de texto

El sistema puede extraer el contenido textual del Documento Fuente, independientemente del formato de entrada.

**Consecuencias (testeables):**
- Para PDF: se extrae texto legible preservando la estructura de párrafos. `[ASSUMPTION: Se usa PyPDF o equivalente. No se procesan imágenes/diagramas embebidos en PDF en v1.]`
- Para Markdown: se preserva la estructura de encabezados y listas, se elimina markup decorativo.
- Para texto plano: se procesa el contenido tal cual.

#### FR-3: Segmentación semántica (chunking)

El sistema puede segmentar el texto extraído en Chunks semánticos que preserven la coherencia del contenido.

**Consecuencias (testeables):**
- Cada Chunk contiene una unidad de sentido completa (no corta a mitad de párrafo o concepto). `[ASSUMPTION: Se usa chunking recursivo por caracteres con overlap, calibrado para documentos técnicos. El tamaño de chunk y overlap se definen en configuración.]`
- Cada Chunk incluye metadata: posición en el documento, encabezado padre (si aplica).

#### FR-4: Generación de embeddings e indexación

El sistema puede generar Embeddings vectoriales para cada Chunk usando Voyage AI y almacenarlos en un Vector Store FAISS.

**Consecuencias (testeables):**
- El índice FAISS se persiste en disco local mediante `save_local`/`load_local` de `langchain-community` (genera `index.faiss` + `index.pkl`). El `index.pkl` contiene el texto completo de cada Chunk con su metadata.
- Si un Documento Fuente ya fue indexado previamente, el sistema carga el índice desde disco sin re-generar embeddings (evita llamadas redundantes a Voyage AI).
- La generación de embeddings usa el modelo de Voyage AI configurado.
- El Vector Store soporta búsqueda por similitud con un parámetro k configurable.

**Out of Scope:**
- Soporte para imágenes, tablas o diagramas dentro de documentos.

### 4.2 Solicitud de Adaptación

**Descripción:** El usuario envía una solicitud especificando el Perfil del Destinatario, el Formato Pedagógico y el Nicho/Contexto. Estos tres parámetros, junto con el Documento Fuente ya indexado, configuran el comportamiento completo del pipeline de generación. La experiencia es: sube un documento, elige tres parámetros, recibe un Paquete Educativo. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-5: Parámetros de personalización

El usuario puede especificar tres parámetros de adaptación en la solicitud.

**Consecuencias (testeables):**
- `perfil_destinatario` acepta uno de: `Principiante`, `Desarrollador Junior/Semi Senior`, `Líder Técnico/Arquitecto`, `Gestor/Ejecutivo No Técnico`.
- `formato_salida` acepta uno de: `Tutorial Paso a Paso`, `Flashcards`, `Quiz Interactivo`, `Resumen Ejecutivo`, `Guión de Clase`.
- `nicho_sector` acepta una cadena libre (texto libre del usuario) o uno de los valores predefinidos: `Fintech`, `Salud`, `E-commerce`, `General`.
- Los tres parámetros son obligatorios. El sistema retorna HTTP 422 con mensaje descriptivo si falta alguno.
- La validación de schemas se realiza con Pydantic (tipado estricto).

#### FR-6: Solicitud como operación atómica

El usuario puede enviar documento + parámetros en una única solicitud API y recibir el Paquete Educativo como respuesta.

**Consecuencias (testeables):**
- Una solicitud = un documento + tres parámetros → un Paquete Educativo.
- La solicitud es síncrona: el cliente espera hasta recibir la respuesta completa. `[ASSUMPTION: Solicitud síncrona para el MVP. Con documentos grandes y 1GB RAM, el tiempo de respuesta podría ser largo (30s-2min). No se implementa procesamiento async con polling en v1.]`
- El sistema retorna HTTP 200 con el Paquete Educativo en caso de éxito, o HTTP 5xx con mensaje de error descriptivo en caso de fallo del pipeline.

### 4.3 Pipeline de Generación Multi-Agente

**Descripción:** El núcleo inteligente del sistema. Un grafo LangGraph orquesta tres Agentes especializados que operan secuencialmente: el Agente Investigador RAG recupera los Chunks relevantes del Vector Store, el Agente Redactor Pedagógico transforma ese material en contenido adaptado al Perfil, Formato y Nicho, y el Agente Crítico/Revisor evalúa la fidelidad del contenido generado respecto al Documento Fuente. El LLM subyacente es Gemini Flash. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-7: Retrieval contextualizado (Agente Investigador RAG)

El Agente Investigador RAG puede recuperar los Chunks más relevantes del Vector Store para fundamentar la generación de contenido.

**Consecuencias (testeables):**
- El agente construye queries de búsqueda sintéticas basadas en los parámetros de la solicitud (Perfil, Formato, Nicho) y la estructura del documento. `[ASSUMPTION: La estrategia de query se resuelve en arquitectura. Opciones: queries temáticas derivadas del outline del documento, queries por sección/encabezado, o full-document retrieval para documentos cortos.]`
- El agente recupera un mínimo de Chunks suficiente para cubrir los temas principales del documento.
- Los Chunks recuperados se pasan como contexto al Agente Redactor Pedagógico.

#### FR-8: Generación de contenido adaptado (Agente Redactor Pedagógico)

El Agente Redactor Pedagógico puede generar contenido educativo estructurado que respete el Perfil, Formato y Nicho de la solicitud.

**Consecuencias (testeables):**
- El contenido generado para un Principiante es lingüística y conceptualmente diferente al generado para un Líder Técnico, dado el mismo Documento Fuente.
- El formato de salida sigue la estructura definida para cada Formato Pedagógico:
  - **Tutorial Paso a Paso:** secuencia numerada de pasos con explicaciones y ejemplos.
  - **Flashcards:** pares frente/dorso con pista didáctica opcional.
  - **Quiz Interactivo:** preguntas con opciones, respuesta correcta y justificación anclada en la fuente.
  - **Resumen Ejecutivo:** síntesis sin jerga técnica excesiva, enfocada en implicaciones y decisiones.
  - **Guión de Clase:** estructura con apertura, desarrollo, actividades y cierre, pensada para un formador.
- Si el Nicho es texto libre (ej: "soy veterinario aprendiendo a programar"), el contenido incorpora ese contexto en los ejemplos y el lenguaje.
- El agente usa Gemini Flash como LLM, con prompts estructurados (role prompting, few-shot cuando aplique).

#### FR-9: Evaluación de fidelidad (Agente Crítico/Revisor)

El Agente Crítico/Revisor puede evaluar el contenido generado por el Redactor y calcular el Anclaje a Fuente Score.

**Consecuencias (testeables):**
- El agente compara el contenido generado contra los Chunks del Documento Fuente.
- Produce un `anclaje_fuente_score` entre 0.0 y 1.0.
- `[ASSUMPTION: MVP usa autoevaluación LLM — el Crítico recibe el contenido generado + chunks fuente y evalúa fidelidad mediante prompt. Método más robusto (comparación de embeddings fuente vs generado) es diferencial.]`
- Produce un campo `claridad_pedagogica` con valoración cualitativa.
- Produce `observaciones` con notas sobre la adaptación realizada.
- Si el score cae por debajo de un umbral configurable, el agente puede solicitar al Redactor una reescritura con mayor anclaje. `[ASSUMPTION: Se implementa un loop de corrección con máximo 1 reintento. El umbral default es 0.7.]`

### 4.4 Salida Estructurada

**Descripción:** El sistema produce un Paquete Educativo como JSON tipado con schema fijo, listo para integración con sistemas externos. No devuelve texto libre — devuelve datos estructurados con metadatos pedagógicos. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-10: Schema de salida JSON

El sistema puede producir un Paquete Educativo con la siguiente estructura fija.

**Consecuencias (testeables):**
- El JSON de respuesta contiene las secciones: `status`, `metadatos`, `contenido_adaptado`, `evaluacion_calidad`.
- `metadatos` incluye: `perfil_aplicado`, `formato_generado`, `tiempo_estimado_estudio_minutos`, `conceptos_clave` (lista), `prerrequisitos` (lista).
- `contenido_adaptado` incluye: `titulo`, `introduccion_contextualizada`, e `items` cuya estructura varía según el Formato Pedagógico.
- `evaluacion_calidad` incluye: `anclaje_fuente_score`, `claridad_pedagogica`, `observaciones`.
- El schema se valida con Pydantic. Si la generación no cumple el schema, el sistema retorna error antes de entregar.

#### FR-11: Consistencia de schema por formato

Cada Formato Pedagógico tiene una subestructura definida dentro de `contenido_adaptado.items`.

**Consecuencias (testeables):**
- **Flashcards:** cada item tiene `frente`, `dorso`, `pista_didactica`.
- **Quiz Interactivo:** cada item tiene `pregunta`, `opciones` (lista), `respuesta_correcta`, `justificacion`.
- **Tutorial Paso a Paso:** cada item tiene `paso_numero`, `titulo`, `explicacion`, `ejemplo` (opcional).
- **Resumen Ejecutivo:** items como `seccion`, `contenido`, `implicacion`.
- **Guión de Clase:** items como `fase` (apertura/desarrollo/actividad/cierre), `contenido`, `duracion_sugerida`, `notas_para_formador`.

### 4.5 Persistencia en OCI Object Storage

**Descripción:** El sistema persiste tanto los Documentos Fuente subidos como los Paquetes Educativos generados en OCI Object Storage (capa Always Free). Esto cumple el requisito obligatorio del hackathon y proporciona trazabilidad entre input y output. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-12: Almacenamiento de documentos fuente

El sistema puede almacenar el Documento Fuente original en un bucket de OCI Object Storage al recibirlo.

**Consecuencias (testeables):**
- El documento se sube al bucket configurado con un identificador único.
- El sistema confirma el upload antes de continuar con el procesamiento.
- `[ASSUMPTION: El bucket se crea manualmente como parte del setup. El nombre y namespace se configuran por variable de entorno.]`

#### FR-13: Almacenamiento de paquetes educativos

El sistema puede almacenar el Paquete Educativo generado (JSON) en OCI Object Storage.

**Consecuencias (testeables):**
- El JSON se sube al mismo bucket con un identificador que referencia el documento fuente, perfil, formato y timestamp.
- La respuesta al usuario incluye `almacenamiento_oci.bucket`, `almacenamiento_oci.objeto_id` y `almacenamiento_oci.status_upload`.
- Si el upload a OCI falla, el sistema aún retorna el Paquete Educativo al usuario (el almacenamiento no bloquea la respuesta). `[ASSUMPTION: Upload a OCI es best-effort, no bloquea la entrega del paquete al usuario.]`

### 4.6 API REST

**Descripción:** La superficie principal de interacción con el sistema. Una API REST construida con FastAPI que expone el endpoint de adaptación de contenido, con validación de entrada, documentación auto-generada y manejo de errores. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-14: Endpoint de adaptación

El sistema expone un endpoint POST que recibe el Documento Fuente y los parámetros de personalización, y retorna el Paquete Educativo.

**Consecuencias (testeables):**
- El endpoint acepta multipart/form-data (archivo + parámetros JSON).
- La documentación OpenAPI se auto-genera vía FastAPI (accesible en `/docs`).
- `[ASSUMPTION: Un único endpoint principal: POST /api/v1/adaptar. Endpoints auxiliares (health check, listar formatos soportados) se agregan según necesidad.]`

#### FR-15: Manejo de errores

El sistema retorna errores descriptivos y consistentes.

**Consecuencias (testeables):**
- Todos los errores retornan JSON con `status: "error"`, `codigo`, `mensaje` descriptivo en español.
- Los códigos HTTP siguen la convención REST: 415 (formato no soportado), 422 (validación fallida), 500 (error interno), 503 (servicio no disponible).

### 4.7 Interfaz Web

**Descripción:** Interfaz web moderna y profesional que permite al usuario interactuar con el sistema sin necesidad de herramientas API externas. Cubre el flujo completo: subir o seleccionar un documento, configurar los parámetros de adaptación, lanzar la generación, y visualizar los resultados de forma atractiva según el formato pedagógico. Incluye un historial de generaciones anteriores. La interfaz es ligera en el servidor — HTML estático servido por FastAPI. Los detalles de implementación técnica (framework JS, SSR, SPA, etc.) se resuelven en arquitectura. Realiza UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-16: Upload y selección de documento

El usuario puede subir un nuevo Documento Fuente o seleccionar uno ya procesado anteriormente desde la interfaz.

**Consecuencias (testeables):**
- La interfaz presenta un área de upload que acepta archivos PDF, Markdown y texto plano.
- Si existen documentos previamente procesados (persistidos en OCI Object Storage), el usuario puede seleccionar uno de ellos en lugar de subir un archivo nuevo.
- El sistema muestra feedback visual durante la carga del archivo.

#### FR-17: Configuración de parámetros de adaptación

El usuario puede seleccionar Perfil del Destinatario, Formato Pedagógico y Nicho/Contexto desde la interfaz.

**Consecuencias (testeables):**
- Perfil y Formato se seleccionan desde controles con las opciones predefinidas (no texto libre).
- Nicho ofrece opciones predefinidas (Fintech, Salud, E-commerce, General) más un campo de texto libre para contextos personalizados.
- Los tres parámetros son obligatorios; la interfaz no permite lanzar la generación sin completarlos.

#### FR-18: Lanzamiento de generación y feedback de progreso

El usuario puede lanzar la generación y recibir feedback visual mientras el pipeline procesa.

**Consecuencias (testeables):**
- Un botón de acción lanza la generación tras completar documento + parámetros.
- La interfaz muestra un estado de carga/progreso durante el procesamiento (que puede tomar 30s-2min).
- Si el pipeline falla, la interfaz muestra un mensaje de error descriptivo en español.

#### FR-19: Visualización de resultados por formato

El usuario puede visualizar el Paquete Educativo generado con una renderización atractiva y adecuada al Formato Pedagógico.

**Consecuencias (testeables):**
- **Flashcards:** se renderizan como tarjetas interactivas con frente/dorso.
- **Quiz Interactivo:** se presenta con preguntas, opciones seleccionables, y revelación de respuesta correcta + justificación.
- **Tutorial Paso a Paso:** se muestra como una secuencia de pasos con explicaciones y ejemplos.
- **Resumen Ejecutivo:** se renderiza como un documento estructurado con secciones y puntos clave.
- **Guión de Clase:** se presenta con fases diferenciadas (apertura, desarrollo, actividad, cierre) y notas para el formador.
- Todas las visualizaciones muestran los metadatos pedagógicos (conceptos clave, prerrequisitos, tiempo estimado) y el `anclaje_fuente_score`.
- `[ASSUMPTION: La renderización es client-side con HTML/CSS/JS estático. No se requiere framework de componentes pesado. Los detalles de diseño visual se definen en UX.]`

#### FR-20: Historial de generaciones

El usuario puede consultar generaciones anteriores desde una barra lateral.

**Consecuencias (testeables):**
- La barra lateral lista generaciones anteriores con: nombre del documento, perfil, formato, fecha.
- Seleccionar una entrada del historial carga y renderiza ese Paquete Educativo sin re-procesarlo.
- El historial se alimenta de los Paquetes Educativos persistidos en OCI Object Storage (FR-13). `[ASSUMPTION: El historial consulta OCI Object Storage para listar paquetes anteriores. No hay base de datos adicional; la metadata se extrae del nombre del objeto o de un índice JSON simple en el bucket.]`

**Feature-specific NFRs:**
- La interfaz completa (HTML + CSS + JS) debe ser lo suficientemente ligera para no agregar carga significativa al servidor de 1GB RAM. El servidor sólo sirve archivos estáticos y proxea las llamadas API.
- `[ASSUMPTION: FastAPI sirve los archivos estáticos de la UI directamente. No se requiere un servidor web separado (nginx, etc.) en v1.]`

## 5. No-Goals (Explícito)

- **NuevaMente no es un chatbot.** No hay campo de chat, no hay conversación. Es transformación de documentos, no Q&A.
- **No es una plataforma EdTech.** No compite con Coursera, Udemy o similares. No tiene cursos, usuarios registrados ni progreso de aprendizaje.
- **No hace fine-tuning ni entrena modelos.** Usa modelos pre-entrenados vía API (Gemini Flash, Voyage AI).
- **No escala horizontalmente.** Corre en una instancia de 1GB RAM. No hay load balancing, no hay autoscaling.
- **No opera en múltiples idiomas.** v1 opera en español, tanto en input como en output. `[NON-GOAL for MVP]`
- **No tiene autenticación ni control de acceso.** Cualquiera con acceso a la API puede usarla. `[NON-GOAL for MVP]`
- **No procesa contenido multimodal.** Imágenes, diagramas o tablas embebidas en documentos no se interpretan en v1. `[NON-GOAL for MVP]`

## 6. Alcance MVP

### 6.1 En Alcance

- Pipeline RAG completo: ingestión → extracción de texto → chunking semántico → embeddings (Voyage AI) → FAISS → retrieval.
- Orquestación multi-agente con LangGraph: Agente Investigador RAG → Agente Redactor Pedagógico → Agente Crítico/Revisor.
- LLM: Gemini Flash.
- API REST con FastAPI como interfaz programática.
- Interfaz web moderna servida como HTML estático por FastAPI: upload de documentos, configuración de parámetros, visualización de resultados por formato, historial de generaciones.
- Entrada: PDF, Markdown, texto plano.
- Salida: JSON estructurado con los 5 Formatos Pedagógicos, metadatos pedagógicos y score de fidelidad.
- Validación de schemas con Pydantic.
- Integración OCI Object Storage para persistencia de documentos y paquetes.
- Mínimo 3 escenarios de demo con documentación real (Python 3.14 y LangChain).
- Documentación completa en GitHub con diagrama de arquitectura.

### 6.2 Fuera de Alcance para MVP

- **UI avanzada con framework SPA** — v1 usa HTML estático servido por FastAPI. Un framework SPA (React, Vue, etc.) se evalúa para v2 si la complejidad de la UI lo justifica.
- **Procesamiento asíncrono** — Solicitudes síncronas en v1. Evaluar async con polling si los tiempos de respuesta exceden lo tolerable.
- **Exportación multiformato** — Markdown, PDF formateado, CSV para Anki. Diferencial deseable.
- **Quizzes con evaluación en tiempo real** — Interfaz interactiva donde el estudiante responde y recibe retroalimentación. Diferencial deseable.
- **Despliegue en OCI Compute** — Instancia Always Free. Deseable pero no bloquea evaluación.
- **Score de fidelidad robusto** — Método basado en embeddings para reemplazar la heurística LLM. v2.
- **Soporte multimodal** — Interpretación de diagramas dentro de documentos. v2+.

## 7. Métricas de Éxito

Contexto: proyecto hackathon + portfolio personal de 1 persona en ~33 días. Las métricas se calibran a ese nivel — honestas y útiles, no enterprise-theater.

**Primarias**

- **SM-1: Diferenciación comprobable de output.** El contenido generado para perfil Principiante es lingüística y estructuralmente distinto al generado para Líder Técnico, dado el mismo Documento Fuente y Formato. Valida FR-8. *Target: demostrable en los 3 escenarios de demo.*
- **SM-2: Cobertura de formatos.** Los 5 Formatos Pedagógicos producen output válido contra schema Pydantic. Valida FR-10, FR-11. *Target: 100% de los formatos generan JSON válido.*
- **SM-3: Anclaje a fuente significativo.** El `anclaje_fuente_score` refleja conexión real con el Documento Fuente, no un número fabricado. Valida FR-9. *Target: score ≥ 0.7 en los escenarios de demo; revisión manual confirma que el score correlaciona con fidelidad observable.*

**Secundarias**

- **SM-4: Checklist del hackathon completo.** Los 8 requisitos obligatorios del hackathon están cubiertos y demostrables. Valida FR-1, FR-4, FR-8, FR-10, FR-12, FR-14. *Target: 8/8 requisitos pasados.*
- **SM-5: Usabilidad sin explicación.** Un usuario sin contexto técnico puede abrir la interfaz web, subir un documento, configurar parámetros y obtener resultados sin asistencia ni documentación. Valida FR-16, FR-17, FR-18, FR-19. *Target: evaluación cualitativa en la demo.*

**Counter-metrics (no optimizar)**

- **SM-C1: Longitud del contenido.** Más texto ≠ mejor adaptación. Si el Resumen Ejecutivo de un Principiante es más largo que el Tutorial del Líder Técnico, algo anda mal. Contrabalancea SM-1.
- **SM-C2: Tiempo de respuesta vs calidad.** No sacrificar calidad de adaptación por velocidad. Que tarde 90 segundos pero el contenido sea genuinamente útil vale más que 5 segundos de output genérico. Contrabalancea eventual optimización de performance.

## 8. Requisitos No Funcionales (Cross-Cutting)

### NFR-1: Restricciones de Hardware

El sistema opera dentro de los límites de 1GB RAM y 1 OCPU (OCI Always Free).

- El índice FAISS en memoria + el proceso de la aplicación no deben exceder ~800MB RSS (dejando margen para el OS). `[ASSUMPTION: Margen de 200MB para el OS es suficiente en la instancia Always Free.]`
- El sistema procesa una solicitud a la vez (concurrencia 1). `[ASSUMPTION: No se requiere concurrencia en v1. FastAPI puede manejar requests en cola, pero el pipeline consume toda la RAM disponible por request.]`
- Si el documento genera un índice FAISS que excede la memoria disponible, el sistema retorna un error descriptivo antes de OOM-kill.

### NFR-2: Rendimiento

- El tiempo de respuesta end-to-end (ingestión → generación → respuesta) debería ser inferior a 2 minutos para documentos de hasta 1000 líneas. `[ASSUMPTION: 2 minutos es el umbral tolerable para una solicitud síncrona de este tipo. Documentos más grandes podrían tardar más.]`
- Las llamadas a APIs externas (Gemini Flash, Voyage AI) representarán la mayor parte de la latencia; el sistema no introduce overhead significativo propio.

### NFR-3: Costo

- Todo servicio utilizado debe estar dentro de la capa Always Free de OCI.
- Las APIs externas (Gemini Flash, Voyage AI) se usan en sus tiers gratuitos o con costo mínimo controlado. `[ASSUMPTION: Gemini Flash y Voyage AI tienen tiers gratuitos o costos por token suficientes para el uso del hackathon.]`
- Ninguna configuración de OCI puede generar costos monetarios (restricción explícita del programa ONE).

### NFR-4: Observabilidad

- Los errores del pipeline se loguean con suficiente contexto para diagnosticar fallos (qué agente falló, con qué input). `[ASSUMPTION: Logging básico a stdout/stderr. No se integra LangSmith u otra plataforma de observabilidad en v1, pero la arquitectura debe permitirlo.]`
- Cada respuesta incluye metadata del procesamiento (formato aplicado, perfil, score de fidelidad).

### NFR-5: Mantenibilidad

- Código organizado en módulos separados: ingestión, pipeline RAG, agentes, API, integración OCI.
- Configuración externalizada (modelo LLM, modelo de embeddings, parámetros de chunking, credenciales OCI).
- Type hints completos (Python 3.12). Pydantic para schemas de entrada y salida.

## 9. Open Questions

1. **Estrategia de query RAG para documentos completos.** ¿Cómo se construyen las queries de retrieval cuando no hay pregunta del usuario? Opciones: queries sintéticas por sección, retrieval por outline, full-document para documentos cortos. *→ Resolver en arquitectura.*
2. **Tamaño máximo de documento procesable.** Sin límite declarado, pero con 1GB RAM hay un techo físico. ¿Se debe detectar y comunicar proactivamente, o dejar que el OOM-kill lo resuelva? *→ Resolver en implementación (idealmente pre-check de tamaño estimado del índice).*
3. ~~**Persistencia de índice FAISS.**~~ *Resuelto: se persiste en disco local via `save_local`/`load_local` de LangChain (index.faiss + index.pkl). Evita re-embedding.*
4. **Rate limiting de APIs externas.** ¿Qué pasa si Gemini Flash o Voyage AI throttlean durante un request? *→ Definir retry policy en implementación.*
5. **Timeout de la solicitud.** ¿Hay un timeout máximo antes de cortar la solicitud? *→ Definir en implementación. Sugerido: 3 minutos.*

## 10. Índice de Asunciones

- **§3 Glosario / Anclaje a Fuente:** MVP calcula score mediante autoevaluación del LLM; método por embeddings es diferencial.
- **§4.1 FR-2:** Se usa PyPDF o equivalente para PDF. No se procesan imágenes/diagramas embebidos.
- **§4.1 FR-3:** Chunking recursivo por caracteres con overlap. Tamaño y overlap en config.
- **§4.1 FR-4:** Índice FAISS se persiste en disco local via `save_local`/`load_local` de langchain-community (index.faiss + index.pkl con chunks + metadata).
- **§4.2 FR-6:** Solicitud síncrona. Tiempo de respuesta puede ser 30s-2min. No hay async con polling en v1.
- **§4.3 FR-7:** Estrategia de query RAG se resuelve en arquitectura.
- **§4.3 FR-9:** Autoevaluación LLM para score de fidelidad. Loop de corrección con max 1 reintento, umbral 0.7.
- **§4.5 FR-12:** Bucket se crea manualmente, configuración por env vars.
- **§4.5 FR-13:** Upload a OCI es best-effort, no bloquea la entrega.
- **§4.6 FR-14:** Un único endpoint principal POST /api/v1/adaptar.
- **§8 NFR-1:** Margen de 200MB para el OS. Concurrencia 1.
- **§8 NFR-2:** Umbral de 2 minutos para documentos de hasta 1000 líneas.
- **§8 NFR-3:** Gemini Flash y Voyage AI tienen tiers gratuitos o costo mínimo suficiente.
- **§8 NFR-4:** Logging básico a stdout/stderr, sin LangSmith en v1.
- **§4.7 FR-19:** Renderización client-side con HTML/CSS/JS estático. Sin framework pesado.
- **§4.7 FR-20:** Historial consulta OCI Object Storage, sin base de datos adicional. Metadata de índice JSON simple.
- **§4.7 NFR:** FastAPI sirve los archivos estáticos de la UI directamente, sin servidor web separado.
