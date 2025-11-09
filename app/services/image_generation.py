"""
Image Generation Service - Handles AI-powered image generation for brand assets.

This service manages logo generation, image variations, and visual asset creation
using DALL-E 3 and other image generation models.
"""

from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
import os
import aiohttp
import asyncio
from PIL import Image
import io
import base64
from datetime import datetime
import hashlib


class ImageGenerationService:
    """
    Service for AI-powered image generation and manipulation.
    
    Handles logo creation, image variations, style transfers, and
    visual asset management for brand identities.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the image generation service.
        
        Args:
            openai_api_key: OpenAI API key (optional, uses env var if not provided)
        """
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Configuration
        self.default_model = "dall-e-3"
        self.default_size = "1024x1024"
        self.default_quality = "standard"
        self.max_retries = 3
        
        # Storage
        self.upload_folder = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
    
    async def generate_logo(
        self,
        business_name: str,
        industry: str,
        style_direction: str,
        brand_values: List[str],
        additional_context: str = None
    ) -> Dict[str, Any]:
        """
        Generate a professional logo using DALL-E 3.
        
        Args:
            business_name: Name of the business
            industry: Industry category
            style_direction: Visual style preference
            brand_values: List of brand values
            additional_context: Additional generation context
            
        Returns:
            Logo data with URL and metadata
            
        Example:
            logo = await service.generate_logo(
                business_name="TechStart",
                industry="Technology",
                style_direction="modern and minimalist",
                brand_values=["innovation", "trust"]
            )
        """
        
        # Craft detailed prompt
        prompt = self._create_logo_prompt(
            business_name=business_name,
            industry=industry,
            style_direction=style_direction,
            brand_values=brand_values,
            additional_context=additional_context
        )
        
        # Generate image
        result = await self._generate_image(
            prompt=prompt,
            size=self.default_size,
            quality="hd"  # High quality for logos
        )
        
        if result.get('error'):
            return result
        
        # Download and process image
        image_url = result['url']
        local_path = await self._download_and_save_image(
            url=image_url,
            filename_prefix=f"logo_{business_name.replace(' ', '_')}"
        )
        
        return {
            'success': True,
            'image_url': image_url,
            'local_path': local_path,
            'original_prompt': prompt,
            'revised_prompt': result.get('revised_prompt'),
            'generation_metadata': {
                'model': self.default_model,
                'size': self.default_size,
                'quality': 'hd',
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    
    async def generate_logo_variations(
        self,
        original_logo_url: str,
        variation_count: int = 3,
        style_direction: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate variations of an existing logo.
        
        Args:
            original_logo_url: URL of original logo
            variation_count: Number of variations to generate
            style_direction: Optional style modification
            
        Returns:
            List of logo variations
            
        Example:
            variations = await service.generate_logo_variations(
                original_logo_url="https://...",
                variation_count=3,
                style_direction="more colorful"
            )
        """
        
        variations = []
        
        # Generate variations in parallel
        tasks = [
            self._generate_logo_variation(
                original_logo_url,
                variation_number=i+1,
                style_direction=style_direction
            )
            for i in range(variation_count)
        ]
        
        variations = await asyncio.gather(*tasks)
        
        return [v for v in variations if not v.get('error')]
    
    async def _generate_logo_variation(
        self,
        original_url: str,
        variation_number: int,
        style_direction: str = None
    ) -> Dict[str, Any]:
        """Generate a single logo variation."""
        
        # Note: DALL-E 3 doesn't support direct image variations
        # We'll need to use DALL-E 2 or create new variations based on description
        
        prompt = f"""
        Create a logo variation (version {variation_number}).
        {"Style direction: " + style_direction if style_direction else "Explore alternative design approach."}
        
        Requirements:
        - Maintain brand recognition
        - Professional and scalable
        - Suitable for various applications
        - Clean, memorable design
        """
        
        result = await self._generate_image(
            prompt=prompt,
            size="1024x1024",
            quality="standard"
        )
        
        if result.get('error'):
            return result
        
        local_path = await self._download_and_save_image(
            url=result['url'],
            filename_prefix=f"logo_variation_{variation_number}"
        )
        
        return {
            'success': True,
            'variation_number': variation_number,
            'image_url': result['url'],
            'local_path': local_path,
            'revised_prompt': result.get('revised_prompt')
        }
    
    async def generate_social_media_assets(
        self,
        logo_url: str,
        brand_colors: List[str],
        business_name: str,
        asset_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate social media assets (covers, posts, etc.).
        
        Args:
            logo_url: URL of the logo
            brand_colors: List of brand color hex codes
            business_name: Business name
            asset_types: Types of assets to generate
            
        Returns:
            Dictionary of generated social media assets
            
        Example:
            assets = await service.generate_social_media_assets(
                logo_url="https://...",
                brand_colors=["#0066CC", "#003366"],
                business_name="TechStart",
                asset_types=["facebook_cover", "twitter_header"]
            )
        """
        
        if asset_types is None:
            asset_types = ["facebook_cover", "twitter_header", "instagram_post"]
        
        assets = {}
        
        for asset_type in asset_types:
            dimensions = self._get_social_dimensions(asset_type)
            
            prompt = self._create_social_asset_prompt(
                asset_type=asset_type,
                business_name=business_name,
                brand_colors=brand_colors
            )
            
            result = await self._generate_image(
                prompt=prompt,
                size=dimensions.get('dalle_size', '1024x1024')
            )
            
            if not result.get('error'):
                local_path = await self._download_and_save_image(
                    url=result['url'],
                    filename_prefix=f"social_{asset_type}"
                )
                
                assets[asset_type] = {
                    'image_url': result['url'],
                    'local_path': local_path,
                    'dimensions': dimensions,
                    'asset_type': asset_type
                }
        
        return assets
    
    async def generate_brand_mockup(
        self,
        logo_url: str,
        mockup_type: str,
        brand_colors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate brand mockups (business cards, letterhead, etc.).
        
        Args:
            logo_url: URL of the logo
            mockup_type: Type of mockup to generate
            brand_colors: Brand color palette
            
        Returns:
            Mockup image data
            
        Example:
            mockup = await service.generate_brand_mockup(
                logo_url="https://...",
                mockup_type="business_card",
                brand_colors=["#0066CC"]
            )
        """
        
        prompt = self._create_mockup_prompt(
            mockup_type=mockup_type,
            brand_colors=brand_colors or []
        )
        
        result = await self._generate_image(
            prompt=prompt,
            size="1024x1024"
        )
        
        if result.get('error'):
            return result
        
        local_path = await self._download_and_save_image(
            url=result['url'],
            filename_prefix=f"mockup_{mockup_type}"
        )
        
        return {
            'success': True,
            'mockup_type': mockup_type,
            'image_url': result['url'],
            'local_path': local_path
        }
    
    async def _generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Core image generation method with retry logic.
        
        Args:
            prompt: Image generation prompt
            size: Image size (1024x1024, 1792x1024, 1024x1792)
            quality: Image quality (standard or hd)
            n: Number of images to generate
            
        Returns:
            Generation result with URL
        """
        
        for attempt in range(self.max_retries):
            try:
                response = await self.client.images.generate(
                    model=self.default_model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=n
                )
                
                return {
                    'success': True,
                    'url': response.data[0].url,
                    'revised_prompt': response.data[0].revised_prompt
                }
                
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a content policy violation
                if "content_policy_violation" in error_msg.lower():
                    return {
                        'error': 'Content policy violation',
                        'message': 'Prompt violated content policy. Please modify and try again.'
                    }
                
                # Retry on other errors
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                return {
                    'error': 'Generation failed',
                    'message': str(e)
                }
        
        return {
            'error': 'Generation failed after retries'
        }
    
    async def _download_and_save_image(
        self,
        url: str,
        filename_prefix: str
    ) -> str:
        """
        Download image from URL and save locally.
        
        Args:
            url: Image URL
            filename_prefix: Prefix for filename
            
        Returns:
            Local file path
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download image: {response.status}")
                    
                    image_data = await response.read()
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            hash_suffix = hashlib.md5(image_data).hexdigest()[:8]
            filename = f"{filename_prefix}_{timestamp}_{hash_suffix}.png"
            
            filepath = os.path.join(self.upload_folder, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return filepath
            
        except Exception as e:
            print(f"Error downloading image: {e}")
            return url  # Return original URL if download fails
    
    def _create_logo_prompt(
        self,
        business_name: str,
        industry: str,
        style_direction: str,
        brand_values: List[str],
        additional_context: str = None
    ) -> str:
        """Create optimized prompt for logo generation."""
        
        values_text = ", ".join(brand_values[:3])
        
        prompt = f"""
        Design a professional, minimalist logo for "{business_name}".
        
        Style: {style_direction}
        Industry: {industry}
        Brand Values: {values_text}
        {f'Context: {additional_context}' if additional_context else ''}
        
        Requirements:
        - Clean, scalable vector-style design
        - Works in color and monochrome
        - Memorable and distinctive
        - Professional and timeless
        - Suitable for digital and print
        - White or transparent background
        - No text unless part of brand name
        - Simple, iconic, recognizable
        """
        
        return prompt.strip()
    
    def _create_social_asset_prompt(
        self,
        asset_type: str,
        business_name: str,
        brand_colors: List[str]
    ) -> str:
        """Create prompt for social media asset generation."""
        
        colors_text = ", ".join(brand_colors[:2])
        
        prompt = f"""
        Create a {asset_type.replace('_', ' ')} design for "{business_name}".
        
        Brand Colors: {colors_text}
        
        Requirements:
        - Professional and engaging
        - Brand-consistent
        - Optimized for social media
        - Eye-catching but elegant
        - Space for logo/text overlay
        """
        
        return prompt.strip()
    
    def _create_mockup_prompt(
        self,
        mockup_type: str,
        brand_colors: List[str]
    ) -> str:
        """Create prompt for brand mockup generation."""
        
        mockup_descriptions = {
            'business_card': 'professional business card design, clean layout',
            'letterhead': 'elegant letterhead design, corporate stationery',
            'envelope': 'branded envelope design, professional correspondence',
            'website': 'modern website homepage mockup, clean UI'
        }
        
        description = mockup_descriptions.get(
            mockup_type,
            f'{mockup_type} mockup design'
        )
        
        prompt = f"""
        Create a photorealistic mockup showing {description}.
        
        Style: Professional, modern, minimalist
        Colors: {', '.join(brand_colors) if brand_colors else 'Elegant neutral tones'}
        
        High quality, realistic presentation.
        """
        
        return prompt.strip()
    
    def _get_social_dimensions(self, asset_type: str) -> Dict[str, Any]:
        """Get dimensions for social media asset types."""
        
        dimensions_map = {
            'facebook_cover': {
                'width': 820,
                'height': 312,
                'dalle_size': '1792x1024'
            },
            'twitter_header': {
                'width': 1500,
                'height': 500,
                'dalle_size': '1792x1024'
            },
            'instagram_post': {
                'width': 1080,
                'height': 1080,
                'dalle_size': '1024x1024'
            },
            'linkedin_banner': {
                'width': 1584,
                'height': 396,
                'dalle_size': '1792x1024'
            },
            'youtube_thumbnail': {
                'width': 1280,
                'height': 720,
                'dalle_size': '1792x1024'
            }
        }
        
        return dimensions_map.get(asset_type, {
            'width': 1024,
            'height': 1024,
            'dalle_size': '1024x1024'
        })
    
    def get_supported_sizes(self) -> List[str]:
        """Get list of supported image sizes."""
        return ["1024x1024", "1792x1024", "1024x1792"]
    
    def get_supported_qualities(self) -> List[str]:
        """Get list of supported quality levels."""
        return ["standard", "hd"]
    
    def estimate_generation_cost(
        self,
        count: int,
        quality: str = "standard"
    ) -> float:
        """
        Estimate cost of image generation.
        
        Args:
            count: Number of images
            quality: Quality level
            
        Returns:
            Estimated cost in USD
        """
        
        # DALL-E 3 pricing (as of 2024)
        price_per_image = {
            'standard': 0.04,  # $0.04 per image
            'hd': 0.08         # $0.08 per image
        }
        
        return count * price_per_image.get(quality, 0.04)