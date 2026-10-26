---
title: "NuevaMente — Sistema Inteligente de Adaptación y Generación de Contenido Educativo"
status: draft
created: 2026-09-23
updated: 2026-09-23
---

# Product Brief: NuevaMente

## Resumen Ejecutivo

NuevaMente es un sistema inteligente que transforma documentación técnica densa en contenido educativo personalizado. A diferencia de un chatbot RAG convencional, NuevaMente no responde preguntas — *transforma* documentos completos en paquetes educativos estructurados y adaptados al perfil del destinatario, al formato pedagógico elegido y al contexto de aplicación que el usuario necesite.

El sistema recibe un documento técnico (PDF, Markdown o texto plano), permite al usuario seleccionar su nivel de conocimiento, el formato de estudio preferido y el nicho o contexto de aplicación, y genera un paquete educativo completo: contenido adaptado, metadatos de aprendizaje (conceptos clave, prerrequisitos, tiempo estimado de estudio) y una evaluación de fidelidad respecto al documento fuente. Todo en salida JSON estructurada, listo para integración con sistemas externos.

El proyecto nace en el marco del Hackathon ONE G10 (Oracle Next Education & Alura) como una demostración de competencia en IA Generativa, RAG, orquestación de agentes y Oracle Cloud Infrastructure — y como herramienta que su propio creador usaría para estudiar.

## El Problema

Las empresas, instituciones educativas y equipos de tecnología producen documentación técnica rica y detallada — manuales de infraestructura, referencias de API, guías de arquitectura — que es valiosa pero a menudo inaccesible para quienes no dominan la jerga técnica avanzada. Un mismo manual de Python necesita enseñarse de formas radicalmente distintas a un principiante en transición de carrera y a un líder técnico que evalúa una decisión de arquitectura.

La adaptación manual de estos materiales consume semanas de trabajo de especialistas y diseñadores instruccionales. Para cuando el material adaptado está listo, la documentación fuente puede haber cambiado. Y cada combinación de audiencia × formato × contexto multiplica el esfuerzo.

El resultado: la mayoría de la documentación técnica no se adapta nunca, y quienes más la necesitan — los que están aprendiendo — son quienes menos pueden consumirla en su forma original.

## La Solución

NuevaMente automatiza este flujo mediante un pipeline de RAG (Retrieval-Augmented Generation) integrado con LLMs. El sistema:

1. **Ingiere** el documento técnico, lo segmenta en chunks semánticos y genera embeddings vectoriales para indexarlo.
2. **Recibe parámetros** del usuario:
   - **Perfil del destinatario**: Principiante, Desarrollador Junior/Semi Senior, Líder Técnico/Arquitecto, Gestor/Ejecutivo No Técnico.
   - **Formato pedagógico**: Tutorial Paso a Paso, Flashcards, Quiz Interactivo, Resumen Ejecutivo, Guión de Clase.
   - **Nicho/contexto**: opciones predefinidas (Fintech, Salud, E-commerce, General) **más input libre** donde el usuario puede describir su propio contexto en sus palabras.
3. **Orquesta** agentes o cadenas de prompts que consultan el índice vectorial del documento fuente para redactar, adaptar y revisar el contenido generado — anclando cada afirmación en la fuente original.
4. **Entrega** un paquete JSON estructurado con el contenido adaptado, metadatos pedagógicos y un score de anclaje a fuente que mide la fidelidad del contenido generado respecto al documento original.
5. **Persiste** los documentos originales y los paquetes generados en OCI Object Storage (capa Always Free).

La experiencia del usuario es simple: sube un documento, elige tres parámetros, y recibe contenido educativo listo para consumir o integrar.

## Qué Hace Diferente a NuevaMente

**Transformación, no conversación.** La mayoría de los proyectos RAG son chatbots donde el usuario pregunta y el sistema responde. NuevaMente no tiene campo de chat — el sistema *transforma* un documento entero en un producto educativo nuevo. Esto es conceptualmente distinto y técnicamente más exigente que un Q&A.

**Mismo input, N salidas completamente distintas.** El verdadero test del sistema es tomar un único archivo — por ejemplo, el tutorial de clases de Python (922 líneas de documentación densa) — y producir flashcards para un principiante, un resumen ejecutivo para un gerente en el contexto Fintech, y un tutorial paso a paso para un desarrollador junior. La fuente es la misma; los productos son irreconocibles entre sí.

**Salida estructurada con metadatos pedagógicos.** No devuelve texto libre — devuelve JSON tipado con conceptos clave, prerrequisitos, tiempo estimado de estudio y el contenido adaptado organizado por secciones. Esto es producción, no prototipo.

**Verificación de fidelidad a la fuente.** El `anclaje_fuente_score` mide cuánto se desvió el LLM del documento original. La mayoría de los sistemas de generación con IA ignoran esta verificación. NuevaMente la hace explícita y medible.

**Personalización abierta sin complejidad adicional.** El campo de nicho acepta texto libre — el usuario puede escribir "soy veterinario aprendiendo a programar" en lugar de elegir de una lista cerrada. Esto va directo al prompt del LLM y personaliza la salida sin agregar complejidad al pipeline.

## A Quién Sirve

NuevaMente es una herramienta genérica de aprendizaje. Su usuario es cualquier persona que necesita aprender de documentación densa y quiere contenido adaptado a su nivel y contexto:

- **Un estudiante de informática** que recibe 900 líneas de documentación de Python sobre clases y necesita flashcards para memorizar los conceptos clave antes de un examen.
- **Un ejecutivo no técnico** que necesita entender qué es una VCN en Oracle Cloud para tomar una decisión de inversión, sin leer 30 páginas de referencia técnica.
- **Un profesor** que quiere generar un quiz interactivo con justificaciones a partir de un capítulo de documentación para sus alumnos.
- **Un desarrollador junior** que necesita un tutorial paso a paso de LangGraph contextualizado a su proyecto de e-commerce.

El sistema no distingue — adapta. La misma documentación puede servir a todos estos perfiles con salidas completamente diferentes.

## Criterios de Éxito

### Para el hackathon (obligatorios)
- Ingestión funcional de documentos técnicos (PDF, Markdown, texto plano).
- Pipeline RAG operativo con chunking, embeddings y búsqueda vectorial (FAISS).
- Adaptación comprobada para al menos 2 perfiles y 2 formatos distintos.
- Salida JSON estructurada + interfaz interactiva o API REST operativa.
- Integración funcional con OCI Object Storage (capa Always Free).
- 3 escenarios de demo con documentación real (Python 3.14 y LangChain).
- Documentación completa en GitHub con diagrama de arquitectura.

### Para el portfolio
- Demostrar dominio práctico de RAG + LLM + LangGraph + OCI.
- Código limpio, bien documentado, con arquitectura que evidencie criterio técnico.
- Un proyecto que se pueda mostrar en una entrevista y explicar cada decisión.

### Señales de que funciona
- El contenido generado para un principiante es genuinamente distinto al de un senior, dado el mismo documento fuente.
- El score de fidelidad refleja anclaje real en el documento, no alucinaciones.
- Un usuario sin contexto técnico puede usar la interfaz sin explicación.

## Alcance

### Primera versión (MVP)
- Pipeline RAG completo: ingestión → chunking → embeddings → FAISS → retrieval.
- Orquestación multi-agente con LangGraph: Agente Investigador RAG → Agente Redactor Pedagógico → Agente Crítico/Revisor.
- LLM a definir: Gemini, OpenAI, Claude u open-source.
- API REST con FastAPI como interfaz principal.
- Salida JSON estructurada con metadatos pedagógicos y score de fidelidad.
- Integración OCI Object Storage para persistencia.
- Soporte para documentos en texto plano y Markdown (PDF como extensión).

### Opcionales priorizados
- **Despliegue en OCI Compute** (instancia Always Free, 1 GB RAM, 1 OCPU).
- **Quizzes con evaluación en tiempo real**.
- **UI ligera y de bajo consumo** (a definir después del API-first).
- **Exportación multiformato** (Markdown, PDF formateado, CSV para Anki).

### Explícitamente fuera de alcance
- Soporte multilingüe (el sistema opera en español).
- Autenticación o multi-tenancy.
- Entrenamiento o fine-tuning de modelos propios.
- Escalado horizontal o infraestructura de producción.

## Visión

Si NuevaMente funciona bien, se convierte en dos cosas:

**Una herramienta personal de estudio.** Un sistema que su creador usa genuinamente para procesar la documentación que necesita aprender — no un proyecto de hackathon que se abandona al día siguiente de la entrega.

**Una pieza de portfolio que habla por sí sola.** Un proyecto que demuestra capacidad de diseñar y construir un sistema de IA completo de punta a punta: desde la ingestión de documentos hasta la generación de contenido pedagógico verificable, desplegado en infraestructura cloud real, con decisiones técnicas justificadas (FAISS sobre ChromaDB por restricciones de RAM, API-first por eficiencia de recursos, LangGraph para orquestación de agentes).

No pretende ser un producto comercial ni competir con plataformas EdTech establecidas. Pretende ser un proyecto honesto, bien construido, que resuelve un problema real: hacer accesible lo inaccesible.
