from typing import Dict, Any, List
from openai import OpenAI
import os
import json


class SentimentAnalyzer:
    """
    Analyzes sentiment and emotional tone of brand copy.
    Uses GPT-4 for nuanced sentiment analysis beyond simple positive/negative.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_brand_copy(self, brand_copy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment across all brand copy elements.
        """
        
        results = {
            'overall_sentiment': None,
            'emotional_tone': [],
            'by_element': {}
        }
        
        # Analyze taglines
        if brand_copy.get('taglines'):
            tagline_sentiment = self._analyze_taglines(brand_copy['taglines'])
            results['by_element']['taglines'] = tagline_sentiment
        
        # Analyze brand story
        if brand_copy.get('brand_story'):
            story_sentiment = self._analyze_text(
                brand_copy['brand_story'].get('medium', ''),
                'brand_story'
            )
            results['by_element']['brand_story'] = story_sentiment
        
        # Analyze website copy
        if brand_copy.get('website_copy'):
            hero = brand_copy['website_copy'].get('hero', {})
            hero_text = f"{hero.get('headline', '')} {hero.get('subheadline', '')}"
            website_sentiment = self._analyze_text(hero_text, 'website_hero')
            results['by_element']['website_copy'] = website_sentiment
        
        # Analyze social content
        if brand_copy.get('social_content'):
            social_bios = brand_copy['social_content'].get('bios', {})
            if social_bios:
                social_text = ' '.join([v for v in social_bios.values() if isinstance(v, str)])
                social_sentiment = self._analyze_text(social_text, 'social_media')
                results['by_element']['social_media'] = social_sentiment
        
        # Calculate overall sentiment
        results['overall_sentiment'] = self._calculate_overall_sentiment(
            results['by_element']
        )
        
        # Extract emotional tone
        results['emotional_tone'] = self._extract_emotional_tone(
            results['by_element']
        )
        
        return results
    
    def _analyze_taglines(self, taglines: List[Dict]) -> Dict[str, Any]:
        """
        Analyze sentiment of taglines.
        """
        
        tagline_texts = [t.get('tagline', '') for t in taglines[:3]]
        combined_text = ' | '.join(tagline_texts)
        
        return self._analyze_text(combined_text, 'taglines')
    
    def _analyze_text(self, text: str, context: str) -> Dict[str, Any]:
        """
        Perform detailed sentiment analysis on text.
        """
        
        prompt = f"""
        Analyze the sentiment and emotional tone of the following {context}:
        
        Text: "{text}"
        
        Provide analysis including:
        1. Overall sentiment (positive, neutral, negative) with score 0-1
        2. Emotional tones present (e.g., inspirational, confident, friendly, professional)
        3. Intensity level (subtle, moderate, strong)
        4. Appropriateness for brand communication
        5. Potential audience reactions
        
        Return as JSON with keys: sentiment, sentiment_score, emotional_tones, intensity, appropriateness, audience_reactions
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert specializing in brand communication."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'emotional_tones': [],
                'error': str(e)
            }
    
    def _calculate_overall_sentiment(self, by_element: Dict) -> Dict[str, Any]:
        """
        Calculate weighted overall sentiment.
        """
        
        scores = []
        weights = {
            'taglines': 0.3,
            'brand_story': 0.25,
            'website_copy': 0.25,
            'social_media': 0.2
        }
        
        for element, weight in weights.items():
            if element in by_element:
                score = by_element[element].get('sentiment_score', 0.5)
                scores.append(score * weight)
        
        overall_score = sum(scores) / sum(weights.values()) if scores else 0.5
        
        if overall_score > 0.65:
            sentiment_label = 'positive'
        elif overall_score < 0.35:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return {
            'sentiment': sentiment_label,
            'score': round(overall_score, 2)
        }
    
    def _extract_emotional_tone(self, by_element: Dict) -> List[str]:
        """
        Extract common emotional tones across all elements.
        """
        
        all_tones = []
        
        for element_data in by_element.values():
            tones = element_data.get('emotional_tones', [])
            if isinstance(tones, list):
                all_tones.extend(tones)
        
        # Count frequency and return most common
        from collections import Counter
        tone_counts = Counter(all_tones)
        
        return [tone for tone, count in tone_counts.most_common(5)]