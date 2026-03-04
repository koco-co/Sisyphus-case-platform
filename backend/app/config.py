from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://sisyphus:YOUR_DB_PASSWORD@localhost:5432/sisyphus"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 30


settings = Settings()
