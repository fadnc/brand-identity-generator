from typing import Dict, Any
from openai import OpenAI
import os
import json


class MarketTrendAnalyzer:
    """
    Analyzes market trends and provides strategic insights for brand positioning.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_trends(self, industry: str, region: str = "Global") -> Dict[str, Any]:
        """
        Analyze current market trends for a specific industry and region.
        """
        
        # Get current trends
        current_trends = self._get_current_trends(industry, region)
        
        # Predict future trends
        future_predictions = self._predict_future_trends(industry, current_trends)
        
        # Identify opportunities
        opportunities = self._identify_opportunities(industry, current_trends)
        
        # Consumer behavior insights
        consumer_insights = self._analyze_consumer_behavior(industry, region)
        
        # Competitive landscape
        competitive_landscape = self._analyze_competitive_landscape(industry)
        
        return {
            'industry': industry,
            'region': region,
            'current_trends': current_trends,
            'future_predictions': future_predictions,
            'opportunities': opportunities,
            'consumer_insights': consumer_insights,
            'competitive_landscape': competitive_landscape,
            'recommendations': self._generate_recommendations(
                current_trends,
                opportunities,
                consumer_insights
            )
        }
    
    def _get_current_trends(self, industry: str, region: str) -> Dict[str, Any]:
        """
        Identify current market trends in the industry.
        """
        
        prompt = f"""
        Analyze current market trends in the {industry} industry for {region}.
        
        Provide insights on:
        1. Top 5 emerging trends shaping the industry
        2. Consumer preferences and behaviors
        3. Technology adoption patterns
        4. Sustainability and social responsibility trends
        5. Visual and aesthetic trends
        6. Communication and messaging trends
        7. Market growth indicators
        
        Return as JSON with keys: emerging_trends, consumer_preferences, technology_trends, 
        sustainability_trends, visual_trends, messaging_trends, market_growth
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a market research analyst providing data-driven trend analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'error': str(e),
                'emerging_trends': [],
                'message': 'Trend analysis failed'
            }
    
    def _predict_future_trends(
        self,
        industry: str,
        current_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict future trends based on current data.
        """
        
        prompt = f"""
        Based on current trends in the {industry} industry, predict future developments.
        
        Current Trends: {json.dumps(current_trends, indent=2)}
        
        Predict:
        1. Trends likely to grow in the next 1-2 years
        2. Trends likely to decline
        3. New emerging opportunities
        4. Potential disruptions
        5. Strategic recommendations for brands
        
        Return as JSON with keys: growing_trends, declining_trends, new_opportunities, 
        potential_disruptions, strategic_recommendations
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic futurist analyzing market trajectories."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'error': str(e),
                'growing_trends': [],
                'declining_trends': []
            }
    
    def _identify_opportunities(
        self,
        industry: str,
        current_trends: Dict[str, Any]
    ) -> list:
        """
        Identify specific brand opportunities based on trends.
        """
        
        prompt = f"""
        Identify specific brand opportunities in the {industry} industry.
        
        Current Market Trends: {json.dumps(current_trends, indent=2)}
        
        For each opportunity, provide:
        1. Opportunity description
        2. Target audience
        3. Competitive advantage potential
        4. Implementation difficulty (low/medium/high)
        5. Potential impact (low/medium/high)
        
        Return as JSON array with objects containing: opportunity, target_audience, 
        competitive_advantage, difficulty, impact
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a brand strategist identifying market opportunities."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('opportunities', [])
            
        except Exception as e:
            return []
    
    def _analyze_consumer_behavior(self, industry: str, region: str) -> Dict[str, Any]:
        """
        Analyze consumer behavior patterns in the industry.
        """
        
        prompt = f"""
        Analyze consumer behavior in the {industry} industry ({region}).
        
        Provide insights on:
        1. Primary motivations and pain points
        2. Decision-making factors
        3. Media consumption habits
        4. Brand loyalty patterns
        5. Price sensitivity
        6. Preferred communication channels
        7. Values and beliefs driving purchases
        
        Return as JSON with corresponding keys.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a consumer psychologist analyzing behavior patterns."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Consumer behavior analysis failed'
            }
    
    def _analyze_competitive_landscape(self, industry: str) -> Dict[str, Any]:
        """
        Analyze the competitive landscape.
        """
        
        prompt = f"""
        Analyze the competitive landscape in the {industry} industry.
        
        Provide:
        1. Market concentration (fragmented, moderately concentrated, highly concentrated)
        2. Barriers to entry
        3. Key success factors
        4. Common differentiation strategies
        5. Pricing dynamics
        6. Distribution channels
        
        Return as JSON with corresponding keys.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Competitive analysis failed'
            }
    
    def _generate_recommendations(
        self,
        current_trends: Dict[str, Any],
        opportunities: list,
        consumer_insights: Dict[str, Any]
    ) -> list:
        """
        Generate actionable recommendations based on all insights.
        """
        
        recommendations = []
        
        # Trend-based recommendations
        emerging_trends = current_trends.get('emerging_trends', [])
        if emerging_trends:
            recommendations.append({
                'category': 'Trend Alignment',
                'recommendation': f"Align brand positioning with emerging trend: {emerging_trends[0] if isinstance(emerging_trends, list) else emerging_trends}",
                'priority': 'high'
            })
        
        # Opportunity-based recommendations
        if opportunities:
            top_opportunity = opportunities[0]
            recommendations.append({
                'category': 'Market Opportunity',
                'recommendation': f"Explore opportunity: {top_opportunity.get('opportunity', 'N/A')}",
                'priority': 'high'
            })
        
        # Consumer-based recommendations
        primary_motivations = consumer_insights.get('primary_motivations', [])
        if primary_motivations:
            recommendations.append({
                'category': 'Consumer Alignment',
                'recommendation': f"Address key consumer motivation in messaging",
                'priority': 'medium'
            })
        
        # Add 2-3 more strategic recommendations
        recommendations.extend([
            {
                'category': 'Differentiation',
                'recommendation': 'Develop unique value proposition that stands out from competitors',
                'priority': 'high'
            },
            {
                'category': 'Digital Presence',
                'recommendation': 'Invest in digital-first brand experience',
                'priority': 'medium'
            }
        ])
        
        return recommendations[:5]  # Return top 5 recommendations