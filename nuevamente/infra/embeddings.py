"""Adaptador de infraestructura para embeddings con Voyage AI.

Encapsula la dependencia de langchain_voyageai de forma que si el proveedor
de embeddings cambia, solo este archivo necesita modificarse.
"""

from langchain_voyageai import VoyageAIEmbeddings

from nuevamente.config import Settings


def get_embeddings(settings: Settings) -> VoyageAIEmbeddings:
    """Construye y retorna una instancia de VoyageAIEmbeddings.

    Args:
        settings: Instancia de Settings con la configuracion centralizada.

    Returns:
        Instancia de VoyageAIEmbeddings lista para usar.
    """
    return VoyageAIEmbeddings(
        voyage_api_key=settings.voyage_api_key,
        model=settings.embedding_model_name,
    )
