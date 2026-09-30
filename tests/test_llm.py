"""Tests unitarios para la infraestructura LLM y configuracion de API keys."""

import os
from unittest.mock import patch

import pytest
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI

from nuevamente.config import Settings
from nuevamente.infra.llm import get_llm


def test_get_llm_instantiation_with_settings_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que get_llm instancia ChatGoogleGenerativeAI pasando api_key de Settings sin ValidationError."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = Settings(google_api_key="test-key-12345")
    llm = get_llm(settings)

    assert isinstance(llm, ChatGoogleGenerativeAI)
    # En ChatGoogleGenerativeAI, google_api_key se almacena como SecretStr
    assert llm.google_api_key.get_secret_value() == "test-key-12345"


def test_get_llm_instantiation_with_environ_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que get_llm puede inicializarse si la API key esta en os.environ y google_api_key en Settings esta vacia."""
    monkeypatch.setenv("GOOGLE_API_KEY", "env-key-99999")

    settings = Settings(google_api_key="")
    llm = get_llm(settings)

    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.google_api_key.get_secret_value() == "env-key-99999"


def test_settings_model_post_init_sets_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que Settings sincroniza GOOGLE_API_KEY, GEMINI_API_KEY y VOYAGE_API_KEY en os.environ."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)

    settings = Settings(google_api_key="gkey-abc", voyage_api_key="vkey-xyz")

    assert os.environ.get("GOOGLE_API_KEY") == "gkey-abc"
    assert os.environ.get("GEMINI_API_KEY") == "gkey-abc"
    assert os.environ.get("VOYAGE_API_KEY") == "vkey-xyz"


def test_settings_model_post_init_preserves_existing_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que Settings no sobreescribe variables de entorno preexistentes (comportamiento setdefault)."""
    monkeypatch.setenv("GOOGLE_API_KEY", "original-google-key")
    monkeypatch.setenv("VOYAGE_API_KEY", "original-voyage-key")

    settings = Settings(google_api_key="nueva-google-key", voyage_api_key="nueva-voyage-key")

    assert os.environ.get("GOOGLE_API_KEY") == "original-google-key"
    assert os.environ.get("VOYAGE_API_KEY") == "original-voyage-key"
