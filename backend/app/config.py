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
    
    # Summarization Settings
    summarization_mode: str = "chunk"  # chunk, map_reduce, full
    chunk_overlap_words: int = 25  # Reduced overlap to minimize duplication
    max_chunk_size_words: int = 300  # Smaller chunks for more focused content
    max_articles_per_pdf: int = 25  # Limit articles per PDF to prevent overwhelming output
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Authentication Settings
    secret_key: str  # Required - must be set via environment variable
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Admin User Configuration
    admin_username: str = "admin"
    admin_password: str  # Required - must be set via environment variable
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings() 