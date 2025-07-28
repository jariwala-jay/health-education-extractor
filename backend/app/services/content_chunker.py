"""Content chunking service for breaking down PDF content into manageable pieces."""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ContentChunk:
    """Represents a chunk of content from a PDF."""
    chunk_id: str
    pdf_document_id: str
    page_number: int
    chunk_index: int
    content: str
    word_count: int
    is_relevant: bool = False
    relevance_score: Optional[float] = None
    chunk_type: str = "text"  # text, header, list, table
    medical_keywords: List[str] = None
    
    def __post_init__(self):
        if self.medical_keywords is None:
            self.medical_keywords = []


class ContentChunker:
    """Service for chunking PDF content into logical units."""
    
    def __init__(self, target_chunk_size: int = None):
        """Initialize content chunker.
        
        Args:
            target_chunk_size: Target word count per chunk (defaults to config setting)
        """
        self.target_chunk_size = target_chunk_size or settings.chunk_size_words
        self.min_chunk_size = max(50, self.target_chunk_size // 4)  # Minimum 50 words
        self.max_chunk_size = self.target_chunk_size * 2  # Allow up to 2x target size
        
        # Health-related keywords for relevance scoring
        self.health_keywords = {
            'conditions': [
                'diabetes', 'hypertension', 'blood pressure', 'heart disease',
                'kidney disease', 'chronic', 'condition', 'disease', 'disorder',
                'syndrome', 'illness', 'medical', 'health', 'clinical',
                'obesity', 'overweight', 'obese', 'weight gain', 'excess weight',
                'body mass index', 'bmi', 'morbid obesity', 'weight problem'
            ],
            'treatments': [
                'medication', 'medicine', 'treatment', 'therapy', 'prescription',
                'drug', 'dose', 'dosage', 'pills', 'tablets', 'injection',
                'weight loss surgery', 'bariatric surgery', 'gastric bypass',
                'weight management', 'weight loss program'
            ],
            'symptoms': [
                'symptoms', 'signs', 'pain', 'ache', 'fever', 'fatigue',
                'nausea', 'dizziness', 'shortness of breath', 'chest pain',
                'joint pain', 'back pain', 'sleep apnea', 'snoring'
            ],
            'lifestyle': [
                'diet', 'nutrition', 'exercise', 'physical activity', 'weight',
                'lifestyle', 'eating', 'food', 'salt', 'sodium', 'calories',
                'weight loss', 'healthy weight', 'portion control', 'portion size',
                'calorie counting', 'meal planning', 'healthy eating', 'balanced diet',
                'weight management', 'fitness', 'cardio', 'strength training'
            ],
            'care': [
                'doctor', 'physician', 'nurse', 'healthcare', 'hospital',
                'clinic', 'appointment', 'checkup', 'monitoring', 'care',
                'nutritionist', 'dietitian', 'weight counselor', 'fitness trainer',
                'weight loss specialist', 'endocrinologist'
            ]
        }
        
        # Flatten keywords for easy searching
        self.all_health_keywords = []
        for category in self.health_keywords.values():
            self.all_health_keywords.extend(category)
    
    def chunk_content(self, pdf_content, pdf_document_id: str) -> List[ContentChunk]:
        """Chunk PDF content into logical units.
        
        Args:
            pdf_content: PDFContent object from PDF parser
            pdf_document_id: ID of the source PDF document
            
        Returns:
            List of ContentChunk objects
        """
        chunks = []
        chunk_counter = 0
        
        logger.info(f"Starting content chunking for PDF {pdf_document_id}")
        
        for page in pdf_content.pages:
            page_chunks = self._chunk_page_content(
                page.text, 
                page.page_number, 
                pdf_document_id,
                chunk_counter
            )
            
            chunks.extend(page_chunks)
            chunk_counter += len(page_chunks)
            
            logger.debug(f"Page {page.page_number}: Created {len(page_chunks)} chunks")
        
        # Filter and score chunks for relevance
        relevant_chunks = self._filter_and_score_chunks(chunks)
        
        logger.info(f"Chunking completed: {len(chunks)} total chunks, {len(relevant_chunks)} relevant")
        return relevant_chunks
    
    def _chunk_page_content(self, text: str, page_number: int, 
                           pdf_document_id: str, start_chunk_index: int) -> List[ContentChunk]:
        """Chunk content from a single page."""
        if not text or len(text.strip()) < self.min_chunk_size:
            return []
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(cleaned_text)
        
        # Group paragraphs into chunks
        chunks = []
        current_chunk = ""
        current_word_count = 0
        chunk_index = start_chunk_index
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            # If adding this paragraph would exceed max size, finalize current chunk
            if (current_word_count + paragraph_words > self.max_chunk_size and 
                current_word_count >= self.min_chunk_size):
                
                if current_chunk.strip():
                    chunk = self._create_chunk(
                        current_chunk.strip(),
                        chunk_index,
                        page_number,
                        pdf_document_id
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                current_chunk = paragraph
                current_word_count = paragraph_words
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_word_count += paragraph_words
        
        # Add final chunk if it meets minimum size
        if current_chunk.strip() and current_word_count >= self.min_chunk_size:
            chunk = self._create_chunk(
                current_chunk.strip(),
                chunk_index,
                page_number,
                pdf_document_id
            )
            chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (simple heuristics)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip very short lines that might be page numbers or headers
            if len(line) < 10:
                continue
            
            # Skip lines that are mostly numbers (page numbers, etc.)
            if re.match(r'^\d+\s*$', line):
                continue
            
            # Skip lines that look like headers/footers
            if re.match(r'^(page|chapter|\d+)\s*\d*\s*$', line, re.IGNORECASE):
                continue
            
            cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into logical paragraphs."""
        # Split on double newlines first
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Further split very long paragraphs
        final_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If paragraph is very long, try to split on sentence boundaries
            words = para.split()
            if len(words) > self.target_chunk_size:
                sentences = re.split(r'[.!?]+\s+', para)
                current_para = ""
                current_words = 0
                
                for sentence in sentences:
                    sentence_words = len(sentence.split())
                    
                    if current_words + sentence_words > self.target_chunk_size and current_words > 0:
                        if current_para.strip():
                            final_paragraphs.append(current_para.strip())
                        current_para = sentence
                        current_words = sentence_words
                    else:
                        if current_para:
                            current_para += ". " + sentence
                        else:
                            current_para = sentence
                        current_words += sentence_words
                
                if current_para.strip():
                    final_paragraphs.append(current_para.strip())
            else:
                final_paragraphs.append(para)
        
        return final_paragraphs
    
    def _create_chunk(self, content: str, chunk_index: int, 
                     page_number: int, pdf_document_id: str) -> ContentChunk:
        """Create a ContentChunk object."""
        import uuid
        
        chunk_id = f"{pdf_document_id}_chunk_{chunk_index}"
        word_count = len(content.split())
        
        # Detect chunk type
        chunk_type = self._detect_chunk_type(content)
        
        # Extract medical keywords
        medical_keywords = self._extract_medical_keywords(content)
        
        return ContentChunk(
            chunk_id=chunk_id,
            pdf_document_id=pdf_document_id,
            page_number=page_number,
            chunk_index=chunk_index,
            content=content,
            word_count=word_count,
            chunk_type=chunk_type,
            medical_keywords=medical_keywords
        )
    
    def _detect_chunk_type(self, content: str) -> str:
        """Detect the type of content chunk."""
        # Check if it's a header (short, title-case, no ending punctuation)
        if (len(content.split()) <= 10 and 
            content.istitle() and 
            not content.endswith(('.', '!', '?'))):
            return "header"
        
        # Check if it's a list (contains bullet points or numbered items)
        if re.search(r'^\s*[•\-\*\d+\.\)]\s+', content, re.MULTILINE):
            return "list"
        
        # Check if it contains tabular data
        if '\t' in content or re.search(r'\s{3,}', content):
            return "table"
        
        return "text"
    
    def _extract_medical_keywords(self, content: str) -> List[str]:
        """Extract medical keywords from content."""
        content_lower = content.lower()
        found_keywords = []
        
        for keyword in self.all_health_keywords:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def _filter_and_score_chunks(self, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """Filter chunks for relevance and assign relevance scores."""
        relevant_chunks = []
        
        for chunk in chunks:
            relevance_score = self._calculate_relevance_score(chunk)
            chunk.relevance_score = relevance_score
            
            # Consider chunk relevant if it has a good relevance score
            if relevance_score >= 0.3:  # Threshold can be adjusted
                chunk.is_relevant = True
                relevant_chunks.append(chunk)
            
            logger.debug(f"Chunk {chunk.chunk_id}: relevance={relevance_score:.2f}, "
                        f"keywords={len(chunk.medical_keywords)}")
        
        return relevant_chunks
    
    def _calculate_relevance_score(self, chunk: ContentChunk) -> float:
        """Calculate relevance score based on health-related content."""
        if not chunk.content:
            return 0.0
        
        content_lower = chunk.content.lower()
        total_words = chunk.word_count
        
        if total_words == 0:
            return 0.0
        
        # Count keyword occurrences by category
        category_scores = {}
        for category, keywords in self.health_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            category_scores[category] = keyword_count / len(keywords)
        
        # Weight different categories
        weights = {
            'conditions': 0.3,
            'treatments': 0.25,
            'symptoms': 0.2,
            'lifestyle': 0.15,
            'care': 0.1
        }
        
        # Calculate weighted score
        weighted_score = sum(
            category_scores.get(category, 0) * weight 
            for category, weight in weights.items()
        )
        
        # Bonus for having multiple categories represented
        categories_present = sum(1 for score in category_scores.values() if score > 0)
        diversity_bonus = min(categories_present * 0.1, 0.3)
        
        # Penalty for very short chunks
        length_factor = min(total_words / self.min_chunk_size, 1.0)
        
        final_score = (weighted_score + diversity_bonus) * length_factor
        
        return min(final_score, 1.0)  # Cap at 1.0 