import os
from pathlib import Path
import tempfile

from dotenv import load_dotenv


def test_load_dotenv_precedence(monkeypatch, tmp_path):
    # Ensure env var in os.environ takes precedence over .env file
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # Set an environment variable that should win
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env-value")

    # Create a .env file with a different value
    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-dotenv-value"')

    # Load using load_dotenv with override=False (should not override existing env)
    load_dotenv(dotenv_path=str(env_file), override=False)

    assert os.getenv("OPENROUTER_API_KEY") == "sk-env-value"


def test_load_dotenv_when_no_env(monkeypatch, tmp_path):
    # Ensure that when env var is not present, .env provides the value
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-dotenv-value"')

    load_dotenv(dotenv_path=str(env_file), override=False)

    assert os.getenv("OPENROUTER_API_KEY") == "sk-dotenv-value"
