from openai import AsyncOpenAI
from typing import Dict, Any, List
import json


class ConsistencyChecker:
    """
    Validates brand consistency across all generated assets.
    Ensures visual identity, copy, and strategy are aligned.
    """
    
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        
    async def validate(
        self,
        strategy: Dict[str, Any],
        visual_identity: Dict[str, Any],
        brand_copy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive consistency check across all brand elements.
        """
        
        # Check strategy-visual alignment
        visual_alignment = await self._check_visual_alignment(strategy, visual_identity)
        
        # Check strategy-copy alignment
        copy_alignment = await self._check_copy_alignment(strategy, brand_copy)
        
        # Check voice consistency across copy
        voice_consistency = await self._check_voice_consistency(
            brand_copy,
            strategy.get('brand_voice', {})
        )
        
        # Check visual-copy harmony
        visual_copy_harmony = await self._check_visual_copy_harmony(
            visual_identity,
            brand_copy
        )
        
        # Calculate overall consistency score
        overall_score = self._calculate_overall_score({
            'visual_alignment': visual_alignment,
            'copy_alignment': copy_alignment,
            'voice_consistency': voice_consistency,
            'visual_copy_harmony': visual_copy_harmony
        })
        
        # Determine if refinement is needed
        needs_refinement = overall_score < 0.75
        
        # Compile issues and recommendations
        issues = []
        recommendations = []
        
        for check_name, check_result in [
            ('visual_alignment', visual_alignment),
            ('copy_alignment', copy_alignment),
            ('voice_consistency', voice_consistency),
            ('visual_copy_harmony', visual_copy_harmony)
        ]:
            if check_result.get('score', 1.0) < 0.75:
                issues.extend(check_result.get('issues', []))
                recommendations.extend(check_result.get('recommendations', []))
        
        return {
            'score': overall_score,
            'needs_refinement': needs_refinement,
            'issues': issues,
            'recommendations': recommendations,
            'detailed_scores': {
                'visual_alignment': visual_alignment.get('score', 0),
                'copy_alignment': copy_alignment.get('score', 0),
                'voice_consistency': voice_consistency.get('score', 0),
                'visual_copy_harmony': visual_copy_harmony.get('score', 0)
            }
        }
    
    async def _check_visual_alignment(
        self,
        strategy: Dict[str, Any],
        visual_identity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if visual identity aligns with brand strategy.
        """
        
        prompt = f"""
        Evaluate if the visual identity aligns with the brand strategy.
        
        Brand Strategy:
        - Positioning: {strategy.get('positioning', {}).get('positioning_statement', '')}
        - Values: {', '.join(strategy.get('brand_values', []))}
        - Visual Direction: {json.dumps(strategy.get('visual_direction', {}), indent=2)}
        
        Visual Identity:
        - Logo Description: {visual_identity.get('logo', {}).get('revised_prompt', '')}
        - Color Palette: {json.dumps(visual_identity.get('color_palette', {}), indent=2)}
        - Typography: {json.dumps(visual_identity.get('typography', {}), indent=2)}
        
        Evaluate:
        1. Does the visual identity reflect the brand values?
        2. Are the colors appropriate for the positioning?
        3. Does the overall aesthetic match the strategic direction?
        4. Is the visual complexity appropriate for the target audience?
        
        Provide:
        - Alignment score (0.0 to 1.0)
        - Specific issues (if any)
        - Recommendations for improvement
        
        Return as JSON with keys: score, issues (array), recommendations (array), analysis
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand consistency analyst. Evaluate alignment objectively."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _check_copy_alignment(
        self,
        strategy: Dict[str, Any],
        brand_copy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if copy aligns with brand strategy and messaging framework.
        """
        
        prompt = f"""
        Evaluate if the brand copy aligns with the strategy.
        
        Brand Strategy:
        - Positioning: {strategy.get('positioning', {}).get('positioning_statement', '')}
        - Messaging Framework: {json.dumps(strategy.get('messaging_framework', {}), indent=2)}
        - Target Demographics: {json.dumps(strategy.get('demographics', {}), indent=2)}
        
        Brand Copy:
        - Taglines: {json.dumps([t.get('tagline', '') for t in brand_copy.get('taglines', [])[:3]])}
        - Brand Story: {brand_copy.get('brand_story', {}).get('short', '')}
        - Website Hero: {brand_copy.get('website_copy', {}).get('hero', {})}
        
        Evaluate:
        1. Does the copy communicate the positioning effectively?
        2. Are the key messages present in the copy?
        3. Is the copy appropriate for the target audience?
        4. Does the copy differentiate from competitors?
        
        Provide:
        - Alignment score (0.0 to 1.0)
        - Specific issues (if any)
        - Recommendations for improvement
        
        Return as JSON with keys: score, issues (array), recommendations (array), analysis
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand messaging analyst. Evaluate strategic alignment."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _check_voice_consistency(
        self,
        brand_copy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if brand voice is consistent across all copy.
        """
        
        # Extract sample copy from different sections
        samples = {
            'tagline': brand_copy.get('taglines', [{}])[0].get('tagline', ''),
            'brand_story': brand_copy.get('brand_story', {}).get('short', ''),
            'website_hero': str(brand_copy.get('website_copy', {}).get('hero', {})),
            'social_bio': str(brand_copy.get('social_content', {}).get('bios', {})),
            'email': str(brand_copy.get('marketing_copy', {}).get('email_marketing', {}))
        }
        
        prompt = f"""
        Evaluate voice consistency across different brand copy.
        
        Defined Brand Voice:
        - Characteristics: {json.dumps(brand_voice.get('characteristics', []))}
        - Tone Variations: {json.dumps(brand_voice.get('tone_variations', {}))}
        - Voice Spectrum: {json.dumps(brand_voice.get('voice_spectrum', {}))}
        
        Copy Samples:
        {json.dumps(samples, indent=2)}
        
        Evaluate:
        1. Is the voice consistent across all samples?
        2. Do the samples reflect the defined voice characteristics?
        3. Are tone variations appropriate for each context?
        4. Are there any jarring inconsistencies?
        
        Provide:
        - Consistency score (0.0 to 1.0)
        - Specific inconsistencies (if any)
        - Recommendations for improvement
        
        Return as JSON with keys: score, issues (array), recommendations (array), analysis
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand voice analyst. Evaluate consistency across touchpoints."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _check_visual_copy_harmony(
        self,
        visual_identity: Dict[str, Any],
        brand_copy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if visual identity and copy work harmoniously together.
        """
        
        prompt = f"""
        Evaluate if visual identity and copy create a harmonious brand experience.
        
        Visual Identity:
        - Style Guide: {json.dumps(visual_identity.get('style_guide', {}), indent=2)}
        - Color Palette: {json.dumps(visual_identity.get('color_palette', {}), indent=2)}
        
        Brand Copy:
        - Taglines: {json.dumps([t.get('tagline', '') for t in brand_copy.get('taglines', [])[:3]])}
        - Brand Story: {brand_copy.get('brand_story', {}).get('short', '')}
        
        Evaluate:
        1. Do the visual and verbal elements complement each other?
        2. Is there a cohesive brand personality across both?
        3. Would they work well together in practical applications?
        4. Do the visual and copy convey the same brand perception?
        
        Provide:
        - Harmony score (0.0 to 1.0)
        - Specific misalignments (if any)
        - Recommendations for better integration
        
        Return as JSON with keys: score, issues (array), recommendations (array), analysis
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand experience analyst. Evaluate holistic brand harmony."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _calculate_overall_score(self, scores: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate weighted overall consistency score.
        """
        
        weights = {
            'visual_alignment': 0.25,
            'copy_alignment': 0.30,
            'voice_consistency': 0.25,
            'visual_copy_harmony': 0.20
        }
        
        total_score = 0.0
        for check_name, weight in weights.items():
            check_score = scores.get(check_name, {}).get('score', 0.0)
            total_score += check_score * weight
        
        return round(total_score, 2)