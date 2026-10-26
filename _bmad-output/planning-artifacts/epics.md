---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-NuevaMente-2026-09-24/prd.md
  - _bmad-output/planning-artifacts/prds/prd-NuevaMente-2026-09-24/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-NuevaMente-2026-09-24/ARCHITECTURE.md
  - hackaton-42.pdf
---

# NuevaMente - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for NuevaMente, decomposing the requirements from the PRD, Architecture, and hackathon evaluation criteria into implementable stories. Epics are prioritized so that mandatory hackathon requirements are fulfilled first, and differentials come after.

## Requirements Inventory

### Functional Requirements

- **FR-1:** El sistema acepta documentos fuente en formato PDF, Markdown (.md) o texto plano (.txt) a traves de la API REST. Retorna HTTP 415 para formatos no soportados, HTTP 422 si el archivo esta vacio o no se puede extraer texto.

- **FR-2:** El sistema extrae el contenido textual del documento fuente independientemente del formato de entrada. PyPDF para PDF, preservacion de estructura para Markdown, texto tal cual para .txt.

- **FR-3:** El sistema segmenta el texto extraido en chunks semanticos que preserven la coherencia del contenido. Chunking recursivo por caracteres con overlap configurable. Cada chunk incluye metadata (posicion, encabezado padre).

- **FR-4:** El sistema genera embeddings vectoriales para cada chunk usando Voyage AI y los almacena en un indice FAISS. El indice se persiste en disco local (index.faiss + index.pkl). Soporta busqueda por similitud con parametro k configurable.

- **FR-5:** El usuario especifica tres parametros de adaptacion: perfil_destinatario (enum de 4 opciones), formato_salida (enum de 5 opciones), nicho_sector (texto libre o predefinido). Validacion con Pydantic.

- **FR-6:** Una solicitud = un documento + tres parametros = un paquete educativo. POST retorna 202 + task_id, GET para polling de status (patron asincrono definido en arquitectura).

- **FR-7:** El Agente Investigador RAG recupera chunks relevantes del vector store. Estrategia dual: fast-path (doc <= 50K tokens, todos los chunks) vs full-coverage (section map + query synthesis + stratified retrieval).

- **FR-8:** El Agente Redactor Pedagogico genera contenido educativo estructurado diferenciado por perfil, formato y nicho. Usa Gemini 3.5 Flash Lite con with_structured_output() para producir instancias Pydantic directamente. Soporta 5 formatos pedagogicos.

- **FR-9:** El Agente Critico/Revisor evalua fidelidad del contenido generado vs documento fuente. Calcula anclaje_fuente_score (0.0-1.0), claridad_pedagogica y observaciones. Loop de correccion con max 1 reintento si score < 0.7.

- **FR-10:** El sistema produce un paquete educativo JSON con secciones: status, metadatos, contenido_adaptado, evaluacion_calidad. Schema validado con Pydantic.

- **FR-11:** Cada formato pedagogico tiene subestructura definida dentro de contenido_adaptado.items: Flashcards (frente/dorso/pista), Quiz (pregunta/opciones/respuesta/justificacion), Tutorial (paso/titulo/explicacion/ejemplo), Resumen Ejecutivo (seccion/contenido/implicacion), Guion de Clase (fase/contenido/duracion/notas).

- **FR-12:** El sistema almacena el documento fuente original en un bucket de OCI Object Storage (Always Free) al recibirlo. Bucket configurado por env vars.

- **FR-13:** El sistema almacena el paquete educativo generado (JSON) en OCI Object Storage. Upload best-effort (no bloquea la entrega al usuario). La respuesta incluye almacenamiento_oci con bucket, objeto_id y status_upload.

- **FR-14:** Endpoint POST /api/v1/adaptar que acepta multipart/form-data. Documentacion OpenAPI auto-generada via FastAPI en /docs.

- **FR-15:** Todos los errores retornan JSON con status "error", codigo y mensaje descriptivo en espanol. Codigos HTTP: 415, 422, 500, 503.

- **FR-16:** La interfaz web permite subir un nuevo documento fuente o seleccionar uno ya procesado. Area de upload con feedback visual.

- **FR-17:** Configuracion de perfil, formato y nicho desde la interfaz. Perfil y formato como selects, nicho con opciones predefinidas + texto libre. Los tres son obligatorios.

- **FR-18:** Boton de accion para lanzar generacion con estado de carga/progreso visible. Mensajes de error descriptivos en espanol si el pipeline falla.

- **FR-19:** Visualizacion de resultados renderizados segun el formato: flashcards interactivas, quiz con opciones seleccionables, tutorial con pasos, resumen ejecutivo con secciones, guion de clase con fases. Todas muestran metadatos pedagogicos y anclaje_fuente_score.

- **FR-20:** Historial de generaciones anteriores en barra lateral (documento, perfil, formato, fecha). Seleccionar una entrada carga el paquete sin re-procesar. Se alimenta de OCI Object Storage.

### NonFunctional Requirements

- **NFR-1:** Restricciones de hardware -- 1GB RAM + 1 OCPU (OCI Always Free). No exceder ~800MB RSS. Concurrencia 1. Error descriptivo si el indice FAISS excede la memoria disponible.

- **NFR-2:** Rendimiento -- tiempo de respuesta end-to-end < 2 minutos para documentos de hasta 1000 lineas. Las APIs externas (Gemini, Voyage AI) representan la mayor parte de la latencia.

- **NFR-3:** Costo $0 -- todo dentro de Always Free OCI + tiers gratuitos de Gemini 3.5 Flash Lite y Voyage AI. Ninguna configuracion puede generar costos monetarios.

- **NFR-4:** Observabilidad -- logging a stdout/stderr con contexto suficiente para diagnosticar fallos (que agente fallo, con que input). Sin LangSmith en v1 pero arquitectura lo permite.

- **NFR-5:** Mantenibilidad -- modulos separados (app/, pipeline/, services/, infra/, core/). Config externalizada con pydantic-settings. Type hints completos (Python 3.12). Pydantic para schemas.

- **NFR-6:** Estilo profesional -- no abusar de emojis en codigo, documentacion, mensajes de error ni interfaz. Los emojis solo son aceptables en diagramas (mermaid) o elementos genuinamente graficos. El proyecto debe verse profesional y no levantar sospechas de generacion automatica.

### Additional Requirements

- Estructura de proyecto greenfield con layout modular: app/ (FastAPI), pipeline/ (LangGraph), services/ (logica de negocio), infra/ (adaptadores), core/ (dominio puro). Regla de dependencia: app -> pipeline -> services -> infra; core es transversal.
- Estado del grafo LangGraph como NuevaMenteState (TypedDict) con campos inmutables (input), intermedios (pipeline), control de flujo y output.
- Patron asincrono para el pipeline: POST retorna 202 + task_id, GET /api/v1/adaptar/{task_id}/status para polling, pipeline ejecuta en background.
- Persistencia FAISS en disco local: data/faiss_indexes/{document_id}/ con index.faiss + index.pkl (gitignored).
- Upload a OCI Object Storage como fire-and-forget: no bloquea la respuesta al usuario.
- Infraestructura de despliegue: Uvicorn directo gestionado por systemd en OCI VM Always Free (1GB RAM + 1 OCPU + 4-8GB swap).
- FastAPI sirve archivos estaticos de la UI directamente, sin servidor web separado.
- Escenarios de demo planificados con documentacion real de Python 3.14 y LangChain: (1) mismo doc distintos perfiles, (2) mismo doc distintos formatos, (3) nicho personalizado.
- Documentacion completa en GitHub con README.md, diagrama de arquitectura y guia de instalacion.

### UX Design Requirements

N/A -- No existe documento UX. La interfaz web se implementa segun las descripciones funcionales del PRD (FR-16 a FR-20) y las decisiones de arquitectura (HTML/CSS/JS estatico servido por FastAPI).

### FR Coverage Map

| FR | Epica | Descripcion |
|----|-------|-------------|
| FR-1 | Epic 1 | Aceptacion de documentos (PDF, .md, .txt) |
| FR-2 | Epic 1 | Extraccion de texto |
| FR-3 | Epic 1 | Segmentacion semantica (chunking) |
| FR-4 | Epic 1 | Embeddings Voyage AI + indexacion FAISS |
| FR-5 | Epic 1 | Parametros de personalizacion |
| FR-6 | Epic 1 | Solicitud atomica (POST 202 + polling) |
| FR-7 | Epic 1 | Retrieval contextualizado (Agente Investigador) |
| FR-8 | Epic 1 | Generacion adaptada (Agente Redactor) |
| FR-9 | Epic 1 | Evaluacion de fidelidad (Agente Critico) |
| FR-10 | Epic 1 | Schema JSON del paquete educativo |
| FR-11 | Epic 1 | Consistencia de schema por formato |
| FR-12 | Epic 2 | Almacenamiento de documentos en OCI |
| FR-13 | Epic 2 | Almacenamiento de paquetes en OCI |
| FR-14 | Epic 1 | Endpoint POST /api/v1/adaptar |
| FR-15 | Epic 1 | Manejo de errores |
| FR-16 | Epic 3 | Upload y seleccion de documentos (web) |
| FR-17 | Epic 3 | Configuracion de parametros (web) |
| FR-18 | Epic 3 | Lanzamiento de generacion con progreso |
| FR-19 | Epic 3 | Visualizacion de resultados por formato |
| FR-20 | Epic 3 | Historial de generaciones |

NFRs 1-6 son transversales y se aplican en todas las epicas.

## Epic List

### Epic 1: Pipeline de Transformacion de Documentos

El usuario puede enviar un documento tecnico via API y recibir un paquete educativo JSON estructurado, adaptado a su perfil, formato y nicho, con evaluacion de fidelidad al documento fuente. Este es el nucleo completo del sistema: ingestion, RAG, multi-agente, structured output, y API REST funcional.

**FRs cubiertos:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-14, FR-15

**Requisitos obligatorios del hackathon cubiertos:** 1 (ingestion), 2 (RAG), 3 (orquestacion LLM), 4 (adaptacion multi-perfil/formato), 5 parcial (salida JSON + API operativa)

### Epic 2: Persistencia en OCI Object Storage

El sistema persiste los documentos fuente subidos y los paquetes educativos generados en OCI Object Storage (capa Always Free), proporcionando trazabilidad entre input y output. Upload best-effort que no bloquea la respuesta al usuario.

**FRs cubiertos:** FR-12, FR-13

**Requisitos obligatorios del hackathon cubiertos:** 6 (OCI Object Storage Always Free)

### Epic 3: Interfaz Web Completa

El usuario puede interactuar con el sistema desde un navegador: subir documentos, configurar parametros, lanzar generaciones con feedback visual, visualizar los resultados renderizados segun el formato pedagogico, y consultar un historial de generaciones anteriores.

**FRs cubiertos:** FR-16, FR-17, FR-18, FR-19, FR-20

**Requisitos obligatorios del hackathon cubiertos:** 5 completo (interfaz interactiva)

### Epic 4: Escenarios de Demostracion y Documentacion

Los evaluadores del hackathon pueden ver al menos 3 escenarios de ejecucion con documentacion real, un README.md completo con diagrama de arquitectura y guia de instalacion, y un repositorio Git con commits claros.

**FRs cubiertos:** Ninguno directamente (cubre requisitos de evaluacion del hackathon)

**Requisitos obligatorios del hackathon cubiertos:** 7 (>=3 ejemplos), 8 (documentacion completa)

### Epic 5: Diferenciales del Hackathon (Opcionales)

Funcionalidades adicionales que suman puntos en la evaluacion pero no son obligatorias: quizzes con evaluacion en tiempo real, exportacion multiformato (Markdown/PDF/CSV Anki), y despliegue en OCI Compute (VM Always Free). Priorizacion interna: (1) Quizzes interactivos, (2) Exportacion multiformato, (3) Despliegue OCI Compute.

**FRs cubiertos:** Extensiones de FR-19 (quiz interactivo en tiempo real), nuevos FRs para exportacion

**Requisitos opcionales del hackathon cubiertos:** Quizzes con evaluacion en tiempo real, Exportacion multiformato, Despliegue en OCI Compute

---

## Epic 1: Pipeline de Transformacion de Documentos

El usuario puede enviar un documento tecnico via API y recibir un paquete educativo JSON estructurado, adaptado a su perfil, formato y nicho, con evaluacion de fidelidad al documento fuente.

### Story 1.1: Fundacion del Proyecto y Configuracion

As a desarrollador,
I want una estructura de proyecto inicializada con la configuracion centralizada, modelos de dominio y schemas Pydantic,
So that tengo la base sobre la que todas las stories posteriores construyen.

**Acceptance Criteria:**

**Given** un directorio vacio del proyecto
**When** se inicializa la estructura
**Then** existen los directorios app/, core/, pipeline/, services/, infra/ y config.py segun ARCHITECTURE.md sec. 6
**And** core/models.py contiene los enums Perfil, FormatoPedagogico, Nicho con los valores definidos en FR-5
**And** core/schemas.py contiene PaqueteEducativoBase y los 5 modelos por formato (FlashcardsPaquete, QuizPaquete, TutorialPaquete, ResumenEjecutivoPaquete, GuionClasePaquete) con la estructura de FR-10 y FR-11
**And** core/exceptions.py contiene las excepciones de dominio
**And** config.py usa pydantic-settings para cargar variables de entorno (modelo LLM, modelo embeddings, parametros chunking, credenciales OCI)
**And** pipeline/state.py contiene NuevaMenteState como TypedDict segun ARCHITECTURE.md sec. 3.3
**And** la regla de dependencia (app -> pipeline -> services -> infra; core transversal) se respeta en los imports

### Story 1.2: Ingestion de Documentos y Pipeline RAG

As a usuario,
I want que el sistema acepte mi documento tecnico (PDF, Markdown o texto plano), extraiga su contenido, lo segmente en chunks semanticos y genere un indice vectorial,
So that el contenido de mi documento quede indexado y listo para retrieval.

**Acceptance Criteria:**

**Given** un archivo en formato .pdf, .md o .txt con contenido textual
**When** el servicio de ingestion procesa el archivo
**Then** el texto se extrae correctamente: PyPDF para PDF, preservacion de estructura para Markdown, texto tal cual para .txt (FR-2)
**And** el texto se segmenta en chunks semanticos con chunking recursivo por caracteres, con tamano de chunk y overlap configurables (FR-3)
**And** cada chunk incluye metadata: posicion en el documento y encabezado padre si aplica (FR-3)
**And** se genera un section_map del documento mediante parsing de estructura (sin LLM)
**And** se generan embeddings vectoriales para cada chunk usando Voyage AI (FR-4)
**And** los embeddings se indexan en FAISS con busqueda por similitud y parametro k configurable (FR-4)
**And** el indice se persiste en disco local en data/faiss_indexes/{document_id}/ con index.faiss + index.pkl (FR-4)
**And** si el documento ya fue indexado previamente, el indice se carga desde disco sin re-generar embeddings

**Given** un archivo con extension no soportada (ej: .docx, .xlsx)
**When** se intenta procesar
**Then** se retorna un error con codigo HTTP 415 (FR-1)

**Given** un archivo vacio o del que no se puede extraer texto
**When** se intenta procesar
**Then** se retorna un error con codigo HTTP 422 y mensaje descriptivo en espanol (FR-1, FR-15)

### Story 1.3: Retrieval Contextualizado (Agente Investigador RAG)

As a sistema,
I want recuperar los chunks mas relevantes del vector store adaptados al perfil, formato y nicho de la solicitud,
So that el Agente Redactor tenga el contexto necesario para generar contenido educativo fiel al documento fuente.

**Acceptance Criteria:**

**Given** un documento indexado con <= 50K tokens en chunks totales
**When** se ejecuta el nodo retrieve
**Then** se activa el fast-path: todos los chunks pasan directamente como retrieved_chunks (sin retrieval FAISS)

**Given** un documento indexado con > 50K tokens en chunks totales
**When** se ejecuta el nodo retrieve
**Then** se construye el section_map compacto (headers + primera oracion por seccion)
**And** se genera 1 llamada LLM para query synthesis: el LLM produce queries sinteticas distribuidas por todo el documento, adaptadas al perfil/formato/nicho
**And** se ejecuta similarity search en FAISS por cada query sintetica
**And** se aplica piso de cobertura: si alguna seccion tiene 0 chunks recuperados, se fuerza inclusion de su chunk mas representativo
**And** el total de chunks se limita por chunk budget, distribuido proporcionalmente por seccion

**Given** cualquier documento procesado
**When** se completa el retrieval
**Then** retrieved_chunks se almacena en el NuevaMenteState para el siguiente nodo

### Story 1.4: Generacion de Contenido Adaptado (Agente Redactor Pedagogico)

As a usuario,
I want que el sistema transforme los chunks recuperados en contenido educativo adaptado a mi perfil, formato pedagogico y nicho,
So that recibo material de estudio personalizado para mis necesidades.

**Acceptance Criteria:**

**Given** retrieved_chunks, perfil "Principiante" y formato "Flashcards"
**When** se ejecuta el nodo draft
**Then** el Agente Redactor genera un FlashcardsPaquete via llm.with_structured_output() usando Gemini 3.5 Flash Lite
**And** cada item contiene frente, dorso y pista_didactica (FR-11)
**And** el lenguaje es accesible, con analogias y sin jerga tecnica excesiva (FR-8)

**Given** retrieved_chunks, perfil "Lider Tecnico/Arquitecto" y formato "Resumen Ejecutivo"
**When** se ejecuta el nodo draft con el mismo documento fuente
**Then** el contenido generado es linguistica y estructuralmente diferente al de un Principiante (FR-8)
**And** cada item contiene seccion, contenido e implicacion (FR-11)

**Given** cualquier combinacion valida de perfil/formato/nicho
**When** se ejecuta el nodo draft
**Then** generated_content es una instancia Pydantic valida del modelo correspondiente al formato
**And** contenido_adaptado incluye titulo, introduccion_contextualizada e items
**And** metadatos incluye perfil_aplicado, formato_generado, tiempo_estimado_estudio_minutos, conceptos_clave y prerrequisitos (FR-10)

**Given** un nicho de texto libre (ej: "veterinario aprendiendo a programar")
**When** se ejecuta el nodo draft
**Then** el contenido incorpora ese contexto en los ejemplos y el lenguaje

**Given** review_result de un reintento (score < 0.7)
**When** se ejecuta el nodo draft por segunda vez
**Then** el Redactor recibe el feedback del Critico y genera contenido con mayor anclaje a la fuente

### Story 1.5: Evaluacion de Fidelidad (Agente Critico/Revisor)

As a usuario,
I want que el sistema evalue la fidelidad del contenido generado respecto al documento fuente,
So that puedo confiar en que el material educativo refleja fielmente el original.

**Acceptance Criteria:**

**Given** generated_content y retrieved_chunks
**When** se ejecuta el nodo review
**Then** el Agente Critico compara el contenido generado contra los chunks fuente
**And** produce anclaje_fuente_score entre 0.0 y 1.0 (FR-9)
**And** produce claridad_pedagogica con valoracion cualitativa (FR-9)
**And** produce observaciones con notas sobre la adaptacion realizada (FR-9)

**Given** anclaje_fuente_score >= 0.7 o retry_count >= 1
**When** se completa la evaluacion
**Then** el pipeline avanza al nodo format_output

**Given** anclaje_fuente_score < 0.7 y retry_count = 0
**When** se completa la evaluacion
**Then** el pipeline retorna al nodo draft con review_result como feedback
**And** retry_count se incrementa a 1

### Story 1.6: Ensamblado del Paquete Educativo y Grafo LangGraph

As a sistema,
I want ensamblar el paquete educativo final con metadatos y evaluacion de calidad, orquestado como un grafo LangGraph completo,
So that el pipeline end-to-end funciona como una unidad desde ingestion hasta output validado.

**Acceptance Criteria:**

**Given** generated_content y review_result aprobado
**When** se ejecuta el nodo format_output
**Then** se ensambla el paquete educativo final con las secciones: status, metadatos, contenido_adaptado, evaluacion_calidad (FR-10)
**And** el JSON resultante pasa validacion Pydantic contra el schema del formato correspondiente

**Given** los nodos ingest, retrieve, draft, review y format_output implementados
**When** se construye el grafo en pipeline/graph.py via build_graph()
**Then** el grafo conecta los nodos secuencialmente: START -> ingest -> retrieve -> draft -> review -> format_output -> END
**And** existe un conditional edge de review que retorna a draft si score < 0.7 y retry < 1
**And** el grafo es ejecutable end-to-end con un NuevaMenteState de entrada

### Story 1.7: API REST y Endpoint de Adaptacion

As a usuario,
I want enviar un documento y parametros a un endpoint API y recibir el paquete educativo generado,
So that puedo integrar NuevaMente con cualquier sistema externo o consumirlo desde la interfaz web.

**Acceptance Criteria:**

**Given** un archivo .txt valido y parametros perfil="Principiante", formato="Flashcards", nicho="General"
**When** envio POST /api/v1/adaptar con multipart/form-data
**Then** recibo 202 Accepted con un task_id (FR-6, FR-14)
**And** el pipeline se ejecuta en background

**Given** un task_id de una tarea en progreso
**When** envio GET /api/v1/adaptar/{task_id}/status
**Then** recibo el estado actual del pipeline (ej: paso actual, porcentaje estimado)

**Given** un task_id de una tarea completada
**When** envio GET /api/v1/adaptar/{task_id}/status
**Then** recibo status "completed" con el paquete educativo JSON completo

**Given** parametros incompletos (falta perfil, formato o nicho)
**When** envio POST /api/v1/adaptar
**Then** recibo HTTP 422 con JSON de error: status "error", codigo y mensaje descriptivo en espanol (FR-15)

**Given** un error interno del pipeline
**When** se completa la ejecucion con fallo
**Then** recibo HTTP 500 con JSON de error descriptivo indicando que agente fallo (FR-15, NFR-4)

**Given** la aplicacion FastAPI iniciada
**When** accedo a /docs
**Then** veo la documentacion OpenAPI auto-generada con todos los endpoints (FR-14)

---

## Epic 2: Persistencia en OCI Object Storage

El sistema persiste los documentos fuente subidos y los paquetes educativos generados en OCI Object Storage (capa Always Free), proporcionando trazabilidad entre input y output. Upload best-effort que no bloquea la respuesta al usuario.

### Story 2.1: Almacenamiento de Documentos Fuente en OCI

As a sistema,
I want almacenar el documento fuente original en OCI Object Storage al recibirlo,
So that los documentos procesados quedan persistidos en la nube para trazabilidad.

**Acceptance Criteria:**

**Given** un documento fuente recibido via POST /api/v1/adaptar
**When** el pipeline comienza a procesar
**Then** el documento se sube al bucket configurado en OCI Object Storage con un identificador unico basado en document_id
**And** el upload se realiza via OCI SDK para Python (oci-sdk)
**And** el sistema confirma el upload exitoso antes de continuar con el procesamiento

**Given** credenciales OCI configuradas por variables de entorno
**When** el servicio de storage se inicializa
**Then** se conecta al bucket especificado dentro de la capa Always Free

**Given** un fallo en el upload a OCI (timeout, error de red)
**When** se intenta persistir el documento
**Then** el pipeline continua normalmente (upload es best-effort, no bloquea)
**And** el error se loguea con contexto suficiente para diagnostico (NFR-4)

### Story 2.2: Almacenamiento de Paquetes Educativos en OCI

As a sistema,
I want almacenar cada paquete educativo generado en OCI Object Storage,
So that los resultados quedan persistidos y son consultables desde el historial.

**Acceptance Criteria:**

**Given** un paquete educativo generado exitosamente por el pipeline
**When** se completa el nodo format_output
**Then** el JSON del paquete se sube al bucket configurado en OCI Object Storage
**And** el identificador del objeto referencia: document_id, perfil, formato y timestamp
**And** la respuesta al usuario incluye almacenamiento_oci con bucket, objeto_id y status_upload (FR-13)

**Given** un fallo en el upload del paquete a OCI
**When** se intenta persistir
**Then** el paquete educativo se retorna al usuario normalmente (upload no bloquea la entrega)
**And** almacenamiento_oci.status_upload indica "fallido" con mensaje descriptivo
**And** el error se loguea (NFR-4)

**Given** el bucket de OCI Object Storage
**When** se consultan los objetos almacenados
**Then** los paquetes educativos son listables y descargables con sus metadatos (soporte para FR-20 en Epic 3)

---

## Epic 3: Interfaz Web Completa

El usuario puede interactuar con el sistema desde un navegador: subir documentos, configurar parametros, lanzar generaciones con feedback visual, visualizar los resultados renderizados segun el formato pedagogico, y consultar un historial de generaciones anteriores.

### Story 3.1: Upload de Documentos y Configuracion de Parametros

As a usuario,
I want abrir una interfaz web, subir mi documento tecnico y configurar los parametros de adaptacion,
So that puedo usar NuevaMente sin necesidad de herramientas API externas.

**Acceptance Criteria:**

**Given** la aplicacion FastAPI iniciada
**When** accedo a la URL raiz en el navegador
**Then** veo una interfaz web profesional con area de upload y controles de parametros
**And** los archivos estaticos (HTML/CSS/JS) se sirven directamente desde FastAPI (app/static/)

**Given** la interfaz web cargada
**When** arrastro o selecciono un archivo PDF, .md o .txt
**Then** el archivo se carga con feedback visual (indicador de progreso o confirmacion)
**And** se muestra el nombre del archivo seleccionado

**Given** la interfaz con un documento cargado
**When** configuro los parametros
**Then** perfil_destinatario se selecciona desde un control con las 4 opciones predefinidas (FR-17)
**And** formato_salida se selecciona desde un control con las 5 opciones predefinidas (FR-17)
**And** nicho_sector ofrece opciones predefinidas (Fintech, Salud, E-commerce, General) mas un campo de texto libre (FR-17)

**Given** algun parametro obligatorio sin completar
**When** intento lanzar la generacion
**Then** la interfaz no permite el envio y muestra indicacion visual de los campos faltantes

**Given** documentos previamente procesados existentes en OCI
**When** la interfaz carga
**Then** puedo seleccionar un documento ya procesado en lugar de subir uno nuevo (FR-16)

### Story 3.2: Generacion con Feedback de Progreso y Visualizacion de Resultados

As a usuario,
I want lanzar la generacion y ver el progreso en tiempo real, y cuando termine, visualizar los resultados renderizados segun el formato pedagogico elegido,
So that tengo una experiencia fluida de principio a fin sin salir del navegador.

**Acceptance Criteria:**

**Given** documento cargado y los tres parametros completados
**When** presiono el boton de generacion
**Then** la interfaz envia POST /api/v1/adaptar con el archivo y parametros
**And** muestra un estado de carga/progreso durante el procesamiento (FR-18)
**And** el estado se actualiza mediante polling al endpoint GET /status

**Given** el pipeline completa exitosamente
**When** el paquete educativo esta listo
**Then** la interfaz renderiza el contenido segun el formato pedagogico:
- Flashcards: tarjetas interactivas con frente/dorso que se pueden voltear (FR-19)
- Quiz Interactivo: preguntas con opciones seleccionables, revelacion de respuesta correcta y justificacion (FR-19)
- Tutorial Paso a Paso: secuencia de pasos con explicaciones y ejemplos (FR-19)
- Resumen Ejecutivo: documento estructurado con secciones y puntos clave (FR-19)
- Guion de Clase: fases diferenciadas con notas para el formador (FR-19)

**And** todas las visualizaciones muestran metadatos pedagogicos (conceptos clave, prerrequisitos, tiempo estimado) y anclaje_fuente_score (FR-19)

**Given** el pipeline falla durante la ejecucion
**When** se detecta el error via polling
**Then** la interfaz muestra un mensaje de error descriptivo en espanol (FR-18)
**And** permite al usuario reintentar

### Story 3.3: Historial de Generaciones

As a usuario,
I want consultar mis generaciones anteriores desde una barra lateral,
So that puedo volver a visualizar resultados previos sin re-procesar el documento.

**Acceptance Criteria:**

**Given** la interfaz web cargada
**When** existen paquetes educativos persistidos en OCI Object Storage
**Then** la barra lateral muestra una lista de generaciones anteriores con: nombre del documento, perfil, formato y fecha (FR-20)

**Given** la lista de generaciones en la barra lateral
**When** selecciono una entrada
**Then** el paquete educativo se carga desde OCI y se renderiza en la vista principal sin re-procesar (FR-20)
**And** la visualizacion usa el mismo renderizado por formato que Story 3.2

**Given** no existen generaciones anteriores
**When** la barra lateral carga
**Then** muestra un estado vacio con mensaje indicativo

**Given** la interfaz web completa (HTML + CSS + JS)
**When** se sirve desde FastAPI
**Then** el peso total es lo suficientemente ligero para no impactar significativamente el servidor de 1GB RAM

---

## Epic 4: Escenarios de Demostracion y Documentacion

Los evaluadores del hackathon pueden ver al menos 3 escenarios de ejecucion con documentacion real, un README.md completo con diagrama de arquitectura y guia de instalacion, y un repositorio Git con commits claros.

### Story 4.1: Ejecucion de Escenarios de Demostracion

As a evaluador del hackathon,
I want ver al menos 3 escenarios distintos de adaptacion con documentacion real,
So that puedo verificar que el sistema funciona correctamente con casos reales.

**Acceptance Criteria:**

**Given** el sistema NuevaMente funcionando end-to-end (Epics 1-3 completadas)
**When** se ejecutan los escenarios de demo
**Then** Escenario 1: classes.txt (Python 3.14) genera Flashcards/Principiante y Resumen Ejecutivo/Lider Tecnico -- demostrando diferenciacion por perfil con el mismo documento
**And** Escenario 2: datastructures.txt (Python 3.14) genera Tutorial, Quiz y Flashcards con el mismo perfil -- demostrando diferenciacion por formato
**And** Escenario 3: classes.txt con perfil Junior y nicho libre "veterinario aprendiendo a programar" -- demostrando contextualizacion por nicho personalizado

**Given** los resultados de cada escenario
**When** se comparan los outputs
**Then** el contenido para Principiante es linguistica y estructuralmente diferente al de Lider Tecnico (SM-1)
**And** los 5 formatos pedagogicos generan JSON valido contra schema Pydantic (SM-2)
**And** el anclaje_fuente_score es >= 0.7 en todos los escenarios (SM-3)

**Given** los resultados generados
**When** se revisan
**Then** los outputs y sus metadatos se conservan como evidencia reproducible para la presentacion

### Story 4.2: Documentacion del Repositorio GitHub

As a evaluador del hackathon,
I want un repositorio Git bien documentado con diagrama de arquitectura y guia de instalacion,
So that puedo entender y reproducir la solucion.

**Acceptance Criteria:**

**Given** el repositorio del proyecto
**When** un evaluador accede al README.md
**Then** contiene: descripcion del proyecto, diagrama de arquitectura (mermaid o imagen), diagrama del flujo RAG/Agentes, guia de instalacion paso a paso, instrucciones de configuracion de variables de entorno, y como ejecutar los escenarios de demo

**Given** el repositorio
**When** se revisa la estructura
**Then** los commits son claros y descriptivos
**And** el codigo esta organizado segun la estructura definida en ARCHITECTURE.md sec. 6

**Given** el README.md
**When** un desarrollador sigue la guia de instalacion
**Then** puede levantar el sistema en local y ejecutar al menos un escenario de demo sin ambiguedad

---

## Epic 5: Diferenciales del Hackathon (Opcionales)

Funcionalidades adicionales que suman puntos en la evaluacion pero no son obligatorias. Priorizacion interna: (1) Quizzes interactivos, (2) Exportacion multiformato, (3) Despliegue OCI Compute.

### Story 5.1: Quizzes con Evaluacion en Tiempo Real

As a estudiante,
I want responder preguntas del quiz directamente en la interfaz y recibir retroalimentacion explicativa inmediata,
So that puedo evaluar mi comprension del tema en el momento.

**Acceptance Criteria:**

**Given** un paquete educativo de formato "Quiz Interactivo" renderizado en la interfaz
**When** selecciono una opcion de respuesta para una pregunta
**Then** la interfaz indica visualmente si la respuesta es correcta o incorrecta
**And** muestra la justificacion anclada al documento fuente
**And** la retroalimentacion aparece inmediatamente sin recargar la pagina

**Given** un quiz completo respondido
**When** termino todas las preguntas
**Then** la interfaz muestra un resumen con: aciertos/total, porcentaje, y conceptos que requieren repaso

### Story 5.2: Exportacion Multiformato

As a usuario,
I want descargar el paquete educativo generado en diferentes formatos,
So that puedo usar el contenido en la herramienta de estudio que prefiera.

**Acceptance Criteria:**

**Given** un paquete educativo renderizado en la interfaz
**When** selecciono la opcion de descarga
**Then** puedo elegir entre los formatos: Markdown (.md), JSON original (.json), o CSV compatible con Anki (.csv)

**Given** la opcion de descarga Markdown
**When** descargo el archivo
**Then** el contenido esta formateado como Markdown legible con la estructura del formato pedagogico

**Given** la opcion de descarga CSV para Anki (solo aplica a Flashcards)
**When** descargo el archivo
**Then** el CSV contiene columnas frente, dorso y pista_didactica, importable directamente en Anki

### Story 5.3: Despliegue en OCI Compute

As a evaluador del hackathon,
I want acceder a NuevaMente desplegado en una instancia de OCI Compute Always Free,
So that puedo verificar que la solucion funciona en la nube de Oracle.

**Acceptance Criteria:**

**Given** una instancia VM.Standard.E2.1.Micro creada en OCI (1GB RAM, 1 OCPU, Always Free)
**When** se despliega la aplicacion
**Then** NuevaMente corre en la instancia gestionada por systemd via Uvicorn en puerto 8000
**And** la instancia tiene 4-8 GB de swap configurado para compensar la limitacion de RAM
**And** la aplicacion es accesible desde internet via HTTP/HTTPS

**Given** el sistema desplegado en OCI
**When** se ejecuta un escenario de demo end-to-end
**Then** el pipeline completa exitosamente dentro de los limites de recursos de la instancia Always Free
**And** ningun servicio utilizado genera costos monetarios (NFR-3)
