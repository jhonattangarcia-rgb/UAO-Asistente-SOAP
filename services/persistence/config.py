"""Configuration loader for the SOAP persistence service.

Reads database connection settings from environment variables.
All values are validated at construction time to fail fast on
misconfiguration.
"""

from __future__ import annotations

from os import getenv

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Raised when a required configuration value is missing or invalid."""


class Config:
    """Configuration loader for the SOAP persistence service."""

    def __init__(self) -> None:
        """Initialize Config by loading required environment variables."""
        self.supabase_url: str = self._require("SUPABASE_URL")
        self.supabase_service_key: str = self._require("SUPABASE_SERVICE_KEY")

    @staticmethod
    def _require(name: str) -> str:
        """Read an environment variable, raising ConfigError if missing."""
        value = getenv(name)
        if not value:
            msg = f"Missing required environment variable: {name}. Ensure it is set in your .env file."
            raise ConfigError(msg)
        return value
