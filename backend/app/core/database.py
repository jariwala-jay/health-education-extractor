"""Database configuration and connection management."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from app.config import settings
from app.models.health_article import HealthArticle
from app.models.pdf_document import PDFDocument

logger = logging.getLogger(__name__)

# Global database client
db_client: Optional[AsyncIOMotorClient] = None


async def init_database():
    """Initialize database connection and Beanie ODM."""
    global db_client
    
    try:
        # Create motor client with SSL configuration for MongoDB Atlas
        db_client = AsyncIOMotorClient(
            settings.mongodb_url,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development - allows self-signed certificates
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        
        # Test connection
        await db_client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
        
        # Get database
        database = db_client[settings.mongodb_db_name]
        
        # Initialize Beanie with document models
        await init_beanie(
            database=database,
            document_models=[HealthArticle, PDFDocument]
        )
        
        logger.info("Beanie ODM initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_database():
    """Close database connection."""
    global db_client
    
    if db_client:
        db_client.close()
        logger.info("Database connection closed")


def get_database():
    """Get the current database instance."""
    if not db_client:
        raise RuntimeError("Database not initialized")
    return db_client[settings.mongodb_db_name] 