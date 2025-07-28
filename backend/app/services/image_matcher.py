"""Unsplash API integration for finding relevant images for health articles."""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    """Represents an image search result."""
    id: str
    url: str
    thumbnail_url: str
    description: Optional[str]
    alt_description: Optional[str]
    author: str
    author_url: str
    download_url: str
    width: int
    height: int
    relevance_score: float = 0.0


class UnsplashImageMatcher:
    """Service for finding relevant images using Unsplash API."""
    
    def __init__(self):
        """Initialize Unsplash image matcher."""
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"
        self.per_page = 10  # Number of images to fetch per search
        
        # Health-related search terms for different categories
        self.category_search_terms = {
            'Hypertension': [
                'blood pressure monitor', 'healthy heart', 'medical checkup',
                'stethoscope', 'blood pressure cuff'
            ],
            'Diabetes': [
                'blood glucose meter', 'healthy food', 'diabetes testing',
                'insulin pen', 'blood sugar', 'diabetic care'
            ],
            'Nutrition': [
                'healthy food', 'fresh vegetables', 'balanced diet',
                'nutritious meal', 'fruits vegetables', 'healthy eating'
            ],
            'Physical Activity': [
                'exercise fitness', 'walking outdoors', 'gym workout',
                'yoga stretching', 'running jogging', 'active lifestyle'
            ],
            'General Health': [
                'healthy lifestyle', 'wellness concept', 'medical care',
                'health checkup', 'preventive care', 'health and wellness'
            ]
        }
        
        # Fallback search terms
        self.fallback_terms = [
            'health and wellness', 'medical care', 'healthy lifestyle',
            'doctor patient', 'health concept', 'wellness'
        ]
    
    async def find_image_for_article(self, title: str, category: str, 
                                   medical_tags: List[str]) -> Optional[ImageResult]:
        """Find the most relevant image for a health article.
        
        Args:
            title: Article title
            category: Article category
            medical_tags: List of medical condition tags
            
        Returns:
            ImageResult object or None if no suitable image found
        """
        try:
            logger.info(f"Searching for image: title='{title}', category='{category}'")
            
            # Generate search queries
            search_queries = self._generate_search_queries(title, category, medical_tags)
            
            # Search for images using multiple queries
            best_image = None
            best_score = 0.0
            
            for query in search_queries:
                images = await self._search_images(query)
                if images:
                    # Score images based on relevance
                    scored_images = self._score_images(images, title, category, medical_tags)
                    
                    # Keep track of the best image
                    for image in scored_images:
                        if image.relevance_score > best_score:
                            best_image = image
                            best_score = image.relevance_score
            
            if best_image:
                logger.info(f"Found image: {best_image.id} with score {best_score:.2f}")
                return best_image
            else:
                logger.warning(f"No suitable image found for article: {title}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding image for article '{title}': {e}")
            return None
    
    def _generate_search_queries(self, title: str, category: str, 
                               medical_tags: List[str]) -> List[str]:
        """Generate search queries based on article content."""
        queries = []
        
        # Use category-specific search terms
        if category in self.category_search_terms:
            queries.extend(self.category_search_terms[category])
        
        # Extract keywords from title
        title_keywords = self._extract_keywords_from_title(title)
        if title_keywords:
            queries.append(title_keywords)
        
        # Use medical tags as search terms
        for tag in medical_tags[:3]:  # Use top 3 tags
            tag_query = tag.lower().replace('_', ' ')
            if tag_query not in queries:
                queries.append(tag_query)
        
        # Add fallback terms if we don't have enough queries
        if len(queries) < 3:
            queries.extend(self.fallback_terms[:3 - len(queries)])
        
        # Limit to top 5 queries to avoid too many API calls
        return queries[:5]
    
    def _extract_keywords_from_title(self, title: str) -> str:
        """Extract relevant keywords from article title."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'with', 'by', 'how', 'what', 'when', 'where', 'why'
        }
        
        words = title.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Join keywords for search
        return ' '.join(keywords[:4])  # Use top 4 keywords
    
    async def _search_images(self, query: str) -> List[ImageResult]:
        """Search for images using Unsplash API."""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    'query': query,
                    'per_page': self.per_page,
                    'orientation': 'landscape',  # Prefer landscape images
                    'content_filter': 'high',  # Filter out inappropriate content
                    'order_by': 'relevant'
                }
                
                headers = {
                    'Authorization': f'Client-ID {self.access_key}'
                }
                
                response = await client.get(
                    f"{self.base_url}/search/photos",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    images = self._parse_image_results(data.get('results', []))
                    logger.debug(f"Found {len(images)} images for query: {query}")
                    return images
                else:
                    logger.warning(f"Unsplash API error: {response.status_code} for query: {query}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching images for query '{query}': {e}")
            return []
    
    def _parse_image_results(self, results: List[Dict[str, Any]]) -> List[ImageResult]:
        """Parse Unsplash API response into ImageResult objects."""
        images = []
        
        for result in results:
            try:
                # Extract image information
                image = ImageResult(
                    id=result['id'],
                    url=result['urls']['regular'],
                    thumbnail_url=result['urls']['thumb'],
                    description=result.get('description'),
                    alt_description=result.get('alt_description'),
                    author=result['user']['name'],
                    author_url=result['user']['links']['html'],
                    download_url=result['links']['download'],
                    width=result['width'],
                    height=result['height']
                )
                
                images.append(image)
                
            except KeyError as e:
                logger.warning(f"Missing field in Unsplash result: {e}")
                continue
        
        return images
    
    def _score_images(self, images: List[ImageResult], title: str, 
                     category: str, medical_tags: List[str]) -> List[ImageResult]:
        """Score images based on relevance to the health article."""
        
        # Create a combined text for matching
        search_text = f"{title} {category} {' '.join(medical_tags)}".lower()
        
        for image in images:
            score = 0.0
            
            # Score based on description match
            if image.description:
                desc_lower = image.description.lower()
                score += self._calculate_text_match_score(search_text, desc_lower) * 0.4
            
            # Score based on alt description match
            if image.alt_description:
                alt_lower = image.alt_description.lower()
                score += self._calculate_text_match_score(search_text, alt_lower) * 0.3
            
            # Prefer images with good aspect ratios (not too narrow or wide)
            aspect_ratio = image.width / image.height if image.height > 0 else 1.0
            if 1.2 <= aspect_ratio <= 2.0:  # Good landscape ratio
                score += 0.1
            elif 0.8 <= aspect_ratio <= 1.2:  # Square-ish
                score += 0.05
            
            # Prefer higher resolution images
            total_pixels = image.width * image.height
            if total_pixels > 1000000:  # > 1MP
                score += 0.1
            elif total_pixels > 500000:  # > 0.5MP
                score += 0.05
            
            # Bonus for health-related keywords in descriptions
            health_keywords = [
                'health', 'medical', 'doctor', 'hospital', 'medicine',
                'wellness', 'care', 'treatment', 'healthy', 'fitness'
            ]
            
            combined_text = f"{image.description or ''} {image.alt_description or ''}".lower()
            health_matches = sum(1 for keyword in health_keywords if keyword in combined_text)
            score += min(health_matches * 0.05, 0.2)  # Max 0.2 bonus
            
            image.relevance_score = min(score, 1.0)  # Cap at 1.0
        
        # Sort by relevance score
        images.sort(key=lambda x: x.relevance_score, reverse=True)
        return images
    
    def _calculate_text_match_score(self, search_text: str, target_text: str) -> float:
        """Calculate how well target text matches search text."""
        if not search_text or not target_text:
            return 0.0
        
        search_words = set(search_text.split())
        target_words = set(target_text.split())
        
        # Calculate Jaccard similarity
        intersection = search_words.intersection(target_words)
        union = search_words.union(target_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    async def get_image_download_url(self, image_id: str) -> Optional[str]:
        """Get the download URL for an image and trigger download tracking.
        
        Args:
            image_id: Unsplash image ID
            
        Returns:
            Download URL or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Client-ID {self.access_key}'
                }
                
                response = await client.get(
                    f"{self.base_url}/photos/{image_id}/download",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('url')
                else:
                    logger.warning(f"Failed to get download URL for image {image_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting download URL for image {image_id}: {e}")
            return None
    
    def get_attribution_text(self, image: ImageResult) -> str:
        """Generate proper attribution text for an Unsplash image.
        
        Args:
            image: ImageResult object
            
        Returns:
            Attribution text
        """
        return f"Photo by {image.author} on Unsplash"
    
    def get_attribution_html(self, image: ImageResult) -> str:
        """Generate proper attribution HTML for an Unsplash image.
        
        Args:
            image: ImageResult object
            
        Returns:
            Attribution HTML
        """
        return (
            f'Photo by <a href="{image.author_url}?utm_source=health_education_extractor&utm_medium=referral">'
            f'{image.author}</a> on '
            f'<a href="https://unsplash.com/?utm_source=health_education_extractor&utm_medium=referral">Unsplash</a>'
        ) 