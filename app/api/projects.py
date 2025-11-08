from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.project import BrandProject, BrandAsset, BrandVariant
from datetime import datetime

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    """
    Get all projects for the current user.
    
    Query parameters:
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Number of results (default: 20)
    - offset: Pagination offset (default: 0)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = BrandProject.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        projects = query.order_by(BrandProject.created_at.desc())\
                        .limit(limit)\
                        .offset(offset)\
                        .all()
        
        return jsonify({
            'projects': [p.to_dict() for p in projects],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch projects: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """
    Get detailed project information by ID.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Include full data and assets
        project_data = project.to_dict(include_full_data=True)
        project_data['assets'] = [asset.to_dict() for asset in project.assets]
        project_data['variants'] = [variant.to_dict() for variant in project.variants]
        
        return jsonify({
            'project': project_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch project: {str(e)}'}), 500


@projects_bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    """
    Create a new brand project (initiates generation).
    
    Request body:
    {
        "business_name": "Acme Corp",
        "industry": "Technology",
        "target_audience": "Tech-savvy millennials",
        "brand_values": ["innovation", "reliability", "sustainability"],
        "competitors": ["CompetitorA", "CompetitorB"]
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check generation limits
        if not user.can_generate():
            return jsonify({
                'error': 'Generation limit reached for this month',
                'message': 'Please upgrade your plan to generate more brand identities'
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('business_name'):
            return jsonify({'error': 'business_name is required'}), 400
        
        # Create project
        project = BrandProject(
            user_id=current_user_id,
            business_name=data['business_name'],
            industry=data.get('industry', ''),
            target_audience=data.get('target_audience', ''),
            brand_values=data.get('brand_values', []),
            status='pending'
        )
        
        db.session.add(project)
        db.session.commit()
        
        # Increment user's generation count
        user.increment_generation_count()
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import generate_brand_identity_task
        
        # Queue generation task (async)
        generate_brand_identity_task.delay(
            project_id=project.id,
            business_name=data['business_name'],
            industry=data.get('industry', ''),
            target_audience=data.get('target_audience', ''),
            brand_values=data.get('brand_values', []),
            competitors=data.get('competitors', [])
        )
        
        return jsonify({
            'message': 'Project created successfully. Generation started.',
            'project': project.to_dict(),
            'generations_remaining': user._get_remaining_generations()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create project: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """
    Update project metadata (name, industry, etc).
    Cannot update generated content directly.
    
    Request body:
    {
        "business_name": "Updated Name",
        "industry": "Updated Industry"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'business_name' in data:
            project.business_name = data['business_name']
        
        if 'industry' in data:
            project.industry = data['industry']
        
        if 'target_audience' in data:
            project.target_audience = data['target_audience']
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Project updated successfully',
            'project': project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update project: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """
    Delete a project and all associated assets.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Delete project (cascade will delete assets and variants)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete project: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>/regenerate', methods=['POST'])
@jwt_required()
def regenerate_project(project_id):
    """
    Regenerate brand identity for an existing project.
    Useful for trying different variations.
    
    Request body (optional):
    {
        "additional_context": "Make it more modern and tech-focused"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check generation limits
        if not user.can_generate():
            return jsonify({
                'error': 'Generation limit reached for this month',
                'message': 'Please upgrade your plan to generate more brand identities'
            }), 403
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Reset project status
        project.status = 'pending'
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Increment generation count
        user.increment_generation_count()
        
        # Get additional context if provided
        data = request.get_json() or {}
        additional_context = data.get('additional_context', '')
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import generate_brand_identity_task
        
        # Queue regeneration task
        generate_brand_identity_task.delay(
            project_id=project.id,
            business_name=project.business_name,
            industry=project.industry,
            target_audience=project.target_audience,
            brand_values=project.brand_values,
            additional_context=additional_context
        )
        
        return jsonify({
            'message': 'Regeneration started',
            'project': project.to_dict(),
            'generations_remaining': user._get_remaining_generations()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to regenerate project: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>/variants', methods=['POST'])
@jwt_required()
def generate_variants(project_id):
    """
    Generate A/B test variants for an existing project.
    
    Request body:
    {
        "variant_count": 3
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed before generating variants'}), 400
        
        # Check generation limits (variants also count)
        if not user.can_generate():
            return jsonify({
                'error': 'Generation limit reached for this month'
            }), 403
        
        data = request.get_json() or {}
        variant_count = min(int(data.get('variant_count', 3)), 5)  # Max 5 variants
        
        # Increment generation count
        user.increment_generation_count()
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import generate_variants_task
        
        # Queue variant generation task
        generate_variants_task.delay(
            project_id=project.id,
            variant_count=variant_count
        )
        
        return jsonify({
            'message': f'Generating {variant_count} variants',
            'variant_count': variant_count,
            'generations_remaining': user._get_remaining_generations()
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate variants: {str(e)}'}), 500