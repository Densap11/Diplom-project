from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    project_name: str = "Сервис внеучебной активности университета"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    media_prefix: str = "/media"
    upload_dir: str = "uploads"

    postgres_server: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_db: str = Field(default="activity_service")

    secret_key: str = Field(default="change-me")
    access_token_expire_minutes: int = Field(default=60)
    algorithm: str = Field(default="HS256")
    token_url: str = "/api/v1/auth/login"

    @property
    def database_url(self) -> str:
        credentials = self.postgres_user
        if self.postgres_password:
            credentials = f"{credentials}:{self.postgres_password}"
        return (
            "postgresql+psycopg://"
            f"{credentials}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
