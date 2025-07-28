"""Duplicate detection service for preventing duplicate health articles."""

import logging
from typing import List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib

from app.config import settings
from app.models.health_article import HealthArticle
from app.services.gemini_summarizer import SummarizedContent

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Service for detecting duplicate health articles using text similarity."""
    
    def __init__(self, similarity_threshold: float = None):
        """Initialize duplicate detector.
        
        Args:
            similarity_threshold: Threshold for considering articles as duplicates
        """
        # Lower the default threshold to catch more similar content
        self.similarity_threshold = similarity_threshold or max(0.65, settings.similarity_threshold * 0.75)
        
        # Title similarity threshold (more strict for titles)
        self.title_similarity_threshold = 0.8
        
        # Initialize TF-IDF vectorizer with better parameters for duplicate detection
        self.vectorizer = TfidfVectorizer(
            max_features=2000,  # Increased vocabulary size
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 3),  # Use unigrams, bigrams, and trigrams
            min_df=1,  # Minimum document frequency
            max_df=0.9,  # Maximum document frequency
            token_pattern=r'\b\w+\b'  # Better tokenization
        )
        
        # Cache for existing articles and their vectors
        self._article_cache = {}
        self._vector_cache = None
        self._cache_dirty = True
        
        logger.info(f"DuplicateDetector initialized with threshold: {self.similarity_threshold:.2f}")
    
    async def check_for_duplicates(self, new_content: SummarizedContent) -> List[Tuple[str, float]]:
        """Check if new content is similar to existing articles.
        
        Args:
            new_content: SummarizedContent object to check
            
        Returns:
            List of tuples (article_id, similarity_score) for potential duplicates
        """
        try:
            logger.info(f"Checking for duplicates: '{new_content.title}'")
            
            # Get existing articles from database
            existing_articles = await self._get_existing_articles()
            
            if not existing_articles:
                logger.info("No existing articles found - no duplicates possible")
                return []
            
            # First check for title-based duplicates (faster)
            title_duplicates = self._check_title_similarity(new_content, existing_articles)
            if title_duplicates:
                logger.warning(f"Found title-based duplicates for '{new_content.title}'")
                return title_duplicates
            
            # Then check for content-based duplicates
            content_duplicates = await self._check_content_similarity(new_content, existing_articles)
            
            # Combine and deduplicate results
            all_duplicates = {}
            for article_id, score in content_duplicates:
                all_duplicates[article_id] = max(all_duplicates.get(article_id, 0), score)
            
            # Filter by threshold and sort
            final_duplicates = [
                (article_id, score) for article_id, score in all_duplicates.items()
                if score >= self.similarity_threshold
            ]
            final_duplicates.sort(key=lambda x: x[1], reverse=True)
            
            if final_duplicates:
                logger.warning(f"Found {len(final_duplicates)} potential duplicates for '{new_content.title}'")
                for article_id, score in final_duplicates[:3]:  # Log top 3
                    logger.warning(f"  - Article {article_id}: {score:.3f} similarity")
            else:
                logger.info(f"No duplicates found for '{new_content.title}' (threshold: {self.similarity_threshold:.2f})")
            
            return final_duplicates
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return []
    
    def _check_title_similarity(self, new_content: SummarizedContent, 
                               existing_articles: List[HealthArticle]) -> List[Tuple[str, float]]:
        """Check for title-based duplicates using string similarity.
        
        Args:
            new_content: New content to check
            existing_articles: List of existing articles
            
        Returns:
            List of tuples (article_id, similarity_score) for title duplicates
        """
        title_duplicates = []
        new_title = new_content.title.lower().strip()
        
        for article in existing_articles:
            existing_title = article.title.lower().strip()
            
            # Calculate string similarity using difflib
            similarity = difflib.SequenceMatcher(None, new_title, existing_title).ratio()
            
            # Also check if one title is contained in the other (for variations)
            if len(new_title) > 10 and len(existing_title) > 10:
                if new_title in existing_title or existing_title in new_title:
                    similarity = max(similarity, 0.85)
            
            # Check for very similar titles with different punctuation/formatting
            clean_new = ''.join(c.lower() for c in new_title if c.isalnum() or c.isspace()).strip()
            clean_existing = ''.join(c.lower() for c in existing_title if c.isalnum() or c.isspace()).strip()
            
            if clean_new == clean_existing:
                similarity = 1.0
            elif clean_new and clean_existing:
                clean_similarity = difflib.SequenceMatcher(None, clean_new, clean_existing).ratio()
                similarity = max(similarity, clean_similarity)
            
            if similarity >= self.title_similarity_threshold:
                title_duplicates.append((str(article.id), similarity))
                logger.info(f"Title similarity found: '{new_title}' vs '{existing_title}' = {similarity:.3f}")
        
        return sorted(title_duplicates, key=lambda x: x[1], reverse=True)
    
    async def _check_content_similarity(self, new_content: SummarizedContent,
                                      existing_articles: List[HealthArticle]) -> List[Tuple[str, float]]:
        """Check for content-based duplicates using TF-IDF similarity.
        
        Args:
            new_content: New content to check
            existing_articles: List of existing articles
            
        Returns:
            List of tuples (article_id, similarity_score) for content duplicates
        """
        # Prepare text for comparison
        new_text = self._prepare_text_for_comparison(new_content)
        
        # Get similarity scores
        similar_articles = await self._find_similar_articles(new_text, existing_articles)
        
        return similar_articles
    
    async def _get_existing_articles(self) -> List[HealthArticle]:
        """Get all existing articles from the database."""
        try:
            # Get all articles except rejected ones
            articles = await HealthArticle.find({
                "processing_status": {"$ne": "rejected"}
            }).to_list()
            
            logger.debug(f"Retrieved {len(articles)} existing articles for duplicate checking")
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving existing articles: {e}")
            return []
    
    def _prepare_text_for_comparison(self, content: SummarizedContent) -> str:
        """Prepare text content for similarity comparison.
        
        Args:
            content: SummarizedContent object
            
        Returns:
            Prepared text string
        """
        # Combine title (weighted more), content, and tags for comprehensive comparison
        text_parts = [
            content.title + " " + content.title,  # Weight title more heavily
            content.content,
            ' '.join(content.medical_condition_tags)
        ]
        
        # Clean and join text
        combined_text = ' '.join(part for part in text_parts if part)
        
        # Basic text cleaning
        cleaned_text = self._clean_text(combined_text)
        return cleaned_text
    
    def _prepare_article_text(self, article: HealthArticle) -> str:
        """Prepare existing article text for comparison.
        
        Args:
            article: HealthArticle object
            
        Returns:
            Prepared text string
        """
        text_parts = [
            article.title + " " + article.title,  # Weight title more heavily
            article.content,
            ' '.join(article.medical_condition_tags)
        ]
        
        combined_text = ' '.join(part for part in text_parts if part)
        cleaned_text = self._clean_text(combined_text)
        return cleaned_text
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better comparison.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Normalize common health terms and abbreviations
        text = re.sub(r'\bdash\b', 'dietary approaches to stop hypertension', text)
        text = re.sub(r'\bhbp\b', 'high blood pressure', text)
        text = re.sub(r'\bbp\b', 'blood pressure', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', ' ', text)
        
        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _find_similar_articles(self, new_text: str, 
                                   existing_articles: List[HealthArticle]) -> List[Tuple[str, float]]:
        """Find articles similar to the new text.
        
        Args:
            new_text: Text of the new article
            existing_articles: List of existing articles
            
        Returns:
            List of tuples (article_id, similarity_score)
        """
        if not existing_articles:
            return []
        
        try:
            # Prepare existing article texts
            existing_texts = []
            article_ids = []
            
            for article in existing_articles:
                article_text = self._prepare_article_text(article)
                if article_text:  # Only include non-empty texts
                    existing_texts.append(article_text)
                    article_ids.append(str(article.id))
            
            if not existing_texts:
                return []
            
            # Combine all texts for vectorization
            all_texts = existing_texts + [new_text]
            
            # Vectorize texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Calculate similarities between new text and existing texts
            new_vector = tfidf_matrix[-1]  # Last vector is the new text
            existing_vectors = tfidf_matrix[:-1]  # All but the last vector
            
            # Calculate cosine similarities
            similarities = cosine_similarity(new_vector, existing_vectors).flatten()
            
            # Create result list
            similar_articles = []
            for i, similarity in enumerate(similarities):
                if i < len(article_ids):  # Safety check
                    similar_articles.append((article_ids[i], float(similarity)))
            
            # Sort by similarity score (highest first)
            similar_articles.sort(key=lambda x: x[1], reverse=True)
            
            # Log top similarities for debugging
            if similar_articles:
                logger.debug(f"Top similarities: {similar_articles[:3]}")
            
            return similar_articles
            
        except Exception as e:
            logger.error(f"Error calculating similarities: {e}")
            return []
    
    async def is_duplicate(self, new_content: SummarizedContent) -> bool:
        """Check if new content is a duplicate of existing articles.
        
        Args:
            new_content: SummarizedContent object to check
            
        Returns:
            True if duplicate found, False otherwise
        """
        duplicates = await self.check_for_duplicates(new_content)
        return len(duplicates) > 0
    
    async def get_most_similar_article(self, new_content: SummarizedContent) -> Optional[Tuple[HealthArticle, float]]:
        """Get the most similar existing article.
        
        Args:
            new_content: SummarizedContent object to check
            
        Returns:
            Tuple of (most_similar_article, similarity_score) or None
        """
        try:
            similar_articles = await self.check_for_duplicates(new_content)
            
            if not similar_articles:
                return None
            
            # Get the most similar article
            most_similar_id, highest_score = similar_articles[0]
            
            # Retrieve the article from database
            article = await HealthArticle.get(most_similar_id)
            if article:
                return (article, highest_score)
            else:
                logger.warning(f"Could not retrieve article {most_similar_id} from database")
                return None
                
        except Exception as e:
            logger.error(f"Error getting most similar article: {e}")
            return None
    
    def get_similarity_explanation(self, similarity_score: float) -> str:
        """Get a human-readable explanation of the similarity score.
        
        Args:
            similarity_score: Similarity score between 0 and 1
            
        Returns:
            Human-readable explanation
        """
        if similarity_score >= 0.9:
            return "Very high similarity - likely duplicate"
        elif similarity_score >= 0.8:
            return "High similarity - possible duplicate"
        elif similarity_score >= 0.7:
            return "Moderate similarity - review recommended"
        elif similarity_score >= 0.5:
            return "Some similarity - minor overlap"
        else:
            return "Low similarity - likely unique content"
    
    async def batch_check_duplicates(self, contents: List[SummarizedContent]) -> List[List[Tuple[str, float]]]:
        """Check multiple contents for duplicates in batch.
        
        Args:
            contents: List of SummarizedContent objects to check
            
        Returns:
            List of duplicate lists for each content
        """
        results = []
        
        logger.info(f"Batch checking {len(contents)} articles for duplicates")
        
        for i, content in enumerate(contents):
            try:
                duplicates = await self.check_for_duplicates(content)
                results.append(duplicates)
                
                logger.debug(f"Article {i+1}/{len(contents)}: {len(duplicates)} duplicates found")
                
            except Exception as e:
                logger.error(f"Error checking duplicates for article {i+1}: {e}")
                results.append([])  # Empty list for failed checks
        
        logger.info(f"Batch duplicate check completed")
        return results
    
    def update_similarity_threshold(self, new_threshold: float):
        """Update the similarity threshold for duplicate detection.
        
        Args:
            new_threshold: New threshold value (0.0 to 1.0)
        """
        if 0.0 <= new_threshold <= 1.0:
            self.similarity_threshold = new_threshold
            logger.info(f"Updated similarity threshold to {new_threshold}")
        else:
            logger.warning(f"Invalid threshold value: {new_threshold}. Must be between 0.0 and 1.0")
    
    def clear_cache(self):
        """Clear the internal cache of articles and vectors."""
        self._article_cache.clear()
        self._vector_cache = None
        self._cache_dirty = True
        logger.info("Duplicate detector cache cleared") 