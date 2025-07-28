#!/usr/bin/env python3
"""
Migration script to update article categories to match the new CategoryEnum values.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Category mapping from old to new values
CATEGORY_MAPPING = {
    "Heart Health": "General Health",
    "Kidney Health": "General Health", 
    "Medication Management": "General Health",
    "Mental Health": "General Health",
    "Exercise": "Physical Activity"  # In case any old "Exercise" values exist
}

async def migrate_categories():
    """Migrate old category values to new ones."""
    
    # Connect to MongoDB with SSL configuration
    client = AsyncIOMotorClient(
        settings.mongodb_url,
        tls=True,
        tlsAllowInvalidCertificates=True,  # For development - allows self-signed certificates
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    db = client[settings.mongodb_db_name]
    collection = db.health_articles
    
    try:
        # Test connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        logger.info("Starting category migration...")
        
        total_updated = 0
        
        for old_category, new_category in CATEGORY_MAPPING.items():
            # Find articles with old category
            cursor = collection.find({"category": old_category})
            articles = await cursor.to_list(length=None)
            
            if articles:
                logger.info(f"Found {len(articles)} articles with category '{old_category}'")
                
                # Update all articles with this old category
                result = await collection.update_many(
                    {"category": old_category},
                    {"$set": {"category": new_category}}
                )
                
                logger.info(f"Updated {result.modified_count} articles from '{old_category}' to '{new_category}'")
                total_updated += result.modified_count
            else:
                logger.info(f"No articles found with category '{old_category}'")
        
        logger.info(f"Migration completed. Total articles updated: {total_updated}")
        
        # Verify the migration
        logger.info("Verifying migration...")
        for old_category in CATEGORY_MAPPING.keys():
            count = await collection.count_documents({"category": old_category})
            if count > 0:
                logger.warning(f"Still found {count} articles with old category '{old_category}'")
            else:
                logger.info(f"✓ No articles found with old category '{old_category}'")
        
        # Show current category distribution
        logger.info("Current category distribution:")
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        async for doc in collection.aggregate(pipeline):
            logger.info(f"  {doc['_id']}: {doc['count']} articles")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        client.close()

async def main():
    """Main function."""
    try:
        await migrate_categories()
        logger.info("Category migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 