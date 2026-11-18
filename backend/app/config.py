from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://fleet_admin:change_me_locally@localhost:5432/smart_fleet"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
