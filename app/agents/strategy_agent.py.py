from openai import AsyncOpenAI
from typing import Dict, Any, List, Optional
import json


class StrategyAgent:
    """
    Specialized agent for brand strategy, positioning, and market analysis.
    Defines the strategic foundation that guides all other agents.
    """
    
    def __init__(self, openai_api_key: str):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        
    async def analyze(
        self,
        business_name: str,
        industry: str,
        target_audience: str,
        brand_values: List[str],
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive brand strategy analysis.
        """
        
        # Competitive analysis
        competitive_analysis = await self._analyze_competitors(
            industry=industry,
            competitors=competitors or []
        )
        
        # Define brand positioning
        positioning = await self._define_positioning(
            business_name=business_name,
            industry=industry,
            target_audience=target_audience,
            brand_values=brand_values,
            competitive_landscape=competitive_analysis
        )
        
        # Define brand voice and personality
        brand_voice = await self._define_brand_voice(
            brand_values=brand_values,
            target_audience=target_audience,
            positioning=positioning
        )
        
        # Visual direction recommendations
        visual_direction = await self._recommend_visual_direction(
            brand_values=brand_values,
            industry=industry,
            positioning=positioning
        )
        
        # Target demographics deep dive
        demographics = await self._analyze_demographics(
            target_audience=target_audience,
            industry=industry
        )
        
        # Messaging framework
        messaging = await self._create_messaging_framework(
            positioning=positioning,
            brand_voice=brand_voice,
            target_audience=target_audience
        )
        
        return {
            'business_name': business_name,
            'industry': industry,
            'brand_values': brand_values,
            'competitive_analysis': competitive_analysis,
            'positioning': positioning,
            'brand_voice': brand_voice,
            'visual_direction': visual_direction,
            'demographics': demographics,
            'messaging_framework': messaging
        }
    
    async def _analyze_competitors(
        self,
        industry: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze competitive landscape and identify differentiation opportunities.
        """
        
        prompt = f"""
        Analyze the competitive landscape for the {industry} industry.
        
        Known Competitors: {', '.join(competitors) if competitors else 'N/A'}
        
        Provide a comprehensive competitive analysis including:
        1. Common positioning strategies in this industry
        2. Visual identity trends (colors, styles, typography)
        3. Messaging and tone patterns
        4. Gaps and opportunities for differentiation
        5. Best practices to follow
        6. Pitfalls to avoid
        
        Return as structured JSON with the following keys:
        - common_strategies
        - visual_trends
        - messaging_patterns
        - differentiation_opportunities
        - best_practices
        - avoid_pitfalls
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a competitive intelligence analyst specializing in brand strategy. Provide insights in JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            return analysis
        except json.JSONDecodeError:
            return {
                "common_strategies": ["Quality focus", "Innovation emphasis"],
                "visual_trends": ["Modern", "Minimalist"],
                "messaging_patterns": ["Customer-centric"],
                "differentiation_opportunities": ["Unique value proposition needed"],
                "best_practices": ["Clear communication"],
                "avoid_pitfalls": ["Generic messaging"]
            }
    
    async def _define_positioning(
        self,
        business_name: str,
        industry: str,
        target_audience: str,
        brand_values: List[str],
        competitive_landscape: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Define unique brand positioning statement and value proposition.
        """
        
        prompt = f"""
        Create a brand positioning strategy for "{business_name}".
        
        Context:
        - Industry: {industry}
        - Target Audience: {target_audience}
        - Brand Values: {', '.join(brand_values)}
        - Competitive Landscape: {json.dumps(competitive_landscape, indent=2)}
        
        Create:
        1. Positioning statement (one sentence)
        2. Unique value proposition
        3. Key differentiators (3-5 points)
        4. Brand promise
        5. Elevator pitch (30 seconds)
        
        Return as JSON with keys: positioning_statement, value_proposition, differentiators, brand_promise, elevator_pitch
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand positioning expert. Create compelling positioning that differentiates from competitors."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _define_brand_voice(
        self,
        brand_values: List[str],
        target_audience: str,
        positioning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Define brand voice and personality traits.
        """
        
        prompt = f"""
        Define the brand voice and personality.
        
        Brand Values: {', '.join(brand_values)}
        Target Audience: {target_audience}
        Positioning: {positioning.get('positioning_statement', '')}
        
        Define:
        1. Voice characteristics (4-5 adjectives with descriptions)
        2. Tone variations for different contexts (formal, casual, supportive, etc.)
        3. Do's and Don'ts for communication
        4. Example phrases that embody the voice
        5. Voice spectrum (where the brand sits on these scales):
           - Formal vs Casual
           - Serious vs Playful
           - Respectful vs Irreverent
           - Enthusiastic vs Matter-of-fact
        
        Return as JSON with keys: characteristics, tone_variations, dos_and_donts, example_phrases, voice_spectrum
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a brand voice specialist. Create a distinctive, consistent voice."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _recommend_visual_direction(
        self,
        brand_values: List[str],
        industry: str,
        positioning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend visual direction for design agent.
        """
        
        prompt = f"""
        Recommend visual direction for brand identity.
        
        Brand Values: {', '.join(brand_values)}
        Industry: {industry}
        Positioning: {positioning.get('positioning_statement', '')}
        
        Provide recommendations for:
        1. Overall aesthetic (e.g., modern, classic, bold, minimal, organic)
        2. Color psychology and palette direction
        3. Shape language (geometric, organic, angular, rounded)
        4. Visual style references
        5. Imagery style
        6. Design principles to follow
        
        Return as JSON with keys: aesthetic, color_direction, shape_language, style_references, imagery_style, design_principles
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative director specializing in visual brand identity."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _analyze_demographics(
        self,
        target_audience: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Deep dive into target demographics and psychographics.
        """
        
        prompt = f"""
        Analyze target demographics for: {target_audience} in {industry}.
        
        Provide detailed analysis:
        1. Age range and generation characteristics
        2. Income level and spending habits
        3. Education and profession
        4. Psychographics (values, interests, lifestyle)
        5. Media consumption habits
        6. Pain points and needs
        7. Decision-making factors
        8. Communication preferences
        
        Return as JSON with corresponding keys.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a market research analyst specializing in consumer insights."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _create_messaging_framework(
        self,
        positioning: Dict[str, Any],
        brand_voice: Dict[str, Any],
        target_audience: str
    ) -> Dict[str, Any]:
        """
        Create comprehensive messaging framework.
        """
        
        prompt = f"""
        Create a messaging framework.
        
        Positioning: {positioning.get('positioning_statement', '')}
        Brand Voice: {json.dumps(brand_voice.get('characteristics', []))}
        Target Audience: {target_audience}
        
        Create:
        1. Primary message (main headline)
        2. Supporting messages (3-5 key points)
        3. Proof points for each message
        4. Call-to-action framework
        5. Message hierarchy for different channels (website, social, email, etc.)
        
        Return as JSON with keys: primary_message, supporting_messages, proof_points, cta_framework, channel_hierarchy
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a messaging strategist. Create clear, compelling message frameworks."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)