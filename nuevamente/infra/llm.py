"""Factory de LLM para el pipeline de NuevaMente.

Encapsula la inicializacion del modelo de lenguaje usando init_chat_model
de LangChain. Si el proveedor cambia, solo este modulo cambia.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from nuevamente.config import Settings


def get_llm(settings: Settings) -> BaseChatModel:
    """Instancia el modelo de lenguaje configurado en Settings.

    Usa init_chat_model con el formato provider:model soportado por LangChain.
    Por ejemplo: google_genai:gemini-2.0-flash-lite.

    Args:
        settings: Instancia de Settings con parametros del LLM.

    Returns:
        Instancia de BaseChatModel lista para invocar.
    """
    kwargs: dict = {
        "temperature": settings.llm_temperature,
        "max_retries": settings.llm_max_retries,
    }
    if settings.google_api_key:
        kwargs["api_key"] = settings.google_api_key

    return init_chat_model(
        settings.llm_model_name,
        **kwargs,
    )
