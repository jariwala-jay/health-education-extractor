#!/usr/bin/env python3
"""
Utility script to identify and clean up duplicate health articles.
This script helps identify existing duplicates in the database and provides options to remove them.
"""

import asyncio
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_database, close_database
from app.models.health_article import HealthArticle
from app.services.duplicate_detector import DuplicateDetector
from app.services.gemini_summarizer import SummarizedContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DuplicateCleanup:
    """Utility class for cleaning up duplicate articles."""
    
    def __init__(self):
        self.duplicate_detector = DuplicateDetector()
    
    async def find_all_duplicates(self) -> Dict[str, List[Tuple[str, float]]]:
        """Find all duplicate articles in the database.
        
        Returns:
            Dictionary mapping article_id to list of similar articles
        """
        logger.info("Finding all duplicate articles...")
        
        # Get all articles
        articles = await HealthArticle.find().to_list()
        logger.info(f"Checking {len(articles)} articles for duplicates")
        
        duplicates_map = {}
        processed_pairs = set()
        
        for i, article in enumerate(articles):
            logger.info(f"Processing article {i+1}/{len(articles)}: {article.title}")
            
            # Convert to SummarizedContent for duplicate checking
            summarized_content = SummarizedContent(
                title=article.title,
                category=article.category,
                content=article.content,
                medical_condition_tags=article.medical_condition_tags,
                source_chunk_id=f"existing_{article.id}"
            )
            
            # Check for duplicates
            duplicates = await self.duplicate_detector.check_for_duplicates(summarized_content)
            
            if duplicates:
                # Filter out self-matches and already processed pairs
                filtered_duplicates = []
                for dup_id, score in duplicates:
                    if dup_id != str(article.id):
                        pair = tuple(sorted([str(article.id), dup_id]))
                        if pair not in processed_pairs:
                            filtered_duplicates.append((dup_id, score))
                            processed_pairs.add(pair)
                
                if filtered_duplicates:
                    duplicates_map[str(article.id)] = filtered_duplicates
        
        return duplicates_map
    
    async def group_duplicates(self) -> List[List[str]]:
        """Group duplicate articles into clusters.
        
        Returns:
            List of duplicate groups (each group is a list of article IDs)
        """
        duplicates_map = await self.find_all_duplicates()
        
        # Build graph of duplicates
        graph = defaultdict(set)
        for article_id, duplicates in duplicates_map.items():
            for dup_id, _ in duplicates:
                graph[article_id].add(dup_id)
                graph[dup_id].add(article_id)
        
        # Find connected components (duplicate groups)
        visited = set()
        duplicate_groups = []
        
        for article_id in graph:
            if article_id not in visited:
                group = []
                stack = [article_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        group.append(current)
                        stack.extend(graph[current] - visited)
                
                if len(group) > 1:
                    duplicate_groups.append(group)
        
        return duplicate_groups
    
    async def analyze_duplicates(self):
        """Analyze and report on duplicate articles."""
        logger.info("=== DUPLICATE ANALYSIS REPORT ===")
        
        duplicate_groups = await self.group_duplicates()
        
        if not duplicate_groups:
            logger.info("✅ No duplicate groups found!")
            return
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups:")
        
        total_duplicates = 0
        for i, group in enumerate(duplicate_groups, 1):
            logger.info(f"\n--- Duplicate Group {i} ({len(group)} articles) ---")
            total_duplicates += len(group) - 1  # All but one are duplicates
            
            # Get article details
            articles = []
            for article_id in group:
                try:
                    article = await HealthArticle.get(article_id)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error retrieving article {article_id}: {e}")
            
            # Sort by creation date (keep oldest)
            articles.sort(key=lambda x: x.created_at if x.created_at else x.id)
            
            for j, article in enumerate(articles):
                status = "KEEP" if j == 0 else "DUPLICATE"
                logger.info(f"  {status}: {article.id} - '{article.title}' ({article.processing_status})")
                logger.info(f"    Created: {article.created_at}")
                logger.info(f"    Category: {article.category}")
                logger.info(f"    Content preview: {article.content[:100]}...")
        
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Total articles: {await HealthArticle.count()}")
        logger.info(f"Duplicate groups: {len(duplicate_groups)}")
        logger.info(f"Articles to remove: {total_duplicates}")
        logger.info(f"Articles to keep: {await HealthArticle.count() - total_duplicates}")
    
    async def cleanup_duplicates(self, dry_run: bool = True):
        """Clean up duplicate articles by removing all but the oldest in each group.
        
        Args:
            dry_run: If True, only show what would be deleted without actually deleting
        """
        logger.info(f"=== DUPLICATE CLEANUP ({'DRY RUN' if dry_run else 'LIVE RUN'}) ===")
        
        duplicate_groups = await self.group_duplicates()
        
        if not duplicate_groups:
            logger.info("✅ No duplicates to clean up!")
            return
        
        deleted_count = 0
        
        for i, group in enumerate(duplicate_groups, 1):
            logger.info(f"\n--- Processing Group {i} ---")
            
            # Get article details
            articles = []
            for article_id in group:
                try:
                    article = await HealthArticle.get(article_id)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error retrieving article {article_id}: {e}")
            
            if len(articles) < 2:
                continue
            
            # Sort by creation date (keep oldest), then by processing status (prefer approved)
            articles.sort(key=lambda x: (
                x.created_at if x.created_at else x.id,
                0 if x.processing_status == 'approved' else 1
            ))
            
            # Keep the first article, delete the rest
            keep_article = articles[0]
            delete_articles = articles[1:]
            
            logger.info(f"  ✅ KEEPING: {keep_article.id} - '{keep_article.title}'")
            
            for article in delete_articles:
                logger.info(f"  ❌ DELETING: {article.id} - '{article.title}'")
                
                if not dry_run:
                    try:
                        await article.delete()
                        deleted_count += 1
                        logger.info(f"    ✅ Deleted successfully")
                    except Exception as e:
                        logger.error(f"    ❌ Error deleting: {e}")
                else:
                    deleted_count += 1
        
        logger.info(f"\n=== CLEANUP SUMMARY ===")
        if dry_run:
            logger.info(f"Would delete {deleted_count} duplicate articles")
            logger.info("Run with --live to actually perform the cleanup")
        else:
            logger.info(f"Successfully deleted {deleted_count} duplicate articles")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up duplicate health articles")
    parser.add_argument('--analyze', action='store_true', help='Analyze and report duplicates')
    parser.add_argument('--cleanup', action='store_true', help='Clean up duplicates (dry run)')
    parser.add_argument('--live', action='store_true', help='Actually delete duplicates (use with --cleanup)')
    
    args = parser.parse_args()
    
    if not (args.analyze or args.cleanup):
        parser.print_help()
        return
    
    # Initialize database
    await init_database()
    
    try:
        cleanup = DuplicateCleanup()
        
        if args.analyze:
            await cleanup.analyze_duplicates()
        
        if args.cleanup:
            await cleanup.cleanup_duplicates(dry_run=not args.live)
    
    finally:
        # Close database
        await close_database()


if __name__ == "__main__":
    asyncio.run(main()) 