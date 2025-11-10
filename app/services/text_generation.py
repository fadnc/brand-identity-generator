"""
Text + Generation Service - Combined text and image generation for marketing assets.

This service creates complete marketing materials by combining AI-generated text
with visuals, producing ready-to-use branded assets like social posts, ads, and more.
"""

from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
import os
import json
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import hashlib
import textwrap


class TextPlusGenerationService:
    """
    Service for generating complete marketing assets with text + visuals.
    
    Combines AI text generation with image generation and composition to create
    ready-to-use marketing materials like social media posts, ads, infographics, etc.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the text + generation service.
        
        Args:
            openai_api_key: OpenAI API key (optional, uses env var if not provided)
        """
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Configuration
        self.upload_folder = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Default fonts (system fonts)
        self.default_fonts = {
            'heading': self._get_system_font('bold', 72),
            'subheading': self._get_system_font('regular', 48),
            'body': self._get_system_font('regular', 32),
            'caption': self._get_system_font('regular', 24)
        }
    
    async def generate_social_post(
        self,
        topic: str,
        platform: str,
        brand_colors: List[str],
        brand_name: str,
        logo_url: str = None,
        style: str = "modern"
    ) -> Dict[str, Any]:
        """
        Generate complete social media post with image and caption.
        
        Args:
            topic: Topic or theme of the post
            platform: Social platform (instagram, facebook, twitter, linkedin)
            brand_colors: Brand color palette
            brand_name: Business name
            logo_url: Optional logo URL
            style: Visual style preference
            
        Returns:
            Complete social post with image and caption
            
        Example:
            post = await service.generate_social_post(
                topic="New product launch",
                platform="instagram",
                brand_colors=["#0066CC", "#FF6600"],
                brand_name="TechStart",
                style="modern"
            )
        """
        
        # Generate caption
        caption_data = await self._generate_social_caption(
            topic=topic,
            platform=platform,
            brand_name=brand_name
        )
        
        # Generate post image
        image_data = await self._generate_social_image(
            topic=topic,
            platform=platform,
            caption=caption_data['caption'],
            brand_colors=brand_colors,
            brand_name=brand_name,
            style=style
        )
        
        # Composite image with text overlay if needed
        final_image = await self._create_text_overlay(
            image_url=image_data['image_url'],
            text=caption_data['headline'],
            brand_colors=brand_colors,
            layout=self._get_platform_layout(platform)
        )
        
        return {
            'success': True,
            'platform': platform,
            'caption': caption_data['caption'],
            'hashtags': caption_data['hashtags'],
            'image_url': image_data['image_url'],
            'final_image_path': final_image,
            'dimensions': self._get_platform_dimensions(platform),
            'best_posting_time': self._suggest_posting_time(platform),
            'engagement_tips': self._get_engagement_tips(platform)
        }
    
    async def generate_ad_creative(
        self,
        product_name: str,
        value_proposition: str,
        target_audience: str,
        ad_platform: str,
        brand_colors: List[str],
        cta_text: str = None
    ) -> Dict[str, Any]:
        """
        Generate complete ad creative with headline, body, and visual.
        
        Args:
            product_name: Product or service name
            value_proposition: Key value proposition
            target_audience: Target audience description
            ad_platform: Ad platform (facebook, google, instagram, linkedin)
            brand_colors: Brand color palette
            cta_text: Call-to-action text (optional)
            
        Returns:
            Complete ad creative package
            
        Example:
            ad = await service.generate_ad_creative(
                product_name="SmartWidget Pro",
                value_proposition="10x faster than competitors",
                target_audience="Small business owners",
                ad_platform="facebook",
                brand_colors=["#0066CC"],
                cta_text="Start Free Trial"
            )
        """
        
        # Generate ad copy
        ad_copy = await self._generate_ad_copy(
            product_name=product_name,
            value_proposition=value_proposition,
            target_audience=target_audience,
            ad_platform=ad_platform
        )
        
        # Generate CTA if not provided
        if not cta_text:
            cta_text = ad_copy.get('cta_suggestions', ['Learn More'])[0]
        
        # Generate ad visual
        ad_visual = await self._generate_ad_visual(
            product_name=product_name,
            headline=ad_copy['headline'],
            brand_colors=brand_colors,
            ad_platform=ad_platform
        )
        
        # Create composite ad with text
        final_ad = await self._compose_ad_creative(
            background_url=ad_visual['image_url'],
            headline=ad_copy['headline'],
            body=ad_copy['body'][:100],  # Truncate for visual
            cta=cta_text,
            brand_colors=brand_colors,
            ad_platform=ad_platform
        )
        
        return {
            'success': True,
            'ad_platform': ad_platform,
            'headline': ad_copy['headline'],
            'body_copy': ad_copy['body'],
            'cta': cta_text,
            'image_url': ad_visual['image_url'],
            'final_ad_path': final_ad,
            'dimensions': self._get_ad_dimensions(ad_platform),
            'targeting_suggestions': self._suggest_targeting(target_audience),
            'budget_recommendation': self._suggest_budget(ad_platform)
        }
    
    async def generate_infographic(
        self,
        title: str,
        data_points: List[Dict[str, Any]],
        brand_colors: List[str],
        style: str = "modern"
    ) -> Dict[str, Any]:
        """
        Generate data-driven infographic with text and visuals.
        
        Args:
            title: Infographic title
            data_points: List of data points with labels and values
            brand_colors: Brand color palette
            style: Visual style
            
        Returns:
            Generated infographic
            
        Example:
            infographic = await service.generate_infographic(
                title="2024 Marketing Stats",
                data_points=[
                    {"label": "Email ROI", "value": "42x", "description": "Return on investment"},
                    {"label": "Social Engagement", "value": "+156%", "description": "Year over year"}
                ],
                brand_colors=["#0066CC", "#FF6600"],
                style="modern"
            )
        """
        
        # Generate infographic layout
        layout = self._design_infographic_layout(
            title=title,
            data_points=data_points,
            style=style
        )
        
        # Generate visual elements for each data point
        visuals = await self._generate_infographic_elements(
            data_points=data_points,
            brand_colors=brand_colors,
            style=style
        )
        
        # Compose complete infographic
        infographic_path = self._compose_infographic(
            title=title,
            data_points=data_points,
            layout=layout,
            brand_colors=brand_colors
        )
        
        return {
            'success': True,
            'title': title,
            'infographic_path': infographic_path,
            'data_points_count': len(data_points),
            'style': style,
            'dimensions': {'width': 1080, 'height': 1920},  # Instagram story size
            'share_ready': True
        }
    
    async def generate_email_banner(
        self,
        headline: str,
        subheadline: str,
        brand_colors: List[str],
        cta_text: str = "Learn More",
        include_image: bool = True
    ) -> Dict[str, Any]:
        """
        Generate email header/banner with text and visuals.
        
        Args:
            headline: Main headline
            subheadline: Supporting text
            brand_colors: Brand color palette
            cta_text: Call-to-action text
            include_image: Whether to include background image
            
        Returns:
            Email banner image
            
        Example:
            banner = await service.generate_email_banner(
                headline="Summer Sale",
                subheadline="Up to 50% off everything",
                brand_colors=["#0066CC"],
                cta_text="Shop Now"
            )
        """
        
        # Generate background if requested
        if include_image:
            background = await self._generate_email_background(
                theme=headline,
                brand_colors=brand_colors
            )
            background_url = background['image_url']
        else:
            background_url = None
        
        # Create banner with text
        banner_path = self._create_email_banner(
            headline=headline,
            subheadline=subheadline,
            cta_text=cta_text,
            brand_colors=brand_colors,
            background_url=background_url
        )
        
        return {
            'success': True,
            'headline': headline,
            'subheadline': subheadline,
            'cta': cta_text,
            'banner_path': banner_path,
            'dimensions': {'width': 600, 'height': 200},
            'html_ready': True
        }
    
    async def generate_presentation_slide(
        self,
        slide_title: str,
        bullet_points: List[str],
        brand_colors: List[str],
        slide_type: str = "content"
    ) -> Dict[str, Any]:
        """
        Generate presentation slide with professional layout.
        
        Args:
            slide_title: Slide title
            bullet_points: List of content points
            brand_colors: Brand color palette
            slide_type: Type (title, content, image, closing)
            
        Returns:
            Presentation slide image
            
        Example:
            slide = await service.generate_presentation_slide(
                slide_title="Our Approach",
                bullet_points=["Innovation first", "Customer focused", "Data driven"],
                brand_colors=["#0066CC"],
                slide_type="content"
            )
        """
        
        # Generate slide background/template
        if slide_type in ['image', 'title']:
            background = await self._generate_slide_background(
                theme=slide_title,
                brand_colors=brand_colors,
                slide_type=slide_type
            )
            background_url = background['image_url']
        else:
            background_url = None
        
        # Create slide layout
        slide_path = self._create_presentation_slide(
            title=slide_title,
            content=bullet_points,
            brand_colors=brand_colors,
            slide_type=slide_type,
            background_url=background_url
        )
        
        return {
            'success': True,
            'title': slide_title,
            'slide_path': slide_path,
            'slide_type': slide_type,
            'dimensions': {'width': 1920, 'height': 1080},
            'points_count': len(bullet_points)
        }
    
    async def _generate_social_caption(
        self,
        topic: str,
        platform: str,
        brand_name: str
    ) -> Dict[str, Any]:
        """Generate social media caption with AI."""
        
        platform_limits = {
            'instagram': 2200,
            'twitter': 280,
            'facebook': 500,
            'linkedin': 3000
        }
        
        char_limit = platform_limits.get(platform, 500)
        
        prompt = f"""
        Create an engaging social media caption for {platform}.
        
        Topic: {topic}
        Brand: {brand_name}
        Character Limit: {char_limit}
        
        Include:
        - Attention-grabbing headline (short, 5-8 words)
        - Engaging caption text
        - 3-5 relevant hashtags
        - Call-to-action
        
        Return as JSON with keys: headline, caption, hashtags (array)
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a social media expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'headline': topic,
                'caption': f"Check out our latest on {topic}!",
                'hashtags': ['#brand', '#new', '#exciting']
            }
    
    async def _generate_social_image(
        self,
        topic: str,
        platform: str,
        caption: str,
        brand_colors: List[str],
        brand_name: str,
        style: str
    ) -> Dict[str, Any]:
        """Generate social media post image."""
        
        colors_text = ', '.join(brand_colors[:2])
        
        prompt = f"""
        Create a {style} social media post image for {platform}.
        
        Topic: {topic}
        Brand Colors: {colors_text}
        Style: {style}, professional, eye-catching
        
        Design for {platform} with engaging visual that supports: "{caption[:100]}"
        """
        
        dimensions = self._get_platform_dimensions(platform)
        size = self._map_dimensions_to_dalle_size(dimensions)
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            return {
                'image_url': response.data[0].url,
                'dimensions': dimensions
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _generate_ad_copy(
        self,
        product_name: str,
        value_proposition: str,
        target_audience: str,
        ad_platform: str
    ) -> Dict[str, Any]:
        """Generate ad copy with AI."""
        
        prompt = f"""
        Create compelling ad copy for {ad_platform}.
        
        Product: {product_name}
        Value Prop: {value_proposition}
        Audience: {target_audience}
        
        Provide:
        - Headline (5-8 words, attention-grabbing)
        - Body copy (2-3 sentences, benefit-focused)
        - 3 CTA suggestions
        
        Return as JSON with keys: headline, body, cta_suggestions (array)
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert ad copywriter."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'headline': f"Discover {product_name}",
                'body': f"{value_proposition}. Perfect for {target_audience}.",
                'cta_suggestions': ['Learn More', 'Get Started', 'Try Now']
            }
    
    async def _generate_ad_visual(
        self,
        product_name: str,
        headline: str,
        brand_colors: List[str],
        ad_platform: str
    ) -> Dict[str, Any]:
        """Generate ad visual with AI."""
        
        colors_text = ', '.join(brand_colors[:2])
        
        prompt = f"""
        Create a professional ad image for {product_name}.
        
        Headline: "{headline}"
        Brand Colors: {colors_text}
        Platform: {ad_platform}
        
        Style: Clean, modern, professional
        Focus: Product benefit and value
        """
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return {'image_url': response.data[0].url}
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _create_text_overlay(
        self,
        image_url: str,
        text: str,
        brand_colors: List[str],
        layout: str = "center"
    ) -> str:
        """Create text overlay on image using PIL."""
        
        # Download image
        image_data = await self._download_image(image_url)
        if not image_data:
            return image_url
        
        img = Image.open(io.BytesIO(image_data))
        draw = ImageDraw.Draw(img)
        
        # Get primary brand color
        text_color = brand_colors[0] if brand_colors else "#FFFFFF"
        
        # Add text
        font = self.default_fonts['heading']
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width, img_height = img.size
        
        if layout == "center":
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        elif layout == "top":
            x = (img_width - text_width) // 2
            y = 50
        else:  # bottom
            x = (img_width - text_width) // 2
            y = img_height - text_height - 50
        
        # Draw text with shadow for visibility
        draw.text((x+2, y+2), text, font=font, fill="#000000")  # Shadow
        draw.text((x, y), text, font=font, fill=text_color)  # Main text
        
        # Save
        return self._save_pil_image(img, 'text_overlay')
    
    async def _compose_ad_creative(
        self,
        background_url: str,
        headline: str,
        body: str,
        cta: str,
        brand_colors: List[str],
        ad_platform: str
    ) -> str:
        """Compose complete ad creative with all elements."""
        
        # Download background
        image_data = await self._download_image(background_url)
        if not image_data:
            # Create blank canvas if download fails
            img = Image.new('RGB', (1080, 1080), color=brand_colors[0] if brand_colors else '#0066CC')
        else:
            img = Image.open(io.BytesIO(image_data))
            img = img.resize((1080, 1080))
        
        draw = ImageDraw.Draw(img)
        
        # Add headline
        headline_font = self.default_fonts['heading']
        draw.text((50, 100), headline, font=headline_font, fill="#FFFFFF")
        
        # Add body
        body_font = self.default_fonts['body']
        wrapped_body = textwrap.fill(body, width=40)
        draw.text((50, 200), wrapped_body, font=body_font, fill="#FFFFFF")
        
        # Add CTA button
        cta_bg_color = brand_colors[1] if len(brand_colors) > 1 else brand_colors[0]
        draw.rectangle([(50, 900), (300, 980)], fill=cta_bg_color)
        cta_font = self.default_fonts['subheading']
        draw.text((100, 920), cta, font=cta_font, fill="#FFFFFF")
        
        return self._save_pil_image(img, f'ad_{ad_platform}')
    
    def _compose_infographic(
        self,
        title: str,
        data_points: List[Dict[str, Any]],
        layout: Dict,
        brand_colors: List[str]
    ) -> str:
        """Compose infographic with PIL."""
        
        # Create canvas
        img = Image.new('RGB', (1080, 1920), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Add title
        title_font = self.default_fonts['heading']
        draw.text((50, 50), title, font=title_font, fill=brand_colors[0])
        
        # Add data points
        y_offset = 200
        for i, point in enumerate(data_points):
            color = brand_colors[i % len(brand_colors)]
            
            # Value
            value_font = self.default_fonts['heading']
            draw.text((50, y_offset), point['value'], font=value_font, fill=color)
            
            # Label
            label_font = self.default_fonts['subheading']
            draw.text((50, y_offset + 100), point['label'], font=label_font, fill="#333333")
            
            # Description
            desc_font = self.default_fonts['body']
            wrapped_desc = textwrap.fill(point.get('description', ''), width=50)
            draw.text((50, y_offset + 160), wrapped_desc, font=desc_font, fill="#666666")
            
            y_offset += 350
        
        return self._save_pil_image(img, 'infographic')
    
    def _create_email_banner(
        self,
        headline: str,
        subheadline: str,
        cta_text: str,
        brand_colors: List[str],
        background_url: str = None
    ) -> str:
        """Create email banner with PIL."""
        
        # Create or load background
        if background_url:
            # Would download and use background
            img = Image.new('RGB', (600, 200), color=brand_colors[0])
        else:
            img = Image.new('RGB', (600, 200), color=brand_colors[0])
        
        draw = ImageDraw.Draw(img)
        
        # Add headline
        headline_font = self.default_fonts['subheading']
        draw.text((30, 30), headline, font=headline_font, fill="#FFFFFF")
        
        # Add subheadline
        sub_font = self.default_fonts['body']
        draw.text((30, 90), subheadline, font=sub_font, fill="#FFFFFF")
        
        # Add CTA
        cta_color = brand_colors[1] if len(brand_colors) > 1 else "#FFFFFF"
        draw.rectangle([(30, 140), (200, 180)], fill=cta_color)
        cta_font = self.default_fonts['caption']
        draw.text((60, 152), cta_text, font=cta_font, fill="#000000")
        
        return self._save_pil_image(img, 'email_banner')
    
    def _create_presentation_slide(
        self,
        title: str,
        content: List[str],
        brand_colors: List[str],
        slide_type: str,
        background_url: str = None
    ) -> str:
        """Create presentation slide with PIL."""
        
        img = Image.new('RGB', (1920, 1080), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Add brand color bar
        draw.rectangle([(0, 0), (1920, 100)], fill=brand_colors[0])
        
        # Add title
        title_font = self.default_fonts['heading']
        draw.text((100, 20), title, font=title_font, fill="#FFFFFF")
        
        # Add content bullets
        y_offset = 250
        bullet_font = self.default_fonts['body']
        for bullet in content:
            draw.text((150, y_offset), f"• {bullet}", font=bullet_font, fill="#333333")
            y_offset += 100
        
        return self._save_pil_image(img, f'slide_{slide_type}')
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
            return None
        except:
            return None
    
    def _save_pil_image(self, img: Image.Image, prefix: str) -> str:
        """Save PIL Image to file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self.upload_folder, filename)
        img.save(filepath, 'PNG')
        return filepath
    
    def _get_system_font(self, weight: str, size: int) -> ImageFont.FreeTypeFont:
        """Get system font or fallback to default."""
        try:
            if weight == 'bold':
                return ImageFont.truetype("Arial-Bold.ttf", size)
            else:
                return ImageFont.truetype("Arial.ttf", size)
        except:
            return ImageFont.load_default()
    
    def _get_platform_dimensions(self, platform: str) -> Dict[str, int]:
        """Get optimal dimensions for platform."""
        dimensions = {
            'instagram': {'width': 1080, 'height': 1080},
            'instagram_story': {'width': 1080, 'height': 1920},
            'facebook': {'width': 1200, 'height': 630},
            'twitter': {'width': 1200, 'height': 675},
            'linkedin': {'width': 1200, 'height': 627},
            'pinterest': {'width': 1000, 'height': 1500}
        }
        return dimensions.get(platform, {'width': 1080, 'height': 1080})
    
    def _get_ad_dimensions(self, platform: str) -> Dict[str, int]:
        """Get ad dimensions for platform."""
        dimensions = {
            'facebook': {'width': 1200, 'height': 628},
            'instagram': {'width': 1080, 'height': 1080},
            'google': {'width': 1200, 'height': 628},
            'linkedin': {'width': 1200, 'height': 627}
        }
        return dimensions.get(platform, {'width': 1200, 'height': 628})
    
    def _map_dimensions_to_dalle_size(self, dimensions: Dict[str, int]) -> str:
        """Map dimensions to DALL-E supported sizes."""
        width = dimensions.get('width', 1024)
        height = dimensions.get('height', 1024)
        
        if width == height:
            return "1024x1024"
        elif width > height:
            return "1792x1024"
        else:
            return "1024x1792"
    
    def _get_platform_layout(self, platform: str) -> str:
        """Get recommended text layout for platform."""
        layouts = {
            'instagram': 'center',
            'facebook': 'top',
            'twitter': 'center',
            'linkedin': 'top'
        }
        return layouts.get(platform, 'center')
    
    def _design_infographic_layout(
        self,
        title: str,
        data_points: List[Dict],
        style: str
    ) -> Dict[str, Any]:
        """Design infographic layout."""
        return {
            'title_position': 'top',
            'data_layout': 'vertical',
            'spacing': 300,
            'style': style
        }
    
    async def _generate_infographic_elements(
        self,
        data_points: List[Dict],
        brand_colors: List[str],
        style: str
    ) -> List[Dict]:
        """Generate visual elements for infographic."""
        # Placeholder - in production would generate icons/graphics
        return []
    
    async def _generate_email_background(
        self,
        theme: str,
        brand_colors: List[str]
    ) -> Dict[str, Any]:
        """Generate email background image."""
        # Would use DALL-E here in production
        return {'image_url': ''}
    
    async def _generate_slide_background(
        self,
        theme: str,
        brand_colors: List[str],
        slide_type: str
    ) -> Dict[str, Any]:
        """Generate slide background."""
        # Would use DALL-E here in production
        return {'image_url': ''}
    
    def _suggest_posting_time(self, platform: str) -> str:
        """Suggest optimal posting time."""
        times = {
            'instagram': '11 AM - 1 PM or 7 PM - 9 PM',
            'facebook': '1 PM - 3 PM',
            'twitter': '12 PM - 1 PM or 5 PM - 6 PM',
            'linkedin': '7 AM - 9 AM or 12 PM - 1 PM'
        }
        return times.get(platform, 'Peak engagement hours')
    
    def _get_engagement_tips(self, platform: str) -> List[str]:
        """Get engagement tips for platform."""
        tips = {
            'instagram': [
                'Use 3-5 relevant hashtags',
                'Include a question to encourage comments',
                'Post during peak hours',
                'Use Instagram Stories for behind-the-scenes'
            ],
            'facebook': [
                'Keep text concise',
                'Use eye-catching visuals',
                'Ask questions to drive engagement',
                'Post when audience is most active'
            ],
            'twitter': [
                'Keep it under 280 characters',
                'Use 1-2 hashtags',
                'Include visual content',
                'Tweet during peak times'
            ],
            'linkedin': [
                'Share professional insights',
                'Use relevant hashtags',
                'Post during business hours',
                'Engage with comments'
            ]
        }
        return tips.get(platform, ['Post consistently', 'Engage with audience'])
    
    def _suggest_targeting(self, audience: str) -> Dict[str, Any]:
        """Suggest ad targeting parameters."""
        return {
            'demographics': {
                'age_range': '25-54',
                'interests': ['Business', 'Technology', 'Innovation'],
                'behaviors': ['Online shopping', 'Tech early adopters']
            },
            'geographic': 'Major metro areas',
            'devices': ['Desktop', 'Mobile'],
            'audience_size': 'Estimated 50K-100K reach'
        }
    
    def _suggest_budget(self, platform: str) -> Dict[str, Any]:
        """Suggest ad budget recommendations."""
        budgets = {
            'facebook': {
                'daily_minimum': 5,
                'recommended_daily': 20,
                'monthly_range': '150-600',
                'cpc_estimate': '0.50-2.00'
            },
            'instagram': {
                'daily_minimum': 5,
                'recommended_daily': 15,
                'monthly_range': '150-500',
                'cpc_estimate': '0.70-2.50'
            },
            'google': {
                'daily_minimum': 10,
                'recommended_daily': 30,
                'monthly_range': '300-900',
                'cpc_estimate': '1.00-5.00'
            },
            'linkedin': {
                'daily_minimum': 10,
                'recommended_daily': 50,
                'monthly_range': '500-1500',
                'cpc_estimate': '2.00-7.00'
            }
        }
        
        return budgets.get(platform, {
            'daily_minimum': 10,
            'recommended_daily': 25,
            'monthly_range': '200-750',
            'cpc_estimate': '1.00-3.00'
        })
    
    async def generate_multi_platform_campaign(
        self,
        campaign_theme: str,
        brand_name: str,
        brand_colors: List[str],
        platforms: List[str] = None,
        logo_url: str = None
    ) -> Dict[str, Any]:
        """
        Generate complete multi-platform marketing campaign.
        
        Args:
            campaign_theme: Campaign theme or topic
            brand_name: Business name
            brand_colors: Brand color palette
            platforms: List of platforms (default: all)
            logo_url: Optional logo URL
            
        Returns:
            Complete campaign with assets for all platforms
            
        Example:
            campaign = await service.generate_multi_platform_campaign(
                campaign_theme="Summer Sale 2024",
                brand_name="TechStart",
                brand_colors=["#0066CC", "#FF6600"],
                platforms=["instagram", "facebook", "twitter", "linkedin"]
            )
        """
        
        if platforms is None:
            platforms = ['instagram', 'facebook', 'twitter', 'linkedin']
        
        # Generate campaign messaging
        campaign_messaging = await self._generate_campaign_messaging(
            theme=campaign_theme,
            brand_name=brand_name
        )
        
        # Generate assets for each platform
        platform_assets = {}
        
        for platform in platforms:
            asset = await self.generate_social_post(
                topic=campaign_theme,
                platform=platform,
                brand_colors=brand_colors,
                brand_name=brand_name,
                logo_url=logo_url
            )
            platform_assets[platform] = asset
        
        # Generate campaign calendar
        calendar = self._generate_posting_calendar(platforms)
        
        return {
            'success': True,
            'campaign_theme': campaign_theme,
            'messaging': campaign_messaging,
            'platform_assets': platform_assets,
            'posting_calendar': calendar,
            'platforms_count': len(platforms),
            'estimated_reach': self._estimate_campaign_reach(platforms),
            'campaign_duration': '2-4 weeks recommended'
        }
    
    async def _generate_campaign_messaging(
        self,
        theme: str,
        brand_name: str
    ) -> Dict[str, Any]:
        """Generate campaign messaging framework."""
        
        prompt = f"""
        Create a campaign messaging framework for {brand_name}.
        
        Campaign Theme: {theme}
        
        Provide:
        - Main campaign tagline
        - Key messages (3-5 points)
        - Tone and voice guidelines
        - Hashtag suggestions
        
        Return as JSON with keys: tagline, key_messages (array), tone, hashtags (array)
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a campaign strategist."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'tagline': theme,
                'key_messages': ['Innovation', 'Quality', 'Value'],
                'tone': 'Professional and engaging',
                'hashtags': ['#brand', '#campaign', '#new']
            }
    
    def _generate_posting_calendar(self, platforms: List[str]) -> List[Dict[str, Any]]:
        """Generate posting calendar for campaign."""
        
        calendar = []
        days = ['Monday', 'Wednesday', 'Friday']
        
        for i, day in enumerate(days):
            for platform in platforms:
                posting_time = self._suggest_posting_time(platform)
                calendar.append({
                    'day': day,
                    'platform': platform,
                    'suggested_time': posting_time,
                    'week': 'Week 1' if i < 3 else 'Week 2'
                })
        
        return calendar
    
    def _estimate_campaign_reach(self, platforms: List[str]) -> Dict[str, Any]:
        """Estimate campaign reach across platforms."""
        
        base_reach = {
            'instagram': 5000,
            'facebook': 8000,
            'twitter': 3000,
            'linkedin': 4000
        }
        
        total_reach = sum(base_reach.get(p, 2000) for p in platforms)
        
        return {
            'estimated_impressions': f"{total_reach:,} - {total_reach * 2:,}",
            'estimated_engagement': f"{int(total_reach * 0.03):,} - {int(total_reach * 0.08):,}",
            'platforms': len(platforms),
            'notes': 'Estimates based on organic reach. Paid promotion will increase reach significantly.'
        }
    
    async def generate_quote_graphic(
        self,
        quote_text: str,
        author: str,
        brand_colors: List[str],
        background_style: str = "minimal"
    ) -> Dict[str, Any]:
        """
        Generate quote graphic for social media.
        
        Args:
            quote_text: Quote text
            author: Quote author or source
            brand_colors: Brand color palette
            background_style: Background style (minimal, bold, image)
            
        Returns:
            Quote graphic image
            
        Example:
            quote = await service.generate_quote_graphic(
                quote_text="Innovation distinguishes between a leader and a follower",
                author="Steve Jobs",
                brand_colors=["#0066CC"],
                background_style="minimal"
            )
        """
        
        # Generate background if needed
        if background_style == "image":
            background = await self._generate_quote_background(brand_colors)
            background_url = background.get('image_url')
        else:
            background_url = None
        
        # Create quote graphic
        quote_path = self._create_quote_graphic(
            quote_text=quote_text,
            author=author,
            brand_colors=brand_colors,
            background_url=background_url,
            style=background_style
        )
        
        return {
            'success': True,
            'quote': quote_text,
            'author': author,
            'graphic_path': quote_path,
            'dimensions': {'width': 1080, 'height': 1080},
            'style': background_style
        }
    
    def _create_quote_graphic(
        self,
        quote_text: str,
        author: str,
        brand_colors: List[str],
        background_url: str = None,
        style: str = "minimal"
    ) -> str:
        """Create quote graphic with PIL."""
        
        # Create canvas
        if style == "minimal":
            img = Image.new('RGB', (1080, 1080), color=brand_colors[0])
        else:
            img = Image.new('RGB', (1080, 1080), color='#FFFFFF')
        
        draw = ImageDraw.Draw(img)
        
        # Add quote text (wrapped)
        quote_font = self.default_fonts['subheading']
        wrapped_quote = textwrap.fill(f'"{quote_text}"', width=30)
        
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), wrapped_quote, font=quote_font)
        text_height = bbox[3] - bbox[1]
        
        y_position = (1080 - text_height) // 2 - 50
        
        # Draw quote
        text_color = "#FFFFFF" if style == "minimal" else "#333333"
        draw.multiline_text(
            (100, y_position),
            wrapped_quote,
            font=quote_font,
            fill=text_color,
            align='center'
        )
        
        # Add author
        author_font = self.default_fonts['body']
        author_text = f"— {author}"
        draw.text(
            (100, y_position + text_height + 50),
            author_text,
            font=author_font,
            fill=text_color
        )
        
        return self._save_pil_image(img, 'quote_graphic')
    
    async def _generate_quote_background(
        self,
        brand_colors: List[str]
    ) -> Dict[str, Any]:
        """Generate abstract background for quote."""
        
        colors_text = ', '.join(brand_colors[:2])
        
        prompt = f"""
        Create an abstract, minimal background suitable for quote text overlay.
        
        Colors: {colors_text}
        Style: Soft, subtle, professional
        Ensure good contrast for white or dark text
        """
        
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return {'image_url': response.data[0].url}
            
        except Exception as e:
            return {'error': str(e)}
    
    async def batch_generate_assets(
        self,
        asset_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple assets in batch.
        
        Args:
            asset_requests: List of asset generation requests
            
        Returns:
            List of generated assets
            
        Example:
            requests = [
                {'type': 'social_post', 'platform': 'instagram', ...},
                {'type': 'ad_creative', 'ad_platform': 'facebook', ...},
                {'type': 'email_banner', 'headline': '...', ...}
            ]
            assets = await service.batch_generate_assets(requests)
        """
        
        tasks = []
        
        for request in asset_requests:
            asset_type = request.get('type')
            
            if asset_type == 'social_post':
                task = self.generate_social_post(**request)
            elif asset_type == 'ad_creative':
                task = self.generate_ad_creative(**request)
            elif asset_type == 'email_banner':
                task = self.generate_email_banner(**request)
            elif asset_type == 'quote_graphic':
                task = self.generate_quote_graphic(**request)
            else:
                continue
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        return [r for r in results if not isinstance(r, Exception) and not r.get('error')]
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported social platforms."""
        return [
            'instagram',
            'facebook',
            'twitter',
            'linkedin',
            'pinterest',
            'tiktok'
        ]
    
    def get_supported_ad_platforms(self) -> List[str]:
        """Get list of supported ad platforms."""
        return [
            'facebook',
            'instagram',
            'google',
            'linkedin',
            'twitter'
        ]
    
    def get_asset_types(self) -> List[str]:
        """Get list of supported asset types."""
        return [
            'social_post',
            'ad_creative',
            'infographic',
            'email_banner',
            'presentation_slide',
            'quote_graphic',
            'multi_platform_campaign'
        ]
    
    async def optimize_asset_for_platform(
        self,
        asset_path: str,
        source_platform: str,
        target_platform: str
    ) -> Dict[str, Any]:
        """
        Optimize asset for different platform.
        
        Args:
            asset_path: Path to source asset
            source_platform: Original platform
            target_platform: Target platform
            
        Returns:
            Optimized asset
            
        Example:
            optimized = await service.optimize_asset_for_platform(
                asset_path="/path/to/instagram_post.png",
                source_platform="instagram",
                target_platform="twitter"
            )
        """
        
        # Load source image
        img = Image.open(asset_path)
        
        # Get target dimensions
        target_dims = self._get_platform_dimensions(target_platform)
        
        # Resize and crop to fit
        img_resized = self._resize_for_platform(img, target_dims)
        
        # Save optimized version
        optimized_path = self._save_pil_image(
            img_resized,
            f'{target_platform}_optimized'
        )
        
        return {
            'success': True,
            'source_platform': source_platform,
            'target_platform': target_platform,
            'optimized_path': optimized_path,
            'dimensions': target_dims
        }
    
    def _resize_for_platform(
        self,
        img: Image.Image,
        target_dims: Dict[str, int]
    ) -> Image.Image:
        """Resize image to fit platform dimensions."""
        
        target_width = target_dims['width']
        target_height = target_dims['height']
        
        # Calculate aspect ratios
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Image is wider, fit to height
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, fit to width
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact dimensions
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img_resized.crop((left, top, right, bottom))