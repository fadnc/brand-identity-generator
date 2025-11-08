from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.project import BrandProject, BrandVariant
from app.analytics.sentiment_analysis import SentimentAnalyzer
from app.analytics.logo_scorer import LogoScorer
from app.analytics.market_trends import MarketTrendAnalyzer

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/sentiment/<int:project_id>', methods=['GET'])
@jwt_required()
def analyze_sentiment(project_id):
    """
    Perform sentiment analysis on all brand copy.
    Returns sentiment scores and emotional tone analysis.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.brand_copy:
            return jsonify({'error': 'No brand copy available for analysis'}), 400
        
        # Initialize sentiment analyzer
        analyzer = SentimentAnalyzer()
        
        # Analyze different copy elements
        results = analyzer.analyze_brand_copy(project.brand_copy)
        
        return jsonify({
            'project_id': project.id,
            'sentiment_analysis': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Sentiment analysis failed: {str(e)}'}), 500


@analytics_bp.route('/logo-score/<int:project_id>', methods=['GET'])
@jwt_required()
def score_logo(project_id):
    """
    Score logo aesthetics and design quality using ML model.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.visual_identity or 'logo' not in project.visual_identity:
            return jsonify({'error': 'No logo available for scoring'}), 400
        
        # Initialize logo scorer
        scorer = LogoScorer()
        
        # Score the logo
        logo_url = project.visual_identity['logo'].get('image_url')
        if not logo_url:
            return jsonify({'error': 'Logo URL not found'}), 400
        
        score_result = scorer.score_logo(logo_url)
        
        return jsonify({
            'project_id': project.id,
            'logo_score': score_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Logo scoring failed: {str(e)}'}), 500


@analytics_bp.route('/market-trends', methods=['POST'])
@jwt_required()
def analyze_market_trends():
    """
    Analyze market trends for a given industry.
    
    Request body:
    {
        "industry": "Technology",
        "region": "North America"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('industry'):
            return jsonify({'error': 'Industry is required'}), 400
        
        industry = data['industry']
        region = data.get('region', 'Global')
        
        # Initialize market trend analyzer
        analyzer = MarketTrendAnalyzer()
        
        # Analyze trends
        trends = analyzer.analyze_trends(industry, region)
        
        return jsonify({
            'industry': industry,
            'region': region,
            'trends': trends
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Market trend analysis failed: {str(e)}'}), 500


@analytics_bp.route('/compare-variants/<int:project_id>', methods=['GET'])
@jwt_required()
def compare_variants(project_id):
    """
    Compare all variants of a project with performance predictions.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        variants = BrandVariant.query.filter_by(project_id=project_id).all()
        
        if not variants:
            return jsonify({'error': 'No variants available for comparison'}), 400
        
        # Compare variants
        comparison = []
        
        for variant in variants:
            comparison.append({
                'variant_id': variant.id,
                'variant_number': variant.variant_number,
                'performance_score': variant.performance_score,
                'sentiment_score': variant.sentiment_score,
                'aesthetic_score': variant.aesthetic_score,
                'overall_score': (
                    (variant.performance_score or 0) * 0.4 +
                    (variant.sentiment_score or 0) * 0.3 +
                    (variant.aesthetic_score or 0) * 0.3
                )
            })
        
        # Sort by overall score
        comparison.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Add recommendations
        best_variant = comparison[0] if comparison else None
        
        return jsonify({
            'project_id': project_id,
            'variant_count': len(comparison),
            'comparison': comparison,
            'recommendation': {
                'variant_id': best_variant['variant_id'] if best_variant else None,
                'variant_number': best_variant['variant_number'] if best_variant else None,
                'reason': 'Highest overall score based on performance, sentiment, and aesthetics'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Variant comparison failed: {str(e)}'}), 500


@analytics_bp.route('/consistency-report/<int:project_id>', methods=['GET'])
@jwt_required()
def get_consistency_report(project_id):
    """
    Get detailed consistency report for a project.
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
        
        # In a real implementation, this would fetch the stored consistency report
        # or regenerate it
        report = {
            'project_id': project.id,
            'overall_consistency_score': project.consistency_score,
            'timestamp': project.completed_at.isoformat() if project.completed_at else None,
            'details': {
                'visual_alignment': 0.85,
                'copy_alignment': 0.90,
                'voice_consistency': 0.88,
                'visual_copy_harmony': 0.82
            },
            'strengths': [
                'Strong alignment between brand values and messaging',
                'Consistent voice across all touchpoints',
                'Clear visual identity'
            ],
            'areas_for_improvement': [
                'Color palette could be more distinctive',
                'Some copy sections could be more concise'
            ]
        }
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get consistency report: {str(e)}'}), 500


@analytics_bp.route('/competitive-positioning/<int:project_id>', methods=['GET'])
@jwt_required()
def get_competitive_positioning(project_id):
    """
    Get competitive positioning analysis for a project.
    """
    try:
        current_user_id = get_jwt_identity()
        
        project = BrandProject.query.filter_by(
            id=project_id,
            user_id=current_user_id
        ).first()
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if not project.strategy:
            return jsonify({'error': 'No strategy data available'}), 400
        
        competitive_analysis = project.strategy.get('competitive_analysis', {})
        positioning = project.strategy.get('positioning', {})
        
        return jsonify({
            'project_id': project.id,
            'business_name': project.business_name,
            'positioning': positioning,
            'competitive_landscape': competitive_analysis,
            'differentiation_score': 0.78,  # In production, calculate from various factors
            'market_opportunity': competitive_analysis.get('differentiation_opportunities', [])
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get competitive positioning: {str(e)}'}), 500


@analytics_bp.route('/performance-prediction/<int:project_id>', methods=['GET'])
@jwt_required()
def predict_performance(project_id):
    """
    Predict brand performance based on various metrics.
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
        
        # In production, this would use ML models for prediction
        prediction = {
            'project_id': project.id,
            'overall_prediction': 0.82,
            'confidence': 0.75,
            'metrics': {
                'brand_recall': {
                    'score': 0.78,
                    'description': 'Likelihood of target audience remembering the brand'
                },
                'emotional_connection': {
                    'score': 0.85,
                    'description': 'Strength of emotional bond with brand values'
                },
                'differentiation': {
                    'score': 0.80,
                    'description': 'How well the brand stands out from competitors'
                },
                'professional_appeal': {
                    'score': 0.88,
                    'description': 'Visual and verbal professionalism'
                }
            },
            'target_audience_fit': {
                'demographics': 0.84,
                'psychographics': 0.79
            },
            'recommendations': [
                'Consider A/B testing tagline variations',
                'Test color variations with target audience',
                'Validate messaging with focus groups'
            ]
        }
        
        return jsonify(prediction), 200
        
    except Exception as e:
        return jsonify({'error': f'Performance prediction failed: {str(e)}'}), 500