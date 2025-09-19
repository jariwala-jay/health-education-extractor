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
    tips: List[str] = None
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.official_sources is None:
            self.official_sources = []
        if self.tips is None:
            self.tips = []


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
                "max_output_tokens": 400,  # Reduced for shorter, bullet-focused content
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
    
    async def summarize_chunk(self, chunk: ContentChunk, target_keywords: List[str] = None) -> Optional[SummarizedContent]:
        """Summarize a content chunk into a health article.
        
        Args:
            chunk: ContentChunk to summarize
            target_keywords: Optional list of keywords to focus on
            
        Returns:
            SummarizedContent object or None if summarization fails
        """
        try:
            logger.info(f"Starting summarization for chunk {chunk.chunk_id}")
            
            # Use chunk's target_keywords if not provided
            if target_keywords is None:
                target_keywords = chunk.target_keywords
            
            # Create the prompt
            prompt = self._create_summarization_prompt(chunk, target_keywords)
            
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
    
    def _create_summarization_prompt(self, chunk: ContentChunk, target_keywords: List[str] = None) -> str:
        """Create a prompt for Gemini to summarize health content."""
        
        # Get suggested category based on keywords
        suggested_category = self._suggest_category(chunk)
        
        # Build target keywords section
        target_keywords_section = ""
        if target_keywords:
            target_keywords_section = f"\nTARGET KEYWORDS: {', '.join(target_keywords)}\nFocus on these topics and avoid unrelated information."
        
        prompt = f"""
You are a health educator creating clear, easy-to-read health articles for people with limited reading skills. Write at a 4th-6th grade reading level using short, familiar words.

CONTENT TO SUMMARIZE:
{chunk.content}{target_keywords_section}

INSTRUCTIONS:
1. Create a specific, informative title (maximum 8 words)
2. Categorize using EXACTLY one of these values: {', '.join([cat.value for cat in CategoryEnum])}
   - Use the exact category name, no variations or additions
3. Write a health article using this format:
   - Start with a 1-2 sentence overview of the topic
   - Present 3-7 bullet points with key facts (each bullet = one important concept)
   - End with an encouraging, actionable takeaway

WRITING RULES:
- Use short sentences (15-20 words max)
- Use simple, everyday words
- Each bullet point should focus on ONE important fact
- Avoid medical jargon - explain terms simply
- No promotional language or contact information
- Focus only on the target keywords or medical topics found in the content
- NO bold text or special formatting
- Use simple bullet points with dashes (-)
- Start with a brief overview, then list tips

RESPONSE FORMAT (JSON):
{{
    "title": "Short, clear title",
    "category": "Nutrition",
    "content": "Brief overview sentence.\\n\\nHealthy tips:\\n- First key fact or recommendation\\n- Second important point\\n- Third helpful tip\\n\\nEncouraging takeaway sentence.",
    "medical_condition_tags": ["specific_condition", "related_topic"],
    "official_sources": ["Medical organizations mentioned"],
    "learn_more_url": "Relevant URL if mentioned",
    "confidence_score": 0.85
}}

EXAMPLE OUTPUT:
{{
    "title": "Managing High Blood Pressure",
    "category": "Hypertension",
    "content": "High blood pressure means your heart works harder to pump blood through your body. This can damage your heart and blood vessels over time.\\n\\nHealthy tips:\\n- Check your blood pressure regularly with your doctor\\n- Eat less salt and processed foods\\n- Walk for 30 minutes most days\\n- Take your blood pressure medicine as prescribed\\n- Limit alcohol to one drink per day for women, two for men\\n- Manage stress through relaxation or exercise\\n\\nSmall changes can make a big difference in keeping your blood pressure healthy.",
    "medical_condition_tags": ["High Blood Pressure", "Heart Health"],
    "official_sources": ["American Heart Association"],
    "learn_more_url": "https://www.heart.org/high-blood-pressure",
    "confidence_score": 0.88
}}

FOCUS: Use only information from the source content. Write for someone who needs simple, clear health information.
"""
        
        return prompt
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category to match enum values."""
        if not category:
            return "General Health"
        
        category_lower = category.lower().strip()
        
        # Map common variations to correct enum values
        category_mapping = {
            'nutrition and healthy eating': 'Nutrition',
            'healthy eating': 'Nutrition',
            'food and nutrition': 'Nutrition',
            'diet and nutrition': 'Nutrition',
            'nutritional health': 'Nutrition',
            'physical activity and exercise': 'Physical Activity',
            'exercise and fitness': 'Physical Activity',
            'fitness and exercise': 'Physical Activity',
            'weight management': 'Obesity',
            'weight loss': 'Obesity',
            'obesity and weight': 'Obesity',
            'diabetes management': 'Diabetes',
            'diabetic care': 'Diabetes',
            'blood pressure management': 'Hypertension',
            'hypertension management': 'Hypertension',
            'high blood pressure': 'Hypertension',
            'general health and wellness': 'General Health',
            'health and wellness': 'General Health',
            'overall health': 'General Health'
        }
        
        # Check for exact matches first
        if category in [cat.value for cat in CategoryEnum]:
            return category
        
        # Check for mapped variations
        if category_lower in category_mapping:
            return category_mapping[category_lower]
        
        # Check for partial matches
        for enum_cat in CategoryEnum:
            if enum_cat.value.lower() in category_lower or category_lower in enum_cat.value.lower():
                return enum_cat.value
        
        # Default to General Health if no match found
        logger.warning(f"Unknown category '{category}', defaulting to 'General Health'")
        return "General Health"
    
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
            
            # Validate and fix category if needed
            data['category'] = self._normalize_category(data.get('category', 'General Health'))
            
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
    
    async def batch_summarize_chunks(self, chunks: List[ContentChunk], target_keywords: List[str] = None) -> List[SummarizedContent]:
        """Summarize multiple chunks in batch with rate limiting.
        
        Args:
            chunks: List of ContentChunk objects to summarize
            target_keywords: Optional list of keywords to focus on
            
        Returns:
            List of SummarizedContent objects
        """
        summarized_contents = []
        
        logger.info(f"Starting batch summarization of {len(chunks)} chunks")
        
        # Process chunks with rate limiting (to avoid API limits)
        for i, chunk in enumerate(chunks):
            try:
                summarized = await self.summarize_chunk(chunk, target_keywords)
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
    
    async def summarize_document(self, chunks: List[ContentChunk], target_keywords: List[str] = None) -> Optional[SummarizedContent]:
        """Summarize a document using different modes based on configuration.
        
        Args:
            chunks: List of ContentChunk objects to summarize
            target_keywords: Optional list of keywords to focus on
            
        Returns:
            SummarizedContent object or None if summarization fails
        """
        try:
            mode = settings.summarization_mode
            logger.info(f"Starting document summarization in {mode} mode with {len(chunks)} chunks")
            
            if mode == "full":
                return await self._summarize_full_document(chunks, target_keywords)
            elif mode == "map_reduce":
                return await self._summarize_map_reduce(chunks, target_keywords)
            else:  # chunk mode - return first successful chunk summary
                for chunk in chunks:
                    result = await self.summarize_chunk(chunk, target_keywords)
                    if result:
                        return result
                return None
                
        except Exception as e:
            logger.error(f"Error in document summarization: {e}")
            return None
    
    async def _summarize_full_document(self, chunks: List[ContentChunk], target_keywords: List[str] = None) -> Optional[SummarizedContent]:
        """Summarize all chunks as one document."""
        # Combine all relevant chunks
        combined_content = "\n\n".join([
            f"Page {chunk.page_number}:\n{chunk.content}" 
            for chunk in chunks if chunk.is_relevant
        ])
        
        if not combined_content.strip():
            return None
        
        # Create a temporary chunk for the combined content
        combined_chunk = ContentChunk(
            chunk_id="combined_document",
            pdf_document_id=chunks[0].pdf_document_id if chunks else "",
            page_number=0,
            chunk_index=0,
            content=combined_content,
            word_count=len(combined_content.split()),
            is_relevant=True,
            target_keywords=target_keywords or []
        )
        
        return await self.summarize_chunk(combined_chunk, target_keywords)
    
    async def _summarize_map_reduce(self, chunks: List[ContentChunk], target_keywords: List[str] = None) -> Optional[SummarizedContent]:
        """Summarize using map-reduce approach with diversity focus."""
        # Step 1: Map - summarize each chunk individually
        chunk_summaries = []
        for chunk in chunks:
            if chunk.is_relevant:
                summary = await self.summarize_chunk(chunk, target_keywords)
                if summary:
                    chunk_summaries.append(summary)
        
        logger.info(f"Map-reduce: Generated {len(chunk_summaries)} chunk summaries from {len(chunks)} chunks")
        
        if not chunk_summaries:
            logger.warning("Map-reduce: No chunk summaries generated")
            return None
        
        # Step 2: Reduce - combine summaries into final article
        if len(chunk_summaries) == 1:
            logger.info("Map-reduce: Only one summary, returning as-is")
            return chunk_summaries[0]
        
        # For now, let's simplify and just take the first few summaries
        # TODO: Implement proper topic grouping later
        max_summaries = min(3, len(chunk_summaries))
        selected_summaries = chunk_summaries[:max_summaries]
        
        logger.info(f"Map-reduce: Selected {len(selected_summaries)} summaries for combination")
        
        # Combine selected summaries
        combined_summaries = "\n\n".join([
            f"Summary {i+1}:\n{summary.content}"
            for i, summary in enumerate(selected_summaries)
        ])
        
        # Create prompt for combining summaries with diversity focus
        prompt = f"""
You are a health educator creating a comprehensive health article from multiple related summaries. Focus on creating ONE cohesive article that covers different aspects of the topic without repetition.

SUMMARIES TO COMBINE:
{combined_summaries}

TARGET KEYWORDS: {', '.join(target_keywords) if target_keywords else 'Focus on medical topics found in the summaries'}

INSTRUCTIONS:
1. Create a single, comprehensive health article that covers different aspects of the topic
2. Use bullet-point format with 5-7 key points that are DISTINCT from each other
3. Each bullet point should cover a different aspect (symptoms, causes, prevention, treatment, lifestyle, etc.)
4. Remove ALL duplicate or very similar information
5. Ensure each bullet point provides unique value
6. Keep the 4th-6th grade reading level
7. Focus on the most important and actionable information
8. Make sure the article feels complete and comprehensive, not repetitive

RESPONSE FORMAT (JSON):
You MUST respond with ONLY valid JSON in this exact format:
{{
    "title": "Comprehensive article title",
    "category": "Nutrition",
    "content": "Comprehensive article with distinct bullet points",
    "medical_condition_tags": ["combined_tags"],
    "official_sources": ["combined_sources"],
    "learn_more_url": "Most_relevant_url",
    "confidence_score": 0.85
}}

IMPORTANT: 
- Use ONLY the exact category values: Hypertension, Diabetes, Nutrition, Physical Activity, Obesity, General Health
- Respond with ONLY the JSON object, no additional text
- Ensure the JSON is properly formatted and valid
"""
        
        # Generate combined content
        logger.info("Map-reduce: Generating combined content from summaries")
        response = await self._generate_content_async(prompt)
        if not response:
            logger.error("Map-reduce: No response from LLM for combination")
            return None
        
        logger.info(f"Map-reduce: Received response of length {len(response)}")
        
        # Parse the response
        try:
            # Try to find JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Map-reduce: No JSON found in response")
                logger.error(f"Map-reduce: Response content: {response[:500]}...")
                return None
            
            json_str = response[json_start:json_end]
            logger.info(f"Map-reduce: Extracted JSON string: {json_str[:200]}...")
            
            data = json.loads(json_str)
            
            # Normalize category
            data['category'] = self._normalize_category(data.get('category', 'General Health'))
            
            logger.info(f"Map-reduce: Successfully parsed JSON, title: {data.get('title', 'No title')}")
            
            # Create SummarizedContent from combined result
            combined_content = SummarizedContent(
                title=data['title'][:200],
                category=data['category'],
                content=data['content'],
                medical_condition_tags=data['medical_condition_tags'][:10],
                official_sources=data.get('official_sources', [])[:5],
                learn_more_url=data.get('learn_more_url'),
                confidence_score=data.get('confidence_score', 0.8),
                source_chunk_id="map_reduce_combined"
            )
            
            # Calculate reading level
            reading_level = self._estimate_reading_level(combined_content.content)
            combined_content.reading_level_score = reading_level
            
            logger.info(f"Map-reduce: Successfully created combined content: {combined_content.title}")
            return combined_content
            
        except Exception as e:
            logger.error(f"Map-reduce: Error parsing response: {e}")
            logger.error(f"Map-reduce: Response was: {response[:500]}...")
            
            # Fallback: return the best individual summary if combination fails
            logger.info("Map-reduce: Falling back to best individual summary")
            if selected_summaries:
                best_summary = max(selected_summaries, key=lambda s: s.confidence_score or 0.5)
                logger.info(f"Map-reduce: Using fallback summary: {best_summary.title}")
                return best_summary
            
            return None
    
    def _group_summaries_by_topic(self, summaries: List[SummarizedContent]) -> List[List[SummarizedContent]]:
        """Group summaries by topic similarity."""
        if len(summaries) <= 1:
            return [summaries]
        
        groups = []
        used_indices = set()
        
        for i, summary in enumerate(summaries):
            if i in used_indices:
                continue
                
            # Start a new group with this summary
            group = [summary]
            used_indices.add(i)
            
            # Find similar summaries to add to this group
            for j, other_summary in enumerate(summaries):
                if j in used_indices or i == j:
                    continue
                
                # Check if summaries are similar (simple title/content similarity)
                if self._are_summaries_similar(summary, other_summary):
                    group.append(other_summary)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_summaries_similar(self, summary1: SummarizedContent, summary2: SummarizedContent) -> bool:
        """Check if two summaries are similar."""
        # Simple similarity check based on title and content overlap
        title1 = summary1.title.lower()
        title2 = summary2.title.lower()
        
        # Check for common words in titles
        words1 = set(title1.split())
        words2 = set(title2.split())
        common_words = words1.intersection(words2)
        
        # If more than 30% of words are common, consider similar
        if len(common_words) > 0 and len(common_words) / max(len(words1), len(words2)) > 0.3:
            return True
        
        # Check for similar content structure
        content1 = summary1.content.lower()
        content2 = summary2.content.lower()
        
        # Count common phrases
        phrases1 = set(content1.split('. '))
        phrases2 = set(content2.split('. '))
        common_phrases = phrases1.intersection(phrases2)
        
        # If more than 20% of phrases are common, consider similar
        if len(common_phrases) > 0 and len(common_phrases) / max(len(phrases1), len(phrases2)) > 0.2:
            return True
        
        return False
    
    def _select_diverse_summaries(self, topic_groups: List[List[SummarizedContent]], max_summaries: int = 3) -> List[SummarizedContent]:
        """Select the most diverse summaries from topic groups."""
        selected = []
        
        # Sort groups by size (larger groups first)
        topic_groups.sort(key=len, reverse=True)
        
        # Take the best summary from each group
        for group in topic_groups:
            if len(selected) >= max_summaries:
                break
            
            # Select the summary with the most comprehensive content
            best_summary = max(group, key=lambda s: len(s.content))
            selected.append(best_summary)
        
        return selected
    
    async def generate_tips(self, content: str, target_keywords: List[str] = None) -> List[str]:
        """Generate daily tips from content.
        
        Args:
            content: Article content to extract tips from
            target_keywords: Optional list of keywords to focus on
            
        Returns:
            List of tip strings
        """
        try:
            keywords_text = ""
            if target_keywords:
                keywords_text = f"\nTARGET KEYWORDS: {', '.join(target_keywords)}"
            
            prompt = f"""
You are a health educator generating very short health tips. Based on the following content{keywords_text}, extract 1-3 concise tips.

CONTENT:
{content}

INSTRUCTIONS:
- Each tip must be 1-2 sentences (30 words max)
- Highlight an interesting fact or actionable recommendation
- Use simple language suitable for 6th grade reading level
- Avoid repeating the same idea
- Focus on practical, helpful information
- Make each tip stand alone
- Do NOT start with "Did you know?" or similar phrases
- Write tips as direct statements or recommendations

OUTPUT: Return as a JSON array of strings.
Example: ["Tip 1 text", "Tip 2 text", "Tip 3 text"]
"""
            
            response = await self._generate_content_async(prompt)
            if not response:
                return []
            
            # Parse JSON response
            try:
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start == -1 or json_end == 0:
                    return []
                
                json_str = response[json_start:json_end]
                tips = json.loads(json_str)
                
                # Validate and clean tips
                valid_tips = []
                for tip in tips:
                    if isinstance(tip, str) and len(tip.strip()) > 10:
                        # Ensure tip is within word limit
                        words = tip.strip().split()
                        if len(words) <= 30:
                            valid_tips.append(tip.strip())
                
                return valid_tips[:3]  # Limit to 3 tips max
                
            except Exception as e:
                logger.error(f"Error parsing tips response: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error generating tips: {e}")
            return [] 