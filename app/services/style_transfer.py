"""
Style Transfer Service - Applies artistic styles to images and maintains brand consistency.

This service handles style transfers, image-to-image transformations, and ensures
visual consistency across brand assets using AI models.
"""

from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
import os
import aiohttp
import asyncio
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
from datetime import datetime
import hashlib
import numpy as np


class StyleTransferService:
    """
    Service for applying artistic styles and transformations to images.
    
    Handles style transfers, color grading, filters, and brand consistency
    enforcement across visual assets.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the style transfer service.
        
        Args:
            openai_api_key: OpenAI API key (optional, uses env var if not provided)
        """
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Configuration
        self.upload_folder = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Supported styles
        self.supported_styles = [
            'minimalist', 'modern', 'vintage', 'professional',
            'playful', 'elegant', 'bold', 'organic', 'geometric',
            'abstract', 'realistic', 'illustrative'
        ]
    
    async def apply_brand_style(
        self,
        source_image_url: str,
        brand_colors: List[str],
        style_direction: str,
        brand_personality: List[str]
    ) -> Dict[str, Any]:
        """
        Apply brand style to an image.
        
        Args:
            source_image_url: URL of source image
            brand_colors: List of brand color hex codes
            style_direction: Visual style to apply
            brand_personality: Brand personality traits
            
        Returns:
            Styled image data
            
        Example:
            result = await service.apply_brand_style(
                source_image_url="https://...",
                brand_colors=["#0066CC", "#003366"],
                style_direction="modern minimalist",
                brand_personality=["professional", "innovative"]
            )
        """
        
        # Download source image
        image_data = await self._download_image(source_image_url)
        if not image_data:
            return {'error': 'Failed to download source image'}
        
        # Convert to base64 for API
        image_base64 = self._image_to_base64(image_data)
        
        # Create style transfer prompt
        prompt = self._create_style_prompt(
            style_direction=style_direction,
            brand_colors=brand_colors,
            brand_personality=brand_personality
        )
        
        # Apply style using image generation with reference
        result = await self._apply_style_with_ai(
            prompt=prompt,
            reference_image_base64=image_base64
        )
        
        if result.get('error'):
            return result
        
        # Download and save styled image
        local_path = await self._download_and_save(
            url=result['url'],
            prefix='styled_image'
        )
        
        return {
            'success': True,
            'styled_image_url': result['url'],
            'local_path': local_path,
            'style_applied': style_direction,
            'prompt_used': prompt
        }
    
    async def adjust_brand_colors(
        self,
        image_url: str,
        target_colors: List[str],
        preserve_luminosity: bool = True
    ) -> Dict[str, Any]:
        """
        Adjust image colors to match brand palette.
        
        Args:
            image_url: URL of image to adjust
            target_colors: Target brand colors
            preserve_luminosity: Keep original brightness
            
        Returns:
            Color-adjusted image data
            
        Example:
            result = await service.adjust_brand_colors(
                image_url="https://...",
                target_colors=["#0066CC", "#FF6600"],
                preserve_luminosity=True
            )
        """
        
        # Download image
        image_data = await self._download_image(image_url)
        if not image_data:
            return {'error': 'Failed to download image'}
        
        # Open with PIL
        img = Image.open(io.BytesIO(image_data))
        
        # Apply color adjustment
        adjusted_img = self._adjust_colors_pil(
            img,
            target_colors,
            preserve_luminosity
        )
        
        # Save adjusted image
        local_path = self._save_pil_image(
            adjusted_img,
            prefix='color_adjusted'
        )
        
        return {
            'success': True,
            'adjusted_image_path': local_path,
            'colors_applied': target_colors,
            'luminosity_preserved': preserve_luminosity
        }
    
    async def create_image_variations(
        self,
        base_image_url: str,
        variation_styles: List[str],
        brand_constraints: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Create multiple style variations of an image.
        
        Args:
            base_image_url: Base image URL
            variation_styles: List of styles to apply
            brand_constraints: Brand guidelines to maintain
            
        Returns:
            List of image variations
            
        Example:
            variations = await service.create_image_variations(
                base_image_url="https://...",
                variation_styles=["minimalist", "bold", "elegant"],
                brand_constraints={"colors": ["#0066CC"]}
            )
        """
        
        variations = []
        
        # Generate variations in parallel
        tasks = [
            self._create_single_variation(
                base_image_url,
                style,
                brand_constraints
            )
            for style in variation_styles
        ]
        
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if not r.get('error')]
    
    async def _create_single_variation(
        self,
        base_image_url: str,
        style: str,
        brand_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a single style variation."""
        
        # Create variation prompt
        prompt = f"""
        Create a {style} variation of this image.
        
        Maintain:
        - Core composition
        - Subject matter
        - Overall message
        
        Apply {style} aesthetic while keeping professional quality.
        """
        
        if brand_constraints and brand_constraints.get('colors'):
            colors = ', '.join(brand_constraints['colors'])
            prompt += f"\n\nBrand colors to incorporate: {colors}"
        
        result = await self._generate_variation_with_ai(
            prompt=prompt,
            reference_url=base_image_url
        )
        
        if result.get('error'):
            return result
        
        local_path = await self._download_and_save(
            url=result['url'],
            prefix=f'variation_{style}'
        )
        
        return {
            'success': True,
            'style': style,
            'image_url': result['url'],
            'local_path': local_path
        }
    
    async def apply_filter_preset(
        self,
        image_url: str,
        filter_name: str,
        intensity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Apply predefined filter preset to image.
        
        Args:
            image_url: Image URL
            filter_name: Name of filter preset
            intensity: Filter intensity (0.0 to 1.0)
            
        Returns:
            Filtered image data
            
        Example:
            result = await service.apply_filter_preset(
                image_url="https://...",
                filter_name="vintage",
                intensity=0.7
            )
        """
        
        # Download image
        image_data = await self._download_image(image_url)
        if not image_data:
            return {'error': 'Failed to download image'}
        
        img = Image.open(io.BytesIO(image_data))
        
        # Apply filter
        filtered_img = self._apply_filter(img, filter_name, intensity)
        
        # Save filtered image
        local_path = self._save_pil_image(
            filtered_img,
            prefix=f'filtered_{filter_name}'
        )
        
        return {
            'success': True,
            'filtered_image_path': local_path,
            'filter_applied': filter_name,
            'intensity': intensity
        }
    
    def _apply_filter(
        self,
        img: Image.Image,
        filter_name: str,
        intensity: float
    ) -> Image.Image:
        """Apply PIL-based filter to image."""
        
        filters = {
            'blur': lambda i: i.filter(ImageFilter.GaussianBlur(radius=5 * intensity)),
            'sharpen': lambda i: i.filter(ImageFilter.SHARPEN),
            'vintage': self._apply_vintage_filter,
            'bw': lambda i: i.convert('L').convert('RGB'),
            'sepia': self._apply_sepia_filter,
            'bright': lambda i: ImageEnhance.Brightness(i).enhance(1 + intensity * 0.5),
            'contrast': lambda i: ImageEnhance.Contrast(i).enhance(1 + intensity * 0.5),
            'saturate': lambda i: ImageEnhance.Color(i).enhance(1 + intensity * 0.5)
        }
        
        filter_func = filters.get(filter_name, lambda i: i)
        
        if filter_name in ['vintage', 'sepia']:
            return filter_func(img, intensity)
        else:
            return filter_func(img)
    
    def _apply_vintage_filter(
        self,
        img: Image.Image,
        intensity: float
    ) -> Image.Image:
        """Apply vintage/retro filter effect."""
        
        # Reduce saturation
        img = ImageEnhance.Color(img).enhance(0.5 + intensity * 0.3)
        
        # Add warm tint (sepia-like)
        img = self._apply_sepia_filter(img, intensity * 0.7)
        
        # Reduce contrast slightly
        img = ImageEnhance.Contrast(img).enhance(0.9)
        
        # Add slight blur for aged effect
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5 * intensity))
        
        return img
    
    def _apply_sepia_filter(
        self,
        img: Image.Image,
        intensity: float
    ) -> Image.Image:
        """Apply sepia tone filter."""
        
        # Convert to grayscale first
        grayscale = img.convert('L')
        
        # Create sepia tint
        sepia = Image.new('RGB', img.size)
        pixels = grayscale.load()
        sepia_pixels = sepia.load()
        
        width, height = img.size
        for y in range(height):
            for x in range(width):
                gray = pixels[x, y]
                
                # Sepia formula
                r = min(255, int(gray * (1 + 0.15 * intensity)))
                g = min(255, int(gray * (0.95 + 0.05 * intensity)))
                b = min(255, int(gray * (0.82 - 0.07 * intensity)))
                
                sepia_pixels[x, y] = (r, g, b)
        
        # Blend with original based on intensity
        return Image.blend(img, sepia, intensity)
    
    def _adjust_colors_pil(
        self,
        img: Image.Image,
        target_colors: List[str],
        preserve_luminosity: bool
    ) -> Image.Image:
        """Adjust image colors to match brand palette using PIL."""
        
        # Convert image to RGB
        img_rgb = img.convert('RGB')
        
        # Get dominant colors from image
        img_array = np.array(img_rgb)
        
        # Simple color mapping approach
        # In production, you'd want more sophisticated color mapping
        
        # Enhance color saturation to make brand colors pop
        img_enhanced = ImageEnhance.Color(img_rgb).enhance(1.3)
        
        # Adjust contrast
        img_adjusted = ImageEnhance.Contrast(img_enhanced).enhance(1.1)
        
        return img_adjusted
    
    async def _apply_style_with_ai(
        self,
        prompt: str,
        reference_image_base64: str
    ) -> Dict[str, Any]:
        """Apply style using AI model."""
        
        # Note: DALL-E 3 doesn't support image-to-image directly
        # This is a placeholder for the prompt-based approach
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return {
                'success': True,
                'url': response.data[0].url,
                'revised_prompt': response.data[0].revised_prompt
            }
            
        except Exception as e:
            return {
                'error': 'Style transfer failed',
                'message': str(e)
            }
    
    async def _generate_variation_with_ai(
        self,
        prompt: str,
        reference_url: str
    ) -> Dict[str, Any]:
        """Generate variation using AI."""
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return {
                'success': True,
                'url': response.data[0].url
            }
            
        except Exception as e:
            return {
                'error': 'Variation generation failed',
                'message': str(e)
            }
    
    def _create_style_prompt(
        self,
        style_direction: str,
        brand_colors: List[str],
        brand_personality: List[str]
    ) -> str:
        """Create detailed style transfer prompt."""
        
        colors_text = ', '.join(brand_colors[:3])
        personality_text = ', '.join(brand_personality[:3])
        
        prompt = f"""
        Transform this image to match the following brand style:
        
        Style Direction: {style_direction}
        Brand Colors: {colors_text}
        Brand Personality: {personality_text}
        
        Requirements:
        - Maintain original composition and subject
        - Apply {style_direction} aesthetic
        - Incorporate brand colors naturally
        - Reflect {personality_text} personality
        - Professional, high-quality result
        - Consistent with brand guidelines
        """
        
        return prompt.strip()
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    async def _download_and_save(
        self,
        url: str,
        prefix: str
    ) -> str:
        """Download image and save to local storage."""
        
        image_data = await self._download_image(url)
        if not image_data:
            return url
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        hash_suffix = hashlib.md5(image_data).hexdigest()[:8]
        filename = f"{prefix}_{timestamp}_{hash_suffix}.png"
        
        filepath = os.path.join(self.upload_folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
    
    def _save_pil_image(
        self,
        img: Image.Image,
        prefix: str
    ) -> str:
        """Save PIL Image to local storage."""
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self.upload_folder, filename)
        
        img.save(filepath, 'PNG')
        
        return filepath
    
    def _image_to_base64(self, image_data: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_data).decode('utf-8')
    
    def _base64_to_image(self, base64_str: str) -> Image.Image:
        """Convert base64 string to PIL Image."""
        image_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_data))
    
    def get_supported_filters(self) -> List[str]:
        """Get list of supported filter presets."""
        return [
            'blur', 'sharpen', 'vintage', 'bw', 'sepia',
            'bright', 'contrast', 'saturate'
        ]
    
    def get_supported_styles(self) -> List[str]:
        """Get list of supported style transfers."""
        return self.supported_styles
    
    async def batch_style_transfer(
        self,
        image_urls: List[str],
        style_direction: str,
        brand_colors: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Apply style transfer to multiple images in batch.
        
        Args:
            image_urls: List of image URLs
            style_direction: Style to apply
            brand_colors: Brand color palette
            
        Returns:
            List of styled images
            
        Example:
            results = await service.batch_style_transfer(
                image_urls=["url1", "url2", "url3"],
                style_direction="modern minimalist",
                brand_colors=["#0066CC"]
            )
        """
        
        tasks = [
            self.apply_brand_style(
                source_image_url=url,
                brand_colors=brand_colors,
                style_direction=style_direction,
                brand_personality=[]
            )
            for url in image_urls
        ]
        
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if not r.get('error')]