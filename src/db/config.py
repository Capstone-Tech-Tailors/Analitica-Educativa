from urllib.parse import quote_plus
from pydantic_settings import BaseSettings

"""
    Database secrets for a PostgreSQL database.
    Each variable in the host OS can be full uppercase or lowercase, doesn't matter.
    Default values will be overridden by cloud environment
"""


class Settings(BaseSettings):
    postgres_user: str = "app_encuestas_docente"
    postgres_password: str = "1234"
    postgres_db: str = "analitica_educativa"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        dialect = "postgresql"
        driver = "asyncpg"
        return f"{dialect}{'+' if driver else ''}{driver}://{quote_plus(self.postgres_user)}:{quote_plus(self.postgres_password)}@{self.postgres_host}:{self.postgres_port}/{quote_plus(self.postgres_db)}"

    class Config:
        case_sensitive = False


settings = Settings()
