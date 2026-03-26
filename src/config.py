"""Configuration management for FortiMonitor MCP Server."""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # FortiMonitor API Configuration
    fortimonitor_base_url: HttpUrl = Field(
        default="https://api2.panopta.com/v2",
        description="Base URL for FortiMonitor API",
    )
    fortimonitor_api_key: str = Field(
        ..., description="API key for FortiMonitor authentication"
    )

    # MCP Server Configuration
    mcp_server_name: str = Field(
        default="unofficial-fortimonitor-mcp", description="Name of the MCP server"
    )
    mcp_server_version: str = Field(
        default="0.1.0", description="Version of the MCP server"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # Schema Caching
    enable_schema_cache: bool = Field(default=True, description="Enable schema caching")
    schema_cache_dir: Path = Field(
        default=Path("cache/schemas"), description="Directory for cached schemas"
    )
    schema_cache_ttl: int = Field(
        default=86400, description="Schema cache TTL in seconds (default: 24 hours)"
    )

    # Optional: Rate Limiting
    rate_limit_requests: int = Field(
        default=100, description="Maximum requests per period"
    )
    rate_limit_period: int = Field(
        default=60, description="Rate limit period in seconds"
    )

    # Knowledge Base Configuration
    knowledge_base_path: Path = Field(
        default=Path("data/vectordb"),
        description="Path to the LanceDB vector store directory",
    )
    knowledge_embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model for embeddings",
    )
    knowledge_chunk_size: int = Field(
        default=800,
        description="Target chunk size in tokens for document splitting",
    )
    knowledge_chunk_overlap: int = Field(
        default=100,
        description="Overlap between consecutive chunks in tokens",
    )
    knowledge_auto_ingest: bool = Field(
        default=False,
        description="Auto-ingest documentation on first launch if store is empty",
    )
    knowledge_sources_file: Path = Field(
        default=Path("data/sources.yaml"),
        description="Path to the YAML file defining documentation sources",
    )

    # License Entitlements (optional, for utilization reporting)
    license_entitlements: Optional[str] = Field(
        default=None,
        description='JSON object mapping addon textkeys to licensed counts, e.g. {"instance.basic": 100, "instance.advanced": 50}',
    )

    @property
    def api_base_url(self) -> str:
        """Get API base URL as string."""
        return str(self.fortimonitor_base_url).rstrip("/")


def get_settings() -> Settings:
    """Get settings instance. Creates new instance each time for testing flexibility."""
    return Settings()


# Global settings instance - lazy loaded
_settings: Optional[Settings] = None


def get_global_settings() -> Settings:
    """Get global settings instance (lazy loaded)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings