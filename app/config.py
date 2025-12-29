from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Класс для хранения настроек приложения."""

    DB_USER: str = "wallet_user"
    DB_PASSWORD: str = "wallet_password"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "wallet_db"

    TEST_DB_USER: str = "wallet_user"
    TEST_DB_PASSWORD: str = "wallet_password"
    TEST_DB_HOST: str = "test_db"
    TEST_DB_PORT: int = 5432
    TEST_DB_NAME: str = "wallet_test_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def TEST_DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.TEST_DB_USER}:"
            f"{self.TEST_DB_PASSWORD}@{self.TEST_DB_HOST}:"
            f"{self.TEST_DB_PORT}/{self.TEST_DB_NAME}"
        )

    PROJECT_NAME: str = "Wallet API"
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
