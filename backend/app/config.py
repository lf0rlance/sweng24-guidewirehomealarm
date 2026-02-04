from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Backend settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS settings - can be a comma-separated string or list
    allowed_origins: str = "*"
    
    # Optional: if you want to expose the backend URL for logging/health checks
    backend_url: str = "http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Convert comma-separated origins to list"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

# Create a single instance to import everywhere
settings = Settings()