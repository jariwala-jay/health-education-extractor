"""Gemini LLM integration for summarizing health content."""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config import settings
from app.models.health_article import CategoryEnum
from app.services.content_chunker import ContentChunk

logger = logging.getLogger(__name__)


@dataclass
class SummarizedContent:
    """Represents summarized health content."""
    title: str
    category: str
    content: str
    medical_condition_tags: List[str]
    official_sources: List[str] = None
    learn_more_url: Optional[str] = None
    reading_level_score: Optional[float] = None
    source_chunk_id: str = ""
    confidence_score: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.official_sources is None:
            self.official_sources = []


class GeminiSummarizer:
    """Service for summarizing health content using Google Gemini."""
    
    def __init__(self):
        """Initialize Gemini summarizer."""
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.2,  # Very low temperature for consistent, factual output
                "top_p": 0.7,  # Reduced for more focused responses
                "top_k": 20,   # Reduced for more deterministic output
                "max_output_tokens": 800,  # Reduced for shorter, more concise content
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # Category mapping for health conditions
        self.category_keywords = {
            CategoryEnum.HYPERTENSION: [
                'blood pressure', 'hypertension', 'high blood pressure', 
                'systolic', 'diastolic', 'bp'
            ],
            CategoryEnum.DIABETES: [
                'diabetes', 'blood sugar', 'glucose', 'insulin', 
                'diabetic', 'type 1', 'type 2'
            ],
            CategoryEnum.NUTRITION: [
                'nutrition', 'diet', 'food', 'eating', 'meal',
                'calories', 'vitamins', 'minerals', 'healthy eating'
            ],
            CategoryEnum.PHYSICAL_ACTIVITY: [
                'exercise', 'physical activity', 'workout', 'fitness',
                'walking', 'running', 'gym', 'cardio', 'strength training'
            ],
            CategoryEnum.OBESITY: [
                'obesity', 'overweight', 'weight loss', 'weight management',
                'bmi', 'body mass index', 'excess weight', 'healthy weight',
                'portion control', 'calorie counting'
            ]
        }
    
    async def summarize_chunk(self, chunk: ContentChunk) -> Optional[SummarizedContent]:
        """Summarize a content chunk into a health article.
        
        Args:
            chunk: ContentChunk to summarize
            
        Returns:
            SummarizedContent object or None if summarization fails
        """
        try:
            logger.info(f"Starting summarization for chunk {chunk.chunk_id}")
            
            # Create the prompt
            prompt = self._create_summarization_prompt(chunk)
            
            # Generate content using Gemini
            response = await self._generate_content_async(prompt)
            
            if not response:
                logger.error(f"No response from Gemini for chunk {chunk.chunk_id}")
                return None
            
            # Parse the response
            summarized_content = self._parse_gemini_response(response, chunk)
            
            if summarized_content:
                logger.info(f"Successfully summarized chunk {chunk.chunk_id}")
                return summarized_content
            else:
                logger.error(f"Failed to parse Gemini response for chunk {chunk.chunk_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error summarizing chunk {chunk.chunk_id}: {e}")
            return None
    
    def _create_summarization_prompt(self, chunk: ContentChunk) -> str:
        """Create a prompt for Gemini to summarize health content."""
        
        # Get suggested category based on keywords
        suggested_category = self._suggest_category(chunk)
        
        prompt = f"""
You are a medical education expert who transforms complex medical information into clear, evidence-based health articles. Your goal is to create educational content that is both scientifically accurate and accessible to people with limited health literacy.

CRITICAL: This is EDUCATIONAL content, NOT promotional material. Focus on medical facts, not advertising.

CONTENT TO SUMMARIZE:
{chunk.content}

INSTRUCTIONS:
1. Create a specific, informative title (maximum 10 words) that describes the medical topic
2. Categorize using one of these: {', '.join([cat.value for cat in CategoryEnum])}
3. Write a natural, flowing educational article (150-250 words max):
   
   CONTENT APPROACH:
   - Start with what the condition/topic is in simple terms
   - Naturally weave in the most important information people need to know
   - Include practical advice that people can actually use
   - Make it read like a helpful explanation, not a checklist
   
   WRITING STYLE:
   - Write in a conversational, educational tone
   - Use short paragraphs (2-3 sentences each)
   - Use bullet points only when listing specific items (like symptoms)
   - Focus on what matters most to the reader
   - End with encouraging, actionable guidance

4. Extract specific medical condition tags (be precise, not generic)
5. Identify authoritative sources mentioned in the content
6. Ensure medical accuracy while maintaining simplicity

AVOID:
- Generic promotional language ("We want to help you live healthier")
- Rigid Q&A format with headers like "Who is at risk?" or "When to see a doctor?"
- Formulaic structure that feels like a checklist
- Vague statements ("eat healthy foods")
- Contact information or website promotion
- Doctor profiles or testimonials
- Marketing content

RESPONSE FORMAT (JSON):
{{
    "title": "Specific medical topic title",
    "category": "Exact category match",
    "content": "Educational article with medical facts, specific guidance, and clear explanations",
    "medical_condition_tags": ["specific_condition", "related_symptom", "treatment_type"],
    "official_sources": ["Medical organizations mentioned"],
    "learn_more_url": "Relevant educational URL if mentioned",
    "confidence_score": 0.85
}}

EXAMPLE OUTPUT:
{{
    "title": "Understanding Type 2 Diabetes",
    "category": "Diabetes",
    "content": "Type 2 diabetes happens when your body cannot use insulin properly to control blood sugar. This causes sugar to build up in your blood instead of going into your cells for energy.\\n\\nMany people don't know they have diabetes because it develops slowly. Common signs include feeling very thirsty, urinating more often, feeling tired, and having blurred vision. Cuts and bruises may also heal more slowly than usual.\\n\\nPeople over 45, those with family history of diabetes, and people who are overweight have higher risk. However, diabetes can affect anyone.\\n\\nThe good news is that small changes can make a big difference. Eating smaller portions, choosing whole foods over processed ones, and walking for 30 minutes most days can help control blood sugar. If you have diabetes, taking medications as prescribed is also important.\\n\\nIf your blood sugar is over 126 mg/dL when fasting, you may have diabetes. Early treatment can prevent serious problems like heart disease and kidney damage, so talk to your doctor about getting tested.",
    "medical_condition_tags": ["Type 2 Diabetes", "Blood glucose", "Diabetes symptoms"],
    "official_sources": ["American Diabetes Association"],
    "learn_more_url": "https://www.diabetes.org/diabetes/type-2",
    "confidence_score": 0.91
}}

FOCUS: Extract and preserve specific medical information from the source content. Transform complex medical concepts into understandable explanations while maintaining scientific accuracy.
"""
        
        return prompt
    
    async def _generate_content_async(self, prompt: str) -> Optional[str]:
        """Generate content using Gemini API asynchronously."""
        try:
            # Run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None
    
    def _parse_gemini_response(self, response: str, chunk: ContentChunk) -> Optional[SummarizedContent]:
        """Parse Gemini's JSON response into SummarizedContent."""
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in Gemini response")
                return None
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['title', 'category', 'content', 'medical_condition_tags']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in Gemini response")
                    return None
            
            # Validate category
            try:
                category = CategoryEnum(data['category'])
            except ValueError:
                logger.warning(f"Invalid category '{data['category']}', defaulting to GENERAL")
                category = CategoryEnum.GENERAL
            
            # Create SummarizedContent object
            summarized_content = SummarizedContent(
                title=data['title'][:200],  # Limit title length
                category=category.value,
                content=data['content'],
                medical_condition_tags=data['medical_condition_tags'][:10],  # Limit tags
                official_sources=data.get('official_sources', [])[:5],  # Limit sources
                learn_more_url=data.get('learn_more_url'),
                confidence_score=data.get('confidence_score', 0.8),
                source_chunk_id=chunk.chunk_id
            )
            
            # Calculate reading level score (simplified estimation)
            reading_level = self._estimate_reading_level(summarized_content.content)
            summarized_content.reading_level_score = reading_level
            
            return summarized_content
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Response text: {response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return None
    
    def _suggest_category(self, chunk: ContentChunk) -> str:
        """Suggest a category based on chunk keywords."""
        content_lower = chunk.content.lower()
        
        # Count matches for each category
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score
        
        # Return the category with the highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category.value
        
        return CategoryEnum.GENERAL.value
    
    def _estimate_reading_level(self, text: str) -> float:
        """Estimate reading level using simplified metrics."""
        if not text:
            return 12.0  # Default high level for empty text
        
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 12.0
        
        # Calculate average sentence length
        total_words = len(text.split())
        avg_sentence_length = total_words / len(sentences)
        
        # Simple heuristic: shorter sentences = lower reading level
        if avg_sentence_length <= 10:
            reading_level = 4.0
        elif avg_sentence_length <= 15:
            reading_level = 6.0
        elif avg_sentence_length <= 20:
            reading_level = 8.0
        else:
            reading_level = 10.0
        
        # Adjust based on complex words (words with 3+ syllables)
        words = text.split()
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        complex_ratio = complex_words / len(words) if words else 0
        
        # Add penalty for complex words
        reading_level += complex_ratio * 4
        
        return min(reading_level, 12.0)  # Cap at 12th grade
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count in a word."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)  # Every word has at least 1 syllable
    
    async def batch_summarize_chunks(self, chunks: List[ContentChunk]) -> List[SummarizedContent]:
        """Summarize multiple chunks in batch with rate limiting.
        
        Args:
            chunks: List of ContentChunk objects to summarize
            
        Returns:
            List of SummarizedContent objects
        """
        summarized_contents = []
        
        logger.info(f"Starting batch summarization of {len(chunks)} chunks")
        
        # Process chunks with rate limiting (to avoid API limits)
        for i, chunk in enumerate(chunks):
            try:
                summarized = await self.summarize_chunk(chunk)
                if summarized:
                    summarized_contents.append(summarized)
                
                # Rate limiting: wait between requests
                if i < len(chunks) - 1:  # Don't wait after the last chunk
                    await asyncio.sleep(1)  # 1 second between requests
                    
            except Exception as e:
                logger.error(f"Error in batch summarization for chunk {chunk.chunk_id}: {e}")
                continue
        
        logger.info(f"Batch summarization completed: {len(summarized_contents)} successful")
        return summarized_contents 