from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Database
    database_url: str = "postgresql+asyncpg://sisyphus:YOUR_DB_PASSWORD@localhost:5432/sisyphus"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # JWT
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30

    # LLM Configuration
    glm_api_key: str = ""
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm_model: str = "glm-4"
    default_llm_provider: str = "glm"


settings = Settings()
