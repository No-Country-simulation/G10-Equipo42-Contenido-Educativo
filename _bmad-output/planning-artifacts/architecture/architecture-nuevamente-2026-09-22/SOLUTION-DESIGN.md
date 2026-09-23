# Documento de Diseño de Solución Técnica — NuevaMente
**Hackathon ONE G10 (Oracle Next Education & Alura)**  
**Proyecto:** NuevaMente – Sistema Inteligente de Adaptación y Generación de Contenido Educativo  
**Arquitecto:** Winston 🏗️ | **Fecha:** 2026-09-22 | **Estado:** Final

---

## 1. Resumen Ejecutivo y Propósito de la Solución

**NuevaMente** resuelve la brecha de accesibilidad del conocimiento técnico denso mediante un pipeline inteligente de **Retrieval-Augmented Generation (RAG)** orquestado con **LangGraph** y presentado mediante una interfaz interactiva en **Streamlit**. 

El sistema transforma manuales y especificaciones técnicas (PDF, Markdown, texto) en cuatro formatos didácticos adaptados a cuatro perfiles pedagógicos ortogonales, garantizando:
1. **Fidelidad Absoluta a la Fuente:** Verificación cuantitativa de anclaje semántico (`anclaje_fuente_score`) y ciclo automatizado de auto-reflexión (mitigación activa de alucinaciones).
2. **Cero Costo en Nube:** Persistencia de artefactos y fuentes exclusivamente en la capa **Always Free de Oracle Cloud Infrastructure (OCI Object Storage)**, complementado con un modo Mock Local determinístico para desarrollo y evaluación ágil.
3. **Contratos Estrictos:** Modelado exhaustivo mediante **Pydantic v2** que elimina fallos de tipado o parseo en el 100% de las respuestas.

---

## 2. Diagramas de Arquitectura (Modelo C4)

### 2.1 C4 Nivel 1: Diagrama de Contexto del Sistema

Muestra cómo interactúan los usuarios y los sistemas externos con **NuevaMente**.

```mermaid
C4Context
    title Diagrama de Contexto - Sistema NuevaMente

    Person(estudiante, "Usuario / Estudiante", "Estudiante de tecnología, desarrollador o líder técnico que busca material didáctico adaptado.")
    System(nuevamente, "Sistema NuevaMente", "Plataforma RAG interactiva que ingiere documentos técnicos y genera contenido educativo adaptado con validación de fidelidad.")

    System_Ext(voyage, "Voyage AI API", "Servicio de embeddings multilingües de alta precisión (voyage-multilingual-2, 1024d).")
    System_Ext(llm_prov, "Google Gemini Flash / LLM Gateway", "Modelo fundacional predeterminado vía contrato estándar OpenAI Chat Completions.")
    System_Ext(oci, "OCI Object Storage", "Almacenamiento de objetos en la nube de Oracle bajo la capa Always Free.")

    Rel(estudiante, nuevamente, "Carga documentos técnicos, configura perfil didáctico e interactúa con el material", "HTTPS / Streamlit")
    Rel(nuevamente, voyage, "Solicita embeddings de chunks (1024d)", "HTTPS / REST")
    Rel(nuevamente, llm_prov, "Solicita generación pedagógica y auditoría de fidelidad", "HTTPS / JSON")
    Rel(nuevamente, oci, "Persiste documentos originales y paquetes educativos JSON", "HTTPS / OCI SDK")
```

---

### 2.2 C4 Nivel 2: Diagrama de Contenedores y Módulos

Detalla la organización interna de los componentes del software y cómo fluyen los datos entre ellos.

```mermaid
graph TB
    subgraph UI_Container ["Contenedor de Presentación (Streamlit UI)"]
        App["app.py / Main Layout"]
        Components["ui/components.py<br/>(FileUploader, Selectors, StatusTracker)"]
        Views["ui/views/<br/>(FlashcardsView, QuizView, TutorialView, ExecSummaryView)"]
        SessionState[("st.session_state<br/>[active_package]")]
    end

    subgraph Pipeline_Container ["Contenedor de Orquestación (LangGraph Engine)"]
        StateGraphEngine["pipeline/graph.py<br/>StateGraph Orquestador"]
        Nodes["pipeline/nodes.py<br/>(ingest, retrieve, generate, evaluate, persist)"]
        Prompts["pipeline/prompts.py<br/>(System Prompts Pedagógicos & Auditoría)"]
    end

    subgraph Domain_Container ["Contenedor de Dominio (Invariantes de Datos)"]
        DomainModels["domain/models.py<br/>(EducationalContentPackage, Flashcard, QuizItem)"]
        GraphState["domain/state.py<br/>(PipelineGraphState TypedDict)"]
    end

    subgraph Services_Container ["Contenedor de Infraestructura (Puertos & Adaptadores)"]
        IngestService["services/ingestion.py<br/>(PyPDF Extractor & Semantic Chunker)"]
        EmbeddingService["services/embeddings.py<br/>(Voyage AI Client)"]
        VectorService["services/vector_store.py<br/>(ChromaDB Local VectorStore)"]
        LLMFactory["services/llm_factory.py<br/>(OpenAI-Compatible Gateway)"]
        StorageAdapter["services/storage.py<br/>(StoragePort: OCI & Mock Adapters)"]
    end

    subgraph Storage_Persist ["Almacenamiento Físico"]
        ChromaStorage[("Disco Local: ./data/chroma_db/")]
        MockStorage[("Disco Local: ./mock_oci_storage/")]
        OCICloud[("Oracle Cloud: OCI Object Storage")]
    end

    %% Relaciones
    App --> Components
    App --> Views
    Views --> SessionState
    Components -->|Invoca stream de eventos| StateGraphEngine

    StateGraphEngine --> Nodes
    Nodes --> Prompts
    Nodes --> GraphState
    Nodes --> DomainModels

    Nodes -->|Extracción| IngestService
    Nodes -->|Embeddings| EmbeddingService
    Nodes -->|Búsqueda K-NN| VectorService
    Nodes -->|Structured Output| LLMFactory
    Nodes -->|Persistencia| StorageAdapter

    VectorService --> ChromaStorage
    StorageAdapter -->|Modo Mock| MockStorage
    StorageAdapter -->|Modo Producción| OCICloud
```

---

## 3. Máquina de Estados del Pipeline (LangGraph StateGraph)

El corazón de la solución es un grafo cíclico de estados gobernado por **LangGraph**, que formaliza las 5 etapas del PRD y gestiona la arista condicional de reintento para mitigación de alucinaciones.

```mermaid
stateDiagram-v2
    [*] --> IngestNode: Carga de documento (PDF/MD/TXT)
    
    IngestNode --> RetrieveNode: Chunks normalizados generados
    
    RetrieveNode --> GenerateNode: K=5 fragmentos recuperados de ChromaDB
    
    GenerateNode --> EvaluateNode: Contenido generado con Gemini Flash
    
    state Decision <<choice>>
    EvaluateNode --> Decision: Cálculo de anclaje_fuente_score
    
    Decision --> GenerateNode: Score < 0.85 Y Retries < 2<br/>(Inyecta feedback de auto-reflexión)
    Decision --> PersistNode: Score >= 0.85 O Retries == 2<br/>(Aprobado o fallback con alerta)
    
    PersistNode --> RenderUI: Guardado en OCI / Mock Local
    
    RenderUI --> [*]: Despliegue interactivo en Streamlit
```

### Definición del Estado del Grafo (`PipelineGraphState`)
El estado muta a través de los nodos mediante un contrato tipado:
- `documento_bytes`: Bytes en memoria del archivo cargado.
- `nombre_archivo`: Nombre y formato original.
- `perfil_destinatario`: Selección pedagógica (Principiante, Junior, Arquitecto, Ejecutivo).
- `formato_salida`: Tipo de material (Flashcards, Quiz, Tutorial, Resumen).
- `nicho_aplicacion`: Contexto temático (Fintech, Salud, E-commerce, General).
- `nivel_detalle`: Didáctico, Técnico o Conciso.
- `chunks_recuperados`: Lista de strings con los fragmentos de mayor similitud semántica.
- `paquete_educativo`: Instancia validada de `EducationalContentPackage`.
- `evaluacion_fidelidad`: Objeto `EvaluacionCalidad` con score cuantitativo y observaciones.
- `retry_count`: Entero incremental (máximo 2) que previene bucles infinitos.
- `almacenamiento_info`: Metadatos de OCI (`bucket`, `objeto_id`, `status_upload`).

---

## 4. Diagrama de Secuencia de Extremo a Extremo

Ilustra la interacción cronológica entre el usuario, la interfaz de Streamlit, el orquestador de LangGraph y los servicios externos.

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Usuario / Evaluador
    participant UI as Streamlit UI (app.py)
    participant Graph as LangGraph StateGraph
    participant Chroma as ChromaDB / Voyage AI
    participant Gemini as Google Gemini Flash
    participant Storage as OCI / Mock Storage

    Usuario->>UI: Sube PDF y selecciona (Ej: Principiante / Flashcards)
    Usuario->>UI: Clic en "Generar Contenido Educativo"
    UI->>UI: st.status("Iniciando pipeline...")
    
    UI->>Graph: graph.stream(PipelineGraphState)
    
    Note over Graph: 1. Ingest Node
    Graph->>Graph: Extrae texto (PyPDF) y calcula SHA-256
    Graph-->>UI: Evento: "Documento extraído (X chunks)"
    
    Note over Graph: 2. Retrieve Node
    Graph->>Chroma: Consulta colección doc_{sha256[:12]}
    alt Colección ya existe en caché
        Chroma-->>Graph: Retorna chunks directamente (0 tokens consumidos)
    else Nueva colección
        Chroma->>Chroma: Genera embeddings con Voyage AI (1024d) e indexa
        Chroma-->>Graph: Retorna Top-5 chunks relevantes
    end
    Graph-->>UI: Evento: "Contexto técnico recuperado (K=5)"
    
    Note over Graph: 3. Generate Node
    Graph->>Gemini: Prompt didáctico + Chunks + Schema Pydantic
    Gemini-->>Graph: JSON estructurado validado
    Graph-->>UI: Evento: "Contenido didáctico generado"
    
    Note over Graph: 4. Evaluate Node (LLM-as-a-Judge)
    Graph->>Gemini: Prompt de fidelidad (Chunks vs Contenido generado a temp=0.0)
    Gemini-->>Graph: anclaje_fuente_score = 0.95 (Aprobado)
    Graph-->>UI: Evento: "Fidelidad validada: 95%"
    
    Note over Graph: 5. Persist Node
    Graph->>Storage: Guardar archivo origen + JSON generado
    Storage-->>Graph: objeto_id = "flashcards-principiante-1718901234.json"
    Graph-->>UI: Evento: "Persistido con éxito (status: completado / mock_local)"
    
    Graph-->>UI: Estado final completado
    UI->>UI: Guarda en st.session_state["active_package"]
    UI-->>Usuario: Renderiza baraja interactiva de Flashcards (flip 3D)
```

---

## 5. Modelo de Datos y Contratos Pydantic v2

El sistema enforcea tipado estricto en todos los niveles. No existen diccionarios libres en la capa de generación ni en las vistas.

```mermaid
classDiagram
    class EducationalContentPackage {
        +str status
        +MetadatosPedagogicos metadatos
        +ContenidoAdaptado contenido_adaptado
        +EvaluacionCalidad evaluacion_calidad
        +AlmacenamientoOCIInfo almacenamiento_oci
    }

    class MetadatosPedagogicos {
        +str perfil_aplicado
        +str formato_generado
        +int tiempo_estudio_minutos
        +List~str~ conceptos_clave
        +str nicho
    }

    class ContenidoAdaptado {
        +str titulo
        +str introduccion
        +List~FlashcardItem~ flashcards
        +List~QuizItem~ quizzes
        +List~TutorialStep~ tutorial_pasos
        +List~ExecutiveItem~ puntos_ejecutivos
    }

    class FlashcardItem {
        +str frente
        +str dorso
        +str pista_didactica
    }

    class QuizItem {
        +str pregunta
        +List~str~ opciones
        +int respuesta_correcta_index
        +str justificacion
    }

    class EvaluacionCalidad {
        +float anclaje_fuente_score
        +str claridad_pedagogica
        +List~str~ observaciones
    }

    class AlmacenamientoOCIInfo {
        +str bucket_name
        +str objeto_id
        +str status_upload
        +str timestamp_utc
    }

    EducationalContentPackage *-- MetadatosPedagogicos
    EducationalContentPackage *-- ContenidoAdaptado
    EducationalContentPackage *-- EvaluacionCalidad
    EducationalContentPackage *-- AlmacenamientoOCIInfo
    ContenidoAdaptado *-- FlashcardItem
    ContenidoAdaptado *-- QuizItem
```

---

## 6. Estrategia de Entornos y Resiliencia

### 6.1 Modo Híbrido OCI / Mock Local
- **Producción / Demo Oficial:** Configurando `OCI_CONFIG_FILE` o variables de tenancy, el adaptador `OCIObjectStorageAdapter` persiste en Oracle Cloud Always Free emitiendo `status_upload="completado"`.
- **Desarrollo / Offline:** Si `OCI_MOCK=true`, el adaptador `MockLocalStorageAdapter` persiste en `./mock_oci_storage/{bucket}/{objeto_id}` emitiendo `status_upload="mock_local"`. Esto permite a cualquier evaluador clonar el repositorio y ejecutar la aplicación al 100% de sus capacidades sin requerir cuenta en Oracle Cloud.

### 6.2 Manejo de Cuotas y Rate Limits
- **Voyage AI & Gemini Flash:** Implementación de retries automáticos con retroceso exponencial (`tenacity`) ante respuestas `HTTP 429` (Too Many Requests).
- **Caché Vectorial:** Al asociar cada colección a `doc_{sha256[:12]}`, si un evaluador prueba repetidamente un mismo archivo PDF durante la presentación, el sistema no realiza ninguna llamada a Voyage AI, reduciendo la latencia a menos de 500 ms y protegiendo la cuota de la API.

---

## 7. Mapeo a Criterios de Evaluación del Hackathon

| Criterio del Jurado | Solución Arquitectónica Implementada | Evidencia Observable en la Demo |
|---|---|---|
| **Arquitectura RAG & Fidelidad Técnica** | Voyage AI (1024d) + ChromaDB + Evaluador de Fidelidad con auto-reflexión en LangGraph. | Métrica visible en UI (`anclaje_fuente_score` ≥ 0.85) e historial de auto-corrección. |
| **Uso Efectivo de Oracle Cloud (OCI)** | Persistencia en OCI Object Storage Always Free sin costo con trazabilidad de `objeto_id`. | Panel lateral con confirmación de persistencia y enlace al bucket de contenidos. |
| **Integridad de Contratos JSON** | Generación estructurada con Pydantic v2 vía `with_structured_output`. | Descarga de JSON válido 100% conforme a las directivas del concurso. |
| **Experiencia de Usuario (UI/UX)** | Streamlit con `st.status()` reactivo y vistas especializadas (Flashcards con flip, quizzes con feedback). | Visualización interactiva rica según el formato pedagógico seleccionado. |
