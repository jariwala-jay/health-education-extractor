#!/usr/bin/env python3
"""
Database cleanup utility for clearing all data from the health education extractor.
This script can clear health articles, PDFs, and uploaded files.

WARNING: This will permanently delete data. Use with caution!
"""

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_database, close_database
from app.models.health_article import HealthArticle
from app.models.pdf_document import PDFDocument
from app.models.app_article import AppArticle
from app.models.daily_tip import DailyTip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseCleaner:
    """Utility class for cleaning up the database and files."""
    
    def __init__(self, uploads_dir: str = "data/uploads"):
        self.uploads_dir = Path(uploads_dir)
    
    async def get_database_stats(self) -> dict:
        """Get current database statistics."""
        try:
            health_articles_count = await HealthArticle.count()
            pdf_documents_count = await PDFDocument.count()
            app_articles_count = await AppArticle.count()
            daily_tips_count = await DailyTip.count()
            
            return {
                "health_articles": health_articles_count,
                "pdf_documents": pdf_documents_count,
                "app_articles": app_articles_count,
                "daily_tips": daily_tips_count,
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    async def clear_health_articles(self, dry_run: bool = True) -> int:
        """Clear all health articles from the database.
        
        Args:
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of articles deleted/would be deleted
        """
        try:
            count = await HealthArticle.count()
            logger.info(f"Found {count} health articles")
            
            if not dry_run and count > 0:
                # Delete all health articles
                result = await HealthArticle.delete_all()
                logger.info(f"Deleted {result.deleted_count} health articles")
                return result.deleted_count
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing health articles: {e}")
            return 0
    
    async def clear_pdf_documents(self, dry_run: bool = True) -> int:
        """Clear all PDF documents from the database and file system.
        
        Args:
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of PDFs deleted/would be deleted
        """
        try:
            pdfs = await PDFDocument.find().to_list()
            count = len(pdfs)
            logger.info(f"Found {count} PDF documents")
            
            if not dry_run and count > 0:
                deleted_files = 0
                
                # Delete files from file system
                for pdf in pdfs:
                    if pdf.file_path and os.path.exists(pdf.file_path):
                        try:
                            os.remove(pdf.file_path)
                            deleted_files += 1
                            logger.info(f"Deleted file: {pdf.file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting file {pdf.file_path}: {e}")
                
                # Delete database records
                result = await PDFDocument.delete_all()
                logger.info(f"Deleted {result.deleted_count} PDF documents from database")
                logger.info(f"Deleted {deleted_files} files from file system")
                
                return result.deleted_count
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing PDF documents: {e}")
            return 0
    
    async def clear_app_articles(self, dry_run: bool = True) -> int:
        """Clear all app articles from the database.
        
        Args:
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of app articles deleted/would be deleted
        """
        try:
            count = await AppArticle.count()
            logger.info(f"Found {count} app articles")
            
            if not dry_run and count > 0:
                result = await AppArticle.delete_all()
                logger.info(f"Deleted {result.deleted_count} app articles")
                return result.deleted_count
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing app articles: {e}")
            return 0
    
    async def clear_daily_tips(self, dry_run: bool = True) -> int:
        """Clear all daily tips from the database.
        
        Args:
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of daily tips deleted/would be deleted
        """
        try:
            count = await DailyTip.count()
            logger.info(f"Found {count} daily tips")
            
            if not dry_run and count > 0:
                result = await DailyTip.delete_all()
                logger.info(f"Deleted {result.deleted_count} daily tips")
                return result.deleted_count
            
            return count
            
        except Exception as e:
            logger.error(f"Error clearing daily tips: {e}")
            return 0
    
    
    def clear_upload_directory(self, dry_run: bool = True) -> int:
        """Clear all files from the uploads directory.
        
        Args:
            dry_run: If True, only count what would be deleted
            
        Returns:
            Number of files deleted/would be deleted
        """
        try:
            if not self.uploads_dir.exists():
                logger.info(f"Uploads directory {self.uploads_dir} does not exist")
                return 0
            
            files = list(self.uploads_dir.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            
            logger.info(f"Found {file_count} files in uploads directory")
            
            if not dry_run and file_count > 0:
                deleted_count = 0
                for file_path in files:
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.error(f"Error deleting file {file_path}: {e}")
                
                # Remove empty directories
                for dir_path in sorted([f for f in files if f.is_dir()], reverse=True):
                    try:
                        if not any(dir_path.iterdir()):  # Directory is empty
                            dir_path.rmdir()
                    except Exception:
                        pass  # Ignore errors when removing directories
                
                logger.info(f"Deleted {deleted_count} files from uploads directory")
                return deleted_count
            
            return file_count
            
        except Exception as e:
            logger.error(f"Error clearing upload directory: {e}")
            return 0
    
    async def clear_all(self, dry_run: bool = True):
        """Clear all data from the database and file system.
        
        Args:
            dry_run: If True, only show what would be deleted
        """
        logger.info(f"=== DATABASE CLEANUP ({'DRY RUN' if dry_run else 'LIVE RUN'}) ===")
        
        # Get initial stats
        stats = await self.get_database_stats()
        logger.info(f"Current database stats: {stats}")
        
        # Clear each collection
        health_articles_deleted = await self.clear_health_articles(dry_run)
        pdf_documents_deleted = await self.clear_pdf_documents(dry_run)
        app_articles_deleted = await self.clear_app_articles(dry_run)
        daily_tips_deleted = await self.clear_daily_tips(dry_run)

        # Clear upload files
        files_deleted = self.clear_upload_directory(dry_run)
        
        # Summary
        logger.info(f"\n=== CLEANUP SUMMARY ===")
        action = "Would delete" if dry_run else "Deleted"
        logger.info(f"{action} {health_articles_deleted} health articles")
        logger.info(f"{action} {pdf_documents_deleted} PDF documents")
        logger.info(f"{action} {app_articles_deleted} app articles")
        logger.info(f"{action} {daily_tips_deleted} daily tips")
        logger.info(f"{action} {files_deleted} uploaded files")
        
        if dry_run:
            logger.info("\nRun with --live to actually perform the cleanup")
        else:
            logger.info("\n✅ Cleanup completed successfully!")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear all data from the health education extractor")
    parser.add_argument('--live', action='store_true', 
                       help='Actually delete data (default is dry run)')
    parser.add_argument('--uploads-dir', default='data/uploads',
                       help='Path to uploads directory (default: data/uploads)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show database statistics')
    
    args = parser.parse_args()
    
    # Initialize database
    await init_database()
    
    try:
        cleaner = DatabaseCleaner(uploads_dir=args.uploads_dir)
        
        if args.stats_only:
            stats = await cleaner.get_database_stats()
            logger.info("=== DATABASE STATISTICS ===")
            for collection, count in stats.items():
                logger.info(f"{collection}: {count}")
        else:
            # Confirm if not dry run
            if args.live:
                logger.warning("⚠️  WARNING: This will permanently delete all data!")
                response = input("Are you sure you want to continue? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Cancelled by user")
                    return
            
            await cleaner.clear_all(
                dry_run=not args.live, 
            )
    
    finally:
        # Close database
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
