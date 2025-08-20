from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_STR: str = "/api"
    PREFIX: str = ""

    # Databases
    DB_URL: str
    DBISAM_DB_URL: str | None = None

    # Security / Files
    JWT_SECRET: str
    FILES_PATH: str = "/data/files"

    # ZATCA Integration
    ZATCA_ENDPOINT: AnyHttpUrl | None = None
    ZATCA_CLIENT_ID: str | None = None
    ZATCA_CLIENT_SECRET: str | None = None
    ZATCA_CERT_B64: str | None = None
    ZATCA_PRIVATE_KEY_B64: str | None = None

    # Store metadata
    STORE_NAME: str | None = None
    STORE_ADDRESS: str | None = None
    STORE_VAT_NUMBER: str | None = None

    class Config:
        env_file = ".env"

Config = Settings()