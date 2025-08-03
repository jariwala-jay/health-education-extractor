"""Service for uploading approved articles to the app database."""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from bson import ObjectId

from app.config import settings
from app.models.health_article import HealthArticle
from app.models.app_article import AppArticle, AppArticleCreate

logger = logging.getLogger(__name__)


class AppDatabaseUploader:
    """Service for uploading articles to the app database."""
    
    def __init__(self):
        self.app_client: Optional[AsyncIOMotorClient] = None
        self.app_database = None
        self._initialized = False
    
    async def init_app_database(self):
        """Initialize connection to the app database."""
        if self._initialized:
            return
            
        try:
            # Create motor client for app database
            self.app_client = AsyncIOMotorClient(
                settings.app_mongodb_url,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            
            # Test connection
            await self.app_client.admin.command('ping')
            logger.info(f"Connected to app database at {settings.app_mongodb_url}")
            
            # Get app database
            self.app_database = self.app_client[settings.app_mongodb_db_name]
            
            # Initialize Beanie with app models
            await init_beanie(
                database=self.app_database,
                document_models=[AppArticle]
            )
            
            self._initialized = True
            logger.info("App database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to app database: {e}")
            raise
    
    async def close_app_database(self):
        """Close app database connection."""
        if self.app_client:
            self.app_client.close()
            logger.info("App database connection closed")
    
    async def upload_article(self, health_article: HealthArticle) -> Optional[str]:
        """
        Upload a health article to the app database.
        
        Args:
            health_article: The approved HealthArticle to upload
            
        Returns:
            The ID of the created AppArticle, or None if failed
        """
        if not self._initialized:
            await self.init_app_database()
        
        try:
            # Check if article already exists in app database
            existing_article = await AppArticle.find_one({"title": health_article.title})
            if existing_article:
                logger.warning(f"Article already exists in app database: {health_article.title}")
                return str(existing_article.id)
            
            # Convert HealthArticle to AppArticle format
            app_article_data = AppArticleCreate(
                title=health_article.title,
                category=health_article.category.value,  # Convert enum to string
                imageUrl=health_article.image_url or "",  # Ensure not None
                medicalConditionTags=health_article.medical_condition_tags,  # Map medical condition tags
                content=health_article.content
            )
            
            # Create and save AppArticle
            app_article = AppArticle(**app_article_data.dict())
            await app_article.insert()
            
            logger.info(f"Successfully uploaded article to app database: {app_article.title} (ID: {app_article.id})")
            return str(app_article.id)
            
        except Exception as e:
            logger.error(f"Failed to upload article to app database: {e}")
            return None
    
    async def update_article(self, app_article_id: str, health_article: HealthArticle) -> bool:
        """
        Update an existing article in the app database.
        
        Args:
            app_article_id: The ID of the AppArticle to update
            health_article: The updated HealthArticle data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._initialized:
            await self.init_app_database()
        
        try:
            app_article = await AppArticle.get(app_article_id)
            if not app_article:
                logger.warning(f"App article not found for update: {app_article_id}")
                return False
            
            # Update fields
            app_article.title = health_article.title
            app_article.category = health_article.category.value
            app_article.imageUrl = health_article.image_url or ""
            app_article.medicalConditionTags = health_article.medical_condition_tags
            app_article.content = health_article.content
            app_article.updated_at = health_article.updated_at
            
            await app_article.save()
            
            logger.info(f"Successfully updated article in app database: {app_article.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update article in app database: {e}")
            return False
    
    async def delete_article(self, app_article_id: str) -> bool:
        """
        Delete an article from the app database.
        
        Args:
            app_article_id: The ID of the AppArticle to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._initialized:
            await self.init_app_database()
        
        try:
            app_article = await AppArticle.get(app_article_id)
            if not app_article:
                logger.warning(f"App article not found for deletion: {app_article_id}")
                return False
            
            await app_article.delete()
            logger.info(f"Successfully deleted article from app database: {app_article.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete article from app database: {e}")
            return False


# Global instance
app_uploader = AppDatabaseUploader() 