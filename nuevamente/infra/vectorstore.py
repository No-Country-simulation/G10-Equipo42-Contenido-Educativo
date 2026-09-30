"""Adaptador de infraestructura para el indice vectorial FAISS.

Encapsula save_local y load_local de FAISS. Si el proveedor de vector store
cambia, solo este archivo necesita modificarse.
"""

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

from nuevamente.config import Settings

logger = logging.getLogger(__name__)


def _index_path(document_id: str, settings: Settings) -> Path:
    """Retorna la ruta del directorio del indice para un document_id."""
    return Path(settings.faiss_index_dir) / document_id


def save_index(faiss_vs: FAISS, document_id: str, settings: Settings) -> None:
    """Persiste el indice FAISS en disco.

    Crea el directorio si no existe y guarda index.faiss + index.pkl.

    Args:
        faiss_vs: Instancia de FAISS con el indice a guardar.
        document_id: Identificador unico del documento (nombre de directorio).
        settings: Instancia de Settings con faiss_index_dir.
    """
    index_dir = _index_path(document_id, settings)
    index_dir.mkdir(parents=True, exist_ok=True)
    faiss_vs.save_local(str(index_dir))
    logger.info("Indice FAISS guardado en disco: %s", index_dir)


def load_index(
    document_id: str,
    embeddings: Embeddings,
    settings: Settings,
) -> FAISS | None:
    """Carga el indice FAISS desde disco si existe.

    Args:
        document_id: Identificador unico del documento.
        embeddings: Instancia de embeddings para reconstruir el retriever.
        settings: Instancia de Settings con faiss_index_dir.

    Returns:
        Instancia de FAISS cargada, o None si el indice no existe en disco.
    """
    index_dir = _index_path(document_id, settings)
    if not index_dir.exists():
        return None

    # allow_dangerous_deserialization=True es seguro aqui porque el indice
    # fue generado localmente por este mismo sistema (no proviene de fuentes externas).
    faiss_vs = FAISS.load_local(
        str(index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    logger.info("Indice FAISS cargado desde disco: %s", index_dir)
    return faiss_vs
