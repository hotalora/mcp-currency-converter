import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch, tmp_path):
    """Set minimal env vars so pydantic-settings doesn't fail."""
    monkeypatch.setenv("LLM_SECRET_NAME", "llm-secret")
    monkeypatch.setenv("LLM_SECRET_FIELD", "api_key")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("MODEL_NAME", "gpt-4o-mini")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("OTEL_ENABLED", "false")
    monkeypatch.setenv("LOGGER_LEVEL", "DEBUG")
    monkeypatch.setenv("TIMEZONE", "America/Bogota")
    monkeypatch.setenv("AGENT_INSTRUCTIONS", "You are helpful.")
    # Crear .env vacío para que BaseSettings no falle
    env_dir = tmp_path / "application" / "settings"
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / ".env").write_text("")
    yield
