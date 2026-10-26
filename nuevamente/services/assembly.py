"""Servicio de ensamblado del paquete educativo final.

Recibe el contenido generado (generated_content) y el resultado de la
evaluacion de fidelidad (review_result) y los combina en un paquete
educativo completo, validado contra el schema Pydantic del formato solicitado.

Regla de dependencia: services/ importa de infra/ y core/, no de pipeline/.
"""

import logging
from typing import Any

from nuevamente.config import Settings
from nuevamente.core.exceptions import PipelineError
from nuevamente.core.schemas import FORMATO_A_SCHEMA

logger = logging.getLogger(__name__)


def assemble_package(
    generated_content: dict[str, Any],
    review_result: dict[str, Any],
    formato: str,
    settings: Settings,
) -> dict[str, Any]:
    """Ensambla y valida el paquete educativo final.

    Combina el contenido generado por el Agente Redactor con el resultado de
    la evaluacion del Agente Critico en un paquete educativo completo con las
    cuatro secciones requeridas: status, metadatos, contenido_adaptado y
    evaluacion_calidad. Valida la estructura resultante contra el schema
    Pydantic del formato pedagogico solicitado.

    Args:
        generated_content: Dict serializable producido por generate_content(),
            equivalente a PaqueteSchema.model_dump() sin la evaluacion_calidad.
            Debe contener al menos las claves 'metadatos' y 'contenido_adaptado'.
        review_result: Dict serializable producido por evaluate_fidelity(),
            equivalente a EvaluacionCalidad.model_dump().
        formato: Formato pedagogico (ej: "Flashcards", "Resumen Ejecutivo").
            Debe estar registrado en FORMATO_A_SCHEMA.
        settings: Configuracion del sistema (actualmente no usada en ensamblado,
            pero incluida por coherencia con otros servicios y extension futura).

    Returns:
        Diccionario serializable con el paquete educativo completo, validado
        por Pydantic. Equivalente a PaqueteSchema.model_dump() con las cuatro
        secciones requeridas.

    Raises:
        PipelineError: Si el formato no esta registrado en FORMATO_A_SCHEMA,
            si generated_content no contiene las claves esperadas, o si la
            validacion Pydantic falla por estructura inesperada.
    """
    if formato not in FORMATO_A_SCHEMA:
        raise PipelineError(
            f"Formato pedagogico '{formato}' no reconocido en FORMATO_A_SCHEMA. "
            f"Formatos validos: {list(FORMATO_A_SCHEMA.keys())}",
            agente="format_output",
        )

    if not generated_content:
        raise PipelineError(
            "generated_content esta vacio: no hay contenido que ensamblar.",
            agente="format_output",
        )

    logger.info(
        "assemble_package: formato=%s claves_generated=%s",
        formato,
        list(generated_content.keys()),
    )

    try:
        paquete_dict = {
            "status": "completed",
            "metadatos": generated_content["metadatos"],
            "contenido_adaptado": generated_content["contenido_adaptado"],
            "evaluacion_calidad": review_result,
        }
        schema_class = FORMATO_A_SCHEMA[formato]
        paquete = schema_class(**paquete_dict)
        resultado = paquete.model_dump()
    except KeyError as exc:
        raise PipelineError(
            f"generated_content no contiene la clave requerida: {exc}. "
            f"Claves presentes: {list(generated_content.keys())}",
            agente="format_output",
            detalle=str(exc),
        ) from exc
    except Exception as exc:
        raise PipelineError(
            f"Error al ensamblar o validar el paquete educativo "
            f"(formato='{formato}'): {exc}",
            agente="format_output",
            detalle=str(exc),
        ) from exc

    logger.info(
        "assemble_package completado: formato=%s status=%s",
        formato,
        resultado.get("status"),
    )

    return resultado
