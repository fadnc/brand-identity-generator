import pytest
from app import create_app, db
from app.models.user import User, UserTier
from app.models.project import BrandProject


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            email="test@example.com",
            full_name="Test User",
            tier=UserTier.FREE
        )
        user.set_password("TestPass123")
        db.session.add(user)
        db.session.commit()
        
        # Return user ID instead of object to avoid detached instance
        user_id = user.id
        
    # Fetch fresh instance in new context
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def premium_user(app):
    """Create a premium test user."""
    with app.app_context():
        user = User(
            email="premium@example.com",
            full_name="Premium User",
            tier=UserTier.PREMIUM
        )
        user.set_password("PremiumPass123")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPass123'
    })
    
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def test_project(app, test_user):
    """Create a test project."""
    with app.app_context():
        project = BrandProject(
            user_id=test_user.id,
            business_name="Test Company",
            industry="Technology",
            target_audience="Tech professionals",
            brand_values=["innovation", "quality"],
            status="pending"
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
    
    with app.app_context():
        return BrandProject.query.get(project_id)


@pytest.fixture
def completed_project(app, test_user):
    """Create a completed test project with data."""
    with app.app_context():
        project = BrandProject(
            user_id=test_user.id,
            business_name="Completed Company",
            industry="E-commerce",
            target_audience="Online shoppers",
            brand_values=["trust", "convenience"],
            status="completed",
            strategy={
                "positioning": {
                    "positioning_statement": "Leading e-commerce platform for quality products"
                },
                "brand_values": ["trust", "convenience"]
            },
            visual_identity={
                "logo": {
                    "image_url": "https://example.com/logo.png"
                },
                "color_palette": {
                    "primary_colors": [
                        {"hex": "#0066CC", "usage": "primary"}
                    ]
                }
            },
            brand_copy={
                "taglines": [
                    {"tagline": "Shop with Confidence", "rationale": "Trust-focused"}
                ],
                "brand_story": {
                    "short": "We make online shopping easy and trustworthy."
                }
            },
            consistency_score=0.85
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
    
    with app.app_context():
        return BrandProject.query.get(project_id)