from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum


class UserTier(enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    tier = db.Column(db.Enum(UserTier), default=UserTier.FREE)
    
    # Usage tracking
    generations_this_month = db.Column(db.Integer, default=0)
    last_generation_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('BrandProject', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_generate(self):
        """Check if user has remaining generations for the month."""
        # Reset counter if it's a new month
        now = datetime.utcnow()
        if self.last_generation_reset.month != now.month:
            self.generations_this_month = 0
            self.last_generation_reset = now
            db.session.commit()
        
        limits = {
            UserTier.FREE: 10,
            UserTier.PREMIUM: 100,
            UserTier.ENTERPRISE: 1000
        }
        
        return self.generations_this_month < limits.get(self.tier, 0)
    
    def increment_generation_count(self):
        """Increment the generation counter."""
        self.generations_this_month += 1
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'tier': self.tier.value,
            'generations_remaining': self._get_remaining_generations(),
            'created_at': self.created_at.isoformat()
        }
    
    def _get_remaining_generations(self):
        limits = {
            UserTier.FREE: 10,
            UserTier.PREMIUM: 100,
            UserTier.ENTERPRISE: 1000
        }
        return limits.get(self.tier, 0) - self.generations_this_month


class BrandProject(db.Model):
    __tablename__ = 'brand_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Project metadata
    business_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    target_audience = db.Column(db.Text)
    brand_values = db.Column(db.JSON)  # Store as JSON array
    
    # Generation status
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    
    # Generated content (stored as JSON)
    strategy = db.Column(db.JSON)
    visual_identity = db.Column(db.JSON)
    brand_copy = db.Column(db.JSON)
    consistency_score = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='projects')
    assets = db.relationship('BrandAsset', back_populates='project', cascade='all, delete-orphan')
    variants = db.relationship('BrandVariant', back_populates='project', cascade='all, delete-orphan')
    
    def to_dict(self, include_full_data=False):
        base_dict = {
            'id': self.id,
            'business_name': self.business_name,
            'industry': self.industry,
            'status': self.status,
            'consistency_score': self.consistency_score,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_full_data:
            base_dict.update({
                'strategy': self.strategy,
                'visual_identity': self.visual_identity,
                'brand_copy': self.brand_copy,
                'target_audience': self.target_audience,
                'brand_values': self.brand_values
            })
        
        return base_dict


class BrandAsset(db.Model):
    __tablename__ = 'brand_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('brand_projects.id'), nullable=False)
    
    # Asset details
    asset_type = db.Column(db.String(50))  # logo, color_palette, social_media_post, etc.
    file_format = db.Column(db.String(20))  # png, svg, pdf, json
    file_url = db.Column(db.String(500))  # S3 URL or local path
    file_size = db.Column(db.Integer)  # in bytes
    
    # Metadata
    metadata = db.Column(db.JSON)  # Additional info like dimensions, color codes, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('BrandProject', back_populates='assets')
    
    def to_dict(self):
        return {
            'id': self.id,
            'asset_type': self.asset_type,
            'file_format': self.file_format,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class BrandVariant(db.Model):
    __tablename__ = 'brand_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('brand_projects.id'), nullable=False)
    
    # Variant data
    variant_number = db.Column(db.Integer)  # 1, 2, 3 for A/B/C testing
    visual_identity = db.Column(db.JSON)
    brand_copy = db.Column(db.JSON)
    
    # Analytics
    performance_score = db.Column(db.Float)  # Predicted performance
    sentiment_score = db.Column(db.Float)
    aesthetic_score = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('BrandProject', back_populates='variants')
    
    def to_dict(self):
        return {
            'id': self.id,
            'variant_number': self.variant_number,
            'visual_identity': self.visual_identity,
            'brand_copy': self.brand_copy,
            'performance_score': self.performance_score,
            'sentiment_score': self.sentiment_score,
            'aesthetic_score': self.aesthetic_score
        }