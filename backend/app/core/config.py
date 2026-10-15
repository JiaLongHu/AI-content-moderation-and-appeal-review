from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./backend/data/app.db"
    frontend_origin: str = "http://localhost:5173"
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    seed_default_password: SecretStr = SecretStr("")
    ai_api_base_url: str = ""
    ai_api_key: SecretStr = SecretStr("")
    ai_model: str = ""
    ai_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def require_jwt_secret(self) -> str:
        value = self.jwt_secret_key.get_secret_value()
        if not value:
            raise RuntimeError("JWT_SECRET_KEY must be set in the environment")
        return value

    def require_seed_password(self) -> str:
        value = self.seed_default_password.get_secret_value()
        if not value:
            raise RuntimeError("SEED_DEFAULT_PASSWORD must be set in the environment")
        return value

    def require_ai_config(self) -> tuple[str, str, str]:
        api_key = self.ai_api_key.get_secret_value()
        if not self.ai_api_base_url or not api_key or not self.ai_model:
            raise RuntimeError(
                "AI_API_BASE_URL, AI_API_KEY and AI_MODEL must be set in the environment"
            )
        return self.ai_api_base_url.rstrip("/"), api_key, self.ai_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
