from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 5000

    allowed_origins: str = "*"

    # Optional override (only set via .env)
    backend_url: Optional[str] = None
    
    # Google OAuth
    google_client_id: Optional[str] = None
    jwt_secret: Optional[str] = None
    
    # Database
    database_password: Optional[str] = None
    database_host: str = "localhost"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

settings = Settings()