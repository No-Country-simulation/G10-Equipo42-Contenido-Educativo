"""Servicio de indexado RAG (Retrieval-Augmented Generation).

Orquesta la segmentacion en chunks, generacion de embeddings con Voyage AI,
indexado en FAISS y persistencia en disco. Si el indice ya existe para un
document_id, lo carga desde disco sin regenerar embeddings.
"""

import logging
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from nuevamente.config import Settings
from nuevamente.core.exceptions import DocumentoVacio
from nuevamente.infra.embeddings import get_embeddings
from nuevamente.infra.vectorstore import load_index, save_index
from nuevamente.services.ingestion import build_section_map

logger = logging.getLogger(__name__)


def ingest_document(
    document_id: str,
    raw_text: str,
    file_name: str,
    settings: Settings,
) -> dict[str, Any]:
    """Indexa un documento en FAISS y retorna chunks y section_map.

    Si el indice ya existe en disco para el document_id, lo carga sin
    regenerar embeddings. Si no existe, segmenta el texto, genera embeddings
    con Voyage AI, crea el indice y lo persiste.

    Args:
        document_id: Identificador unico del documento (usado como clave del indice).
        raw_text: Texto crudo extraido del documento.
        file_name: Nombre original del archivo (para metadata y section_map).
        settings: Instancia de Settings con parametros de chunking y embeddings.

    Returns:
        Dict con claves:
        - "chunks": lista de dicts con page_content y metadata por chunk.
        - "section_map": lista de dicts con heading, level y start_offset.

    Raises:
        DocumentoVacio: Si raw_text esta vacio.
    """
    if not raw_text.strip():
        raise DocumentoVacio(
            f"El documento '{file_name}' no tiene contenido para indexar."
        )

    logger.info(
        "Iniciando ingestion: document_id=%s file_name=%s", document_id, file_name
    )

    section_map = build_section_map(raw_text, file_name)
    embeddings = get_embeddings(settings)

    # Intentar cargar indice desde disco
    faiss_vs = load_index(document_id, embeddings, settings)

    if faiss_vs is not None:
        # Indice ya existia: derivar chunks de los documentos almacenados
        docs = list(faiss_vs.docstore._dict.values())
        chunks = [{"page_content": d.page_content, **d.metadata} for d in docs]
        # Ordenar por chunk_index para mantener consistencia
        chunks.sort(key=lambda c: c.get("chunk_index", 0))
        logger.info(
            "Indice cargado desde disco: %d chunks para document_id=%s",
            len(chunks),
            document_id,
        )
    else:
        # Indice nuevo: segmentar, embedir e indexar
        chunks, faiss_vs = _build_index(
            document_id, raw_text, file_name, section_map, embeddings, settings
        )
        save_index(faiss_vs, document_id, settings)
        logger.info(
            "Indice nuevo creado y guardado: %d chunks para document_id=%s",
            len(chunks),
            document_id,
        )

    return {"chunks": chunks, "section_map": section_map}


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _build_index(
    document_id: str,
    raw_text: str,
    file_name: str,
    section_map: list[dict],
    embeddings: Embeddings,
    settings: Settings,
) -> tuple[list[dict], Any]:
    """Segmenta el texto, genera embeddings y construye el indice FAISS.

    Args:
        document_id: Identificador del documento.
        raw_text: Texto crudo.
        file_name: Nombre del archivo para metadata.
        section_map: Mapa de secciones para enriquecer metadata de chunks.
        embeddings: Instancia de VoyageAIEmbeddings.
        settings: Settings con chunk_size y chunk_overlap.

    Returns:
        Tupla (lista de dicts de chunks, instancia FAISS).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )

    # Crear documentos LangChain con metadata base
    documents = splitter.create_documents(
        texts=[raw_text],
        metadatas=[{"source": file_name, "document_id": document_id}],
    )

    # Enriquecer metadata con chunk_index y parent_heading
    for idx, doc in enumerate(documents):
        doc.metadata["chunk_index"] = idx
        doc.metadata["parent_heading"] = _find_parent_heading(
            doc.metadata.get("start_index", 0), section_map
        )

    faiss_vs = FAISS.from_documents(documents, embeddings)

    # Convertir a lista de dicts para el state
    chunks = [
        {"page_content": doc.page_content, **doc.metadata} for doc in documents
    ]

    return chunks, faiss_vs


def _find_parent_heading(start_index: int, section_map: list[dict]) -> str:
    """Busca el heading padre de un chunk por su posicion en el texto.

    Retorna el texto del ultimo heading cuyo start_offset sea <= start_index.
    Retorna "" si section_map esta vacio o ninguno aplica.

    Args:
        start_index: Posicion inicial del chunk en el texto crudo.
        section_map: Lista de dicts con heading, level y start_offset.

    Returns:
        Texto del heading padre, o "" si no hay ninguno.
    """
    parent = ""
    for section in section_map:
        if section["start_offset"] <= start_index:
            parent = section["heading"]
        else:
            break
    return parent
