# Addendum Técnico: NuevaMente – Especificaciones de Soporte

Este documento acompaña al PRD principal y preserva detalles de implementación técnica, esquemas y directrices de arquitectura derivados de la especificación del Hackathon ONE.

## 1. Esquema JSON de Entrada y Salida Oficial

### 1.1 Solicitud (Entrada de la API / UI)
```json
{
  "documento_titulo": "Introduccion a la Arquitectura de Redes VCN en OCI",
  "documento_contenido": "La Virtual Cloud Network (VCN) es una red privada y personalizable configurada en Oracle Cloud Infrastructure...",
  "perfil_destinatario": "Principiante",
  "formato_salida": "Flashcards",
  "nicho_sector": "General",
  "nivel_detalle": "Didactico"
}
```

### 1.2 Respuesta Oficial Requerida (Contrato Estricto)
```json
{
  "status": "exito",
  "metadatos": {
    "perfil_aplicado": "Principiante",
    "formato_generado": "Flashcards",
    "tiempo_estimado_estudio_minutos": 5,
    "conceptos_clave": ["VCN", "Subredes", "Internet Gateway", "Security Lists"]
  },
  "contenido_adaptado": {
    "titulo": "Dominando Redes en la Nube (VCN) desde Cero",
    "introduccion_contextualizada": "Imagina la VCN como tu propio barrio privado y seguro dentro de la nube de Oracle, donde tu decides quien entra y quien sale.",
    "items": [
      {
        "frente": "Que es una VCN en Oracle Cloud?",
        "dorso": "Es tu red virtual privada y personalizada dentro de la nube de Oracle, funcionando como la infraestructura de red de tu empresa.",
        "pista_didactica": "Piensa en ella como el terreno cercado donde residen tus servidores."
      }
    ]
  },
  "evaluacion_calidad": {
    "anclaje_fuente_score": 0.98,
    "claridad_pedagogica": "Alta",
    "observaciones": "Lenguaje ajustado con analogias para publico principiante, sin tecnicismos excesivos."
  },
  "almacenamiento_oci": {
    "bucket": "nuevamente-contenidos-educativos",
    "objeto_id": "contenido-vcn-principiante-flashcards-001.json",
    "status_upload": "completado"
  }
}
```

## 2. Puntos Clave de Integración con OCI Object Storage
- SDK: `oci` para Python (`pip install oci`).
- Configuración de autenticación mediante archivo `.oci/config` o variables de entorno (User OCID, Tenancy OCID, Fingerprint, Private Key PEM).
- Servicios Always Free: 10 GB de Object Storage gratuito y 50,000 llamadas a la API de almacenamiento por mes.
- Almacenamiento dividido en dos namespaces/carpetas lógicas o buckets:
  1. `nuevamente-documentos-origen`: Documentos originales (PDF/MD/TXT subidos).
  2. `nuevamente-contenidos-educativos`: Paquetes JSON estructurados generados por el pipeline.

## 3. Estrategia de RAG y Modelos de Lenguaje
- **Extracción de PDF:** `pypdf` o `pdfplumber`.
- **Chunking:** `RecursiveCharacterTextSplitter` con solapamiento (`chunk_size=800`, `chunk_overlap=150`).
- **Embeddings:** Modelos multilingües eficientes (e.g. `text-embedding-004` de Google Gemini o modelos ligeros HuggingFace/SentenceTransformers tipo `all-MiniLM-L6-v2` si se prefiere 100% local sin costo de tokens).
- **Vector Store:** ChromaDB en modo persistente en carpeta local (`_bmad-output/vector_store` o similar).
- **Evaluación de Fidelidad:** Cadena de verificación cruzada que extrae proposiciones clave y mide coincidencia semántica con los chunks recuperados.
