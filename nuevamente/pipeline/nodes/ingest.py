"""Nodo LangGraph para la ingestion de documentos.

Thin wrapper que extrae los datos necesarios del NuevaMenteState,
delega al servicio de RAG y retorna el dict parcial con chunks y section_map
para que LangGraph lo fusione con el state actual.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.pipeline.state import NuevaMenteState
from nuevamente.services.rag import ingest_document

logger = logging.getLogger(__name__)


def ingest_node(state: NuevaMenteState) -> dict[str, Any]:
    """Nodo de ingestion: extrae texto, genera chunks e indexa en FAISS.

    Lee document_id, raw_text y file_name del state, delega a ingest_document
    y retorna un dict parcial con chunks y section_map para el merge de LangGraph.

    Args:
        state: Estado actual del grafo NuevaMente.

    Returns:
        Dict parcial con "chunks" y "section_map" para fusionar en el state.
    """
    document_id: str = state["document_id"]
    raw_text: str = state["raw_text"]
    file_name: str = state["file_name"]

    logger.info("Ejecutando nodo ingest para document_id=%s", document_id)

    settings = Settings()
    result = ingest_document(
        document_id=document_id,
        raw_text=raw_text,
        file_name=file_name,
        settings=settings,
    )

    logger.info(
        "Nodo ingest completado: %d chunks generados para document_id=%s",
        len(result["chunks"]),
        document_id,
    )

    return {
        "chunks": result["chunks"],
        "section_map": result["section_map"],
    }
