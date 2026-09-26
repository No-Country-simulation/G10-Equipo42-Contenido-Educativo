"""Servicio de generacion de contenido educativo adaptado.

Implementa el Agente Redactor Pedagogico: transforma los chunks recuperados
en un paquete educativo estructurado usando with_structured_output() de LangChain
para producir instancias Pydantic directamente validadas.

Regla de dependencia: services/ importa de infra/ y core/, no de pipeline/.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from nuevamente.config import Settings
from nuevamente.core.exceptions import PipelineError
from nuevamente.core.schemas import FORMATO_A_SCHEMA
from nuevamente.infra.llm import get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes de prompt por perfil
# ---------------------------------------------------------------------------

_INSTRUCCIONES_POR_PERFIL: dict[str, str] = {
    "Principiante": (
        "El destinatario es un principiante sin experiencia previa en el tema. "
        "Usa lenguaje claro y accesible, analogias del mundo cotidiano, y evita "
        "la jerga tecnica. Define cada termino tecnico cuando lo uses por primera vez. "
        "Prioriza la comprension sobre la exhaustividad."
    ),
    "Junior": (
        "El destinatario es un profesional junior con conocimientos basicos del area. "
        "Puedes usar terminologia tecnica estandar pero explica los conceptos mas avanzados. "
        "Incluye ejemplos practicos y escenarios de uso real."
    ),
    "Senior": (
        "El destinatario es un profesional senior con solida experiencia tecnica. "
        "Usa terminologia tecnica con precision. Profundiza en matices, mejores practicas "
        "y consideraciones de diseno. Omite explicaciones de conceptos basicos."
    ),
    "Lider Tecnico/Arquitecto": (
        "El destinatario es un lider tecnico o arquitecto de software. "
        "Enfocate en implicaciones arquitectonicas, trade-offs de diseno, escalabilidad "
        "y estrategia tecnologica. El contenido debe ser denso en informacion y orientado "
        "a decisiones de alto impacto."
    ),
}

_INSTRUCCIONES_POR_FORMATO: dict[str, str] = {
    "Flashcards": (
        "Genera el contenido como un conjunto de tarjetas de estudio (flashcards). "
        "Cada tarjeta debe tener: frente (pregunta o concepto clave), dorso (respuesta "
        "o explicacion concisa) y pista_didactica (ayuda mnemotecnica o conexion con "
        "otro concepto). Las tarjetas deben cubrir los puntos mas importantes del documento."
    ),
    "Quiz Interactivo": (
        "Genera el contenido como un quiz de opcion multiple. Cada pregunta debe tener: "
        "enunciado claro, 4 opciones de respuesta plausibles, la respuesta correcta "
        "identificada, y una justificacion que explique por que es correcta y que ancle "
        "la respuesta al documento fuente."
    ),
    "Tutorial Paso a Paso": (
        "Genera el contenido como un tutorial secuencial. Cada paso debe tener: numero "
        "de secuencia, titulo descriptivo, explicacion detallada del que y el por que, "
        "y un ejemplo practico cuando sea posible. Los pasos deben guiar al lector "
        "de lo basico a lo avanzado."
    ),
    "Resumen Ejecutivo": (
        "Genera el contenido como un resumen ejecutivo estructurado por secciones. "
        "Cada seccion debe tener: nombre de la seccion, contenido sintetizado de los "
        "puntos clave, e implicacion practica derivada de ese contenido. Prioriza "
        "la informacion accionable y los hallazgos mas relevantes."
    ),
    "Guion de Clase": (
        "Genera el contenido como un guion de clase estructurado por fases. "
        "Cada fase debe tener: nombre (ej: Apertura, Desarrollo, Actividad, Cierre), "
        "contenido a desarrollar, duracion estimada en minutos, y notas para el formador "
        "con sugerencias pedagogicas. La estructura debe seguir una progresion logica."
    ),
}


# ---------------------------------------------------------------------------
# Funcion publica principal
# ---------------------------------------------------------------------------


def generate_content(
    retrieved_chunks: list[dict[str, Any]],
    perfil: str,
    formato: str,
    nicho: str,
    review_result: dict[str, Any] | None,
    settings: Settings,
) -> dict[str, Any]:
    """Genera contenido educativo adaptado a partir de los chunks recuperados.

    Usa llm.with_structured_output() para producir directamente una instancia
    Pydantic del schema correspondiente al formato solicitado, garantizando
    que el output sea valido segun el schema definido en core/schemas.py.

    Args:
        retrieved_chunks: Chunks del documento recuperados por el Agente Investigador.
        perfil: Perfil del destinatario (ej: "Principiante", "Senior").
        formato: Formato pedagogico (ej: "Flashcards", "Resumen Ejecutivo").
        nicho: Nicho o contexto sectorial del destinatario (texto libre o predefinido).
        review_result: Resultado de evaluacion del Agente Critico (None en primera generacion).
        settings: Configuracion del sistema con parametros del LLM.

    Returns:
        Diccionario serializable con la estructura del paquete educativo generado,
        equivalente a PaqueteSchema.model_dump() del formato solicitado.

    Raises:
        PipelineError: Si el formato no esta registrado en FORMATO_A_SCHEMA.
    """
    if formato not in FORMATO_A_SCHEMA:
        raise PipelineError(
            f"Formato pedagogico '{formato}' no reconocido. "
            f"Formatos validos: {list(FORMATO_A_SCHEMA.keys())}"
        )

    schema_class = FORMATO_A_SCHEMA[formato]
    is_retry = review_result is not None

    logger.info(
        "Iniciando generacion: perfil=%s formato=%s nicho=%s retry=%s chunks=%d",
        perfil,
        formato,
        nicho,
        is_retry,
        len(retrieved_chunks),
    )

    messages = _build_messages(retrieved_chunks, perfil, formato, nicho, review_result)

    llm = get_llm(settings)
    structured_llm = llm.with_structured_output(schema_class)

    try:
        resultado = structured_llm.invoke(messages)
    except Exception as exc:
        raise PipelineError(
            f"El Agente Redactor fallo al generar contenido estructurado "
            f"(formato='{formato}', perfil='{perfil}'): {exc}"
        ) from exc

    logger.info(
        "Generacion completada: formato=%s tipo=%s",
        formato,
        type(resultado).__name__,
    )

    return resultado.model_dump()



# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _build_messages(
    retrieved_chunks: list[dict[str, Any]],
    perfil: str,
    formato: str,
    nicho: str,
    review_result: dict[str, Any] | None,
) -> list[SystemMessage | HumanMessage]:
    """Construye los mensajes para el LLM: SystemMessage de rol + HumanMessage con contexto.

    Args:
        retrieved_chunks: Chunks del documento fuente.
        perfil: Perfil del destinatario.
        formato: Formato pedagogico solicitado.
        nicho: Nicho o contexto sectorial.
        review_result: Feedback del Agente Critico si es un reintento.

    Returns:
        Lista de mensajes [SystemMessage, HumanMessage] lista para invocar al LLM.
    """
    instruccion_perfil = _INSTRUCCIONES_POR_PERFIL.get(
        perfil,
        f"El destinatario tiene el perfil '{perfil}'. Adapta el lenguaje y profundidad en consecuencia.",
    )
    instruccion_formato = _INSTRUCCIONES_POR_FORMATO.get(
        formato,
        f"Genera el contenido en formato '{formato}'.",
    )

    system_content = (
        f"Eres un experto en pedagogia y comunicacion educativa. "
        f"Tu rol es transformar contenido tecnico en material educativo de alta calidad.\n\n"
        f"Perfil del destinatario: {instruccion_perfil}\n\n"
        f"Contexto de aplicacion (nicho): El contenido debe ser relevante para el contexto "
        f"'{nicho}'. Usa ejemplos, analogias y terminologia especifica de ese campo cuando "
        f"sea posible y natural.\n\n"
        f"Formato de salida requerido: {instruccion_formato}\n\n"
        f"Principios de calidad:\n"
        f"- El contenido debe estar fielmente anclado al documento fuente proporcionado.\n"
        f"- No inventes informacion que no este en el documento.\n"
        f"- Los metadatos (conceptos_clave, prerrequisitos, tiempo_estimado) deben "
        f"reflejar el contenido real generado.\n"
        f"- El titulo y la introduccion deben estar contextualizados al perfil y nicho."
    )

    contexto_documento = _build_context_text(retrieved_chunks)

    human_content = (
        f"Documento fuente (chunks recuperados):\n\n"
        f"{contexto_documento}\n\n"
        f"Genera un paquete educativo completo en formato '{formato}' para un destinatario "
        f"con perfil '{perfil}' en el contexto de '{nicho}'. "
        f"El paquete debe incluir titulo, introduccion_contextualizada y todos los items "
        f"del formato solicitado, ademas de metadatos pedagogicos completos."
    )

    if review_result is not None:
        score = review_result.get("anclaje_fuente_score", 0.0)
        observaciones = review_result.get("observaciones", "Sin observaciones especificas.")
        human_content += (
            f"\n\nFEEDBACK DEL REVISOR (reintento de generacion):\n"
            f"El intento anterior obtuvo un score de fidelidad de {score:.2f}/1.0, "
            f"que esta por debajo del umbral aceptable (0.7).\n"
            f"Observaciones del revisor: {observaciones}\n\n"
            f"Por favor, mejora el anclaje al documento fuente: cita conceptos especificos "
            f"del texto, evita generalizaciones no respaldadas por el documento, y asegurate "
            f"de que cada item este directamente fundamentado en el contenido proporcionado."
        )

    return [
        SystemMessage(content=system_content),
        HumanMessage(content=human_content),
    ]


def _build_context_text(chunks: list[dict[str, Any]]) -> str:
    """Concatena los chunks en un bloque de texto legible para el LLM.

    Args:
        chunks: Lista de chunks con 'page_content' y metadata opcional.

    Returns:
        Texto concatenado con separadores por chunk.
    """
    if not chunks:
        return "(Sin contenido recuperado del documento fuente)"

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        content = chunk.get("page_content", "")
        heading = chunk.get("parent_heading", "")
        if heading:
            parts.append(f"[Seccion: {heading}]\n{content}")
        else:
            parts.append(f"[Fragmento {i}]\n{content}")

    return "\n\n---\n\n".join(parts)
