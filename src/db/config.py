from urllib.parse import quote_plus
from pydantic_settings import BaseSettings

"""
    Database secrets for a PostgreSQL database.
    Each variable in the host OS can be full uppercase or lowercase, doesn't matter.
    Default values will be overridden by cloud environment
"""

class Settings(BaseSettings):
    db_user: str = "app_encuestas_docente"
    db_password: str = "1234"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "analitica_educativa"

    @property
    def database_url(self) -> str:
        dialect = "postgresql"
        driver = "asyncpg"
        return f"{dialect}{'+' if driver else ''}{driver}://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}@{self.db_host}:{self.db_port}/{quote_plus(self.db_name)}"

    class Config:
        case_sensitive = False

settings = Settings()
