import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Gestione centralizzata delle configurazioni dell'applicazione.
    Legge automaticamente dal file .env nella radice del progetto.
    """
    
    APP_NAME: str = "Info.AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    TEMPERATURE: float = 0.2

    CHROMA_DB_DIR: Path = BASE_DIR / "data" / "chroma_db"
    DOCUMENTS_DIR: Path = BASE_DIR / "data" / "documents"


    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"  
    )


settings = Settings()

os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)