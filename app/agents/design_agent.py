from openai import AsyncOpenAI
from typing import Dict, Any, List
import aiohttp
import colorsys
from PIL import Image
import io
import base64


class DesignAgent:
    """
    Specialized agent for visual brand identity generation.
    Handles logo creation, color palettes, and visual style consistency.
    """
    
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        
    async def generate_visuals(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        style_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete visual identity including logo, colors, and style guide.
        """
        
        # Generate logo concepts
        logo_data = await self._generate_logo(business_name, strategy, style_preferences)
        
        # Extract color palette from logo
        color_palette = await self._extract_color_palette(logo_data['image_url'])
        
        # Generate typography recommendations
        typography = await self._recommend_typography(strategy, style_preferences)
        
        # Create visual style guide
        style_guide = await self._create_style_guide(
            logo_data,
            color_palette,
            typography,
            strategy
        )
        
        return {
            'logo': logo_data,
            'color_palette': color_palette,
            'typography': typography,
            'style_guide': style_guide
        }
    
    async def _generate_logo(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        style_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate logo using DALL-E 3.
        """
        
        # Craft detailed prompt based on strategy
        visual_direction = style_preferences.get('aesthetic', 'modern and professional')
        industry_context = strategy.get('industry', 'general business')
        brand_personality = ', '.join(strategy.get('brand_values', []))
        
        prompt = f"""
        Design a professional, minimalist logo for "{business_name}".
        
        Style: {visual_direction}
        Industry: {industry_context}
        Brand Personality: {brand_personality}
        
        Requirements:
        - Clean, scalable vector-style design
        - Works in both color and monochrome
        - Memorable and distinctive
        - Suitable for digital and print
        - No text unless it's part of the brand name
        - White or transparent background
        
        The logo should be simple, iconic, and instantly recognizable.
        """
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return {
                'image_url': image_url,
                'original_prompt': prompt,
                'revised_prompt': revised_prompt,
                'generation_metadata': {
                    'model': 'dall-e-3',
                    'size': '1024x1024'
                }
            }
            
        except Exception as e:
            raise Exception(f"Logo generation failed: {str(e)}")
    
    async def _extract_color_palette(self, image_url: str) -> Dict[str, Any]:
        """
        Extract dominant colors from generated logo to create brand palette.
        Uses k-means clustering on image pixels.
        """
        
        try:
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    image_data = await resp.read()
            
            # Open with PIL
            image = Image.open(io.BytesIO(image_data))
            image = image.convert('RGB')
            
            # Resize for faster processing
            image.thumbnail((100, 100))
            
            # Get pixel data
            pixels = list(image.getdata())
            
            # Simple color extraction (top 5 most common colors)
            from collections import Counter
            color_counts = Counter(pixels)
            dominant_colors = color_counts.most_common(5)
            
            # Convert to hex and create palette
            palette = []
            for color, count in dominant_colors:
                hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                
                # Calculate color properties
                h, s, v = colorsys.rgb_to_hsv(color[0]/255, color[1]/255, color[2]/255)
                
                palette.append({
                    'hex': hex_color,
                    'rgb': color,
                    'hsl': {
                        'h': int(h * 360),
                        's': int(s * 100),
                        'l': int(v * 100)
                    },
                    'usage': self._suggest_color_usage(v, s)
                })
            
            return {
                'primary_colors': palette[:2],
                'secondary_colors': palette[2:],
                'all_colors': palette
            }
            
        except Exception as e:
            # Fallback to default palette
            return self._generate_default_palette()
    
    def _suggest_color_usage(self, value: float, saturation: float) -> str:
        """Suggest usage based on color properties."""
        if value > 0.8:
            return "background or highlight"
        elif saturation > 0.6:
            return "accent or call-to-action"
        else:
            return "text or neutral"
    
    async def _recommend_typography(
        self,
        strategy: Dict[str, Any],
        style_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend font pairings based on brand strategy.
        """
        
        # Use GPT-4 to recommend typography
        prompt = f"""
        Recommend typography for a brand with these characteristics:
        
        Industry: {strategy.get('industry', 'general')}
        Brand Values: {', '.join(strategy.get('brand_values', []))}
        Visual Style: {style_preferences.get('aesthetic', 'modern')}
        
        Provide:
        1. Primary font (for headings) - name and reasoning
        2. Secondary font (for body text) - name and reasoning
        3. Font pairing rationale
        4. Usage guidelines
        
        Recommend Google Fonts for easy web implementation.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert typography designer."},
                {"role": "user", "content": prompt}
            ]
        )
        
        typography_rec = response.choices[0].message.content
        
        return {
            'recommendation': typography_rec,
            'google_fonts_ready': True
        }
    
    async def _create_style_guide(
        self,
        logo_data: Dict,
        color_palette: Dict,
        typography: Dict,
        strategy: Dict
    ) -> Dict[str, Any]:
        """
        Compile comprehensive visual style guide.
        """
        
        return {
            'logo_usage': {
                'minimum_size': '32px',
                'clear_space': 'Equal to logo height',
                'backgrounds': ['white', 'dark', 'brand colors'],
                'dont_list': [
                    "Don't distort or rotate",
                    "Don't change colors without approval",
                    "Don't add effects or shadows"
                ]
            },
            'color_system': color_palette,
            'typography_system': typography,
            'spacing_scale': ['4px', '8px', '16px', '24px', '32px', '48px', '64px'],
            'brand_personality': strategy.get('brand_values', [])
        }
    
    def _generate_default_palette(self) -> Dict[str, Any]:
        """Fallback color palette if extraction fails."""
        return {
            'primary_colors': [
                {'hex': '#0066CC', 'usage': 'primary brand color'},
                {'hex': '#003366', 'usage': 'dark accent'}
            ],
            'secondary_colors': [
                {'hex': '#66B2FF', 'usage': 'light accent'},
                {'hex': '#E6F2FF', 'usage': 'background'}
            ]
        }
    
    async def refine_visuals(
        self,
        current_visuals: Dict,
        feedback: List[str],
        strategy: Dict
    ) -> Dict[str, Any]:
        """
        Refine visual identity based on feedback.
        """
        # Implementation for refinement based on feedback
        # Could regenerate logo with modified prompt or adjust color palette
        pass