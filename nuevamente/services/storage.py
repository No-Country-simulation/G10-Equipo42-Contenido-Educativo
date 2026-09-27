"""Servicio de persistencia en OCI Object Storage.

Capa best-effort: cualquier fallo del SDK OCI queda registrado en el log
pero nunca propaga al llamante. Todos los metodos retornan un dict con
el campo 'status' indicando el resultado de la operacion.

Ambos metodos (upload_documento_fuente y upload_paquete_educativo) usan
la misma clave de retorno 'status' para mantener consistencia en el contrato
de la interfaz de StorageService.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import time
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

    def upload_paquete_educativo(
        self,
        package_dict: dict,
        document_id: str,
        perfil: str,
        formato: str,
    ) -> dict[str, str]:
        """Sube el paquete educativo generado a OCI Object Storage.

        El objeto se almacena bajo el prefijo 'paquetes/' con el document_id,
        perfil, formato y timestamp como nombre: 'paquetes/<id>_<perfil>_<formato>_<ts>.json'.

        El JSON se serializa con ensure_ascii=False y se sube como bytes UTF-8.
        Llamada sincrona: debe invocarse desde un thread (p.ej. dentro de
        asyncio.to_thread) para no bloquear el event loop.

        Args:
            package_dict: Diccionario del paquete educativo generado por el pipeline.
            document_id: UUID de la tarea/documento (garantiza unicidad).
            perfil: Perfil del destinatario (tal cual viene del state).
            formato: Formato pedagogico (tal cual viene del state).

        Returns:
            dict con 'status' en {'ok', 'fallido', 'deshabilitado'} y campos
            adicionales segun el resultado:
            - ok: {'status': 'ok', 'bucket': '<nombre>', 'objeto_id': 'paquetes/<...>.json'}
            - fallido: {'status': 'fallido', 'mensaje': '<descripcion del error>'}
            - deshabilitado: {'status': 'deshabilitado'}
        """
        if not self._enabled:
            return {"status": "deshabilitado"}

        timestamp = int(time.time())
        object_name = f"paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json"
        data = json.dumps(package_dict, ensure_ascii=False).encode("utf-8")

        try:
            assert self._client is not None  # siempre True cuando _enabled es True
            self._client.upload_object(object_name=object_name, data=data)
            logger.info(
                "Paquete educativo subido a OCI: objeto=%s size=%d bytes",
                object_name,
                len(data),
            )
            return {
                "status": "ok",
                "bucket": self._client.bucket_name,
                "objeto_id": object_name,
            }
        except Exception as exc:
            logger.error(
                "Error al subir paquete educativo a OCI: objeto=%s error=%s",
                object_name,
                exc,
            )
            return {"status": "fallido", "mensaje": str(exc)}

    # ---------------------------------------------------------------------------
    # API publica — listado
    # ---------------------------------------------------------------------------

    def list_paquetes(self) -> list[dict]:
        """Lista los paquetes educativos almacenados en OCI Object Storage.

        Consulta el prefijo 'paquetes/' del bucket y parsea los nombres de los
        objetos para extraer metadata (document_id, perfil, formato, timestamp).

        El nombre de los objetos sigue el patron:
        paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json

        Returns:
            Lista de dicts con claves: objeto_id, perfil, formato,
            fecha_epoch (int), fecha_iso (str ISO 8601 UTC).
            Lista vacia si OCI esta deshabilitado o si ocurre un error.
        """
        if not self._enabled:
            return []

        try:
            assert self._client is not None  # siempre True cuando _enabled es True
            object_names = self._client.list_objects("paquetes/")
        except Exception as exc:
            logger.error(
                "Error al listar paquetes en OCI: error=%s",
                exc,
            )
            return []

        generaciones: list[dict] = []
        for object_name in object_names:
            try:
                # Formato: paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json
                # rsplit con maxsplit=3 separa los ultimos 3 underscores
                base = object_name.replace("paquetes/", "").replace(".json", "")
                parts = base.rsplit("_", 3)
                if len(parts) != 4:
                    logger.warning(
                        "Nombre de objeto con formato inesperado: %s — omitido",
                        object_name,
                    )
                    continue
                document_id, perfil, formato, ts_str = parts
                fecha_epoch = int(ts_str)
                fecha_iso = datetime.datetime.fromtimestamp(
                    fecha_epoch, tz=datetime.timezone.utc
                ).isoformat()
                generaciones.append(
                    {
                        "objeto_id": object_name,
                        "document_id": document_id,
                        "perfil": perfil,
                        "formato": formato,
                        "fecha_epoch": fecha_epoch,
                        "fecha_iso": fecha_iso,
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Error al parsear metadata de objeto '%s': %s — omitido",
                    object_name,
                    exc,
                )
                continue

        # Ordenar de mas reciente a mas antiguo
        generaciones.sort(key=lambda g: g["fecha_epoch"], reverse=True)
        logger.info(
            "Paquetes listados desde OCI: total=%d",
            len(generaciones),
        )
        return generaciones

    def get_paquete(self, objeto_id: str) -> dict | None:
        """Descarga y parsea un paquete educativo desde OCI Object Storage.

        Args:
            objeto_id: Nombre completo del objeto en el bucket (e.g. 'paquetes/...json').

        Returns:
            Dict del paquete educativo parseado desde JSON, o None si OCI esta
            deshabilitado, el objeto no existe, o cualquier otro error ocurre.
        """
        if not self._enabled:
            return None

        try:
            assert self._client is not None  # siempre True cuando _enabled es True
            raw_bytes = self._client.get_object(objeto_id)
            paquete = json.loads(raw_bytes.decode("utf-8"))
            logger.info(
                "Paquete educativo descargado desde OCI: objeto=%s",
                objeto_id,
            )
            return paquete
        except Exception as exc:
            logger.error(
                "Error al descargar paquete desde OCI: objeto=%s error=%s",
                objeto_id,
                exc,
            )
            return None


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
