from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.project import BrandProject, BrandAsset
from app.services.export import ExportService
import os

generation_bp = Blueprint('generation', __name__)


@generation_bp.route('/status/<int:project_id>', methods=['GET'])
@jwt_required()
def get_generation_status(project_id):
    """
    Get the current generation status of a project.
    Useful for polling during async generation.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        response = {
            'project_id': project.id,
            'status': project.status,
            'business_name': project.business_name,
            'consistency_score': project.consistency_score,
            'created_at': project.created_at.isoformat(),
            'completed_at': project.completed_at.isoformat() if project.completed_at else None
        }
        
        # Add progress information based on status
        if project.status == 'pending':
            response['message'] = 'Generation queued'
            response['progress'] = 0
        elif project.status == 'processing':
            response['message'] = 'Generating brand identity...'
            response['progress'] = 50
        elif project.status == 'completed':
            response['message'] = 'Generation complete'
            response['progress'] = 100
            response['asset_count'] = len(project.assets)
        elif project.status == 'failed':
            response['message'] = 'Generation failed'
            response['progress'] = 0
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500


@generation_bp.route('/export/<int:project_id>', methods=['POST'])
@jwt_required()
def export_brand_package(project_id):
    """
    Export complete brand package in various formats.
    
    Request body:
    {
        "format": "pdf" | "zip" | "json",
        "include_assets": true,
        "include_guidelines": true
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
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed before exporting'}), 400
        
        data = request.get_json() or {}
        export_format = data.get('format', 'pdf').lower()
        include_assets = data.get('include_assets', True)
        include_guidelines = data.get('include_guidelines', True)
        
        if export_format not in ['pdf', 'zip', 'json']:
            return jsonify({'error': 'Invalid format. Must be pdf, zip, or json'}), 400
        
        # Initialize export service
        export_service = ExportService()
        
        # Generate export
        if export_format == 'pdf':
            file_path = export_service.export_to_pdf(
                project,
                include_guidelines=include_guidelines
            )
        elif export_format == 'zip':
            file_path = export_service.export_to_zip(
                project,
                include_assets=include_assets,
                include_guidelines=include_guidelines
            )
        else:  # json
            file_path = export_service.export_to_json(project)
        
        # In production, return S3 URL or send file
        # For now, return file path
        return jsonify({
            'message': 'Export generated successfully',
            'file_path': file_path,
            'format': export_format,
            'download_url': f'/api/generate/download/{os.path.basename(file_path)}'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


@generation_bp.route('/logo/<int:project_id>/variations', methods=['POST'])
@jwt_required()
def generate_logo_variations(project_id):
    """
    Generate additional logo variations for a project.
    
    Request body:
    {
        "style_direction": "more modern",
        "count": 3
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
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed first'}), 400
        
        data = request.get_json() or {}
        style_direction = data.get('style_direction', '')
        count = min(int(data.get('count', 3)), 5)
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import generate_logo_variations_task
        
        # Queue logo variation generation
        generate_logo_variations_task.delay(
            project_id=project.id,
            style_direction=style_direction,
            count=count
        )
        
        return jsonify({
            'message': f'Generating {count} logo variations',
            'count': count
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate logo variations: {str(e)}'}), 500


@generation_bp.route('/tagline/<int:project_id>/alternatives', methods=['POST'])
@jwt_required()
def generate_tagline_alternatives(project_id):
    """
    Generate alternative taglines for a project.
    
    Request body:
    {
        "direction": "more playful",
        "count": 5
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
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed first'}), 400
        
        data = request.get_json() or {}
        direction = data.get('direction', '')
        count = min(int(data.get('count', 5)), 10)
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import generate_tagline_alternatives_task
        
        # Queue tagline generation
        generate_tagline_alternatives_task.delay(
            project_id=project.id,
            direction=direction,
            count=count
        )
        
        return jsonify({
            'message': f'Generating {count} alternative taglines',
            'count': count
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate taglines: {str(e)}'}), 500


@generation_bp.route('/refine/<int:project_id>', methods=['POST'])
@jwt_required()
def refine_brand_identity(project_id):
    """
    Refine specific aspects of the brand identity.
    
    Request body:
    {
        "refine_visuals": true,
        "refine_copy": true,
        "feedback": "Make it more professional and less playful"
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
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed before refining'}), 400
        
        data = request.get_json() or {}
        refine_visuals = data.get('refine_visuals', False)
        refine_copy = data.get('refine_copy', False)
        feedback = data.get('feedback', '')
        
        if not feedback:
            return jsonify({'error': 'Feedback is required for refinement'}), 400
        
        # Update project status
        project.status = 'processing'
        db.session.commit()
        
        # Import here to avoid circular imports
        from app.tasks.generation_tasks import refine_brand_identity_task
        
        # Queue refinement task
        refine_brand_identity_task.delay(
            project_id=project.id,
            refine_visuals=refine_visuals,
            refine_copy=refine_copy,
            feedback=feedback
        )
        
        return jsonify({
            'message': 'Refinement started',
            'refining': {
                'visuals': refine_visuals,
                'copy': refine_copy
            }
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start refinement: {str(e)}'}), 500


@generation_bp.route('/preview/<int:project_id>', methods=['GET'])
@jwt_required()
def preview_brand_application(project_id):
    """
    Generate preview of brand identity applied to various mockups.
    Returns URLs to mockup images showing logo on business cards, website, etc.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.status != 'completed':
            return jsonify({'error': 'Project must be completed first'}), 400
        
        # Get logo asset
        logo_asset = BrandAsset.query.filter_by(
            project_id=project.id,
            asset_type='logo'
        ).first()
        
        if not logo_asset:
            return jsonify({'error': 'Logo not found'}), 404
        
        # In production, this would generate actual mockups
        # For now, return placeholder structure
        mockups = {
            'business_card': {
                'url': logo_asset.file_url,
                'type': 'business_card',
                'description': 'Logo on business card'
            },
            'website_header': {
                'url': logo_asset.file_url,
                'type': 'website',
                'description': 'Logo in website header'
            },
            'social_media': {
                'url': logo_asset.file_url,
                'type': 'social',
                'description': 'Logo as social media profile picture'
            },
            'letterhead': {
                'url': logo_asset.file_url,
                'type': 'print',
                'description': 'Logo on letterhead'
            }
        }
        
        return jsonify({
            'project_id': project.id,
            'mockups': mockups
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate preview: {str(e)}'}), 500