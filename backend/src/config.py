"""
config.py — Application settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./biochain.db"

    # Security / JWT
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Optimization
    solver_timeout: int = 300  # seconds
    milp_solver: str = "appsi_highs"  # Changed from cbc for Windows compatibility
    carbon_tax_default: float = 0.03  # USD / kg CO2e

    # CORS
    cors_origins: list[str] = ["*"]

    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env.example"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
