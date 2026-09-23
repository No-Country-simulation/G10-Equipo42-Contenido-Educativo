---
title: NuevaMente – Sistema Inteligente de Adaptación y Generación de Contenido Educativo
status: draft
created: 2026-09-22
updated: 2026-09-22
---

# PRD: NuevaMente – Sistema Inteligente de Adaptación y Generación de Contenido Educativo

## 0. Propósito del Documento
Este Documento de Requisitos de Producto (PRD) establece el alcance, capacidades funcionales, restricciones técnicas y criterios de éxito para **NuevaMente**, una plataforma inteligente de EdTech desarrollada para el **Hackathon ONE G10 (Oracle Next Education & Alura)**. El documento está dirigido al equipo de ingeniería, diseñadores instruccionales y evaluadores del Hackathon (jurado de empresas de tecnología). Define con precisión qué debe construir el MVP, fijando restricciones inflexibles como el uso exclusivo de la capa **Always Free de Oracle Cloud Infrastructure (OCI)** y la mitigación rigurosa de alucinaciones mediante RAG. Audiencia primaria de evaluación: ingenieros y representantes de empresas de tecnología; esto orienta qué demostrar primero en el pitch (fidelidad, arquitectura RAG, contrato JSON estructurado).

---

## 1. Visión del Producto
La documentación técnica, los manuales de arquitectura en la nube y los estándares de ingeniería son fuentes de conocimiento ricas pero densas, complejas y a menudo inaccesibles para audiencias no técnicas o personas en transición de carrera. Adaptar manualmente estos contenidos para diferentes niveles pedagógicos (desde un estudiante que aprende su primera red virtual hasta un CTO o un desarrollador junior) consume semanas de trabajo manual por parte de diseñadores instruccionales y expertos en la materia.

**NuevaMente** automatiza esta transformación en cuestión de minutos. Mediante un pipeline avanzado de **Retrieval-Augmented Generation (RAG)** y una orquestación inteligente de agentes/cadenas de prompts con LLMs, el sistema ingiere documentos técnicos (PDF, Markdown o texto plano) y genera automáticamente experiencias didácticas personalizadas (tutoriales paso a paso, flashcards nemotécnicas, quizzes explicativos y resúmenes ejecutivos) adaptadas al perfil del destinatario y al nicho de aplicación. Todo el contenido generado se ancla con rigor matemático y semántico en las fuentes originales, emitiendo un reporte de fidelidad y persistiendo los artefactos de forma 100% gratuita y escalable en **OCI Object Storage**.

---

## 2. Usuarios Objetivo y Experiencia

### 2.1 Jobs To Be Done (JTBD)
- **Estudiantes / Principiantes en Tecnología:** "Cuando intento aprender un concepto técnico complejo de la nube o programación, quiero explicaciones con analogías cotidianas y recursos de memorización (flashcards) para asimilar los fundamentos sin sentirme intimidado por tecnicismos."
- **Desarrolladores Junior / Semi Senior:** "Cuando leo una especificación técnica o manual de producto, quiero guías paso a paso y tutoriales con código claro para implementar la funcionalidad rápidamente en mis tareas diarias."
- **Líderes Técnicos / Arquitectos:** "Cuando evalúo una nueva tecnología o estándar, quiero resúmenes técnicos densos y cuestionarios con justificación para validar conceptos clave y transferir buenas prácticas a mi equipo."
- **Gestores / Ejecutivos (No Técnicos):** "Cuando recibo reportes o manuales de sistemas, quiero resúmenes de alto nivel (TL;DR) e impacto de negocio para tomar decisiones estratégicas de inversión sin tener que descifrar la sintaxis técnica."

### 2.2 No-Usuarios (v1)
- Alumnos de nivel escolar primario o contenido no técnico/académico general sin documentación base.
- Equipos que busquen un CMS completo o plataforma LMS corporativa integrada con SCORM/Moodle en v1.

### 2.3 Recorridos de Usuario Principales (User Journeys)

#### UJ-1. Sofía (en transición de carrera) convierte un manual de redes OCI en Flashcards didácticas
- **Persona y contexto:** Sofía, estudiante del programa ONE proveniente de otra carrera, necesita aprender qué es una Virtual Cloud Network (VCN) para su examen práctico.
- **Estado inicial:** Accede a la interfaz web de NuevaMente vía navegador local/web (sin autenticación requerida en MVP).
- **Ruta de acción:**
  1. Carga el archivo PDF de arquitectura VCN de Oracle Cloud.
  2. Selecciona el perfil *"Principiante / Transición de Carrera"*, formato *"Flashcards de Memorización"* y nicho *"General"*.
  3. Presiona el botón *"Generar Contenido Educativo"*.
  4. Visualiza el panel de progreso en tiempo real con sub-pasos expandibles: Ingestión → Indexación RAG → Generación Didáctica → Evaluación de Fidelidad → Almacenamiento en OCI (realiza FR-10, FR-12).
- **Clímax:** La pantalla presenta una baraja interactiva de flashcards con analogías ("Una VCN es como un barrio privado cerrado dentro de la nube donde tú decides quién entra") junto con una pista didáctica y una insignia de calidad: *"Fidelidad a la fuente: 98% (Alta)"*.
- **Resolución:** Sofía interactúa volteando las tarjetas (acción flip visual), descarga el archivo JSON estructurado y visualiza el enlace persistente en OCI Object Storage con `objeto_id` confirmado.
- **Caso borde:** Si el PDF contiene texto corrupto o escaneado ilegible, el sistema notifica amistosamente el error antes de invocar el LLM, solicitando un formato de texto seleccionable o Markdown.
- **Condiciones de salida comprobables (pre-AC):**
  - El JSON generado tiene `status: "exito"` y al menos 3 flashcards con campos `frente`, `dorso` y `pista_didactica` no vacíos.
  - `anclaje_fuente_score` ≥ 0.85 en la respuesta.
  - El campo `almacenamiento_oci.status_upload` es `"completado"` (o `"mock_local"` en modo desarrollo).
  - El panel de progreso mostró exactamente los 5 sub-pasos antes de presentar el resultado.

#### UJ-2. Marcos (Tech Lead) genera un Quiz y Tutorial para capacitar a sus Juniors
- **Persona y contexto:** Marcos necesita transferir conocimiento sobre directivas de seguridad en AWS/OCI a su equipo junior antes de un despliegue.
- **Estado inicial:** Abre NuevaMente desde la interfaz interactiva.
- **Ruta de acción:**
  1. Ingresa la documentación en formato Markdown pegada en el editor o subida como archivo `.md`.
  2. Configura los parámetros: Perfil *"Desarrollador Junior / Semi Senior"*, Formato *"Quiz Interactivo con Justificaciones"*, Nicho *"Fintech"*.
  3. Solicita la generación.
- **Clímax:** El sistema genera 5 preguntas de selección múltiple donde cada opción incorrecta explica exactamente por qué es errónea basándose en los extractos del documento técnico original.
- **Resolución:** Marcos interactúa con el quiz en la UI (selecciona opciones, ve la justificación), exporta el JSON estructurado para compartirlo en la sesión de equipo.
- **Condiciones de salida comprobables (pre-AC):**
  - El JSON contiene exactamente 5 items tipo quiz, cada uno con campos `pregunta`, `opciones` (mínimo 4), `respuesta_correcta` y `justificacion` no vacíos.
  - La UI permite seleccionar cada opción y revela la justificación al confirmar.
  - `anclaje_fuente_score` ≥ 0.85.

#### UJ-3. Elena (Directora de Tecnología) evalúa un reporte de arquitectura de seguridad en 5 minutos
- **Persona y contexto:** Elena, CTO de una empresa Fintech, recibe un manual técnico de 40 páginas sobre controles de seguridad en OCI. Necesita evaluar su pertinencia para un proyecto sin leer el documento completo.
- **Estado inicial:** Accede a NuevaMente desde el navegador, en una reunión ejecutiva de 20 minutos.
- **Ruta de acción:**
  1. Carga el PDF del reporte de seguridad.
  2. Selecciona el perfil *"Gestor / Ejecutivo (No Técnico)"*, formato *"Resumen Ejecutivo (TL;DR)"*, nicho *"Fintech"* y nivel de detalle *"Conciso"*.
  3. Solicita la generación.
- **Clímax:** NuevaMente produce en menos de 30 segundos un resumen estructurado de 3 a 5 puntos clave de alto impacto de negocio, sin tecnicismos, incluyendo: hallazgo principal, impacto estimado en operaciones, recomendación de acción ejecutiva y score de confianza en la fuente.
- **Resolución:** Elena puede decidir con fundamento si el reporte merece asignación presupuestaria, sin depender del equipo técnico para decodificarlo.
- **Condiciones de salida comprobables (pre-AC):**
  - El JSON contiene entre 3 y 5 items de tipo TL;DR con campos `hallazgo`, `impacto_negocio` y `recomendacion` no vacíos.
  - El contenido no usa jerga técnica sin definición previa en el ítem (verificable por ausencia de acrónimos sin explicar en el campo `hallazgo`).
  - `anclaje_fuente_score` ≥ 0.80 (umbral ligeramente menor ya que la abstracción ejecutiva implica mayor paráfrasis justificada).
  - Tiempo de generación < 30 segundos.

---

## 3. Glosario de Términos del Dominio
- **Documento Técnico de Origen:** Archivo de entrada (PDF, Markdown o texto) que contiene la fuente fidedigna de conocimiento a procesar.
- **Chunk (Fragmento):** Porción de texto delimitada semánticamente extraída del documento de origen para su vectorización.
- **Embedding (Voyage AI):** Vector numérico de alta dimensionalidad generado mediante el modelo **`voyage-multilingual-2`** de Voyage AI, que representa el significado semántico de un chunk optimizado para documentación técnica multilingüe (español/inglés).
- **Vector Store (ChromaDB):** Base de datos vectorial embebida en Python (ChromaDB) utilizada para la búsqueda semántica por similitud de coseno. Tecnología fijada para el MVP.
- **RAG (Retrieval-Augmented Generation):** Técnica de recuperación y enriquecimiento contextual que provee a la LLM los chunks pertinentes para fundamentar las respuestas en la fuente original.
- **LLM Principal (Gemini Flash):** Google Gemini Flash (1.5 o 2.0) es el modelo de lenguaje fundacional predeterminado para la generación de contenido educativo. El sistema es intercambiable con cualquier proveedor que soporte la **OpenAI Chat Completions API** (`/v1/chat/completions`).
- **Score de Anclaje a la Fuente (`anclaje_fuente_score`):** Métrica cuantitativa (0.0 a 1.0) calculada por el revisor del sistema que mide el porcentaje de afirmaciones verificables en los chunks recuperados.
- **Paquete de Contenido Educativo:** Objeto JSON validado con tipado estricto que agrupa metadatos pedagógicos, contenido adaptado, evaluación de calidad y referencias de almacenamiento.
- **OCI Object Storage Always Free:** Servicio de almacenamiento de objetos en la nube de Oracle, configurado estrictamente en la capa gratuita (Always Free) para almacenar los documentos originales y paquetes JSON generados.
- **Mock Local OCI:** Modo de emulación de OCI para desarrollo local. Persiste el JSON en disco bajo un directorio local controlado y retorna un `objeto_id` determinístico que respeta el mismo contrato de campos Pydantic que el modo producción.

---

## 4. Características y Requisitos Funcionales

### 4.1 Ingestión y Procesamiento de Documentos Técnicos
**Descripción:** Módulo responsable de recibir los archivos técnicos en diversos formatos, extraer su contenido textual limpio, validar su longitud mínima y prepararlo para la tokenización. Realiza UJ-1, UJ-2, UJ-3.

#### FR-1: Soporte Multiformato de Entrada
El sistema debe permitir la carga e ingestión de archivos en formatos `.pdf`, `.md` (Markdown) y `.txt` (texto sin formato), así como el ingreso de texto directo vía interfaz.
**Consecuencias comprobables:**
- Al subir un archivo PDF válido mediante `pypdf`, el sistema extrae el 100% del texto seleccionable sin errores de codificación UTF-8.
- Si se carga un archivo no soportado (ej.: `.docx`, `.exe`), el sistema rechaza la carga retornando un mensaje de validación amigable sin colapsar el backend.

#### FR-2: Normalización y Limpieza de Texto
El sistema debe limpiar caracteres especiales, encabezados/pies de página repetitivos y saltos de línea anómalos antes del proceso de chunking.

---

### 4.2 Pipeline RAG con Voyage AI y ChromaDB
**Descripción:** Segmenta el texto en fragmentos coherentes, genera embeddings mediante **Voyage AI (`voyage-multilingual-2`)** y almacena las representaciones en **ChromaDB** (Vector Store local fijo para el MVP) para permitir la recuperación precisa de contexto didáctico.

#### FR-3: Segmentación Inteligente (Chunking)
El sistema debe segmentar el texto extraído utilizando una estrategia con solapamiento (`chunk_size` y `chunk_overlap` configurables, valores por defecto: `chunk_size=800`, `chunk_overlap=150` caracteres).
**Consecuencias comprobables:**
- Ningún chunk excede el límite máximo de tokens configurado.
- Los chunks preservan la coherencia semántica en los límites de párrafos o secciones técnicas.

#### FR-4: Generación de Embeddings con Voyage AI
El sistema debe usar exclusivamente el modelo **`voyage-multilingual-2`** de Voyage AI para la generación de embeddings de todos los chunks. La dimensión del vector queda fijada por el modelo (`1024`d) y no debe modificarse sin migrar el índice de ChromaDB.
**Consecuencias comprobables:**
- Todos los vectores almacenados en ChromaDB tienen dimensión `1024`.
- Si la llamada a la API de Voyage AI falla, el sistema retorna un error descriptivo y no continúa el pipeline.

#### FR-5: Indexación y Búsqueda en ChromaDB
El sistema debe indexar los embeddings en una colección persistente de ChromaDB y recuperar los $K$ fragmentos más relevantes (valor por defecto: `K=5`) basados en la consulta pedagógica generada.
**Consecuencias comprobables:**
- Ante una solicitud de adaptación, ChromaDB retorna los fragmentos con mayor similitud semántica en un tiempo inferior a 1.5 segundos.

---

### 4.3 Orquestación con LLMs y Adaptación Didáctica
**Descripción:** Orquesta prompts estructurados utilizando LLMs para transformar los fragmentos técnicos en el material educativo solicitado. El LLM predeterminado es **Google Gemini Flash**; la integración debe abstraerse mediante una capa intercambiable compatible con la **OpenAI Chat Completions API** (`/v1/chat/completions`) para soportar cualquier proveedor compatible (OpenAI, Mistral, Ollama, etc.) sin cambios de código.

#### FR-6: Parametrización Multidimensional
El sistema debe recibir obligatoriamente los siguientes parámetros para guiar la transformación:
1. **Perfil del Destinatario:** Principiante / Transición de Carrera, Desarrollador Junior / Semi Senior, Líder Técnico / Arquitecto, Gestor / Ejecutivo (No Técnico).
2. **Formato Pedagógico de Salida:** Guía Práctica Paso a Paso (Tutorial), Flashcards de Memorización, Quiz Interactivo con Justificaciones, Resumen Ejecutivo (TL;DR), Guion de Clase / Video.
3. **Nicho / Contexto de Aplicación:** Fintech, Salud, E-commerce, General.
4. **Nivel de Detalle:** Didáctico, Técnico, Conciso.

#### FR-7: Capa de Abstracción LLM (OpenAI-Compatible)
El sistema debe implementar una capa de cliente LLM configurable que:
- Use **Gemini Flash** como proveedor predeterminado.
- Soporte cualquier proveedor alternativo que exponga una API OpenAI-compatible (`/v1/chat/completions`) mediante configuración de `LLM_BASE_URL` y `LLM_API_KEY` en variables de entorno.
- Permita cambiar de proveedor sin modificar el código de negocio.
**Consecuencias comprobables:**
- Modificando únicamente las variables de entorno `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL` y `LLM_API_KEY`, el sistema opera con un proveedor alternativo (ej.: Ollama local) sin cambios en el código de la capa de negocio.

#### FR-8: Generación Estructurada y Tipada (Pydantic / Structured Outputs)
La salida generada por la LLM debe ajustarse estrictamente al esquema JSON oficial especificado por el Hackathon ONE, conteniendo:
- `status`: `"exito"` | `"error"`
- `metadatos`: perfil aplicado, formato generado, tiempo estimado de estudio en minutos, conceptos clave.
- `contenido_adaptado`: título, introducción contextualizada, items (según el formato elegido, e.g. frente/dorso/pista en flashcards; preguntas/opciones/justificacion en quizzes; hallazgo/impacto_negocio/recomendacion en TL;DR).
- `evaluacion_calidad`: score de anclaje, claridad pedagógica, observaciones.
- `almacenamiento_oci`: nombre de bucket, objeto_id, status de subida.
**Consecuencias comprobables:**
- El 100% de las respuestas exitosas pasan la validación estricta del modelo Pydantic sin errores de parseo de JSON.

---

### 4.4 Evaluación de Calidad y Mitigación de Alucinaciones
**Descripción:** Evalúa de manera automatizada si el contenido producido se encuentra estrictamente fundamentado en la documentación técnica de origen, previniendo invenciones del modelo.

#### FR-9: Cálculo de Score de Anclaje a la Fuente
El sistema debe evaluar el contenido generado contra los chunks recuperados del documento original y asignar un valor numérico `anclaje_fuente_score` entre 0.0 y 1.0.
**Consecuencias comprobables:**
- Si un contenido introduce conceptos o directivas no respaldadas por la fuente original, el score de anclaje decrece y se refleja una advertencia en las observaciones de calidad.
- Si el score es inferior al umbral configurable (por defecto `0.70` para perfiles técnicos, `0.65` para perfiles ejecutivos), el sistema reintenta la generación automáticamente hasta 2 veces o emite una alerta pedagógica al usuario.

---

### 4.5 Persistencia en Nube OCI Object Storage (Always Free)
**Descripción:** Integración obligatoria con Oracle Cloud Infrastructure para almacenar los documentos técnicos originales cargados y los paquetes educativos en JSON generados.

#### FR-10: Carga y Almacenamiento en Bucket OCI Always Free
El sistema debe utilizar el SDK oficial de OCI para Python (`oci`) o llamadas REST autenticadas para persistir:
1. El archivo fuente original en el bucket de entrada (`nuevamente-documentos-origen`).
2. El archivo JSON estructurado generado en el bucket de contenidos (`nuevamente-contenidos-educativos`).
**Consecuencias comprobables:**
- Toda operación de guardado genera un `objeto_id` único con patrón `{formato}-{perfil_slug}-{timestamp}.json` y confirma el campo `"status_upload": "completado"`.
- La configuración utiliza credenciales Always Free sin invocar servicios facturables de OCI.

#### FR-11: Modo Mock Local para Desarrollo (Contrato Explícito)
El sistema debe proveer un modo de emulación local activado mediante la variable de entorno `OCI_MOCK=true`. En este modo:
- Los archivos se guardan en el directorio local `./mock_oci_storage/{bucket_name}/{objeto_id}` relativo a la raíz del proyecto.
- El `objeto_id` se genera con el mismo patrón determinístico que en producción: `{formato}-{perfil_slug}-{timestamp}.json`.
- El campo `almacenamiento_oci.status_upload` retorna `"mock_local"` (no `"completado"`) para distinguir entornos.
- El modelo Pydantic acepta `"mock_local"` como valor válido del campo `status_upload` en modo desarrollo.
**Consecuencias comprobables:**
- Con `OCI_MOCK=true`, el sistema completa el flujo completo (incluyendo la fase de "Almacenamiento") sin credenciales OCI, guardando el JSON en `./mock_oci_storage/`.
- El JSON guardado localmente es byte-a-byte idéntico al que se subiría a OCI en producción (misma serialización, mismos campos).

---

### 4.6 Interfaz Interactiva de Usuario (Streamlit)
**Descripción:** Frontend intuitivo y dinámico construido con **Streamlit** que permite cargar archivos, configurar los selectores pedagógicos y visualizar el contenido adaptado interactivamente. Streamlit es la tecnología fija para el MVP.

#### FR-12: Carga y Configuración en UI
La interfaz debe disponer de componentes para:
- Subir archivos (PDF, MD, TXT) mediante `st.file_uploader`.
- Selectores desplegables (`st.selectbox`) para Perfil, Formato, Nicho y Nivel de Detalle.
- Botón principal "Generar Contenido Educativo".

#### FR-13: Panel de Progreso en Tiempo Real
La interfaz debe mostrar el avance del pipeline mediante `st.status()` con sub-pasos expandibles que reflejen en tiempo real cada fase: Ingestión → Indexación RAG → Generación Didáctica → Evaluación de Fidelidad → Almacenamiento en OCI. El usuario debe ver feedback de cada etapa antes de que finalice la siguiente.
**Consecuencias comprobables:**
- El usuario visualiza al menos 5 actualizaciones de estado progresivas durante la generación.
- Si una etapa falla, el panel de estado muestra exactamente en qué fase ocurrió el error con un mensaje descriptivo.

#### FR-14: Visualización Rica del Contenido Educativo
La interfaz debe renderizar visualmente el resultado según el formato seleccionado:
- Flashcards visuales interactivas con flip (frente / dorso / pista).
- Quizzes interactivos donde el usuario pueda seleccionar opciones y ver la justificación en tiempo real.
- Tutoriales paso a paso con bloques de código formateados y syntax highlighting.
- Resúmenes ejecutivos con estructura de puntos clave de alto impacto.
- Panel lateral con métricas de calidad (`anclaje_fuente_score`, tiempo estimado de estudio) e indicador del estado de persistencia en OCI.

---

## 5. No-Objetivos Explícitos (Non-Goals para el MVP)
- **No es una plataforma de gestión de usuarios (LMS/Auth completo):** No se implementará en el MVP registro de usuarios con contraseñas, pagos o roles complejos. La app opera en modo sesión interactiva.
- **No habrá fine-tuning de modelos fundacionales:** No se entrenarán nuevos pesos neuronales; se utiliza RAG + Prompt Engineering + Structured Outputs.
- **No se consumirán servicios de pago en OCI:** Queda estrictamente prohibido aprovisionar recursos fuera de la capa Always Free de OCI para evitar cualquier cargo a los estudiantes del programa ONE.
- **No se dará soporte inicial a archivos de imagen/audio sin texto:** No se procesarán en el MVP videos ni audios en bruto, enfocándose en documentos técnicos escritos (PDF/MD/TXT).
- **No se migrarán embeddings en runtime:** El modelo de embeddings (`voyage-multilingual-2`) está fijado para el MVP. Cambiar el modelo implica reindexar; esta operación no se expone como función de usuario.

---

## 6. Alcance del MVP

### 6.1 Dentro del Alcance (In Scope)
- Pipeline completo de ingesta para PDF (PyPDF), Markdown y TXT.
- Pipeline RAG con chunking y embeddings **Voyage AI `voyage-multilingual-2`** + Vector Store **ChromaDB**.
- Capa de abstracción LLM compatible con OpenAI API; **Gemini Flash** como proveedor predeterminado.
- Adaptación demostrable de un mismo documento técnico a los **4 perfiles** y al menos **3 formatos didácticos distintos** en la demo del Hackathon.
- Evaluación automatizada de fidelidad técnica (`anclaje_fuente_score`) con reintento automático.
- Integración funcional con **OCI Object Storage** (Always Free) mediante `oci-sdk` + modo **Mock Local** con contrato Pydantic idéntico.
- Interfaz interactiva en **Streamlit** con progreso en tiempo real y visualizaciones ricas.
- Demostración de al menos **3 escenarios reales de adaptación** (UJ-1, UJ-2, UJ-3).
- Documentación completa con arquitectura y guía de despliegue en `README.md`.

### 6.2 Fuera del Alcance para el MVP (Diferenciales Opcionales)
- Despliegue en máquina virtual Linux en OCI Compute Instance (Diferencial Opcional).
- Sistema Multi-Agente con grafo de decisión en LangGraph (Enrutador, Investigador, Redactor, Revisor) (Diferencial Opcional).
- Exportación a CSV de Anki o PDF descargable con estilo (Diferencial Opcional).
- Soporte multimodal de diagramas técnicos con modelos de visión (Diferencial Opcional).

---

## 7. Métricas de Éxito y Criterios de Evaluación

### Métricas Principales (Primary)
- **SM-1 (Fidelidad Técnica):** El 100% de las respuestas generadas en los escenarios de prueba deben obtener un `anclaje_fuente_score` ≥ 0.85 para perfiles técnicos y ≥ 0.80 para perfiles ejecutivos. Valida FR-5, FR-9.
- **SM-2 (Integridad del Contrato JSON):** 100% de las respuestas exitosas cumplen la validación de esquema Pydantic en el primer intento o tras reintento automático (máx. 2). Valida FR-8.
- **SM-3 (Persistencia Efectiva en OCI):** 100% de los paquetes educativos generados durante la demo se registran en el bucket Always Free de OCI con `status_upload: "completado"`. Valida FR-10.
- **SM-4 (Versatilidad Pedagógica Comprobada):** El sistema genera con éxito al menos 3 combinaciones ortogonales con diferenciación real observable en tono y estructura (UJ-1, UJ-2, UJ-3). Valida FR-6.

### Métricas Secundarias
- **SM-5 (Tiempo de Respuesta):** Tiempo total de procesamiento y generación de contenido inferior a 30 segundos por documento promedio (1 a 10 páginas). Valida UJ-3.

### Contra-métricas (Lo que NO se debe optimizar a expensas de la calidad)
- **SM-C1 (Extensión vs Claridad):** No optimizar por generar respuestas verbose. Para perfiles principiantes y ejecutivos, la concisión y las analogías claras priman sobre la cantidad de texto.
- **SM-C2 (Velocidad vs Verificación):** No omitir la fase de verificación de anclaje para reducir latencia. La fidelidad al material técnico original es el pilar central del proyecto y el criterio más valorado por el jurado técnico.

---

## 8. Requisitos No Funcionales Transversales y Restricciones (NFRs)

### 8.1 Restricciones de Costo y Nube (Inflexibles)
- **Cero Costo Monetario:** Todas las dependencias de nube deben operar estrictamente bajo la capa Always Free de Oracle Cloud Infrastructure.

### 8.2 Stack Tecnológico Fijado para el MVP
| Componente | Tecnología Fijada |
|---|---|
| Interfaz de Usuario | Streamlit |
| Embeddings | Voyage AI — `voyage-multilingual-2` |
| Vector Store | ChromaDB (persistente en disco local) |
| LLM Predeterminado | Google Gemini Flash (1.5 / 2.0) |
| Protocolo de Intercambio LLM | OpenAI Chat Completions API (`/v1/chat/completions`) |
| Almacenamiento en Nube | OCI Object Storage (Always Free) |
| Tipado de Contratos | Pydantic v2 |
| Extracción de PDFs | pypdf / pdfplumber |

### 8.3 Rendimiento y Resiliencia
- **Manejo de Excepciones:** Errores de red con APIs de LLM, Voyage AI o OCI deben capturarse amigablemente con mensajes descriptivos en la UI sin stack traces expuestos.
- **Control de Cuotas de API:** Implementación de retries con backoff exponencial para rate limits de proveedores (Gemini, Voyage AI).

### 8.4 Privacidad y Seguridad
- Las claves de API (Gemini API Key, Voyage AI API Key, credenciales OCI) se gestionan exclusivamente mediante variables de entorno (`.env` / `secrets.toml`) y jamás se commitean al repositorio Git.

---

## 9. Decisiones Tomadas (ex-Preguntas Abiertas)
1. ✅ **LLM Principal:** Google Gemini Flash (1.5/2.0). La capa de integración expone el contrato OpenAI-compatible para permitir cambiar a cualquier proveedor alternativo (OpenAI, Mistral, Ollama) mediante configuración de variables de entorno, sin cambios de código.
2. ⏳ **Credenciales OCI:** Pendiente de configuración por el equipo. El modo `OCI_MOCK=true` está definido con contrato explícito (FR-11) para desbloquear el desarrollo local hasta que se dispongan las credenciales.
3. ✅ **Interfaz de Usuario:** Streamlit. Tecnología fijada para el MVP por velocidad de desarrollo y soporte nativo de `st.status()` para progreso en tiempo real.
4. ✅ **Modelo de Embeddings:** Voyage AI — `voyage-multilingual-2`. Dimensión de vector: `1024`. Fijo para el MVP; migración de índice requerida si se cambia.
5. ✅ **Jurado del Hackathon:** Empresas de tecnología. La demo debe priorizar: arquitectura RAG, contrato JSON, fidelidad técnica y versatilidad de perfiles.

---

## 10. Índice de Suposiciones (`[ASSUMPTION]`)
- **[ASSUMPTION-1]:** Streamlit es la interfaz recomendada. *Cerrado — decisión confirmada.*
- **[ASSUMPTION-2]:** El modo mock local de OCI replica fielmente el contrato Pydantic de producción. *Cerrado — definido en FR-11.*
- **[ASSUMPTION-3]:** ChromaDB como Vector Store predeterminado por su instalación embebida en Python sin dependencias de servicios externos. *Cerrado — decisión confirmada.*
