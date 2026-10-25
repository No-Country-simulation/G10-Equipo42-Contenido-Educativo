"""Tests para StorageService híbrido (Local-First y OCI Object Storage).

Cubre:
- Comportamiento Local-First cuando OCI está habilitado, deshabilitado o fallido.
- Resiliencia ante fallos de red en OCI (preservando el dato en local).
- Desduplicación determinista en list_paquetes() (local + OCI).
- Descarga optimizada get_paquete() (local-first con fallback y cacheo OCI).
- Sincronización automática sync_pending_to_oci().
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nuevamente.services.storage import StorageService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(
    bucket_name: str = "test-bucket",
    local_dir: Path | None = None,
) -> MagicMock:
    """Crea un mock de Settings con los campos OCI y local_storage_dir configurados."""
    settings = MagicMock()
    settings.oci_bucket_name = bucket_name
    settings.oci_namespace = "test-namespace"
    settings.oci_compartment_id = "test-compartment"
    settings.oci_config_file = "~/.oci/config"
    settings.oci_config_profile = "DEFAULT"
    if local_dir is not None:
        settings.local_storage_dir = local_dir
    else:
        import tempfile
        settings.local_storage_dir = Path(tempfile.gettempdir()) / "nuevamente_tests_isolated"
    return settings


def _make_storage_service(
    bucket_name: str = "test-bucket",
    local_dir: Path | None = None,
) -> StorageService:
    """Crea un StorageService con OCIStorageClient mockeado."""
    settings = _make_settings(bucket_name=bucket_name, local_dir=local_dir)
    with patch("nuevamente.services.storage.OCIStorageClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.bucket_name = bucket_name
        mock_client_cls.return_value = mock_client
        service = StorageService(settings)
    return service


# ---------------------------------------------------------------------------
# upload_documento_fuente — Local-First con OCI
# ---------------------------------------------------------------------------


class TestUploadDocumentoFuente:
    """Tests para StorageService.upload_documento_fuente."""

    def test_ok_hibrido(self, tmp_path: Path) -> None:
        """Estado 'ok': se guarda en disco local y se sube a OCI."""
        service = _make_storage_service(local_dir=tmp_path)
        assert service._enabled is True

        result = service.upload_documento_fuente(
            file_bytes=b"contenido pdf de prueba",
            file_name="documento.pdf",
            document_id="abc-123",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/abc-123.pdf"
        # Verificar guardado local
        local_file = tmp_path / "documentos" / "abc-123.pdf"
        assert local_file.exists()
        assert local_file.read_bytes() == b"contenido pdf de prueba"

        # Verificar upload a OCI
        service._client.upload_object.assert_called_once_with(
            object_name="documentos/abc-123.pdf",
            data=b"contenido pdf de prueba",
        )

    def test_oci_fallido_pero_local_ok(self, tmp_path: Path) -> None:
        """Si OCI falla, el guardado local tiene éxito y el resultado es 'ok' con advertencia OCI."""
        service = _make_storage_service(local_dir=tmp_path)
        service._client.upload_object.side_effect = RuntimeError("Timeout de red OCI")

        result = service.upload_documento_fuente(
            file_bytes=b"datos",
            file_name="archivo.txt",
            document_id="xyz-999",
        )

        assert result["status"] == "ok"
        assert result["almacenamiento_oci"] == "fallido"
        assert result["objeto_id"] == "documentos/xyz-999.txt"
        assert (tmp_path / "documentos" / "xyz-999.txt").exists()

    def test_oci_deshabilitado_local_ok(self, tmp_path: Path) -> None:
        """Sin OCI configurado, se guarda localmente con éxito."""
        settings = _make_settings(bucket_name="", local_dir=tmp_path)
        service = StorageService(settings)

        assert service._enabled is False

        result = service.upload_documento_fuente(
            file_bytes=b"datos",
            file_name="archivo.pdf",
            document_id="id-001",
        )

        assert result["status"] == "ok"
        assert result["almacenamiento_oci"] == "deshabilitado"
        assert result["objeto_id"] == "documentos/id-001.pdf"
        assert (tmp_path / "documentos" / "id-001.pdf").exists()

    def test_ok_extension_md(self, tmp_path: Path) -> None:
        """El object_name preserva la extension .md del archivo original."""
        service = _make_storage_service(local_dir=tmp_path)

        result = service.upload_documento_fuente(
            file_bytes=b"# Titulo",
            file_name="readme.md",
            document_id="doc-md-456",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/doc-md-456.md"
        assert (tmp_path / "documentos" / "doc-md-456.md").exists()

    def test_ok_sin_extension(self, tmp_path: Path) -> None:
        """Archivo sin extension: object_name termina sin punto."""
        service = _make_storage_service(local_dir=tmp_path)

        result = service.upload_documento_fuente(
            file_bytes=b"texto plano",
            file_name="documento",
            document_id="doc-noext-789",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/doc-noext-789"
        assert (tmp_path / "documentos" / "doc-noext-789").exists()


# ---------------------------------------------------------------------------
# upload_paquete_educativo — Local-First con OCI
# ---------------------------------------------------------------------------


class TestUploadPaqueteEducativo:
    """Tests para StorageService.upload_paquete_educativo."""

    def test_ok_hibrido(self, tmp_path: Path) -> None:
        """Estado 'ok': se guarda localmente y se sube a OCI."""
        service = _make_storage_service(bucket_name="mi-bucket", local_dir=tmp_path)
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

        # Verificar guardado local
        filename = result["objeto_id"].replace("paquetes/", "")
        local_file = tmp_path / "paquetes" / filename
        assert local_file.exists()
        saved_dict = json.loads(local_file.read_text(encoding="utf-8"))
        assert saved_dict["titulo"] == "Curso de Python"

    def test_oci_fallido_pero_local_ok(self, tmp_path: Path) -> None:
        """Si OCI falla, el paquete queda preservado en local."""
        service = _make_storage_service(local_dir=tmp_path)
        service._client.upload_object.side_effect = ConnectionError("OCI no disponible")

        result = service.upload_paquete_educativo(
            package_dict={"titulo": "Test Fallo OCI"},
            document_id="pkg-fail",
            perfil="profesional",
            formato="guia",
        )

        assert result["status"] == "ok"
        assert result["almacenamiento_oci"] == "fallido"
        filename = result["objeto_id"].replace("paquetes/", "")
        assert (tmp_path / "paquetes" / filename).exists()

    def test_oci_deshabilitado_local_ok(self, tmp_path: Path) -> None:
        """Sin OCI configurado, se guarda localmente y devuelve ok."""
        settings = _make_settings(bucket_name="", local_dir=tmp_path)
        service = StorageService(settings)

        result = service.upload_paquete_educativo(
            package_dict={"titulo": "Test Local Solo"},
            document_id="pkg-dis",
            perfil="basico",
            formato="resumen",
        )

        assert result["status"] == "ok"
        assert result["almacenamiento_oci"] == "deshabilitado"
        filename = result["objeto_id"].replace("paquetes/", "")
        assert (tmp_path / "paquetes" / filename).exists()

    def test_ok_clave_status_normalizada(self, tmp_path: Path) -> None:
        """Verifica que la clave de retorno es 'status' (no 'status_upload')."""
        service = _make_storage_service(local_dir=tmp_path)

        result = service.upload_paquete_educativo(
            package_dict={},
            document_id="clave-test",
            perfil="universitario",
            formato="modulo",
        )

        assert "status" in result
        assert "status_upload" not in result


# ---------------------------------------------------------------------------
# list_paquetes — Desduplicación Local + OCI
# ---------------------------------------------------------------------------


class TestListPaquetes:
    """Tests para StorageService.list_paquetes."""

    def test_list_solo_local(self, tmp_path: Path) -> None:
        """Lista paquetes desde disco local cuando OCI está deshabilitado."""
        settings = _make_settings(bucket_name="", local_dir=tmp_path)
        service = StorageService(settings)

        # Crear 2 paquetes locales
        pkgs_dir = tmp_path / "paquetes"
        (pkgs_dir / "doc1_universitario_Flashcards_1700000000.json").write_text(
            json.dumps({"titulo": "Flashcards 1"}), encoding="utf-8"
        )
        (pkgs_dir / "doc2_profesional_Quiz_1700000100.json").write_text(
            json.dumps({"titulo": "Quiz 2"}), encoding="utf-8"
        )

        items = service.list_paquetes()
        assert len(items) == 2
        assert items[0]["objeto_id"] == "paquetes/doc2_profesional_Quiz_1700000100.json"
        assert items[1]["objeto_id"] == "paquetes/doc1_universitario_Flashcards_1700000000.json"
        assert items[0]["fecha_epoch"] == 1700000100

    def test_list_desduplicacion_hibrida(self, tmp_path: Path) -> None:
        """Verifica que un paquete que existe en local y en OCI aparece UNA SOLA VEZ."""
        service = _make_storage_service(local_dir=tmp_path)

        # Paquete que existe en local Y en OCI
        pkg_ambos = "paquetes/doc1_universitario_Flashcards_1700000000.json"
        # Paquete solo en local
        pkg_local_solo = "paquetes/doc2_profesional_Quiz_1700000100.json"
        # Paquete solo en OCI
        pkg_oci_solo = "paquetes/doc3_escolar_Tutorial_1700000200.json"

        # Escribir locales
        pkgs_dir = tmp_path / "paquetes"
        (pkgs_dir / "doc1_universitario_Flashcards_1700000000.json").write_text("{}", encoding="utf-8")
        (pkgs_dir / "doc2_profesional_Quiz_1700000100.json").write_text("{}", encoding="utf-8")

        # Mock OCI list_objects
        service._client.list_objects.return_value = [pkg_ambos, pkg_oci_solo]

        items = service.list_paquetes()
        # Debe haber exactamente 3 (no 4)
        assert len(items) == 3

        ids = [it["objeto_id"] for it in items]
        assert ids.count(pkg_ambos) == 1
        assert pkg_local_solo in ids
        assert pkg_oci_solo in ids
        # Ordenado por fecha descendente
        assert items[0]["objeto_id"] == pkg_oci_solo
        assert items[1]["objeto_id"] == pkg_local_solo
        assert items[2]["objeto_id"] == pkg_ambos


# ---------------------------------------------------------------------------
# get_paquete — Local-First con fallback OCI
# ---------------------------------------------------------------------------


class TestGetPaquete:
    """Tests para StorageService.get_paquete."""

    def test_get_desde_local(self, tmp_path: Path) -> None:
        """Si existe en local, se lee de disco sin consultar OCI."""
        service = _make_storage_service(local_dir=tmp_path)
        pkgs_dir = tmp_path / "paquetes"
        filename = "doc1_perfil_formato_1700000000.json"
        (pkgs_dir / filename).write_text(json.dumps({"contenido": "local"}), encoding="utf-8")

        paquete = service.get_paquete(f"paquetes/{filename}")
        assert paquete is not None
        assert paquete["contenido"] == "local"
        service._client.get_object.assert_not_called()

    def test_get_fallback_oci_y_cachea(self, tmp_path: Path) -> None:
        """Si no existe en local, lo descarga de OCI y guarda copia local."""
        service = _make_storage_service(local_dir=tmp_path)
        objeto_id = "paquetes/remoto_perfil_formato_1700000000.json"
        service._client.get_object.return_value = json.dumps({"contenido": "desde oci"}).encode("utf-8")

        paquete = service.get_paquete(objeto_id)
        assert paquete is not None
        assert paquete["contenido"] == "desde oci"
        service._client.get_object.assert_called_once_with(objeto_id)

        # Verificar que se cacheó localmente
        local_file = tmp_path / "paquetes" / "remoto_perfil_formato_1700000000.json"
        assert local_file.exists()


# ---------------------------------------------------------------------------
# sync_pending_to_oci — Sincronización hacia OCI
# ---------------------------------------------------------------------------


class TestSyncPendingToOCI:
    """Tests para StorageService.sync_pending_to_oci."""

    def test_sync_sube_faltantes(self, tmp_path: Path) -> None:
        """Sube documentos y paquetes locales que no están aún en OCI."""
        service = _make_storage_service(local_dir=tmp_path)

        # Crear archivos locales
        docs_dir = tmp_path / "documentos"
        pkgs_dir = tmp_path / "paquetes"
        (docs_dir / "doc1.pdf").write_bytes(b"pdf data")
        (pkgs_dir / "pkg1.json").write_bytes(b"{}")

        # OCI bucket vacío
        service._client.list_objects.side_effect = lambda prefix: []

        res = service.sync_pending_to_oci()
        assert res["status"] == "ok"
        assert res["synced_docs"] == 1
        assert res["synced_pkgs"] == 1

        service._client.upload_object.assert_any_call("documentos/doc1.pdf", b"pdf data")
        service._client.upload_object.assert_any_call("paquetes/pkg1.json", b"{}")

    def test_sync_omite_ya_existentes(self, tmp_path: Path) -> None:
        """No sube archivos que ya existen en OCI."""
        service = _make_storage_service(local_dir=tmp_path)
        docs_dir = tmp_path / "documentos"
        (docs_dir / "doc_existente.pdf").write_bytes(b"pdf data")

        service._client.list_objects.side_effect = lambda prefix: ["documentos/doc_existente.pdf"]

        res = service.sync_pending_to_oci()
        assert res["status"] == "ok"
        assert res["synced_docs"] == 0
        service._client.upload_object.assert_not_called()

    def test_sync_deshabilitado(self, tmp_path: Path) -> None:
        """Si OCI está deshabilitado, sync retorna status 'deshabilitado' sin error."""
        settings = _make_settings(bucket_name="", local_dir=tmp_path)
        service = StorageService(settings)

        res = service.sync_pending_to_oci()
        assert res["status"] == "deshabilitado"
        assert res["synced_docs"] == 0


# ---------------------------------------------------------------------------
# upload_documento_fuente_async
# ---------------------------------------------------------------------------


class TestUploadDocumentoFuenteAsync:
    """Tests para el wrapper asincrono upload_documento_fuente_async."""

    @pytest.mark.asyncio
    async def test_ok_async(self, tmp_path: Path) -> None:
        """El wrapper asincrono delega correctamente al metodo sincrono."""
        service = _make_storage_service(local_dir=tmp_path)

        result = await service.upload_documento_fuente_async(
            file_bytes=b"bytes async",
            file_name="async_doc.pdf",
            document_id="async-001",
        )

        assert result["status"] == "ok"
        assert result["objeto_id"] == "documentos/async-001.pdf"
        assert (tmp_path / "documentos" / "async-001.pdf").exists()


# ---------------------------------------------------------------------------
# Inicializacion con fallo del cliente OCI
# ---------------------------------------------------------------------------


class TestStorageServiceInit:
    """Tests para el comportamiento de inicializacion de StorageService."""

    def test_init_fallo_cliente_deja_deshabilitado(self, tmp_path: Path) -> None:
        """Si OCIStorageClient falla en __init__, el servicio opera en modo local."""
        settings = _make_settings(bucket_name="bucket-valido", local_dir=tmp_path)
        with patch(
            "nuevamente.services.storage.OCIStorageClient",
            side_effect=RuntimeError("No se encontro ~/.oci/config"),
        ):
            service = StorageService(settings)

        assert service._enabled is False
        assert service._client is None

        # Al fallar OCI, sigue funcionando en modo local
        result = service.upload_documento_fuente(b"contenido", "f.pdf", "id-x")
        assert result["status"] == "ok"
        assert result["almacenamiento_oci"] == "deshabilitado"
        assert (tmp_path / "documentos" / "id-x.pdf").exists()

    def test_bucket_name_propiedad_publica(self) -> None:
        """Verifica que bucket_name es accesible como propiedad publica en OCIStorageClient."""
        from nuevamente.infra.oci import OCIStorageClient

        assert isinstance(OCIStorageClient.bucket_name, property)
