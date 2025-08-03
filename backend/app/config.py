"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "health_education_extractor"

    # App Database Configuration (for published articles)
    # Uses same connection as main database but different database name
    app_mongodb_db_name: str = "test"

    @property
    def app_mongodb_url(self) -> str:
        """App database uses the same connection string as main database."""
        return self.mongodb_url

    # Google AI (Gemini) API
    gemini_api_key: str
    
    # Image APIs
    unsplash_access_key: str
    unsplash_secret_key: str
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    max_file_size_mb: int = 50
    chunk_size_words: int = 200
    
    # Processing Settings
    similarity_threshold: float = 0.85
    max_images_per_article: int = 1
    reading_level_target: int = 6
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Authentication Settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Admin User Configuration
    admin_username: str = "admin"
    admin_password: str = "admin123"  # Change this in production!
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings() 