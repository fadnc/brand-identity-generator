"""
Competitor Analysis Service - Analyzes competitors and market positioning.

This service performs competitive intelligence gathering and analysis to help
position the brand effectively in the market.
"""

from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
import os
import json
import asyncio


class CompetitorAnalysisService:
    """
    Service for analyzing competitors and market landscape.
    
    Provides competitive intelligence, market positioning analysis,
    and differentiation opportunities for brand strategy.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the competitor analysis service.
        
        Args:
            openai_api_key: OpenAI API key (optional, uses env var if not provided)
        """
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
    
    async def analyze_competitors(
        self,
        industry: str,
        competitors: List[str],
        target_audience: str = None,
        brand_values: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive competitor analysis.
        
        Args:
            industry: Industry/market category
            competitors: List of competitor names
            target_audience: Target demographic
            brand_values: List of brand values
            
        Returns:
            Complete competitor analysis
            
        Example:
            analysis = await service.analyze_competitors(
                industry="E-commerce",
                competitors=["Amazon", "Shopify"],
                target_audience="Small business owners"
            )
        """
        
        # Analyze each competitor
        competitor_profiles = await self._analyze_competitor_profiles(
            competitors,
            industry
        )
        
        # Market landscape analysis
        market_landscape = await self._analyze_market_landscape(
            industry,
            competitors
        )
        
        # Identify positioning gaps
        positioning_gaps = await self._identify_positioning_gaps(
            industry,
            competitor_profiles,
            target_audience,
            brand_values
        )
        
        # SWOT analysis
        swot_analysis = await self._perform_swot_analysis(
            industry,
            competitor_profiles,
            brand_values
        )
        
        # Differentiation opportunities
        differentiation = await self._identify_differentiation_opportunities(
            industry,
            competitor_profiles,
            positioning_gaps,
            brand_values
        )
        
        # Competitive pricing analysis
        pricing_analysis = await self._analyze_competitive_pricing(
            industry,
            competitors
        )
        
        return {
            'competitor_profiles': competitor_profiles,
            'market_landscape': market_landscape,
            'positioning_gaps': positioning_gaps,
            'swot_analysis': swot_analysis,
            'differentiation_opportunities': differentiation,
            'pricing_analysis': pricing_analysis,
            'recommendations': self._generate_recommendations(
                positioning_gaps,
                differentiation,
                swot_analysis
            )
        }
    
    async def _analyze_competitor_profiles(
        self,
        competitors: List[str],
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze individual competitor profiles.
        
        Args:
            competitors: List of competitor names
            industry: Industry context
            
        Returns:
            List of competitor profile dictionaries
        """
        
        # Analyze competitors in parallel
        tasks = [
            self._analyze_single_competitor(competitor, industry)
            for competitor in competitors
        ]
        
        profiles = await asyncio.gather(*tasks)
        return profiles
    
    async def _analyze_single_competitor(
        self,
        competitor: str,
        industry: str
    ) -> Dict[str, Any]:
        """
        Analyze a single competitor in depth.
        
        Args:
            competitor: Competitor name
            industry: Industry context
            
        Returns:
            Competitor profile dictionary
        """
        
        prompt = f"""
        Analyze the competitor "{competitor}" in the {industry} industry.
        
        Provide a comprehensive profile including:
        
        1. Company Overview:
           - Brief description
           - Market position
           - Years in business (estimate)
           - Company size
        
        2. Brand Identity:
           - Brand positioning
           - Key messaging
           - Visual style (describe their typical aesthetic)
           - Brand personality traits
        
        3. Target Audience:
           - Primary demographic
           - Customer personas
           - Market segments served
        
        4. Product/Service Offerings:
           - Core offerings
           - Unique features
           - Pricing tier
        
        5. Marketing Strategy:
           - Key channels used
           - Content strategy
           - Social media presence
           - Advertising approach
        
        6. Strengths:
           - What they do well
           - Competitive advantages
           - Market reputation
        
        7. Weaknesses:
           - Known pain points
           - Customer complaints
           - Areas where they underperform
        
        8. Visual Identity:
           - Typical color schemes
           - Logo style
           - Overall design aesthetic
        
        Return as JSON with these exact keys: company_overview, brand_identity,
        target_audience, offerings, marketing_strategy, strengths, weaknesses, visual_identity
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Provide detailed, factual analysis based on publicly available information."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower for more factual analysis
            )
            
            profile = json.loads(response.choices[0].message.content)
            profile['competitor_name'] = competitor
            
            return profile
            
        except Exception as e:
            print(f"Error analyzing competitor {competitor}: {e}")
            return {
                'competitor_name': competitor,
                'error': str(e),
                'company_overview': f"Analysis unavailable for {competitor}"
            }
    
    async def _analyze_market_landscape(
        self,
        industry: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze overall market landscape and trends.
        
        Args:
            industry: Industry to analyze
            competitors: List of competitors
            
        Returns:
            Market landscape analysis
        """
        
        prompt = f"""
        Analyze the market landscape for the {industry} industry.
        
        Key competitors include: {', '.join(competitors)}
        
        Provide analysis on:
        
        1. Market Size & Growth:
           - Current market size estimate
           - Growth rate and trends
           - Future projections
        
        2. Market Concentration:
           - Is the market fragmented or concentrated?
           - Who are the market leaders?
           - Market share distribution
        
        3. Industry Trends:
           - Emerging trends
           - Technology disruptions
           - Consumer behavior shifts
        
        4. Barriers to Entry:
           - What makes it difficult to enter this market?
           - Required resources
           - Regulatory considerations
        
        5. Competitive Dynamics:
           - How fierce is the competition?
           - Common competitive strategies
           - Price wars or value competition?
        
        6. Customer Expectations:
           - What do customers expect from brands in this space?
           - Evolving needs
           - Pain points in the market
        
        Return as JSON with keys: market_size, market_concentration, trends,
        barriers_to_entry, competitive_dynamics, customer_expectations
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market research analyst specializing in competitive landscapes."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error analyzing market landscape: {e}")
            return {'error': str(e)}
    
    async def _identify_positioning_gaps(
        self,
        industry: str,
        competitor_profiles: List[Dict],
        target_audience: str,
        brand_values: List[str]
    ) -> Dict[str, Any]:
        """
        Identify gaps in market positioning that can be exploited.
        
        Args:
            industry: Industry context
            competitor_profiles: Analyzed competitor data
            target_audience: Target demographic
            brand_values: Desired brand values
            
        Returns:
            Positioning gaps analysis
        """
        
        # Summarize competitor positioning
        positioning_summary = "\n".join([
            f"- {c['competitor_name']}: {c.get('brand_identity', {}).get('brand_positioning', 'N/A')}"
            for c in competitor_profiles
            if 'error' not in c
        ])
        
        prompt = f"""
        Identify positioning gaps in the {industry} market.
        
        Current Competitor Positioning:
        {positioning_summary}
        
        Target Audience: {target_audience or 'General'}
        Desired Brand Values: {', '.join(brand_values or ['N/A'])}
        
        Identify:
        
        1. Underserved Segments:
           - Which customer segments are not well-served?
           - What needs are not being met?
        
        2. Positioning Gaps:
           - What positioning strategies are NOT being used?
           - Where is there white space in the market?
        
        3. Value Proposition Opportunities:
           - What value propositions are missing?
           - How can we differentiate?
        
        4. Messaging Gaps:
           - What messages are competitors not using?
           - What emotional appeals are underutilized?
        
        5. Audience Gaps:
           - Which demographics are underserved?
           - What psychographics are being ignored?
        
        6. Price Positioning:
           - Are there gaps in pricing tiers?
           - Premium or budget opportunities?
        
        Return as JSON with keys: underserved_segments, positioning_gaps,
        value_proposition_opportunities, messaging_gaps, audience_gaps, price_positioning
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a brand strategy consultant identifying market opportunities."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error identifying positioning gaps: {e}")
            return {'error': str(e)}
    
    async def _perform_swot_analysis(
        self,
        industry: str,
        competitor_profiles: List[Dict],
        brand_values: List[str]
    ) -> Dict[str, Any]:
        """
        Perform SWOT analysis based on competitive landscape.
        
        Args:
            industry: Industry context
            competitor_profiles: Competitor data
            brand_values: Brand values
            
        Returns:
            SWOT analysis
        """
        
        # Extract competitor strengths and weaknesses
        competitor_strengths = []
        competitor_weaknesses = []
        
        for profile in competitor_profiles:
            if 'error' not in profile:
                competitor_strengths.extend(
                    profile.get('strengths', {}).get('competitive_advantages', [])
                    if isinstance(profile.get('strengths'), dict)
                    else []
                )
                competitor_weaknesses.extend(
                    profile.get('weaknesses', {}).get('known_pain_points', [])
                    if isinstance(profile.get('weaknesses'), dict)
                    else []
                )
        
        prompt = f"""
        Perform a SWOT analysis for a new brand entering the {industry} market.
        
        Competitor Strengths: {', '.join(competitor_strengths[:5]) if competitor_strengths else 'None identified'}
        Competitor Weaknesses: {', '.join(competitor_weaknesses[:5]) if competitor_weaknesses else 'None identified'}
        Our Brand Values: {', '.join(brand_values or ['To be determined'])}
        
        Provide:
        
        1. Strengths (Internal Positive):
           - What advantages do we have?
           - What resources can we leverage?
           - What do we do better than competitors?
        
        2. Weaknesses (Internal Negative):
           - What do we lack?
           - Where are we vulnerable?
           - What should we improve?
        
        3. Opportunities (External Positive):
           - What market opportunities exist?
           - What trends can we capitalize on?
           - What competitor gaps can we fill?
        
        4. Threats (External Negative):
           - What obstacles do we face?
           - What are competitors doing well?
           - What market challenges exist?
        
        For each quadrant, provide 5-7 specific points.
        
        Return as JSON with keys: strengths (array), weaknesses (array),
        opportunities (array), threats (array)
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic planning consultant conducting SWOT analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error performing SWOT analysis: {e}")
            return {
                'strengths': [],
                'weaknesses': [],
                'opportunities': [],
                'threats': [],
                'error': str(e)
            }
    
    async def _identify_differentiation_opportunities(
        self,
        industry: str,
        competitor_profiles: List[Dict],
        positioning_gaps: Dict,
        brand_values: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Identify specific opportunities for brand differentiation.
        
        Args:
            industry: Industry context
            competitor_profiles: Competitor data
            positioning_gaps: Identified gaps
            brand_values: Brand values
            
        Returns:
            List of differentiation opportunities
        """
        
        prompt = f"""
        Identify specific differentiation opportunities in the {industry} market.
        
        Context:
        - Number of competitors analyzed: {len(competitor_profiles)}
        - Positioning gaps identified: {json.dumps(positioning_gaps.get('positioning_gaps', 'Various'))}
        - Brand values: {', '.join(brand_values or ['To be determined'])}
        
        Identify 7-10 specific differentiation opportunities. For each, provide:
        
        1. Opportunity Title (brief, catchy)
        2. Description (what makes this unique)
        3. Implementation Difficulty (low/medium/high)
        4. Potential Impact (low/medium/high)
        5. Required Resources
        6. Time to Market
        7. Competitive Advantage Duration
        
        Focus on opportunities that are:
        - Actually achievable for a new brand
        - Meaningful to customers
        - Difficult for competitors to copy
        - Aligned with modern market trends
        
        Return as JSON with key "opportunities" containing an array of objects
        with keys: title, description, difficulty, impact, resources, time_to_market,
        advantage_duration
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a brand differentiation strategist identifying unique positioning opportunities."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('opportunities', [])
            
        except Exception as e:
            print(f"Error identifying differentiation: {e}")
            return []
    
    async def _analyze_competitive_pricing(
        self,
        industry: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze competitive pricing strategies.
        
        Args:
            industry: Industry context
            competitors: List of competitors
            
        Returns:
            Pricing analysis
        """
        
        prompt = f"""
        Analyze pricing strategies in the {industry} market.
        
        Key competitors: {', '.join(competitors)}
        
        Provide:
        
        1. Pricing Models:
           - Common pricing models used (subscription, one-time, freemium, etc.)
           - Typical price ranges
        
        2. Price Positioning:
           - Premium players and their pricing
           - Budget options available
           - Mid-market positioning
        
        3. Value Perception:
           - What justifies higher prices?
           - What drives budget positioning?
        
        4. Pricing Strategies:
           - Penetration pricing
           - Value-based pricing
           - Competitive pricing
        
        5. Recommendations:
           - Optimal pricing strategy for new entrant
           - Price positioning suggestions
        
        Return as JSON with keys: pricing_models, price_positioning,
        value_perception, pricing_strategies, recommendations
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pricing strategy consultant."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error analyzing pricing: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(
        self,
        positioning_gaps: Dict,
        differentiation: List[Dict],
        swot: Dict
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Args:
            positioning_gaps: Identified gaps
            differentiation: Differentiation opportunities
            swot: SWOT analysis
            
        Returns:
            List of recommendations
        """
        
        recommendations = []
        
        # From positioning gaps
        if positioning_gaps.get('positioning_gaps'):
            recommendations.append(
                f"Exploit positioning gap: {positioning_gaps['positioning_gaps']}"
                if isinstance(positioning_gaps['positioning_gaps'], str)
                else "Focus on identified positioning gaps in the market"
            )
        
        # From differentiation (top 3)
        top_diff = sorted(
            differentiation,
            key=lambda x: (
                1 if x.get('impact') == 'high' else 0,
                1 if x.get('difficulty') == 'low' else 0
            ),
            reverse=True
        )[:3]
        
        for diff in top_diff:
            recommendations.append(
                f"Differentiation opportunity: {diff.get('title', 'N/A')}"
            )
        
        # From SWOT opportunities
        opportunities = swot.get('opportunities', [])
        if opportunities:
            recommendations.append(
                f"Capitalize on market opportunity: {opportunities[0]}"
                if isinstance(opportunities[0], str)
                else "Leverage identified market opportunities"
            )
        
        return recommendations[:5]  # Top 5 recommendations
    
    async def quick_competitor_scan(
        self,
        industry: str,
        competitor_name: str
    ) -> Dict[str, Any]:
        """
        Quick scan of a single competitor (faster, less detailed).
        
        Args:
            industry: Industry context
            competitor_name: Competitor to analyze
            
        Returns:
            Quick competitor summary
            
        Example:
            scan = await service.quick_competitor_scan(
                industry="SaaS",
                competitor_name="Salesforce"
            )
        """
        
        prompt = f"""
        Provide a quick competitive scan of {competitor_name} in the {industry} industry.
        
        Brief summary including:
        1. Market position (2-3 sentences)
        2. Key strengths (3 points)
        3. Key weaknesses (3 points)
        4. Target audience
        5. Pricing tier (budget/mid/premium)
        
        Be concise. Return as JSON.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Faster model for quick scans
                messages=[
                    {"role": "system", "content": "You are a competitive analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': str(e)}