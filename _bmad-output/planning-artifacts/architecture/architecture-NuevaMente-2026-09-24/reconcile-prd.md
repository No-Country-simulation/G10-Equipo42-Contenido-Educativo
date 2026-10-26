# Reconciliación: PRD NuevaMente (prd.md + addendum.md)

**Input:** `_bmad-output/planning-artifacts/prds/prd-NuevaMente-2026-09-24/prd.md`

## Veredicto: ✅ Cubierto — todos los requisitos trazados en la arquitectura

## Detalle por Feature

| PRD Feature / Requisito | Trazado en Spine | AD / Componente |
|---|---|---|
| FR-1, FR-2 (ingestión, extracción) | ✅ | AD-1, AD-5 → `services/ingestion.py` |
| FR-3 (chunking semántico) | ✅ | AD-3 → section map + chunks con metadata |
| FR-4 (embeddings + FAISS) | ✅ | AD-8 → un índice por documento en disco |
| FR-5 (parámetros personalización) | ✅ | AD-6 → `core/models.py` enums |
| FR-6 (solicitud atómica) | ✅ | AD-7 → POST 202 + polling (evolución del "síncrono" del PRD) |
| FR-7 (Agente Investigador RAG) | ✅ | AD-2, AD-3 → nodo `retrieve`, `services/rag.py` |
| FR-8 (Agente Redactor) | ✅ | AD-2, AD-6 → nodo `draft`, `with_structured_output()` |
| FR-9 (Agente Crítico) | ✅ | AD-2 → nodo `review`, loop condicional |
| FR-10, FR-11 (schema JSON) | ✅ | AD-6 → modelos Pydantic por formato |
| FR-12, FR-13 (OCI Storage) | ✅ | AD-9 → fire-and-forget post-entrega |
| FR-14, FR-15 (API REST) | ✅ | AD-7, AD-12 → endpoints definidos |
| FR-16 a FR-20 (Interfaz Web) | ✅ | AD-11 → `app/static/`, FastAPI sirve static |
| NFR-1 (hardware) | ✅ | AD-11 → 1GB + swap 4-8GB |
| NFR-2 (rendimiento) | ✅ | AD-3 → fast-path + stratified |
| NFR-3 (costo) | ✅ | AD-11 → todo Always Free |
| NFR-4 (observabilidad) | ✅ | AD-12 → logging con task_id |
| NFR-5 (mantenibilidad) | ✅ | AD-1, AD-5 → módulos separados |

## Evoluciones respecto al PRD

1. **FR-6 "solicitud síncrona" → API async con polling (AD-7).** El PRD asumía síncrono. La arquitectura evoluciona a async con task_id + polling para habilitar progreso real en la UI sin bloquear Uvicorn. Compatible con la intención del PRD (el usuario manda un request y recibe el resultado), superior en experiencia.

2. **"Gemini Flash" genérico → Gemini 3.5 Flash Lite confirmado.** El PRD decía "Gemini Flash" sin especificar versión. La arquitectura fija Gemini 3.5 Flash Lite por su free tier generoso (15 RPM, 250K TPM, 500 RPD).

3. **Open Question 1 (estrategia query RAG) → resuelta (AD-3).** Fast-path + stratified full-coverage retrieval con piso de cobertura por sección.

4. **ASSUMPTION chunking recursivo → enriquecido con section map.** El PRD asumía "chunking recursivo por caracteres con overlap". La arquitectura lo extiende: además del chunking, se construye un mapa de secciones para guiar el retrieval y garantizar cobertura.

## Gaps encontrados

Ninguno bloqueante. Todas las decisiones marcadas como `[ASSUMPTION]` o `Open Question` en el PRD están resueltas o explícitamente diferidas.
