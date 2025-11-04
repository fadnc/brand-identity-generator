import pytest
from app.models.user import User


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'full_name': 'New User'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'AnotherPass123',
            'full_name': 'Another User'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'SecurePass123',
            'full_name': 'Test User'
        })
        
        assert response.status_code == 400
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'weak',
            'full_name': 'Test User'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'password' in data['error'].lower()
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'TestPass123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'WrongPassword'
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_no_auth(self, client):
        """Test getting user info without authentication."""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_update_profile(self, client, auth_headers):
        """Test updating user profile."""
        response = client.put('/api/auth/me', 
            headers=auth_headers,
            json={'full_name': 'Updated Name'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['full_name'] == 'Updated Name'
    
    def test_change_password(self, client, auth_headers):
        """Test changing password."""
        response = client.post('/api/auth/change-password',
            headers=auth_headers,
            json={
                'current_password': 'TestPass123',
                'new_password': 'NewSecurePass456'
            }
        )
        
        assert response.status_code == 200
        
        # Verify new password works
        login_response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'NewSecurePass456'
        })
        assert login_response.status_code == 200
    
    def test_upgrade_tier(self, client, auth_headers):
        """Test upgrading user tier."""
        response = client.post('/api/auth/upgrade',
            headers=auth_headers,
            json={'tier': 'premium'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['tier'] == 'premium'


class TestAuthorizationLimits:
    """Test generation limits and authorization."""
    
    def test_free_tier_generation_limit(self, client, test_user, auth_headers):
        """Test that free tier users hit generation limit."""
        # Set generations to limit
        test_user.generations_this_month = 10
        from app import db
        with client.application.app_context():
            db.session.commit()
        
        # Try to create project
        response = client.post('/api/projects/',
            headers=auth_headers,
            json={
                'business_name': 'Test Company',
                'industry': 'Tech'
            }
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'limit' in data['error'].lower()
    
    def test_premium_tier_higher_limit(self, client, app, premium_user):
        """Test that premium users have higher limits."""
        # Login as premium user
        login_response = client.post('/api/auth/login', json={
            'email': 'premium@example.com',
            'password': 'PremiumPass123'
        })
        token = login_response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Set generations high but below premium limit
        with app.app_context():
            user = User.query.filter_by(email='premium@example.com').first()
            user.generations_this_month = 50
            from app import db
            db.session.commit()
        
        # Should still be able to generate
        response = client.post('/api/projects/',
            headers=headers,
            json={
                'business_name': 'Premium Company',
                'industry': 'Finance'
            }
        )
        
        assert response.status_code == 201