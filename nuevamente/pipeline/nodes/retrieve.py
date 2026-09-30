"""Nodo LangGraph para el retrieval contextualizado de chunks.

Thin wrapper que extrae los datos necesarios del NuevaMenteState,
delega al servicio de retrieval y retorna el dict parcial con
retrieved_chunks para que LangGraph lo fusione con el state actual.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.pipeline.state import NuevaMenteState
from nuevamente.services.retrieval import retrieve_chunks

logger = logging.getLogger(__name__)


def retrieve_node(state: NuevaMenteState) -> dict[str, Any]:
    """Nodo de retrieval: recupera chunks relevantes del indice FAISS.

    Lee document_id, chunks, section_map, perfil, formato y nicho del state,
    delega a retrieve_chunks y retorna un dict parcial con retrieved_chunks
    para el merge de LangGraph.

    Args:
        state: Estado actual del grafo NuevaMente.

    Returns:
        Dict parcial con "retrieved_chunks" para fusionar en el state.

    Raises:
        PipelineError: Si el indice FAISS no existe en disco (full-coverage path).
    """
    document_id: str = state["document_id"]
    chunks: list[dict[str, Any]] = state["chunks"]
    section_map: list[dict[str, Any]] = state.get("section_map", [])
    perfil: str = state["perfil"]
    formato: str = state["formato"]
    nicho: str = state["nicho"]

    logger.info("Ejecutando nodo retrieve para document_id=%s", document_id)

    settings = Settings()
    retrieved = retrieve_chunks(
        document_id=document_id,
        chunks=chunks,
        section_map=section_map,
        perfil=perfil,
        formato=formato,
        nicho=nicho,
        settings=settings,
    )

    logger.info(
        "Nodo retrieve completado: %d chunks recuperados para document_id=%s",
        len(retrieved),
        document_id,
    )

    return {"retrieved_chunks": retrieved}
