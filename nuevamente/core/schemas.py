"""Schemas Pydantic para el paquete educativo y sus variantes por formato.

Cada formato pedagogico tiene su propio modelo que hereda de PaqueteEducativoBase
y define la estructura especifica de contenido_adaptado con sus items tipados.
La validacion de schema es inherente a la llamada al LLM via with_structured_output().
"""

from pydantic import BaseModel, Field

from nuevamente.core.models import FormatoPedagogico


# ---------------------------------------------------------------------------
# Metadatos y evaluacion (componentes transversales)
# ---------------------------------------------------------------------------


class MetadatosPedagogicos(BaseModel):
    """Metadatos del paquete educativo generado."""

    perfil_aplicado: str = Field(
        description="Perfil del destinatario utilizado en la generacion",
    )
    formato_generado: str = Field(
        description="Formato pedagogico del contenido generado",
    )
    tiempo_estimado_estudio_minutos: int = Field(
        description="Tiempo estimado de estudio en minutos",
        ge=1,
    )
    conceptos_clave: list[str] = Field(
        description="Lista de conceptos clave cubiertos en el contenido",
    )
    prerrequisitos: list[str] = Field(
        default_factory=list,
        description="Conocimientos previos recomendados para aprovechar el contenido",
    )


class EvaluacionCalidad(BaseModel):
    """Resultado de la evaluacion de fidelidad del contenido generado."""

    anclaje_fuente_score: float = Field(
        description="Score de fidelidad al documento fuente (0.0 a 1.0)",
        ge=0.0,
        le=1.0,
    )
    claridad_pedagogica: str = Field(
        description="Valoracion cualitativa de la claridad pedagogica del contenido",
    )
    observaciones: str = Field(
        description="Notas del Agente Critico sobre la adaptacion realizada",
    )


# ---------------------------------------------------------------------------
# Base del paquete educativo
# ---------------------------------------------------------------------------


class PaqueteEducativoBase(BaseModel):
    """Estructura base comun a todos los formatos de paquete educativo.

    Cada formato concreto hereda de esta base y define su propio
    modelo de contenido_adaptado con items especificos.
    """

    status: str = Field(
        description="Estado del paquete: 'completed' o 'error'",
    )
    metadatos: MetadatosPedagogicos
    evaluacion_calidad: EvaluacionCalidad


# ---------------------------------------------------------------------------
# Items por formato pedagogico
# ---------------------------------------------------------------------------


class FlashcardItem(BaseModel):
    """Un item de flashcard: frente, dorso y pista didactica."""

    frente: str = Field(description="Pregunta o concepto en el frente de la tarjeta")
    dorso: str = Field(description="Respuesta o explicacion en el dorso de la tarjeta")
    pista_didactica: str = Field(description="Pista para facilitar el recuerdo")


class QuizItem(BaseModel):
    """Un item de quiz: pregunta con opciones, respuesta correcta y justificacion."""

    pregunta: str = Field(description="Pregunta del quiz")
    opciones: list[str] = Field(description="Lista de opciones de respuesta")
    respuesta_correcta: str = Field(description="La opcion correcta")
    justificacion: str = Field(
        description="Explicacion de por que la respuesta es correcta, anclada al documento fuente",
    )


class TutorialPasoItem(BaseModel):
    """Un paso de tutorial: numero, titulo, explicacion y ejemplo."""

    paso: int = Field(description="Numero del paso en la secuencia", ge=1)
    titulo: str = Field(description="Titulo descriptivo del paso")
    explicacion: str = Field(description="Explicacion detallada del paso")
    ejemplo: str = Field(
        default="",
        description="Ejemplo practico que ilustra el paso",
    )


class ResumenEjecutivoItem(BaseModel):
    """Una seccion de resumen ejecutivo: seccion, contenido e implicacion."""

    seccion: str = Field(description="Nombre de la seccion del resumen")
    contenido: str = Field(description="Contenido sintetizado de la seccion")
    implicacion: str = Field(
        description="Implicacion practica o conclusion derivada del contenido",
    )


class GuionClaseItem(BaseModel):
    """Una fase del guion de clase: fase, contenido, duracion y notas."""

    fase: str = Field(description="Nombre de la fase de la clase (ej: Apertura, Desarrollo, Cierre)")
    contenido: str = Field(description="Contenido a desarrollar en esta fase")
    duracion_minutos: int = Field(description="Duracion estimada en minutos", ge=1)
    notas_formador: str = Field(
        default="",
        description="Notas adicionales para el formador",
    )


# ---------------------------------------------------------------------------
# Contenido adaptado por formato
# ---------------------------------------------------------------------------


class ContenidoAdaptadoBase(BaseModel):
    """Estructura base del contenido adaptado, comun a todos los formatos."""

    titulo: str = Field(description="Titulo del contenido educativo generado")
    introduccion_contextualizada: str = Field(
        description="Introduccion adaptada al perfil y nicho del destinatario",
    )


class ContenidoAdaptadoFlashcards(ContenidoAdaptadoBase):
    """Contenido adaptado en formato Flashcards."""

    items: list[FlashcardItem] = Field(description="Lista de flashcards generadas")


class ContenidoAdaptadoQuiz(ContenidoAdaptadoBase):
    """Contenido adaptado en formato Quiz Interactivo."""

    items: list[QuizItem] = Field(description="Lista de preguntas del quiz")


class ContenidoAdaptadoTutorial(ContenidoAdaptadoBase):
    """Contenido adaptado en formato Tutorial Paso a Paso."""

    items: list[TutorialPasoItem] = Field(description="Lista de pasos del tutorial")


class ContenidoAdaptadoResumenEjecutivo(ContenidoAdaptadoBase):
    """Contenido adaptado en formato Resumen Ejecutivo."""

    items: list[ResumenEjecutivoItem] = Field(description="Secciones del resumen ejecutivo")


class ContenidoAdaptadoGuionClase(ContenidoAdaptadoBase):
    """Contenido adaptado en formato Guion de Clase."""

    items: list[GuionClaseItem] = Field(description="Fases del guion de clase")


# ---------------------------------------------------------------------------
# Paquetes educativos completos (uno por formato)
# ---------------------------------------------------------------------------


class FlashcardsPaquete(PaqueteEducativoBase):
    """Paquete educativo completo en formato Flashcards."""

    contenido_adaptado: ContenidoAdaptadoFlashcards


class QuizPaquete(PaqueteEducativoBase):
    """Paquete educativo completo en formato Quiz Interactivo."""

    contenido_adaptado: ContenidoAdaptadoQuiz


class TutorialPaquete(PaqueteEducativoBase):
    """Paquete educativo completo en formato Tutorial Paso a Paso."""

    contenido_adaptado: ContenidoAdaptadoTutorial


class ResumenEjecutivoPaquete(PaqueteEducativoBase):
    """Paquete educativo completo en formato Resumen Ejecutivo."""

    contenido_adaptado: ContenidoAdaptadoResumenEjecutivo


class GuionClasePaquete(PaqueteEducativoBase):
    """Paquete educativo completo en formato Guion de Clase."""

    contenido_adaptado: ContenidoAdaptadoGuionClase


# Mapa de formato a modelo Pydantic, util para seleccion dinamica
FORMATO_A_SCHEMA: dict[str, type[PaqueteEducativoBase]] = {
    FormatoPedagogico.FLASHCARDS.value: FlashcardsPaquete,
    FormatoPedagogico.QUIZ_INTERACTIVO.value: QuizPaquete,
    FormatoPedagogico.TUTORIAL_PASO_A_PASO.value: TutorialPaquete,
    FormatoPedagogico.RESUMEN_EJECUTIVO.value: ResumenEjecutivoPaquete,
    FormatoPedagogico.GUION_DE_CLASE.value: GuionClasePaquete,
}
