"""Servicio de persistencia en OCI Object Storage.

Capa best-effort: cualquier fallo del SDK OCI queda registrado en el log
pero nunca propaga al llamante. Todos los metodos retornan un dict con
el campo 'status' indicando el resultado de la operacion.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from nuevamente.config import Settings
from nuevamente.infra.oci import OCIStorageClient

logger = logging.getLogger(__name__)


class StorageService:
    """Servicio de almacenamiento en OCI Object Storage.

    Wrappea OCIStorageClient con semantica best-effort: los errores
    se loguean en nivel ERROR pero no se propagan al llamante.

    Si oci_bucket_name esta vacio en Settings, el servicio se deshabilita:
    loguea un WARNING al inicializarse y todas las llamadas retornan
    {'status': 'deshabilitado'} sin intentar conectarse a OCI.

    Args:
        settings: Instancia de Settings con los campos oci_*.
    """

    def __init__(self, settings: Settings) -> None:
        self._enabled = bool(settings.oci_bucket_name)
        if not self._enabled:
            logger.warning(
                "StorageService deshabilitado: oci_bucket_name no configurado. "
                "Configura OCI_BUCKET_NAME para habilitar la persistencia."
            )
            self._client: OCIStorageClient | None = None
            return

        try:
            self._client = OCIStorageClient(settings)
        except Exception as exc:
            logger.error(
                "StorageService: fallo al inicializar OCIStorageClient: %s. "
                "El servicio queda deshabilitado.",
                exc,
            )
            self._enabled = False
            self._client = None

    # ---------------------------------------------------------------------------
    # API publica — sincronos
    # ---------------------------------------------------------------------------

    def upload_documento_fuente(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
    ) -> dict[str, str]:
        """Sube el documento fuente original a OCI Object Storage.

        El objeto se almacena bajo el prefijo 'documentos/' con el document_id
        como nombre base y la extension original del archivo (p.ej.
        'documentos/<document_id>.pdf').

        Args:
            file_bytes: Contenido binario del archivo recibido.
            file_name: Nombre original del archivo (se usa para extraer la extension).
            document_id: UUID de la tarea/documento (garantiza unicidad).

        Returns:
            dict con 'status' en {'ok', 'fallido', 'deshabilitado'} y campos
            adicionales segun el resultado:
            - ok: {'status': 'ok', 'objeto_id': 'documentos/<id><ext>'}
            - fallido: {'status': 'fallido', 'mensaje': '<descripcion del error>'}
            - deshabilitado: {'status': 'deshabilitado'}
        """
        if not self._enabled:
            return {"status": "deshabilitado"}

        extension = Path(file_name).suffix  # incluye el punto, p.ej. '.pdf'
        object_name = f"documentos/{document_id}{extension}"

        try:
            assert self._client is not None  # siempre True cuando _enabled es True
            self._client.upload_object(object_name=object_name, data=file_bytes)
            logger.info(
                "Documento fuente subido a OCI: objeto=%s size=%d bytes",
                object_name,
                len(file_bytes),
            )
            return {"status": "ok", "objeto_id": object_name}
        except Exception as exc:
            logger.error(
                "Error al subir documento fuente a OCI: objeto=%s error=%s",
                object_name,
                exc,
            )
            return {"status": "fallido", "mensaje": str(exc)}

    # ---------------------------------------------------------------------------
    # API publica — asincronos
    # ---------------------------------------------------------------------------

    async def upload_documento_fuente_async(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
    ) -> dict[str, str]:
        """Wrapper asincrono de upload_documento_fuente.

        Ejecuta la llamada sincrona al SDK OCI en un thread separado para
        no bloquear el event loop de FastAPI/Uvicorn.

        Args y Returns: identicos a upload_documento_fuente.
        """
        try:
            return await asyncio.to_thread(
                self.upload_documento_fuente, file_bytes, file_name, document_id
            )
        except Exception as exc:
            logger.error(
                "Error inesperado en upload_documento_fuente_async: document_id=%s error=%s",
                document_id,
                exc,
            )
            return {"status": "fallido", "mensaje": str(exc)}


# ---------------------------------------------------------------------------
# Instancia modulo-nivel (singleton de aplicacion)
# ---------------------------------------------------------------------------

storage_service = StorageService(Settings())
