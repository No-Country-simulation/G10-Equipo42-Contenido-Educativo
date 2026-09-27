"""Cliente OCI Object Storage para NuevaMente.

Adaptador de infraestructura que envuelve el SDK oficial de OCI.
Las excepciones del SDK se propagan sin capturar; el manejo
best-effort es responsabilidad del servicio de la capa superior
(services/storage.py).
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

import oci

if TYPE_CHECKING:
    from nuevamente.config import Settings

logger = logging.getLogger(__name__)


class OCIStorageClient:
    """Cliente de OCI Object Storage.

    Inicializa la configuracion desde el archivo ~/.oci/config (o el path
    configurado en Settings) y crea un ObjectStorageClient autenticado.

    Las llamadas al SDK son sincronas. Usar asyncio.to_thread cuando se
    invoque desde contextos asincronos.

    Args:
        settings: Instancia de Settings con los campos oci_*.
    """

    def __init__(self, settings: Settings) -> None:
        oci_config = oci.config.from_file(
            file_location=str(settings.oci_config_file),
            profile_name=settings.oci_config_profile,
        )
        self._client = oci.object_storage.ObjectStorageClient(oci_config)
        self._namespace = settings.oci_namespace
        self._bucket_name = settings.oci_bucket_name
        logger.info(
            "OCIStorageClient inicializado: namespace=%s bucket=%s",
            self._namespace,
            self._bucket_name,
        )

    @property
    def bucket_name(self) -> str:
        """Nombre del bucket OCI configurado."""
        return self._bucket_name

    def upload_object(
        self,
        object_name: str,
        data: bytes,
        *,
        namespace: str | None = None,
        bucket_name: str | None = None,
    ) -> None:
        """Sube un objeto a OCI Object Storage.

        Args:
            object_name: Nombre (key) del objeto dentro del bucket.
            data: Contenido binario del objeto.
            namespace: Namespace OCI. Si es None usa el de Settings.
            bucket_name: Nombre del bucket. Si es None usa el de Settings.

        Raises:
            oci.exceptions.ServiceError: Si OCI retorna un error HTTP.
            oci.exceptions.RequestException: Si hay problemas de red/timeout.
            Exception: Cualquier otra excepcion del SDK.
        """
        ns = namespace or self._namespace
        bucket = bucket_name or self._bucket_name
        self._client.put_object(
            namespace_name=ns,
            bucket_name=bucket,
            object_name=object_name,
            put_object_body=io.BytesIO(data),
        )
        logger.debug(
            "Objeto subido exitosamente: namespace=%s bucket=%s objeto=%s size=%d bytes",
            ns,
            bucket,
            object_name,
            len(data),
        )
