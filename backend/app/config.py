"""Configuration settings for the Health Education Extractor."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Main application settings."""
    
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
    unsplash_secret_key: Optional[str] = None
    
    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    max_file_size_mb: int = 50
    chunk_size_words: int = 200
    
    # Processing Settings
    similarity_threshold: float = 0.70  # Lowered from 0.85 to catch more duplicates
    max_images_per_article: int = 1
    reading_level_target: int = 6
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 