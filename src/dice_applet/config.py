from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    secret_key: str
    teacher_password_hash: str
    allowed_origins: str = "https://www.klaasvogel.nl"
    log_level: str = "INFO"

    @property
    def origins_list(self) -> list[str]:
        """Return allowed_origins as a list of trimmed origin strings."""
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
