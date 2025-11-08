"""
BrandProject Model - Manages brand identity generation projects.

This module contains the BrandProject model for handling brand identity
generation requests, storing generated content, and tracking project status.
"""

from app import db
from datetime import datetime, timedelta
import enum
import secrets


class ProjectStatus(enum.Enum):
    """Status of brand identity generation project."""
    PENDING = "pending"          # Queued for generation
    PROCESSING = "processing"    # Currently being generated
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"           # Generation failed
    CANCELLED = "cancelled"     # User cancelled


class BrandProject(db.Model):
    """
    Brand Project model representing a brand identity generation request.
    
    Stores input parameters, generated content (strategy, visuals, copy),
    and project metadata including quality metrics and version history.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        business_name (str): Name of the business
        industry (str): Industry category
        target_audience (str): Target demographic description
        brand_values (list): JSON array of brand values
        status (ProjectStatus): Current generation status
        strategy (dict): Generated brand strategy (JSON)
        visual_identity (dict): Generated visual assets (JSON)
        brand_copy (dict): Generated marketing copy (JSON)
        consistency_score (float): Brand consistency rating (0-1)
        
    Relationships:
        user: Many-to-One with User
        assets: One-to-Many with BrandAsset
        variants: One-to-Many with BrandVariant
    """
    __tablename__ = 'brand_projects'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = db.Column(db.Integer, primary_key=True)
    
    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # PROJECT METADATA
    # ========================================================================
    project_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)  # Array of tags for organization
    
    # ========================================================================
    # INPUT PARAMETERS
    # ========================================================================
    business_name = db.Column(
        db.String(200),
        nullable=False,
        index=True
    )
    industry = db.Column(db.String(100), index=True)
    target_audience = db.Column(db.Text)
    brand_values = db.Column(db.JSON)  # Array of strings
    competitors = db.Column(db.JSON)   # Array of competitor names
    additional_context = db.Column(db.Text)
    style_preferences = db.Column(db.JSON)  # User's style preferences
    
    # ========================================================================
    # GENERATION STATUS
    # ========================================================================
    status = db.Column(
        db.Enum(ProjectStatus),
        default=ProjectStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = db.Column(db.Text)  # If status is FAILED
    error_code = db.Column(db.String(50))  # Error categorization
    progress_percentage = db.Column(db.Integer, default=0)
    progress_message = db.Column(db.String(200))  # Current step description
    
    # ========================================================================
    # GENERATED CONTENT (JSON STORAGE)
    # ========================================================================
    strategy = db.Column(db.JSON)           # Strategy agent output
    visual_identity = db.Column(db.JSON)    # Design agent output
    brand_copy = db.Column(db.JSON)         # Copywriting agent output
    
    # ========================================================================
    # QUALITY METRICS
    # ========================================================================
    consistency_score = db.Column(db.Float)  # 0.0 to 1.0
    quality_score = db.Column(db.Float)      # Overall quality rating
    aesthetic_score = db.Column(db.Float)    # Visual quality
    sentiment_score = db.Column(db.Float)    # Copy sentiment
    
    # ========================================================================
    # GENERATION METADATA
    # ========================================================================
    generation_time_seconds = db.Column(db.Float)
    tokens_used = db.Column(db.Integer)
    estimated_cost = db.Column(db.Float)  # In USD
    model_versions = db.Column(db.JSON)  # Which AI models were used
    generation_config = db.Column(db.JSON)  # Configuration used
    
    # ========================================================================
    # USER INTERACTIONS
    # ========================================================================
    is_favorite = db.Column(db.Boolean, default=False, index=True)
    user_rating = db.Column(db.Integer)  # 1-5 stars
    user_feedback = db.Column(db.Text)
    view_count = db.Column(db.Integer, default=0)
    
    # ========================================================================
    # SHARING & COLLABORATION
    # ========================================================================
    is_public = db.Column(db.Boolean, default=False, index=True)
    share_token = db.Column(db.String(64), unique=True, index=True)
    share_password = db.Column(db.String(255))  # Optional password protection
    allow_comments = db.Column(db.Boolean, default=False)
    
    # ========================================================================
    # VERSION CONTROL
    # ========================================================================
    version = db.Column(db.Integer, default=1)
    parent_project_id = db.Column(
        db.Integer,
        db.ForeignKey('brand_projects.id')
    )
    is_archived = db.Column(db.Boolean, default=False)
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    completed_at = db.Column(db.DateTime)
    last_viewed_at = db.Column(db.DateTime)
    archived_at = db.Column(db.DateTime)
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    user = db.relationship('User', back_populates='projects')
    
    assets = db.relationship(
        'BrandAsset',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    variants = db.relationship(
        'BrandVariant',
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # Self-referential relationship for versions
    child_versions = db.relationship(
        'BrandProject',
        backref=db.backref('parent_project', remote_side=[id]),
        lazy='dynamic'
    )
    
    # ========================================================================
    # TABLE CONFIGURATION
    # ========================================================================
    __table_args__ = (
        db.Index('idx_project_user_status', 'user_id', 'status'),
        db.Index('idx_project_created', 'created_at'),
        db.Index('idx_project_business_name', 'business_name'),
        db.Index('idx_project_industry', 'industry'),
        db.Index('idx_project_share_token', 'share_token'),
        db.Index('idx_project_favorite', 'is_favorite'),
    )
    
    # ========================================================================
    # REPRESENTATION
    # ========================================================================
    def __repr__(self):
        return f'<BrandProject {self.id}: {self.business_name}>'
    
    # ========================================================================
    # STATUS MANAGEMENT
    # ========================================================================
    
    def mark_processing(self, message: str = "Starting generation...") -> None:
        """
        Mark project as currently processing.
        
        Args:
            message: Progress message to display
            
        Example:
            project.mark_processing("Generating brand strategy...")
        """
        self.status = ProjectStatus.PROCESSING
        self.progress_percentage = 10
        self.progress_message = message
        db.session.commit()
    
    def mark_completed(self, generation_time_seconds: float = None) -> None:
        """
        Mark project as completed successfully.
        
        Args:
            generation_time_seconds: Time taken to generate (optional)
            
        Example:
            project.mark_completed(generation_time_seconds=42.5)
        """
        self.status = ProjectStatus.COMPLETED
        self.progress_percentage = 100
        self.progress_message = "Generation completed!"
        self.completed_at = datetime.utcnow()
        
        if generation_time_seconds:
            self.generation_time_seconds = generation_time_seconds
        
        db.session.commit()
    
    def mark_failed(self, error_message: str, error_code: str = None) -> None:
        """
        Mark project as failed with error details.
        
        Args:
            error_message: Detailed error description
            error_code: Error category code (optional)
            
        Example:
            project.mark_failed(
                error_message="OpenAI API timeout",
                error_code="API_TIMEOUT"
            )
        """
        self.status = ProjectStatus.FAILED
        self.error_message = error_message
        self.error_code = error_code
        self.progress_message = "Generation failed"
        db.session.commit()
    
    def mark_cancelled(self) -> None:
        """
        Mark project as cancelled by user.
        
        Example:
            project.mark_cancelled()
        """
        self.status = ProjectStatus.CANCELLED
        self.progress_message = "Cancelled by user"
        db.session.commit()
    
    def update_progress(self, percentage: int, message: str = None) -> None:
        """
        Update generation progress.
        
        Args:
            percentage: Progress percentage (0-100)
            message: Optional progress message
            
        Example:
            project.update_progress(50, "Generating visual identity...")
        """
        self.progress_percentage = max(0, min(100, percentage))
        
        if message:
            self.progress_message = message
        
        db.session.commit()
    
    def retry_generation(self) -> None:
        """
        Reset project status to retry failed generation.
        
        Example:
            if project.status == ProjectStatus.FAILED:
                project.retry_generation()
        """
        self.status = ProjectStatus.PENDING
        self.progress_percentage = 0
        self.error_message = None
        self.error_code = None
        db.session.commit()
    
    # ========================================================================
    # CONTENT MANAGEMENT
    # ========================================================================
    
    def has_generated_content(self) -> bool:
        """
        Check if project has any generated content.
        
        Returns:
            True if any content exists
            
        Example:
            if not project.has_generated_content():
                return "No content available yet"
        """
        return bool(self.strategy or self.visual_identity or self.brand_copy)
    
    def get_logo_url(self) -> str:
        """
        Get URL of the primary logo.
        
        Returns:
            Logo URL or None
            
        Example:
            logo = project.get_logo_url()
            if logo:
                img_tag = f'<img src="{logo}">'
        """
        if self.visual_identity and 'logo' in self.visual_identity:
            return self.visual_identity['logo'].get('image_url')
        return None
    
    def get_primary_tagline(self) -> str:
        """
        Get the primary tagline.
        
        Returns:
            Tagline text or None
            
        Example:
            tagline = project.get_primary_tagline()
        """
        if self.brand_copy and 'taglines' in self.brand_copy:
            taglines = self.brand_copy['taglines']
            if taglines and len(taglines) > 0:
                return taglines[0].get('tagline')
        return None
    
    def get_color_palette(self) -> list:
        """
        Get the primary color palette.
        
        Returns:
            List of color hex codes
            
        Example:
            colors = project.get_color_palette()
            # ['#0066CC', '#003366', '#66B2FF']
        """
        if self.visual_identity and 'color_palette' in self.visual_identity:
            palette = self.visual_identity['color_palette']
            if 'primary_colors' in palette:
                return [c.get('hex') for c in palette['primary_colors']]
        return []
    
    def get_brand_story(self, length: str = 'medium') -> str:
        """
        Get brand story of specified length.
        
        Args:
            length: 'short', 'medium', or 'long'
            
        Returns:
            Brand story text or None
            
        Example:
            story = project.get_brand_story('short')
        """
        if self.brand_copy and 'brand_story' in self.brand_copy:
            return self.brand_copy['brand_story'].get(length)
        return None
    
    def get_preview_data(self) -> dict:
        """
        Get quick preview data for project cards/lists.
        
        Returns:
            Dictionary with preview information
            
        Example:
            preview = project.get_preview_data()
            # {'logo': '...', 'tagline': '...', 'colors': [...]}
        """
        return {
            'logo_url': self.get_logo_url(),
            'tagline': self.get_primary_tagline(),
            'colors': self.get_color_palette(),
            'industry': self.industry,
            'consistency_score': self.consistency_score
        }
    
    # ========================================================================
    # ASSET MANAGEMENT
    # ========================================================================
    
    def get_asset_count(self) -> int:
        """
        Get total number of assets.
        
        Returns:
            Asset count
            
        Example:
            count = project.get_asset_count()
        """
        return self.assets.count()
    
    def get_assets_by_type(self, asset_type: str):
        """
        Get assets of a specific type.
        
        Args:
            asset_type: Type of asset (e.g., 'logo', 'social_media_post')
            
        Returns:
            List of BrandAsset objects
            
        Example:
            logos = project.get_assets_by_type('logo')
        """
        from app.models.brand_assets import AssetType
        return self.assets.filter_by(asset_type=asset_type).all()
    
    def get_total_storage_size(self) -> int:
        """
        Get total storage used by project assets.
        
        Returns:
            Total bytes used
            
        Example:
            size_mb = project.get_total_storage_size() / (1024 * 1024)
        """
        total = db.session.query(
            db.func.sum(db.text('file_size'))
        ).filter(
            db.text('project_id = :pid')
        ).params(pid=self.id).scalar()
        
        return total or 0
    
    # ========================================================================
    # VARIANT MANAGEMENT
    # ========================================================================
    
    def get_variant_count(self) -> int:
        """
        Get number of A/B test variants.
        
        Returns:
            Variant count
            
        Example:
            count = project.get_variant_count()
        """
        return self.variants.count()
    
    def get_best_variant(self):
        """
        Get the variant with the highest overall score.
        
        Returns:
            BrandVariant object or None
            
        Example:
            best = project.get_best_variant()
            if best:
                print(f"Best variant: {best.variant_number}")
        """
        from sqlalchemy import desc
        return self.variants.order_by(
            desc('performance_score')
        ).first()
    
    def get_selected_variant(self):
        """
        Get the variant marked as selected/final.
        
        Returns:
            BrandVariant object or None
            
        Example:
            selected = project.get_selected_variant()
        """
        return self.variants.filter_by(is_selected=True).first()
    
    # ========================================================================
    # VERSION CONTROL
    # ========================================================================
    
    def create_new_version(self, user_id: int):
        """
        Create a new version of this project.
        Duplicates the project with a new version number.
        
        Args:
            user_id: ID of user creating the version
            
        Returns:
            New BrandProject object
            
        Example:
            new_version = project.create_new_version(user.id)
        """
        new_project = BrandProject(
            user_id=user_id,
            business_name=self.business_name,
            industry=self.industry,
            target_audience=self.target_audience,
            brand_values=self.brand_values,
            competitors=self.competitors,
            additional_context=self.additional_context,
            style_preferences=self.style_preferences,
            parent_project_id=self.id,
            version=self.version + 1
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        return new_project
    
    def get_version_history(self) -> list:
        """
        Get all versions of this project.
        
        Returns:
            List of BrandProject objects
            
        Example:
            versions = project.get_version_history()
            for v in versions:
                print(f"Version {v.version}: {v.created_at}")
        """
        if self.parent_project_id:
            # Get root project
            root = BrandProject.query.get(self.parent_project_id)
            if root:
                return [root] + root.child_versions.order_by('version').all()
        
        # This is the root, return all children
        return [self] + self.child_versions.order_by('version').all()
    
    def archive(self) -> None:
        """
        Archive this project.
        
        Example:
            project.archive()
        """
        self.is_archived = True
        self.archived_at = datetime.utcnow()
        db.session.commit()
    
    def unarchive(self) -> None:
        """
        Unarchive this project.
        
        Example:
            project.unarchive()
        """
        self.is_archived = False
        self.archived_at = None
        db.session.commit()
    
    # ========================================================================
    # SHARING & COLLABORATION
    # ========================================================================
    
    def generate_share_token(self) -> str:
        """
        Generate a unique share token for public sharing.
        
        Returns:
            Share token string
            
        Example:
            token = project.generate_share_token()
            share_url = f"https://app.com/shared/{token}"
        """
        self.share_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.share_token
    
    def make_public(self, password: str = None) -> str:
        """
        Make project publicly accessible.
        
        Args:
            password: Optional password for access
            
        Returns:
            Share token
            
        Example:
            token = project.make_public(password="secret123")
        """
        self.is_public = True
        
        if password:
            from werkzeug.security import generate_password_hash
            self.share_password = generate_password_hash(password)
        
        if not self.share_token:
            self.generate_share_token()
        
        db.session.commit()
        return self.share_token
    
    def make_private(self) -> None:
        """
        Make project private (remove public access).
        
        Example:
            project.make_private()
        """
        self.is_public = False
        db.session.commit()
    
    def verify_share_password(self, password: str) -> bool:
        """
        Verify share password if protected.
        
        Args:
            password: Password to verify
            
        Returns:
            True if correct or no password set
            
        Example:
            if not project.verify_share_password(password):
                return "Incorrect password"
        """
        if not self.share_password:
            return True
        
        from werkzeug.security import check_password_hash
        return check_password_hash(self.share_password, password)
    
    # ========================================================================
    # USER INTERACTIONS
    # ========================================================================
    
    def record_view(self) -> None:
        """
        Record a view of this project.
        
        Example:
            project.record_view()
        """
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
        db.session.commit()
    
    def set_user_rating(self, rating: int, feedback: str = None) -> None:
        """
        Set user rating for this project.
        
        Args:
            rating: Rating from 1-5
            feedback: Optional feedback text
            
        Example:
            project.set_user_rating(5, "Amazing results!")
        """
        self.user_rating = max(1, min(5, rating))
        
        if feedback:
            self.user_feedback = feedback
        
        db.session.commit()
    
    def toggle_favorite(self) -> bool:
        """
        Toggle favorite status.
        
        Returns:
            New favorite status
            
        Example:
            is_fav = project.toggle_favorite()
        """
        self.is_favorite = not self.is_favorite
        db.session.commit()
        return self.is_favorite
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self, include_full_data: bool = False) -> dict:
        """
        Convert project to dictionary.
        
        Args:
            include_full_data: Include all generated content
            
        Returns:
            Dictionary representation
            
        Example:
            data = project.to_dict()
            return jsonify(data)
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'project_name': self.project_name,
            'business_name': self.business_name,
            'industry': self.industry,
            'description': self.description,
            'status': self.status.value,
            'progress_percentage': self.progress_percentage,
            'progress_message': self.progress_message,
            'consistency_score': self.consistency_score,
            'quality_score': self.quality_score,
            'is_favorite': self.is_favorite,
            'user_rating': self.user_rating,
            'version': self.version,
            'is_archived': self.is_archived,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'generation_time_seconds': self.generation_time_seconds,
            'asset_count': self.get_asset_count(),
            'variant_count': self.get_variant_count(),
            'preview': self.get_preview_data()
        }
        
        if include_full_data:
            data.update({
                'target_audience': self.target_audience,
                'brand_values': self.brand_values,
                'competitors': self.competitors,
                'additional_context': self.additional_context,
                'strategy': self.strategy,
                'visual_identity': self.visual_identity,
                'brand_copy': self.brand_copy,
                'error_message': self.error_message,
                'tokens_used': self.tokens_used,
                'estimated_cost': self.estimated_cost,
                'model_versions': self.model_versions,
                'user_feedback': self.user_feedback
            })
        
        if self.is_public and self.share_token:
            data['share_url'] = f"/shared/{self.share_token}"
        
        return data
    
    def to_public_dict(self) -> dict:
        """
        Convert to public-safe dictionary (for shared links).
        Excludes sensitive information.
        
        Returns:
            Public project data
            
        Example:
            public_data = project.to_public_dict()
        """
        return {
            'id': self.id,
            'business_name': self.business_name,
            'industry': self.industry,
            'description': self.description,
            'preview': self.get_preview_data(),
            'consistency_score': self.consistency_score,
            'created_at': self.created_at.isoformat(),
            'view_count': self.view_count
        }
    
    # ========================================================================
    # STATIC METHODS & QUERIES
    # ========================================================================
    
    @staticmethod
    def get_by_share_token(token: str):
        """
        Get public project by share token.
        
        Args:
            token: Share token
            
        Returns:
            BrandProject or None
            
        Example:
            project = BrandProject.get_by_share_token(token)
        """
        return BrandProject.query.filter_by(
            share_token=token,
            is_public=True
        ).first()
    
    @staticmethod
    def get_user_projects(
        user_id: int,
        status: ProjectStatus = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0
    ):
        """
        Get projects for a specific user with filtering and pagination.
        
        Args:
            user_id: User ID
            status: Optional status filter
            include_archived: Include archived projects
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            Tuple of (projects list, total count)
            
        Example:
            projects, total = BrandProject.get_user_projects(
                user_id=user.id,
                status=ProjectStatus.COMPLETED,
                limit=10
            )
        """
        query = BrandProject.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if not include_archived:
            query = query.filter_by(is_archived=False)
        
        total = query.count()
        projects = query.order_by(
            db.desc(BrandProject.created_at)
        ).limit(limit).offset(offset).all()
        
        return projects, total
    
    @staticmethod
    def get_recent_projects(days: int = 7, limit: int = 10):
        """
        Get recently created completed projects.
        
        Args:
            days: Number of days to look back
            limit: Maximum results
            
        Returns:
            List of recent projects
            
        Example:
            recent = BrandProject.get_recent_projects(days=7)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return BrandProject.query.filter(
            BrandProject.created_at >= cutoff_date,
            BrandProject.status == ProjectStatus.COMPLETED,
            BrandProject.is_archived == False
        ).order_by(
            db.desc(BrandProject.created_at)
        ).limit(limit).all()
    
    @staticmethod
    def get_statistics() -> dict:
        """
        Get overall project statistics.
        
        Returns:
            Dictionary with statistics
            
        Example:
            stats = BrandProject.get_statistics()
            print(f"Success rate: {stats['success_rate']}%")
        """
        total = BrandProject.query.count()
        completed = BrandProject.query.filter_by(
            status=ProjectStatus.COMPLETED
        ).count()
        processing = BrandProject.query.filter_by(
            status=ProjectStatus.PROCESSING
        ).count()
        failed = BrandProject.query.filter_by(
            status=ProjectStatus.FAILED
        ).count()
        
        avg_rating = db.session.query(
            db.func.avg(BrandProject.user_rating)
        ).filter(
            BrandProject.user_rating.isnot(None)
        ).scalar()
        
        avg_generation_time = db.session.query(
            db.func.avg(BrandProject.generation_time_seconds)
        ).filter(
            BrandProject.generation_time_seconds.isnot(None)
        ).scalar()
        
        return {
            'total_projects': total,
            'completed': completed,
            'processing': processing,
            'failed': failed,
            'success_rate': round((completed / total * 100), 2) if total > 0 else 0,
            'average_rating': round(float(avg_rating), 2) if avg_rating else None,
            'average_generation_time': round(float(avg_generation_time), 2) if avg_generation_time else None
        }