"""Grafo LangGraph del pipeline de NuevaMente.

Define y compila el StateGraph completo que orquesta todos los nodos
del pipeline de transformacion de documentos en paquetes educativos:
ingest -> retrieve -> draft -> review -> [retry o format_output] -> END.

El conditional edge aplica la logica de retry: si el Agente Critico asigna
un score de fidelidad < 0.7 y aun no se ha agotado el maximo de reintentos
(max 1), el pipeline vuelve al Agente Redactor. En caso contrario, el
paquete se ensambla y se entrega.
"""

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from nuevamente.pipeline.nodes.draft import draft_node
from nuevamente.pipeline.nodes.format_output import format_output_node
from nuevamente.pipeline.nodes.ingest import ingest_node
from nuevamente.pipeline.nodes.retrieve import retrieve_node
from nuevamente.pipeline.nodes.review import review_node
from nuevamente.pipeline.state import NuevaMenteState

logger = logging.getLogger(__name__)

# Umbral de fidelidad aceptable (consistent con Agente Critico y epic-1-context.md)
_UMBRAL_FIDELIDAD: float = 0.7
# Maximo de reintentos permitidos (1 = un solo reintento tras el primer fallo)
_MAX_RETRY: int = 1


def _should_retry(state: NuevaMenteState) -> Literal["draft", "format_output"]:
    """Router del conditional edge post-review.

    Decide si el pipeline debe volver al Agente Redactor para un reintento
    (cuando el score de fidelidad es bajo y aun queda capacidad de retry)
    o avanzar al ensamblado final del paquete educativo.

    Args:
        state: Estado actual del grafo, que incluye review_result y retry_count.

    Returns:
        "draft" si se debe reintentar la generacion, "format_output" en caso
        contrario (score aceptable o limite de reintentos alcanzado).
    """
    review_result = state.get("review_result") or {}
    score = review_result.get("anclaje_fuente_score", 1.0)
    retry_count = state.get("retry_count", 0)

    if score < _UMBRAL_FIDELIDAD and retry_count < _MAX_RETRY:
        logger.info(
            "_should_retry: score=%.2f retry_count=%d -> reintento (draft)",
            score,
            retry_count,
        )
        return "draft"

    logger.info(
        "_should_retry: score=%.2f retry_count=%d -> format_output",
        score,
        retry_count,
    )
    return "format_output"


def build_graph():
    """Construye y compila el grafo LangGraph del pipeline de NuevaMente.

    El grafo es stateless (sin checkpointer) y lineal con un conditional edge
    de retry en el nodo review. Cada invocacion es independiente.

    Topologia:
        START -> ingest -> retrieve -> draft -> review -> [router] -> format_output -> END
                                          ^----- retry (si score < 0.7 y retry < 1) --/

    Returns:
        CompiledStateGraph listo para invocar con .invoke(initial_state).
    """
    builder = StateGraph(NuevaMenteState)

    # Registrar nodos
    builder.add_node("ingest", ingest_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("draft", draft_node)
    builder.add_node("review", review_node)
    builder.add_node("format_output", format_output_node)

    # Edges secuenciales
    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "retrieve")
    builder.add_edge("retrieve", "draft")
    builder.add_edge("draft", "review")

    # Conditional edge con logica de retry
    builder.add_conditional_edges(
        "review",
        _should_retry,
        {"draft": "draft", "format_output": "format_output"},
    )

    # Edge final
    builder.add_edge("format_output", END)

    compiled = builder.compile()

    logger.info(
        "build_graph: grafo compilado exitosamente nodos=%s",
        list(builder.nodes),
    )

    return compiled
