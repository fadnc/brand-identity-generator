from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from typing import Dict, Any, List
import json

from app.agents.design_agent import DesignAgent
from app.agents.copywriting_agent import CopywritingAgent
from app.agents.strategy_agent import StrategyAgent
from app.services.consistency_checker import ConsistencyChecker


class BrandOrchestrator:
    """
    Orchestrates multiple specialized agents to create a cohesive brand identity.
    Uses LangChain for coordination and state management.
    """
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            api_key=openai_api_key
        )
        
        # Initialize specialized agents
        self.strategy_agent = StrategyAgent(openai_api_key)
        self.design_agent = DesignAgent(openai_api_key)
        self.copywriting_agent = CopywritingAgent(openai_api_key)
        self.consistency_checker = ConsistencyChecker(openai_api_key)
        
        # Coordination prompt
        self.coordinator_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a brand strategy coordinator. Your job is to:
1. Analyze the business input and create a strategic brief
2. Coordinate between design, copywriting, and strategy agents
3. Ensure all outputs are consistent and aligned with brand goals
4. Make decisions about iteration and refinement

Provide your response as a JSON object with clear directives for each agent."""),
            ("user", "{input}")
        ])
        
    async def generate_brand_identity(
        self,
        business_name: str,
        industry: str,
        target_audience: str,
        brand_values: List[str],
        competitors: List[str] = None,
        additional_context: str = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method that coordinates all agents to create
        a complete brand identity.
        """
        
        # Step 1: Strategic Analysis
        print("🎯 Step 1: Strategic Analysis...")
        strategy = await self.strategy_agent.analyze(
            business_name=business_name,
            industry=industry,
            target_audience=target_audience,
            brand_values=brand_values,
            competitors=competitors
        )
        
        # Step 2: Visual Identity Generation
        print("🎨 Step 2: Visual Identity Generation...")
        visual_identity = await self.design_agent.generate_visuals(
            business_name=business_name,
            strategy=strategy,
            style_preferences=strategy.get('visual_direction', {})
        )
        
        # Step 3: Brand Copy & Messaging
        print("✍️ Step 3: Brand Copy & Messaging...")
        brand_copy = await self.copywriting_agent.generate_copy(
            business_name=business_name,
            strategy=strategy,
            brand_voice=strategy.get('brand_voice', {})
        )
        
        # Step 4: Consistency Check
        print("✅ Step 4: Consistency Check...")
        consistency_report = await self.consistency_checker.validate(
            strategy=strategy,
            visual_identity=visual_identity,
            brand_copy=brand_copy
        )
        
        # Step 5: Refinement if needed
        if consistency_report.get('needs_refinement', False):
            print("🔄 Step 5: Refinement...")
            visual_identity, brand_copy = await self._refine_outputs(
                consistency_report,
                visual_identity,
                brand_copy,
                strategy
            )
        
        # Compile final brand package
        brand_package = {
            'business_name': business_name,
            'strategy': strategy,
            'visual_identity': visual_identity,
            'brand_copy': brand_copy,
            'consistency_score': consistency_report.get('score', 0),
            'metadata': {
                'industry': industry,
                'target_audience': target_audience,
                'brand_values': brand_values
            }
        }
        
        return brand_package
    
    async def _refine_outputs(
        self,
        consistency_report: Dict,
        visual_identity: Dict,
        brand_copy: Dict,
        strategy: Dict
    ) -> tuple:
        """
        Refine outputs based on consistency checker feedback.
        """
        issues = consistency_report.get('issues', [])
        
        # Refine visuals if needed
        if any('visual' in issue.lower() for issue in issues):
            visual_identity = await self.design_agent.refine_visuals(
                current_visuals=visual_identity,
                feedback=issues,
                strategy=strategy
            )
        
        # Refine copy if needed
        if any('copy' in issue.lower() or 'messaging' in issue.lower() for issue in issues):
            brand_copy = await self.copywriting_agent.refine_copy(
                current_copy=brand_copy,
                feedback=issues,
                strategy=strategy
            )
        
        return visual_identity, brand_copy
    
    async def generate_ab_variants(
        self,
        brand_package: Dict[str, Any],
        variant_count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate A/B testing variants of the brand identity.
        """
        variants = []
        
        for i in range(variant_count):
            variant_prompt = f"""
            Generate variant {i+1} of the brand identity.
            Keep the core strategy but explore alternative executions.
            
            Original Brand Package:
            {json.dumps(brand_package, indent=2)}
            """
            
            # Generate variant with slightly different parameters
            variant = await self.generate_brand_identity(
                business_name=brand_package['business_name'],
                industry=brand_package['metadata']['industry'],
                target_audience=brand_package['metadata']['target_audience'],
                brand_values=brand_package['metadata']['brand_values'],
                additional_context=f"This is variant {i+1}. Explore alternative creative directions."
            )
            
            variants.append(variant)
        
        return variants