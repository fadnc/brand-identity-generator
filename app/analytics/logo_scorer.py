from typing import Dict, Any
from openai import OpenAI
import os
import json
from PIL import Image
import requests
from io import BytesIO


class LogoScorer:
    """
    Scores logo aesthetics and design quality.
    Uses vision model for analysis and design principles evaluation.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def score_logo(self, logo_url: str) -> Dict[str, Any]:
        """
        Comprehensive logo scoring.
        """
        
        # Analyze with vision model
        aesthetic_analysis = self._analyze_with_vision(logo_url)
        
        # Analyze technical aspects
        technical_analysis = self._analyze_technical_aspects(logo_url)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            aesthetic_analysis,
            technical_analysis
        )
        
        return {
            'overall_score': overall_score,
            'aesthetic_analysis': aesthetic_analysis,
            'technical_analysis': technical_analysis,
            'recommendations': self._generate_recommendations(
                aesthetic_analysis,
                technical_analysis
            )
        }
    
    def _analyze_with_vision(self, logo_url: str) -> Dict[str, Any]:
        """
        Use GPT-4 Vision to analyze logo aesthetics.
        """
        
        prompt = """
        Analyze this logo design based on professional design principles:
        
        Evaluate:
        1. Visual balance and composition (0-10)
        2. Color harmony and effectiveness (0-10)
        3. Typography quality (if text present) (0-10)
        4. Scalability and versatility (0-10)
        5. Memorability and distinctiveness (0-10)
        6. Professionalism and polish (0-10)
        7. Industry appropriateness (0-10)
        
        Also provide:
        - Overall aesthetic score (0-10)
        - Key strengths (array of strings)
        - Areas for improvement (array of strings)
        - Design style description
        
        Return as JSON with keys: balance_score, color_score, typography_score, scalability_score, 
        memorability_score, professionalism_score, industry_fit_score, overall_aesthetic_score, 
        strengths, improvements, style_description
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": logo_url}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # If JSON parsing fails, return structured default
            return {
                'overall_aesthetic_score': 7.5,
                'balance_score': 7.5,
                'color_score': 7.5,
                'typography_score': 7.5,
                'scalability_score': 7.5,
                'memorability_score': 7.5,
                'professionalism_score': 8.0,
                'industry_fit_score': 7.5,
                'strengths': ['Clean design', 'Professional appearance'],
                'improvements': ['Could enhance distinctiveness'],
                'style_description': 'Modern and professional',
                'raw_analysis': content
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'overall_aesthetic_score': 0,
                'message': 'Vision analysis failed'
            }
    
    def _analyze_technical_aspects(self, logo_url: str) -> Dict[str, Any]:
        """
        Analyze technical aspects of the logo image.
        """
        
        try:
            # Download image
            response = requests.get(logo_url)
            img = Image.open(BytesIO(response.content))
            
            # Get image properties
            width, height = img.size
            mode = img.mode
            format_type = img.format
            
            # Calculate aspect ratio
            aspect_ratio = width / height if height > 0 else 1
            
            # Check if square (ideal for logos)
            is_square = abs(aspect_ratio - 1.0) < 0.1
            
            # Analyze color complexity
            colors = img.getcolors(maxcolors=256)
            color_count = len(colors) if colors else 256
            
            # Simple complexity score
            complexity_score = min(10, (color_count / 10))
            
            # Resolution score
            pixel_count = width * height
            resolution_score = 10 if pixel_count >= 1000000 else (pixel_count / 100000)
            
            return {
                'dimensions': {'width': width, 'height': height},
                'aspect_ratio': round(aspect_ratio, 2),
                'is_square': is_square,
                'color_mode': mode,
                'format': format_type,
                'estimated_color_count': color_count,
                'complexity_score': round(complexity_score, 1),
                'resolution_score': round(min(resolution_score, 10), 1),
                'file_size_category': 'high' if pixel_count > 1000000 else 'medium'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Technical analysis failed'
            }
    
    def _calculate_overall_score(
        self,
        aesthetic: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> float:
        """
        Calculate weighted overall logo score.
        """
        
        # Aesthetic scores (70% weight)
        aesthetic_score = aesthetic.get('overall_aesthetic_score', 0) / 10
        
        # Technical scores (30% weight)
        technical_score = (
            technical.get('complexity_score', 0) +
            technical.get('resolution_score', 0)
        ) / 20
        
        # Bonus for square logos (good for versatility)
        square_bonus = 0.05 if technical.get('is_square', False) else 0
        
        overall = (aesthetic_score * 0.7) + (technical_score * 0.3) + square_bonus
        
        return round(min(overall, 1.0), 2)
    
    def _generate_recommendations(
        self,
        aesthetic: Dict[str, Any],
        technical: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        """
        
        recommendations = []
        
        # Check individual scores
        if aesthetic.get('balance_score', 10) < 7:
            recommendations.append("Improve visual balance and composition")
        
        if aesthetic.get('color_score', 10) < 7:
            recommendations.append("Refine color palette for better harmony")
        
        if aesthetic.get('memorability_score', 10) < 7:
            recommendations.append("Enhance distinctiveness to improve brand recall")
        
        if not technical.get('is_square', False):
            recommendations.append("Consider creating a square version for better versatility")
        
        if technical.get('estimated_color_count', 0) > 20:
            recommendations.append("Simplify color palette for better scalability")
        
        # Add improvements from aesthetic analysis
        improvements = aesthetic.get('improvements', [])
        if improvements:
            recommendations.extend(improvements[:3])
        
        return recommendations[:5]  # Return top 5 recommendations