"""Nodo LangGraph: format_output (ensamblado del paquete educativo final).

Thin wrapper que lee los campos necesarios de NuevaMenteState,
llama al servicio de ensamblado y retorna el dict parcial con
educational_package para fusionar en el state.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.pipeline.state import NuevaMenteState
from nuevamente.services.assembly import assemble_package

logger = logging.getLogger(__name__)


def format_output_node(state: NuevaMenteState) -> dict[str, Any]:
    """Nodo del grafo LangGraph para el ensamblado del paquete educativo final.

    Lee generated_content, review_result y formato del state, delega la
    logica al servicio de ensamblado y retorna el dict parcial con
    educational_package para fusionarlo en NuevaMenteState.

    Args:
        state: Estado actual del grafo LangGraph.

    Returns:
        Dict parcial con la clave 'educational_package' (dict serializable
        que representa el paquete educativo completo validado por Pydantic).
    """
    document_id = state.get("document_id", "desconocido")
    generated_content = state.get("generated_content", {})
    review_result = state.get("review_result", {})
    formato = state.get("formato", "")

    logger.info(
        "format_output_node: document_id=%s formato=%s",
        document_id,
        formato,
    )

    settings = Settings()
    educational_package = assemble_package(
        generated_content=generated_content,
        review_result=review_result,
        formato=formato,
        settings=settings,
    )

    logger.info(
        "format_output_node completado: document_id=%s status=%s",
        document_id,
        educational_package.get("status"),
    )

    return {"educational_package": educational_package}
