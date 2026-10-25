"""Servicio de persistencia híbrido (Local-First y OCI Object Storage).

Capa best-effort y resiliente:
- Persistencia Local-First: guarda tanto los documentos originales como los paquetes
  educativos JSON en el sistema de archivos local (`data/storage/`), garantizando que
  el historial y la recuperación de contenidos funcionen incluso sin conexión a OCI.
- Sincronización OCI: si las credenciales de OCI están configuradas en Settings,
  sube los archivos a OCI Object Storage de forma no bloqueante y sincroniza en segundo
  plano los archivos pendientes.
- Consulta unificada y desduplicada: `list_paquetes` fusiona el historial local y el
  de OCI sin duplicados, utilizando el `objeto_id` determinista.
- Recuperación optimizada: `get_paquete` lee primero de disco local (<1ms) y, si no existe,
  lo descarga desde OCI y lo cachea en local.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import time
from pathlib import Path
from typing import Any

from nuevamente.config import Settings
from nuevamente.infra.oci import OCIStorageClient

logger = logging.getLogger(__name__)


class StorageService:
    """Servicio de almacenamiento híbrido (Local-First y OCI Object Storage).

    Wrappea OCIStorageClient y el almacenamiento en disco local con semántica best-effort:
    los errores de red de OCI se loguean en nivel ERROR pero no interrumpen la entrega
    al usuario ni el historial, que queda respaldado en el almacenamiento local.

    Args:
        settings: Instancia de Settings con configuraciones locales y de OCI.
    """

    def __init__(self, settings: Settings) -> None:
        # Configuración de almacenamiento local
        local_dir = getattr(settings, "local_storage_dir", None)
        if isinstance(local_dir, (str, Path)):
            self._local_storage_dir = Path(local_dir)
        else:
            self._local_storage_dir = Path("data/storage")

        self._docs_dir = self._local_storage_dir / "documentos"
        self._pkgs_dir = self._local_storage_dir / "paquetes"
        try:
            self._docs_dir.mkdir(parents=True, exist_ok=True)
            self._pkgs_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.error("No se pudieron crear directorios de almacenamiento local: %s", exc)

        # Configuración de OCI Object Storage
        bucket_name = getattr(settings, "oci_bucket_name", "")
        self._enabled = bool(bucket_name)
        if not self._enabled:
            logger.warning(
                "OCI deshabilitado: oci_bucket_name no configurado. "
                "Operando en modo de persistencia local."
            )
            self._client: OCIStorageClient | None = None
            return

        try:
            self._client = OCIStorageClient(settings)
        except Exception as exc:
            logger.error(
                "StorageService: fallo al inicializar OCIStorageClient: %s. "
                "Operando en modo de persistencia local.",
                exc,
            )
            self._enabled = False
            self._client = None

    # ---------------------------------------------------------------------------
    # API pública — guardado
    # ---------------------------------------------------------------------------

    def upload_documento_fuente(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
    ) -> dict[str, str]:
        """Guarda el documento fuente original localmente y en OCI (si está activo).

        El objeto se almacena bajo el prefijo 'documentos/' con el document_id
        como nombre base y la extension original del archivo (p.ej.
        'documentos/<document_id>.pdf').

        Args:
            file_bytes: Contenido binario del archivo recibido.
            file_name: Nombre original del archivo (se usa para extraer la extensión).
            document_id: UUID de la tarea/documento (garantiza unicidad).

        Returns:
            dict con 'status' ('ok' o 'fallido'), 'objeto_id' y metadatos del guardado.
        """
        extension = Path(file_name).suffix  # incluye el punto, p.ej. '.pdf'
        object_name = f"documentos/{document_id}{extension}"

        # 1. Persistencia local
        local_ok = False
        try:
            target_path = self._docs_dir / f"{document_id}{extension}"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(file_bytes)
            local_ok = True
            logger.info("Documento fuente guardado localmente: %s (%d bytes)", target_path, len(file_bytes))
        except Exception as exc:
            logger.error("Error al guardar documento fuente localmente: %s", exc)

        # 2. Persistencia en OCI si está habilitado
        oci_status = "deshabilitado"
        if self._enabled and self._client is not None:
            try:
                self._client.upload_object(object_name=object_name, data=file_bytes)
                oci_status = "ok"
                logger.info("Documento fuente subido a OCI: objeto=%s size=%d bytes", object_name, len(file_bytes))
            except Exception as exc:
                oci_status = "fallido"
                logger.error("Error al subir documento fuente a OCI: objeto=%s error=%s", object_name, exc)

        if not local_ok and oci_status != "ok":
            return {"status": "fallido", "mensaje": "Fallo al guardar en local y en OCI."}

        res: dict[str, str] = {"status": "ok", "objeto_id": object_name}
        if oci_status != "ok":
            res["almacenamiento_oci"] = oci_status
        return res

    def upload_paquete_educativo(
        self,
        package_dict: dict,
        document_id: str,
        perfil: str,
        formato: str,
    ) -> dict[str, str]:
        """Guarda el paquete educativo generado localmente y en OCI (si está activo).

        El objeto se almacena bajo el prefijo 'paquetes/' con el document_id,
        perfil (sanitizado), formato y timestamp como nombre:
        'paquetes/<id>_<perfil>_<formato>_<ts>.json'.

        Args:
            package_dict: Diccionario del paquete educativo generado por el pipeline.
            document_id: UUID de la tarea/documento (garantiza unicidad).
            perfil: Perfil del destinatario (tal cual viene del state).
            formato: Formato pedagógico (tal cual viene del state).

        Returns:
            dict con 'status' ('ok' o 'fallido'), 'objeto_id' y metadatos de persistencia.
        """
        # Sanitizar caracteres conflictivos en nombres de archivos (/ en 'Lider Tecnico/Arquitecto')
        safe_perfil = perfil.replace("/", "-")
        safe_formato = formato.replace("/", "-")
        timestamp = int(time.time())
        filename = f"{document_id}_{safe_perfil}_{safe_formato}_{timestamp}.json"
        object_name = f"paquetes/{filename}"
        data = json.dumps(package_dict, ensure_ascii=False, indent=2).encode("utf-8")

        # Guardar título generado por IA en metadata cache para listados rápidos
        titulo = (
            (package_dict.get("contenido_adaptado") or {}).get("titulo")
            or package_dict.get("titulo")
            or ""
        )
        if titulo:
            self._save_metadata_cache(object_name, str(titulo))
            # Cachear también con el perfil original si contenía slash para retrocompatibilidad
            if "/" in perfil:
                alt_obj = f"paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json"
                self._save_metadata_cache(alt_obj, str(titulo))

        # 1. Guardar localmente
        local_ok = False
        try:
            target_path = self._pkgs_dir / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(data)
            local_ok = True
            logger.info("Paquete educativo guardado localmente: %s (%d bytes)", target_path, len(data))
        except Exception as exc:
            logger.error("Error al guardar paquete educativo localmente: %s", exc)

        # 2. Subir a OCI si está habilitado
        oci_status = "deshabilitado"
        if self._enabled and self._client is not None:
            try:
                self._client.upload_object(object_name=object_name, data=data)
                oci_status = "ok"
                logger.info("Paquete educativo subido a OCI: objeto=%s size=%d bytes", object_name, len(data))
            except Exception as exc:
                oci_status = "fallido"
                logger.error("Error al subir paquete educativo a OCI: objeto=%s error=%s", object_name, exc)

        if not local_ok and oci_status != "ok":
            return {"status": "fallido", "mensaje": "Fallo al guardar en local y en OCI."}

        res: dict[str, str] = {
            "status": "ok",
            "objeto_id": object_name,
        }
        if oci_status == "ok":
            res["bucket"] = self._client.bucket_name
        else:
            res["almacenamiento_oci"] = oci_status
        return res

    # ---------------------------------------------------------------------------
    # API pública — listado y consulta
    # ---------------------------------------------------------------------------

    def _load_metadata_cache(self) -> dict[str, str]:
        """Carga el diccionario de títulos y metadatos cacheados localmente."""
        cache_file = Path("data/history_metadata.json")
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_metadata_cache(self, objeto_id: str, titulo: str) -> None:
        """Guarda un título asociado a un paquete en el archivo de caché local."""
        try:
            cache_file = Path("data/history_metadata.json")
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = self._load_metadata_cache()
            data[objeto_id] = titulo
            cache_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("No se pudo escribir en history_metadata.json: %s", exc)

    def _parse_package_metadata(self, object_name: str, cached_titles: dict[str, str]) -> dict | None:
        """Extrae metadata a partir del object_name y del caché de títulos."""
        try:
            base = object_name.replace("paquetes/", "").replace(".json", "")
            # Normalizar cualquier slash interno en subdirectorios
            base_flat = base.replace("\\", "/").replace("/", "-")
            parts = base_flat.rsplit("_", 3)
            if len(parts) != 4:
                return None
            document_id, perfil_raw, formato_raw, ts_str = parts
            fecha_epoch = int(ts_str)
            fecha_iso = datetime.datetime.fromtimestamp(
                fecha_epoch, tz=datetime.timezone.utc
            ).isoformat()

            # Restaurar perfil legible
            perfil = "Lider Tecnico/Arquitecto" if perfil_raw == "Lider Tecnico-Arquitecto" else perfil_raw
            formato = formato_raw

            # Buscar título en caché
            titulo = cached_titles.get(object_name)
            if not titulo and "/" in perfil:
                alt_obj = f"paquetes/{document_id}_{perfil}_{formato}_{ts_str}.json"
                titulo = cached_titles.get(alt_obj)
            if not titulo and perfil_raw != perfil:
                alt_obj = f"paquetes/{document_id}_{perfil_raw}_{formato}_{ts_str}.json"
                titulo = cached_titles.get(alt_obj)

            return {
                "objeto_id": object_name,
                "document_id": document_id,
                "perfil": perfil,
                "formato": formato,
                "fecha_epoch": fecha_epoch,
                "fecha_iso": fecha_iso,
                "titulo": titulo or f"{formato} — {perfil}",
            }
        except Exception as exc:
            logger.warning("Error al parsear metadata de objeto '%s': %s — omitido", object_name, exc)
            return None

    def list_paquetes(self) -> list[dict]:
        """Lista los paquetes educativos almacenados localmente y en OCI sin duplicados.

        Combina los archivos locales de 'data/storage/paquetes/' con los objetos en OCI.
        Desduplica estrictamente por la clave canónica 'objeto_id'.

        Returns:
            Lista de dicts con claves: objeto_id, document_id, perfil, formato,
            fecha_epoch (int), fecha_iso (str ISO 8601 UTC), titulo (str).
            Ordenada de más reciente a más antiguo.
        """
        cached_titles = self._load_metadata_cache()
        items_by_object_id: dict[str, dict] = {}

        # 1. Escanear paquetes en disco local (usar rglob por robustez)
        if self._pkgs_dir.exists():
            for file_path in self._pkgs_dir.rglob("*.json"):
                rel_path = file_path.relative_to(self._pkgs_dir).as_posix()
                object_name = f"paquetes/{rel_path}"
                item = self._parse_package_metadata(object_name, cached_titles)
                if item:
                    items_by_object_id[item["objeto_id"]] = item

        # 2. Consultar paquetes en OCI (si está habilitado)
        if self._enabled and self._client is not None:
            try:
                oci_objects = self._client.list_objects("paquetes/")
                for object_name in oci_objects:
                    # Desduplicación determinista: si ya está registrado desde local, no se duplica
                    if object_name not in items_by_object_id:
                        item = self._parse_package_metadata(object_name, cached_titles)
                        if item:
                            items_by_object_id[item["objeto_id"]] = item
            except Exception as exc:
                logger.error("Error al listar paquetes en OCI: error=%s", exc)

        generaciones = list(items_by_object_id.values())
        generaciones.sort(key=lambda g: g["fecha_epoch"], reverse=True)
        logger.info("Paquetes listados (híbrido): total=%d", len(generaciones))
        return generaciones

    def get_paquete(self, objeto_id: str) -> dict | None:
        """Descarga y parsea un paquete educativo (Local-First con fallback a OCI).

        Args:
            objeto_id: Nombre completo del objeto (e.g. 'paquetes/...json').

        Returns:
            Dict del paquete educativo parseado desde JSON, o None si no existe
            ni en local ni en OCI.
        """
        rel_path = objeto_id.replace("paquetes/", "") if objeto_id.startswith("paquetes/") else objeto_id
        local_file = self._pkgs_dir / rel_path

        # Si no existe directamente y rel_path tiene slash, probar con guión sanitizado
        if not local_file.exists() and "/" in rel_path:
            safe_rel = rel_path.replace("/", "-")
            if (self._pkgs_dir / safe_rel).exists():
                local_file = self._pkgs_dir / safe_rel

        # 1. Intentar leer desde local
        if local_file.exists():
            try:
                raw_bytes = local_file.read_bytes()
                paquete = json.loads(raw_bytes.decode("utf-8"))
                logger.info("Paquete educativo recuperado desde disco local: %s", local_file)
                titulo = (
                    (paquete.get("contenido_adaptado") or {}).get("titulo")
                    or paquete.get("titulo")
                    or ""
                )
                if titulo:
                    self._save_metadata_cache(objeto_id, str(titulo))
                return paquete
            except Exception as exc:
                logger.warning("Error al leer paquete local %s: %s", local_file, exc)

        # 2. Si no está en local, buscar en OCI si está habilitado
        if self._enabled and self._client is not None:
            try:
                raw_bytes = self._client.get_object(objeto_id)
                paquete = json.loads(raw_bytes.decode("utf-8"))
                logger.info("Paquete educativo descargado desde OCI: objeto=%s", objeto_id)
                # Guardar copia local en caché para lecturas futuras
                try:
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    local_file.write_bytes(raw_bytes)
                except Exception as exc:
                    logger.debug("No se pudo cachear paquete en local: %s", exc)

                titulo = (
                    (paquete.get("contenido_adaptado") or {}).get("titulo")
                    or paquete.get("titulo")
                    or ""
                )
                if titulo:
                    self._save_metadata_cache(objeto_id, str(titulo))
                return paquete
            except Exception as exc:
                logger.error("Error al descargar paquete desde OCI: objeto=%s error=%s", objeto_id, exc)

        return None

    # ---------------------------------------------------------------------------
    # Wrappers asíncronos y Sincronización hacia OCI
    # ---------------------------------------------------------------------------

    async def upload_documento_fuente_async(
        self,
        file_bytes: bytes,
        file_name: str,
        document_id: str,
    ) -> dict[str, str]:
        """Wrapper asíncrono de upload_documento_fuente."""
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

    def sync_pending_to_oci(self) -> dict[str, Any]:
        """Sincroniza archivos locales pendientes hacia OCI Object Storage.

        Sube todos los documentos y paquetes de data/storage/ que aún no existan
        en el bucket de OCI.
        """
        if not self._enabled or self._client is None:
            logger.info("sync_pending_to_oci omitido: OCI deshabilitado.")
            return {"status": "deshabilitado", "synced_docs": 0, "synced_pkgs": 0}

        try:
            oci_docs = set(self._client.list_objects("documentos/"))
            oci_pkgs = set(self._client.list_objects("paquetes/"))
        except Exception as exc:
            logger.error("sync_pending_to_oci: no se pudo listar objetos en OCI: %s", exc)
            return {"status": "fallido", "mensaje": str(exc), "synced_docs": 0, "synced_pkgs": 0}

        synced_docs = 0
        synced_pkgs = 0

        # Sincronizar documentos locales
        if self._docs_dir.exists():
            for doc_file in self._docs_dir.iterdir():
                if doc_file.is_file():
                    object_name = f"documentos/{doc_file.name}"
                    if object_name not in oci_docs:
                        try:
                            self._client.upload_object(object_name, doc_file.read_bytes())
                            synced_docs += 1
                            logger.info("Documento local sincronizado a OCI: %s", object_name)
                        except Exception as exc:
                            logger.warning("Fallo al sincronizar documento %s a OCI: %s", object_name, exc)

        # Sincronizar paquetes locales
        if self._pkgs_dir.exists():
            for pkg_file in self._pkgs_dir.rglob("*.json"):
                rel_path = pkg_file.relative_to(self._pkgs_dir).as_posix()
                object_name = f"paquetes/{rel_path}"
                if object_name not in oci_pkgs:
                    try:
                        self._client.upload_object(object_name, pkg_file.read_bytes())
                        synced_pkgs += 1
                        logger.info("Paquete local sincronizado a OCI: %s", object_name)
                    except Exception as exc:
                        logger.warning("Fallo al sincronizar paquete %s a OCI: %s", object_name, exc)

        logger.info(
            "sync_pending_to_oci finalizado: %d docs y %d paquetes sincronizados.",
            synced_docs,
            synced_pkgs,
        )
        return {
            "status": "ok",
            "synced_docs": synced_docs,
            "synced_pkgs": synced_pkgs,
        }

    async def sync_pending_to_oci_async(self) -> dict[str, Any]:
        """Wrapper asíncrono para sync_pending_to_oci."""
        return await asyncio.to_thread(self.sync_pending_to_oci)


# ---------------------------------------------------------------------------
# Instancia módulo-nivel (singleton de aplicación)
# ---------------------------------------------------------------------------

storage_service = StorageService(Settings())
