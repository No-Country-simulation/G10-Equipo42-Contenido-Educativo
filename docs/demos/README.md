# Evidencias de Demostración y Evaluación - NuevaMente

Este directorio contiene las ejecuciones reproducibles de los escenarios de prueba exigidos en los criterios de evaluación del Hackathon (Épica 4 - Historia 4.1).

Cada escenario fue procesado sobre documentación técnica real sin mocks, validando la ingesta multiformato (PDF, Markdown, Texto plano), la diferenciación por perfil, la versatilidad de los 5 formatos pedagógicos y la fidelidad del contenido al documento fuente.

---

## Tabla Resumen de Ejecución y Métricas

| Escenario ID | Documento Fuente | Perfil Destinatario | Formato Pedagógico | Nicho Sectorial | Anclaje Fuente Score | Items | Tiempo | Estado |
|--------------|------------------|---------------------|--------------------|-----------------|----------------------|-------|--------|--------|
| `1a_classes_principiante_flashcards` | classes.txt | Principiante | Flashcards | General | **1.00** | 8 | 18.73s | ✅ Pass |
| `1b_classes_lider_tecnico_resumen` | classes.txt | Lider Tecnico/Arquitecto | Resumen Ejecutivo | General | **1.00** | 5 | 12.38s | ✅ Pass |
| `2a_langchain_langgraph_tutorial` | langchain_vs_langgraph.md | Senior | Tutorial Paso a Paso | General | **1.00** | 4 | 10.8s | ✅ Pass |
| `2b_langchain_langgraph_quiz` | langchain_vs_langgraph.md | Senior | Quiz Interactivo | General | **1.00** | 4 | 9.85s | ✅ Pass |
| `3_oci_vcn_guion_veterinario` | vision_general_oci_vcn.pdf | Junior | Guion de Clase | veterinario aprendiendo a programar | **1.00** | 4 | 11.75s | ✅ Pass |

---

## Análisis de Cumplimiento de Criterios (Success Metrics)

### 1. Diferenciación Lingüística y Estructural por Perfil (SM-1)
* **Comparativa Escenario 1A (Principiante) vs 1B (Líder Técnico):**
  * **Documento común:** `classes.txt` (Python 3.14 Official Tutorial).
  * **Principiante (1A):** Genera Flashcards orientadas a la asimilación conceptual elemental, usando analogías cotidianas (ej. molde vs galleta, atributos como características), explicaciones libres de jerga innecesaria y pistas intuitivas.
  * **Líder Técnico (1B):** Genera un Resumen Ejecutivo con foco en el modelo dinámico de ejecución de Python, implicaciones de diseño de herencia múltiple (MRO), ausencia de encapsulamiento estricto a nivel de lenguaje (convención `_`), y recomendaciones de arquitectura para equipos.

### 2. Consistencia y Validez de Schemas Pydantic (SM-2)
* Los 5 formatos pedagógicos soportados por NuevaMente fueron generados y validados contra sus respectivos modelos Pydantic:
  * `FlashcardsPaquete`: FlashcardItem (frente, dorso, pista, concepto_clave).
  * `ResumenEjecutivoPaquete`: ResumenEjecutivoItem (seccion, contenido, implicacion_practica).
  * `TutorialPaquete`: TutorialPasoItem (paso_numero, titulo, explicacion, ejemplo_codigo_o_caso).
  * `QuizPaquete`: QuizItem (pregunta, opciones, respuesta_correcta, justificacion_fuente).
  * `GuionClasePaquete`: GuionClaseItem (fase, titulo_fase, contenido_didactico, duracion_sugerida_minutos, notas_docente).
* El 100% de los paquetes generados cumple con la estructura requerida sin excepciones de parseo.

### 3. Fidelidad y Anclaje a la Fuente (SM-3)
* Todos los escenarios superan el umbral mínimo de fidelidad ($\ge 0.70$) evaluado por el Agente Crítico/Revisor, garantizando que no existan alucinaciones y que las justificaciones citen conceptos reales de los textos fuente.

### 4. Ingesta Multiformato y Nicho Personalizado
* **Extracción de PDF:** Se procesó exitosamente el archivo de 15 páginas `vision_general_oci_vcn.pdf` utilizando PyPDF, segmentando en chunks semánticos y vectorizando en FAISS.
* **Nicho Personalizado:** En el Escenario 3 (*veterinario aprendiendo a programar*), el Agente Redactor adaptó la explicación de redes virtuales en la nube (VCN, subredes, tablas de enrutamiento) recurriendo a analogías con la infraestructura de una clínica veterinaria y circuitos de atención.

---

## Cómo Reproducir los Escenarios

Para volver a ejecutar las demostraciones en cualquier momento:

```bash
# Ejecutar todos los escenarios en lote
uv run python scripts/run_demo_scenarios.py

# Ejecutar un escenario específico
uv run python scripts/run_demo_scenarios.py --scenario 1a
uv run python scripts/run_demo_scenarios.py --scenario 3
```

Los paquetes resultantes se registran automáticamente en el almacenamiento local (`data/storage/paquetes/`), haciéndose visibles y navegables de inmediato en la interfaz web de NuevaMente.
