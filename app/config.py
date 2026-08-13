import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from a local .env file into the os environment
load_dotenv()


class Settings(BaseSettings):
    """
    Application Configuration Settings.
    Uses Pydantic BaseSettings to define, validate, and manage global environment variables.
    """
    PROJECT_NAME: str = "E_Library Management System"

    # ___ Security & Authentication ___
    # The cryptographic key used to sign JWT access tokens. Loaded securely from .env.
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    # Hashing algorithm used for JWT encoding/decoding.
    ALGORITHM: str = "HS256"
    # Token lifespan before the user is required to log in again (set to 24 hours)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ___ External API Integrations (LLM Gateway) ___
    # The base endpoint for the Userfacet AI proxy service.
    AI_API_BASE_URL: str = "https://ai-api.userfacet.com"
    # Secure API token injected via environment variables.
    AI_API_TOKEN: str = os.getenv("MY_API_TOKEN")

    # ___ Database Configuration ___
    # Connection string for the local SQLite database, utilizing aiosqlite for asynchronous I/O.
    DATABASE_URL: str = "sqlite+aiosqlite:///./elibrary.db"


# Instantiate the settings globally so it can be imported and used across the application routers and services
settings = Settings()