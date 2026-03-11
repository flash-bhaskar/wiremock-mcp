"""Application configuration via pydantic-settings with .env support."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """WireMock MCP server configuration.

    All settings can be overridden via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    wiremock_base_url: str = "http://localhost:8080"
    wiremock_timeout_seconds: int = 30
    wiremock_verify_ssl: bool = True
    personas_dir: str = ""
    log_level: str = "INFO"

    @property
    def personas_path(self) -> Path:
        """Resolve the personas library directory path."""
        if self.personas_dir:
            return Path(self.personas_dir)
        return Path(__file__).parent / "personas" / "library"

    @property
    def admin_url(self) -> str:
        """WireMock admin API base URL."""
        return f"{self.wiremock_base_url.rstrip('/')}/__admin"


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
