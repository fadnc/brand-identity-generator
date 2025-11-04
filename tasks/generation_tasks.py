from app import celery, db
from app.models.project import BrandProject, BrandAsset, BrandVariant
from app.agents.orchestrator import BrandOrchestrator
from app.services.image_generation import ImageService
from datetime import datetime
import os
import traceback


@celery.task(bind=True, max_retries=3)
def generate_brand_identity_task(
    self,
    project_id: int,
    business_name: str,
    industry: str,
    target_audience: str,
    brand_values: list,
    competitors: list = None,
    additional_context: str = None
):
    """
    Async task to generate complete brand identity.
    """
    try:
        # Update project status
        project = BrandProject.query.get(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        project.status = 'processing'
        db.session.commit()
        
        # Initialize orchestrator
        openai_api_key = os.getenv('OPENAI_API_KEY')
        orchestrator = BrandOrchestrator(openai_api_key)
        
        # Generate brand identity (this is async)
        import asyncio
        brand_package = asyncio.run(
            orchestrator.generate_brand_identity(
                business_name=business_name,
                industry=industry,
                target_audience=target_audience,
                brand_values=brand_values,
                competitors=competitors,
                additional_context=additional_context
            )
        )
        
        # Save results to database
        project.strategy = brand_package['strategy']
        project.visual_identity = brand_package['visual_identity']
        project.brand_copy = brand_package['brand_copy']
        project.consistency_score = brand_package['consistency_score']
        project.status = 'completed'
        project.completed_at = datetime.utcnow()
        
        # Save logo as asset
        logo_data = brand_package['visual_identity']['logo']
        logo_asset = BrandAsset(
            project_id=project.id,
            asset_type='logo',
            file_format='png',
            file_url=logo_data['image_url'],
            metadata={
                'prompt': logo_data['original_prompt'],
                'revised_prompt': logo_data['revised_prompt']
            }
        )
        db.session.add(logo_asset)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'project_id': project_id,
            'consistency_score': project.consistency_score
        }
        
    except Exception as e:
        # Update project status to failed
        project = BrandProject.query.get(project_id)
        if project:
            project.status = 'failed'
            db.session.commit()
        
        # Log error
        error_msg = f"Generation failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # Retry if not max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'project_id': project_id,
            'error': str(e)
        }


@celery.task(bind=True, max_retries=2)
def generate_variants_task(self, project_id: int, variant_count: int):
    """
    Generate A/B test variants for a project.
    """
    try:
        project = BrandProject.query.get(project_id)
        if not project or project.status != 'completed':
            raise Exception("Project must be completed before generating variants")
        
        # Initialize orchestrator
        openai_api_key = os.getenv('OPENAI_API_KEY')
        orchestrator = BrandOrchestrator(openai_api_key)
        
        # Generate variants
        import asyncio
        brand_package = {
            'business_name': project.business_name,
            'metadata': {
                'industry': project.industry,
                'target_audience': project.target_audience,
                'brand_values': project.brand_values
            }
        }
        
        variants = asyncio.run(
            orchestrator.generate_ab_variants(brand_package, variant_count)
        )
        
        # Save variants to database
        for i, variant_package in enumerate(variants, 1):
            variant = BrandVariant(
                project_id=project.id,
                variant_number=i,
                visual_identity=variant_package['visual_identity'],
                brand_copy=variant_package['brand_copy'],
                performance_score=variant_package.get('consistency_score', 0.0)
            )
            db.session.add(variant)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'project_id': project_id,
            'variants_generated': variant_count
        }
        
    except Exception as e:
        error_msg = f"Variant generation failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'project_id': project_id,
            'error': str(e)
        }


@celery.task(bind=True, max_retries=2)
def generate_logo_variations_task(
    self,
    project_id: int,
    style_direction: str,
    count: int
):
    """
    Generate additional logo variations.
    """
    try:
        project = BrandProject.query.get(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        # Get existing strategy
        strategy = project.strategy
        visual_direction = strategy.get('visual_direction', {})
        
        # Modify direction based on user input
        if style_direction:
            visual_direction['additional_direction'] = style_direction
        
        # Initialize design agent
        from app.agents.design_agent import DesignAgent
        openai_api_key = os.getenv('OPENAI_API_KEY')
        design_agent = DesignAgent(openai_api_key)
        
        # Generate variations
        import asyncio
        for i in range(count):
            logo_data = asyncio.run(
                design_agent._generate_logo(
                    business_name=project.business_name,
                    strategy=strategy,
                    style_preferences=visual_direction
                )
            )
            
            # Save as asset
            asset = BrandAsset(
                project_id=project.id,
                asset_type='logo_variation',
                file_format='png',
                file_url=logo_data['image_url'],
                metadata={
                    'variation_number': i + 1,
                    'prompt': logo_data['original_prompt']
                }
            )
            db.session.add(asset)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'project_id': project_id,
            'variations_generated': count
        }
        
    except Exception as e:
        error_msg = f"Logo variation failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'project_id': project_id,
            'error': str(e)
        }


@celery.task(bind=True, max_retries=2)
def generate_tagline_alternatives_task(
    self,
    project_id: int,
    direction: str,
    count: int
):
    """
    Generate alternative taglines with specific direction.
    """
    try:
        project = BrandProject.query.get(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        from app.agents.copywriting_agent import CopywritingAgent
        openai_api_key = os.getenv('OPENAI_API_KEY')
        copywriting_agent = CopywritingAgent(openai_api_key)
        
        # Get current strategy and brand voice
        strategy = project.strategy
        brand_voice = strategy.get('brand_voice', {})
        
        # Modify brand voice based on direction
        if direction:
            brand_voice['additional_direction'] = direction
        
        # Generate new taglines
        import asyncio
        taglines = asyncio.run(
            copywriting_agent._generate_taglines(
                business_name=project.business_name,
                strategy=strategy,
                brand_voice=brand_voice
            )
        )
        
        # Add to existing brand copy
        current_copy = project.brand_copy or {}
        current_taglines = current_copy.get('taglines', [])
        current_taglines.extend(taglines[:count])
        current_copy['taglines'] = current_taglines
        
        project.brand_copy = current_copy
        db.session.commit()
        
        return {
            'status': 'success',
            'project_id': project_id,
            'taglines_generated': count,
            'new_taglines': taglines[:count]
        }
        
    except Exception as e:
        error_msg = f"Tagline generation failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'project_id': project_id,
            'error': str(e)
        }


@celery.task(bind=True, max_retries=2)
def refine_brand_identity_task(
    self,
    project_id: int,
    refine_visuals: bool,
    refine_copy: bool,
    feedback: str
):
    """
    Refine brand identity based on user feedback.
    """
    try:
        project = BrandProject.query.get(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        import asyncio
        
        # Refine visuals if requested
        if refine_visuals:
            from app.agents.design_agent import DesignAgent
            design_agent = DesignAgent(openai_api_key)
            
            refined_visuals = asyncio.run(
                design_agent.refine_visuals(
                    current_visuals=project.visual_identity,
                    feedback=[feedback],
                    strategy=project.strategy
                )
            )
            project.visual_identity = refined_visuals
        
        # Refine copy if requested
        if refine_copy:
            from app.agents.copywriting_agent import CopywritingAgent
            copywriting_agent = CopywritingAgent(openai_api_key)
            
            refined_copy = asyncio.run(
                copywriting_agent.refine_copy(
                    current_copy=project.brand_copy,
                    feedback=[feedback],
                    strategy=project.strategy
                )
            )
            project.brand_copy = refined_copy
        
        project.status = 'completed'
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'project_id': project_id,
            'refined': {
                'visuals': refine_visuals,
                'copy': refine_copy
            }
        }
        
    except Exception as e:
        project = BrandProject.query.get(project_id)
        if project:
            project.status = 'completed'  # Revert to completed on failure
            db.session.commit()
        
        error_msg = f"Refinement failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'project_id': project_id,
            'error': str(e)
        }