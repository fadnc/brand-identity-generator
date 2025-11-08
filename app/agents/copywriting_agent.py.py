from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List
import json


class CopywritingAgent(BaseAgent):
    """
    Specialized agent for brand copywriting, messaging, and content generation.
    Creates taglines, brand stories, marketing copy, and social media content.
    
    Inherits from BaseAgent for common functionality like LLM calls, logging, and error handling.
    """
    
    def __init__(self, openai_api_key: str):
        super().__init__(openai_api_key, agent_name="CopywritingAgent")
        
        # Copywriting-specific configuration
        self.temperature = 0.8  # Higher for more creative outputs
        
    async def execute(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main execution method - generates complete brand copy.
        
        Args:
            business_name: Name of the business
            strategy: Brand strategy from StrategyAgent
            brand_voice: Brand voice characteristics
            **kwargs: Additional parameters
            
        Returns:
            Complete brand copy package
        """
        # Validate inputs
        self._validate_input(
            required_fields=["business_name", "strategy", "brand_voice"],
            business_name=business_name,
            strategy=strategy,
            brand_voice=brand_voice
        )
        
        self.logger.info(f"Starting copy generation for: {business_name}")
        
        # Generate all copy components
        copy_package = await self.generate_copy(
            business_name=business_name,
            strategy=strategy,
            brand_voice=brand_voice
        )
        
        self.logger.info("Copy generation completed successfully")
        return copy_package
    
    async def generate_copy(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive brand copy including taglines, descriptions, and marketing content.
        """
        
        # Generate taglines (multiple options)
        self.logger.info("Generating taglines...")
        taglines = await self._generate_taglines(business_name, strategy, brand_voice)
        
        # Generate brand story
        self.logger.info("Generating brand story...")
        brand_story = await self._generate_brand_story(business_name, strategy, brand_voice)
        
        # Generate website copy
        self.logger.info("Generating website copy...")
        website_copy = await self._generate_website_copy(business_name, strategy, brand_voice)
        
        # Generate social media content
        self.logger.info("Generating social media content...")
        social_content = await self._generate_social_content(business_name, strategy, brand_voice)
        
        # Generate marketing copy for different channels
        self.logger.info("Generating marketing copy...")
        marketing_copy = await self._generate_marketing_copy(business_name, strategy, brand_voice)
        
        # Generate elevator pitch variations
        self.logger.info("Generating elevator pitches...")
        elevator_pitches = await self._generate_elevator_pitches(business_name, strategy, brand_voice)
        
        # Generate press release boilerplate
        self.logger.info("Generating press materials...")
        press_materials = await self._generate_press_materials(business_name, strategy, brand_voice)
        
        return {
            'taglines': taglines,
            'brand_story': brand_story,
            'website_copy': website_copy,
            'social_content': social_content,
            'marketing_copy': marketing_copy,
            'elevator_pitches': elevator_pitches,
            'press_materials': press_materials,
            'metadata': {
                'generated_for': business_name,
                'total_components': 7,
                'usage_stats': self.get_total_usage()
            }
        }
    
    async def _generate_taglines(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple tagline options with rationale.
        """
        
        positioning = strategy.get('positioning', {}).get('positioning_statement', '')
        values = ', '.join(strategy.get('brand_values', []))
        voice_traits = self._extract_voice_traits(brand_voice)
        
        system_prompt = self._create_system_prompt(
            role_description="award-winning copywriter specializing in brand taglines",
            guidelines=[
                "Create memorable, concise taglines that capture brand essence",
                "Each tagline should be 3-7 words maximum",
                "Avoid clichés and generic statements",
                "Ensure taglines are distinctive and ownable",
                "Consider trademark and uniqueness",
                "Match the brand voice characteristics"
            ]
        )
        
        user_prompt = f"""
        Generate 10 tagline options for "{business_name}".
        
        Brand Context:
        - Positioning: {positioning}
        - Values: {values}
        - Voice: {voice_traits}
        
        Requirements for each tagline:
        - 3-7 words maximum
        - Memorable and distinctive
        - Reflects brand positioning
        - Uses brand voice appropriately
        - Avoids industry clichés
        
        For each tagline, provide:
        1. The tagline text
        2. Brief rationale (why it works)
        3. Tone (inspirational, bold, friendly, professional, etc.)
        4. Best use case (e.g., "Perfect for hero sections and ads")
        5. Trademark risk assessment (low/medium/high)
        
        Return as JSON with structure:
        {{
            "taglines": [
                {{
                    "tagline": "string",
                    "rationale": "string",
                    "tone": "string",
                    "use_case": "string",
                    "trademark_risk": "low|medium|high",
                    "character_count": number
                }}
            ]
        }}
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9  # Higher creativity for taglines
        )
        
        return response.get('taglines', [])
    
    async def _generate_brand_story(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate compelling brand story in multiple lengths.
        """
        
        positioning = strategy.get('positioning', {}).get('positioning_statement', '')
        value_prop = strategy.get('positioning', {}).get('value_proposition', '')
        demographics = strategy.get('demographics', {})
        
        system_prompt = self._create_system_prompt(
            role_description="brand storyteller and narrative expert",
            guidelines=[
                "Create authentic, engaging stories that resonate emotionally",
                "Focus on the 'why' behind the brand",
                "Use narrative structure with clear arc",
                "Connect with audience values and aspirations",
                "Avoid corporate jargon and buzzwords",
                "Make it human and relatable"
            ]
        )
        
        user_prompt = f"""
        Write a compelling brand story for "{business_name}".
        
        Context:
        - Positioning: {positioning}
        - Value Proposition: {value_prop}
        - Target Audience: {demographics.get('age_range', 'general audience')}
        - Psychographics: {demographics.get('psychographics', 'N/A')}
        
        Create three versions:
        1. Short version (50-75 words) - for social media bios and brief intros
        2. Medium version (150-200 words) - for website "About" page
        3. Long version (300-400 words) - for press kit, detailed storytelling, and investor materials
        
        Each version should:
        - Connect emotionally with the audience
        - Highlight the brand's unique value and mission
        - Reflect the brand voice naturally
        - Include a call to action or inspiring conclusion
        - Tell a cohesive story (not just facts)
        
        Return as JSON:
        {{
            "short": "string",
            "medium": "string",
            "long": "string",
            "narrative_elements": {{
                "hook": "Opening hook used",
                "conflict": "Problem or challenge addressed",
                "resolution": "How the brand solves it",
                "call_to_action": "Inspiring conclusion"
            }}
        }}
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response
    
    async def _generate_website_copy(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate website copy for key pages and sections.
        """
        
        messaging = strategy.get('messaging_framework', {})
        primary_msg = messaging.get('primary_message', '')
        supporting_msgs = messaging.get('supporting_messages', [])
        
        system_prompt = self._create_system_prompt(
            role_description="conversion-focused web copywriter",
            guidelines=[
                "Write clear, scannable copy for web",
                "Focus on benefits over features",
                "Use active voice and strong verbs",
                "Create compelling headlines that hook readers",
                "Include clear calls-to-action",
                "Optimize for both users and search engines"
            ]
        )
        
        user_prompt = f"""
        Generate website copy for "{business_name}".
        
        Brand Messaging:
        - Primary Message: {primary_msg}
        - Supporting Messages: {json.dumps(supporting_msgs)}
        
        Create copy for these sections:
        
        1. Hero section:
           - Main headline (5-10 words, attention-grabbing)
           - Subheadline (10-20 words, clarifies value)
           - Primary CTA text
           - Secondary CTA text
        
        2. Value propositions (3 sections):
           - Each with: Icon theme, Headline, Description (2-3 sentences), Benefit statement
        
        3. How it works (3-4 steps):
           - Step number, Title, Description (1-2 sentences)
        
        4. Social proof section:
           - Section headline
           - Customer testimonial prompts (what to ask customers)
           - Trust indicators text
        
        5. FAQ section (7-10 questions):
           - Question and detailed answer
           - Cover: pricing, features, support, getting started, security
        
        6. CTA variations (7 different CTAs for different contexts):
           - Hero CTA
           - Mid-page CTA
           - Pricing CTA
           - Footer CTA
           - Exit intent CTA
           - Email signup CTA
           - Demo/trial CTA
        
        Return as JSON with nested structure for each section.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000
        )
        
        return response
    
    async def _generate_social_content(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate social media content templates and posts.
        """
        
        voice_traits = self._extract_voice_traits(brand_voice)
        demographics = strategy.get('demographics', {})
        
        system_prompt = self._create_system_prompt(
            role_description="social media content strategist and community manager",
            guidelines=[
                "Create engaging, shareable social content",
                "Understand platform-specific best practices",
                "Use appropriate hashtags and formatting",
                "Encourage interaction and engagement",
                "Balance promotional and value content",
                "Maintain authentic brand voice"
            ]
        )
        
        user_prompt = f"""
        Create social media content for "{business_name}".
        
        Brand Voice: {voice_traits}
        Target Audience: {demographics.get('psychographics', '')}
        Media Consumption: {demographics.get('media_consumption_habits', 'Various social platforms')}
        
        Generate:
        
        1. Social media bios (150 chars max each):
           - Instagram bio
           - Twitter/X bio
           - LinkedIn company description (200 chars)
           - Facebook page description
           - TikTok bio
        
        2. Launch announcement post (3 variations):
           - Enthusiastic version
           - Professional version
           - Story-driven version
        
        3. Content post templates (10 fill-in-the-blank templates):
           - Educational posts
           - Behind-the-scenes
           - User testimonial frames
           - Product highlights
           - Team spotlights
           - Industry insights
           - Tips and tricks
           - Milestone celebrations
           - User-generated content prompts
           - Engagement questions
        
        4. Hashtag strategy:
           - 5 primary hashtags (brand/category)
           - 10 secondary hashtags (niche/community)
           - 5 trending hashtags to monitor
        
        5. Content pillars (5 themes for regular posting):
           - Theme name
           - Description
           - Post frequency suggestion
           - Example topics
        
        6. Story/Reel templates (5 ideas):
           - Concept
           - Hook
           - Content flow
           - CTA
        
        7. Engagement responses:
           - Thank you for positive feedback
           - Response to questions
           - Handling complaints professionally
           - Encouraging user content
        
        Return as comprehensive JSON structure.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.fallback_model,  # Use 3.5 for cost efficiency
            max_tokens=2500
        )
        
        return response
    
    async def _generate_marketing_copy(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate marketing copy for various channels.
        """
        
        value_prop = strategy.get('positioning', {}).get('value_proposition', '')
        differentiators = strategy.get('positioning', {}).get('differentiators', [])
        
        system_prompt = self._create_system_prompt(
            role_description="multi-channel marketing copywriter",
            guidelines=[
                "Write persuasive, action-oriented copy",
                "Tailor messaging to each channel",
                "Focus on clear value communication",
                "Use power words and emotional triggers",
                "Include strong calls-to-action",
                "Optimize for conversions"
            ]
        )
        
        user_prompt = f"""
        Create marketing copy for "{business_name}".
        
        Value Proposition: {value_prop}
        Key Differentiators: {json.dumps(differentiators)}
        
        Generate:
        
        1. Email marketing:
           a) Welcome email series (3 emails):
              - Email 1: Subject, Preview text, Body, CTA
              - Email 2: Subject, Preview text, Body, CTA
              - Email 3: Subject, Preview text, Body, CTA
           
           b) Newsletter template:
              - Subject line formula
              - Opening paragraph template
              - Content section structure
              - Closing and CTA
           
           c) Promotional email:
              - 5 subject line variations
              - Body copy template
              - Urgency elements
              - Multiple CTAs
        
        2. Ad copy:
           a) Google Ads:
              - 5 headline variations (30 chars max)
              - 3 description variations (90 chars max)
              - Display ad text (short and long)
           
           b) Facebook/Instagram ads:
              - Primary text (125 chars, punchy)
              - Headline (40 chars)
              - Description (30 chars)
              - 3 creative variations
           
           c) LinkedIn ads (B2B focus):
              - Professional headline
              - Introductory text
              - CTA copy
        
        3. Landing page copy:
           - Above-fold headline
           - Subheadline
           - Benefit bullets (5-7)
           - Objection handling section
           - Final CTA section
        
        4. Press release template:
           - Boilerplate paragraph (100 words about company)
           - Key facts section
           - Quote template for spokesperson
        
        5. Partnership pitch:
           - One-paragraph elevator pitch for B2B partnerships
           - Mutual value proposition
           - Collaboration ideas
        
        6. Sales enablement:
           - One-pager summary
           - Key objections and responses
           - Value talking points
        
        Return as structured JSON.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2500
        )
        
        return response
    
    async def _generate_elevator_pitches(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate elevator pitch variations for different contexts.
        """
        
        positioning = strategy.get('positioning', {}).get('positioning_statement', '')
        value_prop = strategy.get('positioning', {}).get('value_proposition', '')
        
        system_prompt = self._create_system_prompt(
            role_description="communications coach and pitch specialist",
            guidelines=[
                "Create clear, compelling pitches",
                "Tailor to specific audiences",
                "Lead with the problem and solution",
                "Include memorable hooks",
                "End with clear next steps",
                "Keep within time/word limits"
            ]
        )
        
        user_prompt = f"""
        Create elevator pitch variations for "{business_name}".
        
        Positioning: {positioning}
        Value Proposition: {value_prop}
        
        Generate 6 pitch variations for different contexts:
        
        1. Investor pitch (30-45 seconds, 75-100 words):
           - Focus: Market opportunity, traction, ROI potential
           - Include: Problem size, solution, business model
        
        2. Customer pitch (30 seconds, 60-80 words):
           - Focus: Benefits, transformation, ease of use
           - Include: Pain point, solution, social proof hint
        
        3. Partner pitch (45 seconds, 90-110 words):
           - Focus: Mutual benefit, collaboration opportunity
           - Include: Shared values, complementary strengths
        
        4. Recruiter pitch (30 seconds, 70-90 words):
           - Focus: Mission, culture, growth opportunity
           - Include: Vision, team, impact potential
        
        5. Casual networking pitch (20 seconds, 40-60 words):
           - Focus: Conversational, relatable, memorable
           - Include: Simple explanation, interesting hook
        
        6. Media pitch (60 seconds, 120-150 words):
           - Focus: Newsworthy angle, industry impact
           - Include: Trend, solution, what makes it unique
        
        For each pitch provide:
        - context: Audience type
        - pitch: The actual pitch text
        - duration_seconds: Estimated speaking time
        - key_points: Array of main points covered
        - hooks: Memorable phrases or statistics used
        - cta: Suggested next step or question
        
        Return as JSON array.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.get('pitches', [])
    
    async def _generate_press_materials(
        self,
        business_name: str,
        strategy: Dict[str, Any],
        brand_voice: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate press release and media materials.
        """
        
        positioning = strategy.get('positioning', {}).get('positioning_statement', '')
        industry = strategy.get('industry', 'general')
        
        system_prompt = self._create_system_prompt(
            role_description="PR professional and media relations expert",
            guidelines=[
                "Write in AP style for press releases",
                "Lead with newsworthy information",
                "Use third-person perspective",
                "Include relevant quotes",
                "Provide context and background",
                "Make it journalist-friendly"
            ]
        )
        
        user_prompt = f"""
        Generate press materials for "{business_name}".
        
        Industry: {industry}
        Positioning: {positioning}
        
        Create:
        
        1. Company boilerplate (100-150 words):
           - Standard description for all press releases
           - Include: what company does, key differentiators, founding info
        
        2. Executive bio template:
           - Founder/CEO description
           - Professional background
           - Vision statement
        
        3. Press release template:
           - Headline format
           - Subheadline format
           - Lead paragraph structure
           - Quote from executive
           - Company boilerplate
           - Media contact section
        
        4. Media kit one-pager:
           - Key facts and figures
           - Notable achievements
           - Product/service overview
           - Use cases
        
        5. Interview Q&A prep:
           - 10 likely questions from journalists
           - Suggested answer frameworks
        
        6. Media pitch email template:
           - Subject line options
           - Opening paragraph
           - Story angle
           - Why now
        
        Return as JSON structure.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response
    
    async def refine_copy(
        self,
        current_copy: Dict[str, Any],
        feedback: List[str],
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refine copy based on feedback from consistency checker or user.
        
        Args:
            current_copy: Current copy that needs refinement
            feedback: List of feedback items to address
            strategy: Brand strategy for alignment
            
        Returns:
            Refined copy
        """
        
        self.logger.info("Starting copy refinement based on feedback")
        
        feedback_text = '\n'.join([f"- {fb}" for fb in feedback])
        
        system_prompt = self._create_system_prompt(
            role_description="brand copy editor and strategist",
            guidelines=[
                "Carefully address each piece of feedback",
                "Maintain brand voice and strategy alignment",
                "Improve clarity and impact",
                "Ensure consistency across all copy",
                "Preserve what's working well"
            ]
        )
        
        user_prompt = f"""
        Refine the following brand copy based on feedback.
        
        Current Copy:
        {json.dumps(current_copy, indent=2)}
        
        Feedback to Address:
        {feedback_text}
        
        Brand Strategy Context:
        {json.dumps(strategy.get('positioning', {}), indent=2)}
        
        Instructions:
        1. Address each feedback point specifically
        2. Maintain the overall structure and organization
        3. Preserve successful elements
        4. Ensure consistency with brand strategy
        5. Improve clarity and impact where needed
        
        Return the complete refined copy in the same JSON structure as the input.
        Include a "refinement_notes" field explaining key changes made.
        """
        
        response = await self._call_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=3000
        )
        
        self.logger.info("Copy refinement completed")
        return response
    
    def _extract_voice_traits(self, brand_voice: Dict[str, Any]) -> str:
        """
        Extract and format brand voice traits into readable string.
        """
        characteristics = brand_voice.get('characteristics', [])
        
        if isinstance(characteristics, list):
            if characteristics and isinstance(characteristics[0], dict):
                traits = [c.get('trait', str(c)) for c in characteristics]
            else:
                traits = characteristics
        else:
            traits = ['professional', 'approachable']
        
        return ', '.join(traits[:5])  # Top 5 traits