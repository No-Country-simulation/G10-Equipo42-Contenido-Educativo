"""Servicio de retrieval contextualizado para el pipeline RAG de NuevaMente.

Implementa la estrategia dual de recuperacion de chunks:
- Fast-path: documentos pequenos (<= fast_path_token_threshold tokens estimados),
  todos los chunks pasan directamente sin llamar al LLM ni a FAISS.
- Full-coverage: documentos grandes, con query synthesis via LLM, similarity
  search en FAISS, deduplicacion, piso de cobertura por seccion y chunk budget.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage

from nuevamente.config import Settings
from nuevamente.core.exceptions import PipelineError
from nuevamente.infra.embeddings import get_embeddings
from nuevamente.infra.llm import get_llm
from nuevamente.infra.vectorstore import load_index

logger = logging.getLogger(__name__)


def retrieve_chunks(
    document_id: str,
    chunks: list[dict[str, Any]],
    section_map: list[dict[str, Any]],
    perfil: str,
    formato: str,
    nicho: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    """Recupera los chunks mas relevantes del indice FAISS para el contexto dado.

    Elige automaticamente entre fast-path (todos los chunks) y full-coverage
    (query synthesis + FAISS + piso de cobertura + chunk budget) basandose
    en el tamano estimado del documento en tokens.

    Args:
        document_id: Identificador unico del documento (clave del indice FAISS).
        chunks: Lista de dicts con page_content y metadata (chunk_index, etc.).
        section_map: Mapa de secciones del documento (heading, level, start_offset).
        perfil: Perfil del destinatario (ej: "Principiante", "Experto").
        formato: Formato pedagogico deseado (ej: "Flashcards", "Tutorial").
        nicho: Nicho o sector del destinatario (texto libre).
        settings: Instancia de Settings con parametros de retrieval.

    Returns:
        Lista de dicts de chunks recuperados, ordenados por chunk_index.

    Raises:
        PipelineError: Si el indice FAISS no existe en disco y se necesita full-coverage.
    """
    total_chars = sum(len(c.get("page_content", "")) for c in chunks)
    estimated_tokens = total_chars / 4

    logger.info(
        "Iniciando retrieval: document_id=%s estimated_tokens=%.0f threshold=%d",
        document_id,
        estimated_tokens,
        settings.fast_path_token_threshold,
    )

    if estimated_tokens <= settings.fast_path_token_threshold:
        logger.info(
            "Fast-path activado: %d chunks pasan directamente (document_id=%s)",
            len(chunks),
            document_id,
        )
        return _fast_path(chunks)

    logger.info(
        "Full-coverage activado: query synthesis + FAISS (document_id=%s)",
        document_id,
    )
    return _full_coverage(
        document_id, chunks, section_map, perfil, formato, nicho, settings
    )


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _fast_path(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retorna todos los chunks ordenados por chunk_index (sin LLM ni FAISS)."""
    return sorted(chunks, key=lambda c: c.get("chunk_index", 0))


def _full_coverage(
    document_id: str,
    chunks: list[dict[str, Any]],
    section_map: list[dict[str, Any]],
    perfil: str,
    formato: str,
    nicho: str,
    settings: Settings,
) -> list[dict[str, Any]]:
    """Estrategia full-coverage: query synthesis, FAISS search, piso y budget.

    Args:
        document_id: Identificador del documento.
        chunks: Todos los chunks del documento (fuente de verdad para el piso).
        section_map: Mapa de secciones del documento.
        perfil: Perfil del destinatario.
        formato: Formato pedagogico.
        nicho: Nicho del destinatario.
        settings: Parametros de retrieval y LLM.

    Returns:
        Lista de chunks recuperados, deduplicados, con piso de cobertura y budget.

    Raises:
        PipelineError: Si el indice FAISS no existe para document_id.
    """
    # 1. Cargar indice FAISS
    embeddings = get_embeddings(settings)
    faiss_vs = load_index(document_id, embeddings, settings)
    if faiss_vs is None:
        raise PipelineError(
            f"Indice FAISS no encontrado para document_id='{document_id}'. "
            "Ejecute la ingestion del documento antes del retrieval."
        )

    # 2. Query synthesis via LLM
    queries = _synthesize_queries(section_map, perfil, formato, nicho, settings)
    logger.info(
        "Query synthesis: %d queries generadas para document_id=%s",
        len(queries),
        document_id,
    )

    # 3. Similarity search en FAISS por cada query + deduplicacion
    retrieved_by_index: dict[int, dict[str, Any]] = {}
    for query in queries:
        results = faiss_vs.similarity_search(query, k=settings.retrieval_k)
        for doc in results:
            idx = doc.metadata.get("chunk_index")
            if idx is None:
                # Documento sin chunk_index en metadata — ignorar (no deberia ocurrir
                # con indices generados por ingest_node, pero protege contra indices
                # construidos externamente)
                continue
            if idx not in retrieved_by_index:
                chunk_dict = {"page_content": doc.page_content, **doc.metadata}
                retrieved_by_index[idx] = chunk_dict

    logger.info(
        "FAISS search completado: %d chunks unicos recuperados (document_id=%s)",
        len(retrieved_by_index),
        document_id,
    )

    # 4. Piso de cobertura: secciones sin representacion
    if section_map:
        retrieved = _apply_coverage_floor(
            retrieved_by_index, chunks, section_map
        )
    else:
        retrieved = retrieved_by_index

    # 5. Aplicar chunk budget y ordenar por chunk_index
    chunk_budget = settings.retrieval_k * 2
    result = sorted(retrieved.values(), key=lambda c: c.get("chunk_index", 0))
    result = result[:chunk_budget]

    logger.info(
        "Retrieval completado: %d chunks en retrieved_chunks (budget=%d, document_id=%s)",
        len(result),
        chunk_budget,
        document_id,
    )
    return result


def _synthesize_queries(
    section_map: list[dict[str, Any]],
    perfil: str,
    formato: str,
    nicho: str,
    settings: Settings,
) -> list[str]:
    """Genera queries de busqueda semantica via LLM (1 llamada).

    Construye un prompt con el section_map compacto y los parametros de
    personalizacion. El LLM retorna una query por linea.

    Args:
        section_map: Mapa de secciones para contexto del documento.
        perfil: Perfil del destinatario.
        formato: Formato pedagogico.
        nicho: Nicho del destinatario.
        settings: Parametros del LLM.

    Returns:
        Lista de strings con las queries sinteticas (al menos 1).
    """
    n_queries = min(max(3, len(section_map)), 8) if section_map else 5

    if section_map:
        section_compacto = "\n".join(
            f"{'#' * s.get('level', 1)} {s.get('heading', '')}"
            for s in section_map
        )
    else:
        section_compacto = "(Sin secciones identificadas — documento sin encabezados)"

    prompt = (
        f"Eres un asistente de recuperacion de informacion.\n"
        f"Mapa de secciones del documento:\n{section_compacto}\n\n"
        f"Genera {n_queries} queries de busqueda semantica para recuperar "
        f"contenido relevante, distribuidas por todo el documento, adaptadas "
        f"para un destinatario \"{perfil}\" que quiere aprender en formato "
        f"\"{formato}\" sobre el nicho \"{nicho}\".\n"
        f"Retorna una query por linea, sin numeracion ni prefijos."
    )

    llm = get_llm(settings)
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content if hasattr(response, "content") else str(response)

    queries = [q.strip() for q in raw.splitlines() if q.strip()]
    if not queries:
        # Fallback de seguridad: query generica
        queries = [f"contenido sobre {nicho} para {perfil} en formato {formato}"]

    return queries


def _apply_coverage_floor(
    retrieved_by_index: dict[int, dict[str, Any]],
    chunks: list[dict[str, Any]],
    section_map: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Aplica el piso de cobertura: agrega un chunk representativo por seccion sin cobertura.

    Para cada seccion del section_map que no tenga ningun chunk recuperado,
    busca en todos los chunks el que tenga el menor chunk_index con
    parent_heading igual al heading de la seccion y lo agrega al resultado.

    Args:
        retrieved_by_index: Chunks recuperados por FAISS, indexados por chunk_index.
        chunks: Todos los chunks del documento.
        section_map: Mapa de secciones del documento.

    Returns:
        Dict actualizado con chunks adicionales del piso de cobertura.
    """
    result = dict(retrieved_by_index)

    # Headings cubiertos en la recuperacion actual
    covered_headings = {
        c.get("parent_heading", "") for c in result.values()
    }

    for section in section_map:
        heading = section.get("heading", "")
        if not heading or heading in covered_headings:
            continue

        # Buscar el chunk con menor chunk_index cuyo parent_heading coincide
        candidates = [
            c for c in chunks if c.get("parent_heading", "") == heading
        ]
        if not candidates:
            continue

        best = min(candidates, key=lambda c: c.get("chunk_index", 0))
        idx = best.get("chunk_index", -1)
        if idx not in result:
            result[idx] = best
            covered_headings.add(heading)
            logger.debug(
                "Piso de cobertura: chunk_index=%d agregado para seccion '%s'",
                idx,
                heading,
            )

    return result
