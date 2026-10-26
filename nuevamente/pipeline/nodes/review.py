"""Nodo LangGraph: review (Agente Critico/Revisor de Fidelidad).

Thin wrapper que lee los campos necesarios de NuevaMenteState,
llama al servicio de evaluacion y retorna el dict parcial con
review_result para fusionar en el state.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.pipeline.state import NuevaMenteState
from nuevamente.services.evaluation import evaluate_fidelity

logger = logging.getLogger(__name__)


def review_node(state: NuevaMenteState) -> dict[str, Any]:
    """Nodo del grafo LangGraph para la evaluacion de fidelidad del contenido generado.

    Lee generated_content y retrieved_chunks del state, delega la logica al
    servicio de evaluacion y retorna el dict parcial con review_result para
    fusionarlo en NuevaMenteState.

    El conditional edge y el control de retry (max 1 reintento) se implementan
    en Story 1.6; este nodo solo produce la evaluacion de fidelidad.

    Args:
        state: Estado actual del grafo LangGraph.

    Returns:
        Dict parcial con la clave 'review_result' (dict serializable
        equivalente a EvaluacionCalidad.model_dump()).
    """
    document_id = state.get("document_id", "desconocido")
    generated_content = state.get("generated_content", {})
    retrieved_chunks = state.get("retrieved_chunks", [])

    logger.info(
        "review_node: document_id=%s chunks_fuente=%d",
        document_id,
        len(retrieved_chunks),
    )

    settings = Settings()
    review_result = evaluate_fidelity(
        generated_content=generated_content,
        retrieved_chunks=retrieved_chunks,
        settings=settings,
    )

    score = review_result.get("anclaje_fuente_score", 0.0)
    logger.info(
        "review_node completado: document_id=%s anclaje_fuente_score=%.2f",
        document_id,
        score,
    )

    return {"review_result": review_result}
