"""Nodo LangGraph: draft (Agente Redactor Pedagogico).

Thin wrapper que lee los campos necesarios de NuevaMenteState,
llama al servicio de generacion y retorna el dict parcial con
generated_content para fusionar en el state.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.pipeline.state import NuevaMenteState
from nuevamente.services.generation import generate_content

logger = logging.getLogger(__name__)


def draft_node(state: NuevaMenteState) -> dict[str, Any]:
    """Nodo del grafo LangGraph para la generacion de contenido educativo.

    Lee retrieved_chunks, perfil, formato, nicho y review_result del state,
    delega la logica al servicio de generacion y retorna el dict parcial
    con generated_content para fusionarlo en NuevaMenteState.

    Args:
        state: Estado actual del grafo LangGraph.

    Returns:
        Dict parcial con la clave 'generated_content' (dict serializable).
    """
    document_id = state.get("document_id", "desconocido")
    retrieved_chunks = state.get("retrieved_chunks", [])
    perfil = state.get("perfil", "")
    formato = state.get("formato", "")
    nicho = state.get("nicho", "")
    review_result = state.get("review_result")
    retry_count = state.get("retry_count", 0)

    logger.info(
        "draft_node: document_id=%s perfil=%s formato=%s nicho=%s "
        "chunks=%d retry_count=%d",
        document_id,
        perfil,
        formato,
        nicho,
        len(retrieved_chunks),
        retry_count,
    )

    settings = Settings()
    generated_content = generate_content(
        retrieved_chunks=retrieved_chunks,
        perfil=perfil,
        formato=formato,
        nicho=nicho,
        review_result=review_result,
        settings=settings,
    )

    logger.info(
        "draft_node completado: document_id=%s formato=%s",
        document_id,
        formato,
    )

    return {"generated_content": generated_content, "retry_count": retry_count + 1}
