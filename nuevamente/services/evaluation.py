"""Servicio de evaluacion de fidelidad del contenido educativo generado.

Implementa el Agente Critico/Revisor: evalua el anclaje del contenido generado
al documento fuente usando with_structured_output(EvaluacionCalidad) de LangChain
para producir una instancia Pydantic directamente validada.

Regla de dependencia: services/ importa de infra/ y core/, no de pipeline/.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from nuevamente.config import Settings
from nuevamente.core.exceptions import PipelineError
from nuevamente.core.schemas import EvaluacionCalidad
from nuevamente.infra.llm import get_llm

logger = logging.getLogger(__name__)


def evaluate_fidelity(
    generated_content: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
    settings: Settings,
) -> dict[str, Any]:
    """Evalua la fidelidad del contenido educativo generado respecto al documento fuente.

    Usa llm.with_structured_output(EvaluacionCalidad) para que el LLM asigne
    un score de anclaje (0.0-1.0) y proporcione observaciones concretas sobre
    las discrepancias entre el contenido generado y el texto fuente.

    Args:
        generated_content: Paquete educativo generado por el Agente Redactor
            (resultado de PaqueteSchema.model_dump()).
        retrieved_chunks: Chunks del documento recuperados por el Agente Investigador,
            usados como fuente de verdad para la evaluacion.
        settings: Configuracion del sistema con parametros del LLM.

    Returns:
        Diccionario serializable equivalente a EvaluacionCalidad.model_dump(),
        con keys: anclaje_fuente_score, claridad_pedagogica, observaciones.

    Raises:
        PipelineError: Si generated_content esta vacio o el LLM falla durante
            la evaluacion.
    """
    if not generated_content:
        raise PipelineError(
            "El Agente Critico no puede evaluar un paquete vacio. "
            "generated_content debe ser un dict no vacio.",
            agente="critico",
            detalle="generated_content={} recibido",
        )

    logger.info(
        "Iniciando evaluacion de fidelidad: chunks_fuente=%d",
        len(retrieved_chunks),
    )

    messages = _build_messages(generated_content, retrieved_chunks)

    llm = get_llm(settings)
    structured_llm = llm.with_structured_output(EvaluacionCalidad)

    try:
        resultado = structured_llm.invoke(messages)
        logger.info(
            "Evaluacion completada: anclaje_fuente_score=%.2f",
            resultado.anclaje_fuente_score,
        )
        return resultado.model_dump()
    except Exception as exc:
        raise PipelineError(
            f"El Agente Critico fallo al evaluar la fidelidad del contenido: {exc}",
            agente="critico",
            detalle=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _build_messages(
    generated_content: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
) -> list[SystemMessage | HumanMessage]:
    """Construye los mensajes para el LLM Critico.

    Args:
        generated_content: Paquete educativo generado a evaluar.
        retrieved_chunks: Chunks del documento fuente como referencia.

    Returns:
        Lista de mensajes [SystemMessage, HumanMessage] lista para invocar al LLM.
    """
    system_content = (
        "Eres un Evaluador de Fidelidad Pedagogica especializado. "
        "Tu rol es verificar que el contenido educativo generado este fielmente "
        "anclado al documento fuente proporcionado, sin inventar informacion "
        "ni incluir afirmaciones no respaldadas por el texto original.\n\n"
        "Debes asignar un 'anclaje_fuente_score' entre 0.0 y 1.0 basado en:\n"
        "- 1.0: Todo el contenido esta directamente respaldado por el documento fuente.\n"
        "- 0.7-0.9: La mayoria del contenido esta anclado, con pequenas extrapolaciones justificadas.\n"
        "- 0.5-0.7: Hay afirmaciones que van mas alla del documento fuente de forma notable.\n"
        "- 0.0-0.5: El contenido contiene informacion significativa no respaldada por el fuente.\n\n"
        "Un score de 0.7 o superior es aceptable. Por debajo de 0.7 el contenido "
        "requiere reintento. En ese caso, tus 'observaciones' deben ser especificas "
        "y accionables: menciona que afirmaciones concretas no estan en el fuente "
        "y como mejorarlas.\n\n"
        "En 'claridad_pedagogica' proporciona una valoracion cualitativa de la "
        "calidad pedagogica del contenido (estructura, claridad, adecuacion al perfil)."
    )

    contenido_texto = _serialize_generated_content(generated_content)
    fuente_texto = _build_source_text(retrieved_chunks)

    human_content = (
        f"CONTENIDO EDUCATIVO GENERADO A EVALUAR:\n\n"
        f"{contenido_texto}\n\n"
        f"{'=' * 60}\n\n"
        f"DOCUMENTO FUENTE (texto de referencia):\n\n"
        f"{fuente_texto}\n\n"
        f"{'=' * 60}\n\n"
        f"Evalua la fidelidad del contenido generado respecto al documento fuente. "
        f"Determina cuantas afirmaciones del contenido estan directamente respaldadas "
        f"por el texto fuente y asigna el score correspondiente. "
        f"Proporciona observaciones concretas sobre las discrepancias encontradas."
    )

    return [
        SystemMessage(content=system_content),
        HumanMessage(content=human_content),
    ]


def _serialize_generated_content(generated_content: dict[str, Any]) -> str:
    """Serializa el paquete educativo generado a texto plano para el prompt.

    Intenta extraer titulo e items del contenido_adaptado de forma legible.
    Si la estructura no es la esperada, usa JSON como fallback.

    Args:
        generated_content: Paquete educativo (resultado de PaqueteSchema.model_dump()).

    Returns:
        Representacion en texto plano del contenido generado.
    """
    try:
        contenido_adaptado = generated_content.get("contenido_adaptado", {})
        titulo = contenido_adaptado.get("titulo", "Sin titulo")
        introduccion = contenido_adaptado.get("introduccion_contextualizada", "")
        items = contenido_adaptado.get("items", [])

        partes = [f"Titulo: {titulo}"]
        if introduccion:
            partes.append(f"Introduccion: {introduccion}")

        if items:
            partes.append(f"\nItems ({len(items)} en total):")
            for i, item in enumerate(items, start=1):
                if isinstance(item, dict):
                    item_texto = "; ".join(
                        f"{k}: {v}" for k, v in item.items() if v and k != "paso"
                    )
                    partes.append(f"  {i}. {item_texto}")

        metadatos = generated_content.get("metadatos", {})
        if metadatos:
            conceptos = metadatos.get("conceptos_clave", [])
            if conceptos:
                partes.append(f"\nConceptos clave: {', '.join(conceptos)}")

        return "\n".join(partes)
    except Exception:
        return json.dumps(generated_content, ensure_ascii=False, indent=2)


def _build_source_text(chunks: list[dict[str, Any]]) -> str:
    """Concatena los chunks del documento fuente en un bloque de texto legible.

    Args:
        chunks: Lista de chunks con 'page_content' y metadata opcional.

    Returns:
        Texto concatenado con separadores por chunk. Mensaje informativo si vacio.
    """
    if not chunks:
        return "(Sin chunks del documento fuente disponibles para comparacion)"

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        content = chunk.get("page_content", "")
        heading = chunk.get("parent_heading", "")
        if heading:
            parts.append(f"[Seccion: {heading}]\n{content}")
        else:
            parts.append(f"[Fragmento {i}]\n{content}")

    return "\n\n---\n\n".join(parts)
