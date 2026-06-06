import os
from typing import Any

from dotenv import load_dotenv


def test_load_dotenv_precedence(monkeypatch: Any, tmp_path: Any) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env-value")

    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-dotenv-value"')

    load_dotenv(dotenv_path=str(env_file), override=False)

    assert os.getenv("OPENROUTER_API_KEY") == "sk-env-value"


def test_load_dotenv_when_no_env(monkeypatch: Any, tmp_path: Any) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-dotenv-value"')

    load_dotenv(dotenv_path=str(env_file), override=False)

    assert os.getenv("OPENROUTER_API_KEY") == "sk-dotenv-value"
