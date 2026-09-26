"""Configuracion centralizada del sistema NuevaMente.

Usa pydantic-settings para cargar variables de entorno con defaults sensatos.
Las variables se pueden configurar via archivo .env o variables de entorno del sistema.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion del sistema NuevaMente.

    Todas las variables tienen valores por defecto funcionales para desarrollo local.
    En produccion, se configuran via variables de entorno o archivo .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    google_api_key: str = ""
    llm_model_name: str = "google_genai:gemini-2.0-flash-lite"
    llm_temperature: float = 0.7
    llm_max_retries: int = 6

    # --- Embeddings ---
    voyage_api_key: str = ""
    embedding_model_name: str = "voyage-3-lite"

    # --- Chunking ---
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # --- RAG ---
    fast_path_token_threshold: int = 50_000
    retrieval_k: int = 10

    # --- FAISS ---
    faiss_index_dir: Path = Path("data/faiss_indexes")

    # --- OCI Object Storage ---
    oci_bucket_name: str = ""
    oci_namespace: str = ""
    oci_compartment_id: str = ""
    oci_config_file: Path = Path("~/.oci/config")
    oci_config_profile: str = "DEFAULT"

    # --- Servidor ---
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
