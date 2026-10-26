"""Modelos de dominio: enums para perfiles, formatos pedagogicos y nichos."""

from enum import Enum


class Perfil(str, Enum):
    """Perfil del destinatario del contenido educativo.

    Define el nivel de experiencia y el tipo de lenguaje/profundidad
    que se utilizara en la generacion del contenido adaptado.
    """

    PRINCIPIANTE = "Principiante"
    JUNIOR = "Junior"
    SENIOR = "Senior"
    LIDER_TECNICO = "Lider Tecnico/Arquitecto"


class FormatoPedagogico(str, Enum):
    """Formato de salida del contenido educativo.

    Cada formato tiene su propio schema Pydantic con estructura
    de items especifica en core/schemas.py.
    """

    FLASHCARDS = "Flashcards"
    QUIZ_INTERACTIVO = "Quiz Interactivo"
    TUTORIAL_PASO_A_PASO = "Tutorial Paso a Paso"
    RESUMEN_EJECUTIVO = "Resumen Ejecutivo"
    GUION_DE_CLASE = "Guion de Clase"


class NichoPredefinido(str, Enum):
    """Opciones predefinidas de nicho/contexto sectorial.

    El usuario puede seleccionar uno de estos valores predefinidos
    o proporcionar texto libre para un nicho personalizado.
    """

    GENERAL = "General"
    FINTECH = "Fintech"
    SALUD = "Salud"
    ECOMMERCE = "E-commerce"
