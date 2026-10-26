"""Servicio de ingestion de documentos.

Responsable de extraer texto de archivos en distintos formatos (PDF, Markdown,
texto plano) y de construir el mapa de secciones del documento a partir de su
estructura (headings Markdown). No depende de LangChain ni de modelos de IA.
"""

import io
import logging
import os
import re

from pypdf import PdfReader

from nuevamente.core.exceptions import DocumentoNoSoportado, DocumentoVacio

logger = logging.getLogger(__name__)

# Extensiones soportadas
EXTENSIONES_SOPORTADAS = {".pdf", ".md", ".txt"}

# Regex para detectar headings Markdown (hasta nivel 6)
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)


def extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extrae el contenido textual de un archivo segun su extension.

    Args:
        file_bytes: Contenido binario del archivo.
        file_name: Nombre original del archivo (incluye extension).

    Returns:
        Texto extraido como string.

    Raises:
        DocumentoNoSoportado: Si la extension del archivo no esta soportada.
        DocumentoVacio: Si el archivo no contiene texto extraible.
    """
    suffix = _get_extension(file_name)

    if suffix == ".pdf":
        text = _extract_from_pdf(file_bytes, file_name)
    elif suffix in {".md", ".txt"}:
        text = _extract_from_text(file_bytes, file_name)
    else:
        raise DocumentoNoSoportado(
            f"Formato de archivo no soportado: '{suffix}'. "
            f"Formatos aceptados: {', '.join(sorted(EXTENSIONES_SOPORTADAS))}"
        )

    if not text.strip():
        raise DocumentoVacio(
            f"El archivo '{file_name}' no contiene texto extraible o esta vacio."
        )

    return text


def build_section_map(raw_text: str, file_name: str) -> list[dict]:
    """Construye el mapa de secciones del documento.

    Para archivos Markdown, parsea los headings (# a ######) y registra su
    nivel, texto y posicion de caracter en el texto crudo. Para otros formatos
    retorna una lista vacia.

    Args:
        raw_text: Texto crudo extraido del documento.
        file_name: Nombre original del archivo (para determinar el formato).

    Returns:
        Lista de dicts con campos: heading (str), level (int), start_offset (int).
        Lista vacia si el formato no es Markdown.
    """
    suffix = _get_extension(file_name)
    if suffix != ".md":
        return []

    section_map = []
    for match in _HEADING_PATTERN.finditer(raw_text):
        level = len(match.group(1))
        heading_text = match.group(2).strip()
        start_offset = match.start()
        section_map.append(
            {
                "heading": heading_text,
                "level": level,
                "start_offset": start_offset,
            }
        )

    return section_map


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _get_extension(file_name: str) -> str:
    """Retorna la extension del archivo en minusculas (con punto)."""
    _, ext = os.path.splitext(file_name)
    return ext.lower()


def _extract_from_pdf(file_bytes: bytes, file_name: str) -> str:
    """Extrae texto de un PDF pagina por pagina."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentoVacio(
            f"No se pudo leer el archivo PDF '{file_name}': {exc}"
        ) from exc

    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    return "\n".join(pages_text)


def _extract_from_text(file_bytes: bytes, file_name: str) -> str:
    """Decodifica un archivo de texto plano o Markdown a string."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise DocumentoVacio(
                f"No se pudo decodificar el archivo '{file_name}': {exc}"
            ) from exc
