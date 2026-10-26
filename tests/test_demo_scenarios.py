"""Tests unitarios y de validación para los escenarios de demostración (Story 4.1).

Verifica la existencia y extraibilidad de los documentos técnicos reales de prueba,
la validación estricta de schemas Pydantic sobre los paquetes generados y el
cumplimiento de las métricas de calidad pedagógica y anclaje a la fuente (SM-1, SM-2, SM-3).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nuevamente.core.models import FormatoPedagogico
from nuevamente.core.schemas import FORMATO_A_SCHEMA
from nuevamente.services.ingestion import extract_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DEMO_DIR = PROJECT_ROOT / "docs" / "demo-docs"
DEMOS_OUTPUT_DIR = PROJECT_ROOT / "docs" / "demos"


class TestDemoDocuments:
    """Verifica que los documentos reales de demostración estén disponibles y sean procesables."""

    @pytest.mark.parametrize(
        "filename,min_chars",
        [
            ("classes.txt", 10_000),
            ("langchain_vs_langgraph.md", 2_000),
            ("vision_general_oci_vcn.pdf", 5_000),
        ],
    )
    def test_demo_documents_exist_and_extractable(self, filename: str, min_chars: int):
        """Los 3 documentos deben existir en docs/demo-docs/ y extraer texto legible."""
        doc_path = DOCS_DEMO_DIR / filename
        assert doc_path.exists(), f"El archivo {filename} debe existir en {DOCS_DEMO_DIR}"

        content_bytes = doc_path.read_bytes()
        assert len(content_bytes) > 0, f"El archivo {filename} no debe estar vacío"

        extracted = extract_text(content_bytes, filename)
        assert len(extracted) >= min_chars, (
            f"El texto extraído de {filename} tiene {len(extracted)} caracteres, esperado >= {min_chars}"
        )


class TestDemoGeneratedPackages:
    """Valida los paquetes educativos JSON generados como evidencia de las demos."""

    def test_demo_scenarios_schema_and_quality(self):
        """Si existen paquetes en docs/demos/, validar schema Pydantic y anclaje >= 0.7."""
        if not DEMOS_OUTPUT_DIR.exists():
            pytest.skip("docs/demos aún no ha sido poblado por run_demo_scenarios.py")

        json_files = list(DEMOS_OUTPUT_DIR.glob("*.json"))
        if not json_files:
            pytest.skip("No hay archivos JSON en docs/demos/ para validar aún.")

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            formato = data.get("metadatos", {}).get("formato_generado")
            assert formato in FORMATO_A_SCHEMA, (
                f"Formato '{formato}' en {json_file.name} no está en FORMATO_A_SCHEMA"
            )

            schema_cls = FORMATO_A_SCHEMA[formato]
            # Validar con Pydantic (lanzará ValidationError si es inválido)
            validated = schema_cls.model_validate(data)
            assert validated.status in ("completed", "success")

            # Validar anclaje a la fuente (SM-3)
            score = validated.evaluacion_calidad.anclaje_fuente_score
            assert score >= 0.7, (
                f"{json_file.name}: anclaje_fuente_score={score:.2f} es menor al umbral requerido 0.70"
            )

            # Validar que existan items pedagógicos
            assert len(validated.contenido_adaptado.items) > 0, (
                f"{json_file.name} no contiene items en contenido_adaptado"
            )

    def test_profile_differentiation_principiante_vs_lider_tecnico(self):
        """Valida que los outputs de Principiante y Líder Técnico sean lingüística y estructuralmente distintos (SM-1)."""
        file_principiante = DEMOS_OUTPUT_DIR / "1a_classes_principiante_flashcards.json"
        file_lider = DEMOS_OUTPUT_DIR / "1b_classes_lider_tecnico_resumen.json"

        if not file_principiante.exists() or not file_lider.exists():
            pytest.skip("Uno o ambos escenarios 1A y 1B aún no se han ejecutado.")

        with open(file_principiante, "r", encoding="utf-8") as f:
            data_prin = json.load(f)
        with open(file_lider, "r", encoding="utf-8") as f:
            data_lider = json.load(f)

        assert "principiante" in data_prin["metadatos"]["perfil_aplicado"].lower()
        assert "lider" in data_lider["metadatos"]["perfil_aplicado"].lower()

        # Formatos distintos
        assert data_prin["metadatos"]["formato_generado"] == FormatoPedagogico.FLASHCARDS.value
        assert data_lider["metadatos"]["formato_generado"] == FormatoPedagogico.RESUMEN_EJECUTIVO.value

        # Títulos o contenidos diferenciados
        titulo_prin = data_prin["contenido_adaptado"].get("titulo", "").lower()
        titulo_lider = data_lider["contenido_adaptado"].get("titulo", "").lower()
        assert titulo_prin != titulo_lider
