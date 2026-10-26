"""Estado del grafo LangGraph para el pipeline de NuevaMente.

Define NuevaMenteState como TypedDict (no Pydantic, por rendimiento en LangGraph).
El pipeline es secuencial sin nodos paralelos, por lo que no se necesitan reducers.
"""

from typing import Any, TypedDict


class NuevaMenteState(TypedDict, total=False):
    """Estado compartido entre todos los nodos del grafo de procesamiento.

    Campos organizados en cuatro grupos:
    - Input: inmutables despues del inicio del pipeline
    - Pipeline intermedio: datos que fluyen entre nodos
    - Control de flujo: estado del loop de correccion
    - Output: resultado final del pipeline

    total=False permite que los campos intermedios y de output
    no esten presentes al inicio del pipeline.
    """

    # --- Input (inmutable post-ingest) ---
    document_id: str
    raw_text: str
    file_name: str
    perfil: str
    formato: str
    nicho: str

    # --- Pipeline intermedio ---
    chunks: list[dict[str, Any]]
    section_map: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    generated_content: dict[str, Any]

    # --- Control de flujo ---
    review_result: dict[str, Any]
    retry_count: int

    # --- Output ---
    educational_package: dict[str, Any]
    oci_upload_status: dict[str, Any]
