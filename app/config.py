from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Класс для хранения настроек приложения."""
    POSTGRES_USER: str = "wallet_user"
    POSTGRES_PASSWORD: str = "wallet_password"
    POSTGRES_DB: str = "wallet_db"
    POSTGRES_HOST: str = "localhost"  # Позже поменять на 'db' для Docker
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    PROJECT_NAME: str = "Wallet API"
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
