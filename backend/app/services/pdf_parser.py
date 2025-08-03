"""PDF parsing service using PyMuPDF."""

import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    """Represents a page extracted from PDF."""
    page_number: int
    text: str
    word_count: int
    has_images: bool
    images: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]


@dataclass
class PDFContent:
    """Complete extracted PDF content."""
    filename: str
    total_pages: int
    pages: List[ExtractedPage]
    metadata: Dict[str, Any]
    total_word_count: int


class PDFParser:
    """PDF parsing service."""
    
    def __init__(self, min_word_count: int = 10):
        """Initialize PDF parser.
        
        Args:
            min_word_count: Minimum word count to consider a page meaningful
        """
        self.min_word_count = min_word_count
    
    async def parse_pdf(self, file_path: str) -> PDFContent:
        """Parse PDF file and extract content.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            PDFContent: Extracted content
            
        Raises:
            Exception: If PDF parsing fails
        """
        try:
            logger.info(f"Starting PDF parsing: {file_path}")
            
            # Open PDF document
            doc = fitz.open(file_path)
            
            # Extract metadata
            metadata = doc.metadata
            total_pages = len(doc)
            
            logger.info(f"PDF has {total_pages} pages")
            
            # Extract content from each page
            pages = []
            total_word_count = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text()
                word_count = len(text.split())
                
                # Skip pages with very little text
                if word_count < self.min_word_count:
                    logger.debug(f"Skipping page {page_num + 1} - insufficient text ({word_count} words)")
                    continue
                
                # Extract images
                images = self._extract_images(page, page_num)
                
                # Extract tables (basic implementation)
                tables = self._extract_tables(page, page_num)
                
                extracted_page = ExtractedPage(
                    page_number=page_num + 1,
                    text=text.strip(),
                    word_count=word_count,
                    has_images=len(images) > 0,
                    images=images,
                    tables=tables
                )
                
                pages.append(extracted_page)
                total_word_count += word_count
                
                logger.debug(f"Processed page {page_num + 1}: {word_count} words, {len(images)} images")
            
            doc.close()
            
            pdf_content = PDFContent(
                filename=file_path.split('/')[-1],
                total_pages=len(pages),
                pages=pages,
                metadata=metadata,
                total_word_count=total_word_count
            )
            
            logger.info(f"PDF parsing completed: {len(pages)} pages, {total_word_count} total words")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
    
    def _extract_images(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract images from a page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of image metadata
        """
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                # Get image metadata
                xref = img[0]
                
                # Get image dimensions and other properties
                image_info = {
                    "page_number": page_num + 1,
                    "image_index": img_index,
                    "xref": xref,
                    "width": img[2] if len(img) > 2 else None,
                    "height": img[3] if len(img) > 3 else None,
                }
                
                images.append(image_info)
                
        except Exception as e:
            logger.warning(f"Error extracting images from page {page_num + 1}: {e}")
        
        return images
    
    def _extract_tables(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Extract table information from a page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            List of table metadata
        """
        tables = []
        
        try:
            # This is a simplified table detection
            # In a production system, you might use more sophisticated libraries
            # like pdfplumber or camelot for better table extraction
            
            # For now, we'll just identify text that looks like tables
            # based on structure patterns
            text = page.get_text()
            lines = text.split('\n')
            
            potential_table_lines = []
            for line in lines:
                # Simple heuristic: lines with multiple tabs or spaces might be table rows
                if line.count('\t') >= 2 or len(line.split()) >= 4:
                    potential_table_lines.append(line.strip())
            
            if len(potential_table_lines) >= 3:  # At least 3 rows to consider it a table
                table_info = {
                    "page_number": page_num + 1,
                    "estimated_rows": len(potential_table_lines),
                    "sample_lines": potential_table_lines[:3]  # Store first 3 lines as sample
                }
                tables.append(table_info)
                
        except Exception as e:
            logger.warning(f"Error extracting tables from page {page_num + 1}: {e}")
        
        return tables
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and formatting issues.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Join with single spaces
        cleaned = ' '.join(lines)
        
        # Remove multiple spaces
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def is_content_relevant(self, text: str) -> bool:
        """Check if text content is relevant for health education.
        
        Args:
            text: Text to check
            
        Returns:
            True if content appears relevant
        """
        if not text or len(text.split()) < self.min_word_count:
            return False
        
        # Keywords that indicate health education content
        health_keywords = [
            'health', 'medical', 'disease', 'condition', 'treatment', 'symptoms',
            'diet', 'nutrition', 'exercise', 'medication', 'doctor', 'patient',
            'blood pressure', 'diabetes', 'heart', 'kidney', 'hypertension',
            'chronic', 'wellness', 'prevention', 'care', 'therapy', 'clinical', 'obesity'
        ]
        
        text_lower = text.lower()
        
        # Count how many health keywords appear in the text
        keyword_count = sum(1 for keyword in health_keywords if keyword in text_lower)
        
        # Consider content relevant if it has at least 2 health keywords
        # or mentions specific conditions
        condition_keywords = ['diabetes', 'hypertension', 'heart disease', 'kidney disease']
        has_condition = any(condition in text_lower for condition in condition_keywords)
        
        return keyword_count >= 2 or has_condition 