"""Tests para StorageService con mocks del SDK OCI.

Cubre los tres estados de cada metodo: ok, fallido, deshabilitado.
Ref: epic-2-retro-item-5 (action item open en sprint-status.yaml)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nuevamente.services.storage import StorageService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(bucket_name: str = "test-bucket") -> MagicMock:
    """Crea un mock de Settings con los campos OCI configurados."""
    settings = MagicMock()
    settings.oci_bucket_name = bucket_name
    settings.oci_namespace = "test-namespace"
    settings.oci_compartment_id = "test-compartment"
    settings.oci_config_file = "~/.oci/config"
    settings.oci_config_profile = "DEFAULT"
    return settings


def _make_storage_service(bucket_name: str = "test-bucket") -> StorageService:
    """Crea un StorageService con OCIStorageClient mockeado."""
    settings = _make_settings(bucket_name=bucket_name)
    with patch("nuevamente.services.storage.OCIStorageClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.bucket_name = bucket_name
        mock_client_cls.return_value = mock_client
        service = StorageService(settings)
    return service


# ---------------------------------------------------------------------------
# upload_documento_fuente — tres estados
# ---------------------------------------------------------------------------


class TestUploadDocumentoFuente:
    """Tests para StorageService.upload_documento_fuente."""

    def test_ok(self) -> None:
        """Estado 'ok': el upload al SDK no lanza excepcion."""
        service = _make_storage_service()
        assert service._enabled is True

        result = service.upload_documento_fuente(
            file_bytes=b"contenido pdf de prueba",
            file_name="documento.pdf",
            document_id="abc-123",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/abc-123.pdf"
        service._client.upload_object.assert_called_once_with(
            object_name="documentos/abc-123.pdf",
            data=b"contenido pdf de prueba",
        )

    def test_fallido(self) -> None:
        """Estado 'fallido': el SDK lanza una excepcion."""
        service = _make_storage_service()
        service._client.upload_object.side_effect = RuntimeError("Timeout de red OCI")

        result = service.upload_documento_fuente(
            file_bytes=b"datos",
            file_name="archivo.txt",
            document_id="xyz-999",
        )

        assert result["status"] == "fallido"
        assert "Timeout de red OCI" in result["mensaje"]

    def test_deshabilitado(self) -> None:
        """Estado 'deshabilitado': oci_bucket_name vacio en Settings."""
        settings = _make_settings(bucket_name="")
        service = StorageService(settings)

        assert service._enabled is False

        result = service.upload_documento_fuente(
            file_bytes=b"datos",
            file_name="archivo.pdf",
            document_id="id-001",
        )

        assert result == {"status": "deshabilitado"}

    def test_ok_extension_md(self) -> None:
        """El object_name preserva la extension .md del archivo original."""
        service = _make_storage_service()

        result = service.upload_documento_fuente(
            file_bytes=b"# Titulo",
            file_name="readme.md",
            document_id="doc-md-456",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/doc-md-456.md"

    def test_ok_sin_extension(self) -> None:
        """Archivo sin extension: object_name termina sin punto."""
        service = _make_storage_service()

        result = service.upload_documento_fuente(
            file_bytes=b"texto plano",
            file_name="documento",
            document_id="doc-noext-789",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/doc-noext-789"


# ---------------------------------------------------------------------------
# upload_paquete_educativo — tres estados
# ---------------------------------------------------------------------------


class TestUploadPaqueteEducativo:
    """Tests para StorageService.upload_paquete_educativo."""

    def test_ok(self) -> None:
        """Estado 'ok': el upload al SDK no lanza excepcion."""
        service = _make_storage_service(bucket_name="mi-bucket")
        paquete = {"titulo": "Curso de Python", "items": []}

        result = service.upload_paquete_educativo(
            package_dict=paquete,
            document_id="pkg-001",
            perfil="universitario",
            formato="modulo",
        )

        assert result["status"] == "ok"
        assert result["bucket"] == "mi-bucket"
        assert result["objeto_id"].startswith("paquetes/pkg-001_universitario_modulo_")
        assert result["objeto_id"].endswith(".json")
        service._client.upload_object.assert_called_once()

    def test_fallido(self) -> None:
        """Estado 'fallido': el SDK lanza una excepcion."""
        service = _make_storage_service()
        service._client.upload_object.side_effect = ConnectionError("OCI no disponible")

        result = service.upload_paquete_educativo(
            package_dict={"titulo": "Test"},
            document_id="pkg-fail",
            perfil="profesional",
            formato="guia",
        )

        assert result["status"] == "fallido"
        assert "OCI no disponible" in result["mensaje"]

    def test_deshabilitado(self) -> None:
        """Estado 'deshabilitado': oci_bucket_name vacio en Settings."""
        settings = _make_settings(bucket_name="")
        service = StorageService(settings)

        result = service.upload_paquete_educativo(
            package_dict={"titulo": "Test"},
            document_id="pkg-dis",
            perfil="basico",
            formato="resumen",
        )

        assert result == {"status": "deshabilitado"}

    def test_ok_clave_status_normalizada(self) -> None:
        """Verifica que la clave de retorno es 'status' (no 'status_upload') para consistencia."""
        service = _make_storage_service()

        result = service.upload_paquete_educativo(
            package_dict={},
            document_id="clave-test",
            perfil="universitario",
            formato="modulo",
        )

        assert "status" in result
        assert "status_upload" not in result, (
            "La clave 'status_upload' fue eliminada en epic-2-retro-item-3; "
            "ambos metodos deben usar 'status'."
        )

    def test_ok_upload_documento_clave_status_normalizada(self) -> None:
        """Verifica que upload_documento_fuente tambien usa 'status' (consistencia de interfaz)."""
        service = _make_storage_service()

        result = service.upload_documento_fuente(
            file_bytes=b"datos",
            file_name="doc.txt",
            document_id="clave-doc-test",
        )

        assert "status" in result
        assert "status_upload" not in result


# ---------------------------------------------------------------------------
# upload_documento_fuente_async — wrapper asincrono
# ---------------------------------------------------------------------------


class TestUploadDocumentoFuenteAsync:
    """Tests para el wrapper asincrono upload_documento_fuente_async."""

    @pytest.mark.asyncio
    async def test_ok_async(self) -> None:
        """El wrapper asincrono delega correctamente al metodo sincrono."""
        service = _make_storage_service()

        result = await service.upload_documento_fuente_async(
            file_bytes=b"bytes async",
            file_name="async_doc.pdf",
            document_id="async-001",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/async-001.pdf"

    @pytest.mark.asyncio
    async def test_fallido_async(self) -> None:
        """El wrapper asincrono captura excepciones y retorna status fallido."""
        service = _make_storage_service()
        service._client.upload_object.side_effect = Exception("Error critico OCI")

        result = await service.upload_documento_fuente_async(
            file_bytes=b"datos",
            file_name="error.pdf",
            document_id="async-fail",
        )

        assert result["status"] == "fallido"


# ---------------------------------------------------------------------------
# Inicializacion con fallo del cliente OCI
# ---------------------------------------------------------------------------


class TestStorageServiceInit:
    """Tests para el comportamiento de inicializacion de StorageService."""

    def test_init_fallo_cliente_deja_deshabilitado(self) -> None:
        """Si OCIStorageClient falla en __init__, el servicio queda deshabilitado."""
        settings = _make_settings(bucket_name="bucket-valido")
        with patch(
            "nuevamente.services.storage.OCIStorageClient",
            side_effect=RuntimeError("No se encontro ~/.oci/config"),
        ):
            service = StorageService(settings)

        assert service._enabled is False
        assert service._client is None

        # Debe retornar deshabilitado en lugar de lanzar excepcion
        result = service.upload_documento_fuente(b"", "f.pdf", "id-x")
        assert result == {"status": "deshabilitado"}

    def test_bucket_name_propiedad_publica(self) -> None:
        """Verifica que bucket_name es accesible como propiedad publica en OCIStorageClient."""
        from nuevamente.infra.oci import OCIStorageClient

        # Verifica que la propiedad existe en la clase (sin instanciar)
        assert isinstance(OCIStorageClient.bucket_name, property), (
            "bucket_name debe ser una propiedad publica en OCIStorageClient "
            "(epic-2-retro-item-4)"
        )
