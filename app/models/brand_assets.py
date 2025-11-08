"""
BrandAsset and BrandVariant Models - Manages generated files and A/B test variants.

This module contains two models:
1. BrandAsset - Stores generated files (logos, PDFs, images)
2. BrandVariant - Stores A/B test variants for comparison
"""

from app import db
from datetime import datetime, timedelta
import enum


class AssetType(enum.Enum):
    """Types of brand assets that can be generated."""
    LOGO = "logo"
    LOGO_VARIATION = "logo_variation"
    COLOR_PALETTE = "color_palette"
    TYPOGRAPHY_GUIDE = "typography_guide"
    STYLE_GUIDE = "style_guide"
    BUSINESS_CARD = "business_card"
    LETTERHEAD = "letterhead"
    SOCIAL_MEDIA_POST = "social_media_post"
    SOCIAL_MEDIA_COVER = "social_media_cover"
    PRESENTATION_TEMPLATE = "presentation_template"
    EMAIL_SIGNATURE = "email_signature"
    WEBSITE_MOCKUP = "website_mockup"
    MARKETING_MATERIAL = "marketing_material"
    BRAND_GUIDELINES = "brand_guidelines"
    OTHER = "other"


class AssetFormat(enum.Enum):
    """File formats for brand assets."""
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    SVG = "svg"
    PDF = "pdf"
    JSON = "json"
    AI = "ai"
    PSD = "psd"
    ZIP = "zip"
    HTML = "html"
    EPS = "eps"


class BrandAsset(db.Model):
    """
    Brand Asset model representing generated files and resources.
    
    Stores logos, documents, images, and other brand materials with
    metadata, versioning, and multi-cloud storage support.
    
    Attributes:
        id (int): Primary key
        project_id (int): Foreign key to BrandProject
        asset_type (AssetType): Type of asset
        file_format (AssetFormat): File format
        file_url (str): URL to access file
        file_size (int): File size in bytes
        
    Relationships:
        project: Many-to-One with BrandProject
    """
    __tablename__ = 'brand_assets'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = db.Column(db.Integer, primary_key=True)
    
    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('brand_projects.id'),
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # ASSET INFORMATION
    # ========================================================================
    asset_type = db.Column(
        db.Enum(AssetType),
        nullable=False,
        index=True
    )
    asset_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)  # Array of tags
    
    # ========================================================================
    # FILE DETAILS
    # ========================================================================
    file_format = db.Column(db.Enum(AssetFormat), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(500))  # Local path if stored locally
    file_size = db.Column(db.Integer)  # Size in bytes
    file_hash = db.Column(db.String(64))  # MD5 or SHA256 hash
    mime_type = db.Column(db.String(100))  # MIME type
    
    # ========================================================================
    # IMAGE SPECIFIC (if applicable)
    # ========================================================================
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    resolution_dpi = db.Column(db.Integer)
    color_mode = db.Column(db.String(20))  # RGB, CMYK, etc.
    has_transparency = db.Column(db.Boolean, default=False)
    
    # ========================================================================
    # METADATA
    # ========================================================================
    metadata = db.Column(db.JSON)  # Additional info (colors, fonts, etc.)
    generation_params = db.Column(db.JSON)  # Parameters used to generate
    ai_model_used = db.Column(db.String(50))  # e.g., "dall-e-3", "gpt-4"
    
    # ========================================================================
    # VERSIONING
    # ========================================================================
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)  # Current version
    parent_asset_id = db.Column(
        db.Integer,
        db.ForeignKey('brand_assets.id')
    )
    
    # ========================================================================
    # USAGE TRACKING
    # ========================================================================
    download_count = db.Column(db.Integer, default=0)
    last_downloaded_at = db.Column(db.DateTime)
    view_count = db.Column(db.Integer, default=0)
    
    # ========================================================================
    # STORAGE
    # ========================================================================
    storage_provider = db.Column(
        db.String(50),
        default='local'
    )  # local, s3, gcs, azure
    storage_region = db.Column(db.String(50))
    storage_bucket = db.Column(db.String(200))
    cdn_url = db.Column(db.String(500))  # CDN URL if available
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    expires_at = db.Column(db.DateTime)  # Optional expiry
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    project = db.relationship('BrandProject', back_populates='assets')
    
    # Self-referential for versions
    child_versions = db.relationship(
        'BrandAsset',
        backref=db.backref('parent_asset', remote_side=[id]),
        lazy='dynamic'
    )
    
    # ========================================================================
    # TABLE CONFIGURATION
    # ========================================================================
    __table_args__ = (
        db.Index('idx_asset_project_type', 'project_id', 'asset_type'),
        db.Index('idx_asset_type', 'asset_type'),
        db.Index('idx_asset_created', 'created_at'),
    )
    
    # ========================================================================
    # REPRESENTATION
    # ========================================================================
    def __repr__(self):
        return f'<BrandAsset {self.id}: {self.asset_type.value}>'
    
    # ========================================================================
    # FILE MANAGEMENT
    # ========================================================================
    
    def get_file_url(self, expiry_seconds: int = 3600) -> str:
        """
        Get URL to access the file.
        Generates pre-signed URL for cloud storage.
        
        Args:
            expiry_seconds: URL expiry time for cloud storage
            
        Returns:
            Accessible file URL
            
        Example:
            url = asset.get_file_url(expiry_seconds=7200)
        """
        if self.cdn_url:
            return self.cdn_url
        
        if self.storage_provider == 's3':
            return self._generate_s3_presigned_url(expiry_seconds)
        elif self.storage_provider == 'gcs':
            return self._generate_gcs_signed_url(expiry_seconds)
        elif self.storage_provider == 'azure':
            return self._generate_azure_sas_url(expiry_seconds)
        else:
            # Local or direct URL
            return self.file_url
    
    def _generate_s3_presigned_url(self, expiry_seconds: int) -> str:
        """Generate AWS S3 pre-signed URL."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            import os
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.storage_region or os.getenv('S3_REGION')
            )
            
            bucket_name = self.storage_bucket or os.getenv('S3_BUCKET_NAME')
            
            # Extract key from full URL or use file_path
            if '/' in self.file_url:
                key = self.file_url.split(f"{bucket_name}/")[-1]
            else:
                key = self.file_path
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiry_seconds
            )
            
            return url
        except Exception as e:
            print(f"Error generating S3 URL: {e}")
            return self.file_url
    
    def _generate_gcs_signed_url(self, expiry_seconds: int) -> str:
        """Generate Google Cloud Storage signed URL."""
        try:
            from google.cloud import storage
            import os
            
            client = storage.Client()
            bucket = client.bucket(self.storage_bucket)
            blob = bucket.blob(self.file_path)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiry_seconds),
                method="GET"
            )
            
            return url
        except Exception as e:
            print(f"Error generating GCS URL: {e}")
            return self.file_url
    
    def _generate_azure_sas_url(self, expiry_seconds: int) -> str:
        """Generate Azure Blob Storage SAS URL."""
        try:
            from azure.storage.blob import BlobServiceClient, generate_blob_sas
            from azure.storage.blob import BlobSasPermissions
            import os
            
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            sas_token = generate_blob_sas(
                account_name=blob_service_client.account_name,
                container_name=self.storage_bucket,
                blob_name=self.file_path,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiry_seconds)
            )
            
            url = f"{self.file_url}?{sas_token}"
            return url
        except Exception as e:
            print(f"Error generating Azure URL: {e}")
            return self.file_url
    
    def record_download(self) -> None:
        """
        Record a download of this asset.
        
        Example:
            asset.record_download()
        """
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()
        db.session.commit()
    
    def record_view(self) -> None:
        """
        Record a view of this asset.
        
        Example:
            asset.record_view()
        """
        self.view_count += 1
        db.session.commit()
    
    def get_file_size_formatted(self) -> str:
        """
        Get human-readable file size.
        
        Returns:
            Formatted file size (e.g., "2.5 MB")
            
        Example:
            size = asset.get_file_size_formatted()  # "245.6 KB"
        """
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} PB"
    
    def get_dimensions(self) -> str:
        """
        Get asset dimensions if applicable.
        
        Returns:
            Dimensions string (e.g., "1920x1080") or None
            
        Example:
            dims = asset.get_dimensions()
        """
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None
    
    # ========================================================================
    # ASSET TYPE CHECKS
    # ========================================================================
    
    def is_image(self) -> bool:
        """Check if asset is an image."""
        return self.file_format in [
            AssetFormat.PNG,
            AssetFormat.JPG,
            AssetFormat.JPEG,
            AssetFormat.SVG
        ]
    
    def is_vector(self) -> bool:
        """Check if asset is vector format."""
        return self.file_format in [
            AssetFormat.SVG,
            AssetFormat.AI,
            AssetFormat.EPS
        ]
    
    def is_document(self) -> bool:
        """Check if asset is a document."""
        return self.file_format in [
            AssetFormat.PDF
        ]
    
    def is_editable(self) -> bool:
        """Check if asset is in editable format."""
        return self.file_format in [
            AssetFormat.AI,
            AssetFormat.PSD,
            AssetFormat.SVG
        ]
    
    def is_web_optimized(self) -> bool:
        """Check if asset is optimized for web."""
        return self.file_format in [
            AssetFormat.PNG,
            AssetFormat.JPG,
            AssetFormat.SVG,
            AssetFormat.HTML
        ] and self.file_size and self.file_size < 1024 * 1024  # Under 1MB
    
    # ========================================================================
    # METADATA MANAGEMENT
    # ========================================================================
    
    def add_metadata(self, key: str, value) -> None:
        """
        Add metadata to the asset.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Example:
            asset.add_metadata('primary_color', '#0066CC')
        """
        if not self.metadata:
            self.metadata = {}
        
        self.metadata[key] = value
        db.session.commit()
    
    def get_metadata(self, key: str, default=None):
        """
        Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
            
        Example:
            color = asset.get_metadata('primary_color', '#000000')
        """
        if not self.metadata:
            return default
        
        return self.metadata.get(key, default)
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self, include_url: bool = True) -> dict:
        """
        Convert asset to dictionary.
        
        Args:
            include_url: Include file URL
            
        Returns:
            Dictionary representation
            
        Example:
            data = asset.to_dict()
        """
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'asset_type': self.asset_type.value,
            'asset_name': self.asset_name,
            'description': self.description,
            'file_format': self.file_format.value,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'width': self.width,
            'height': self.height,
            'dimensions': self.get_dimensions(),
            'resolution_dpi': self.resolution_dpi,
            'version': self.version,
            'is_active': self.is_active,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'metadata': self.metadata,
            'storage_provider': self.storage_provider,
            'created_at': self.created_at.isoformat(),
            'is_image': self.is_image(),
            'is_vector': self.is_vector(),
            'is_editable': self.is_editable(),
            'is_web_optimized': self.is_web_optimized()
        }
        
        if include_url:
            data['file_url'] = self.get_file_url()
            if self.cdn_url:
                data['cdn_url'] = self.cdn_url
        
        return data
    
    # ========================================================================
    # STATIC METHODS
    # ========================================================================
    
    @staticmethod
    def get_by_project_and_type(project_id: int, asset_type: AssetType):
        """
        Get assets by project and type.
        
        Args:
            project_id: Project ID
            asset_type: Type of asset
            
        Returns:
            List of BrandAsset objects
            
        Example:
            logos = BrandAsset.get_by_project_and_type(
                project_id=1,
                asset_type=AssetType.LOGO
            )
        """
        return BrandAsset.query.filter_by(
            project_id=project_id,
            asset_type=asset_type,
            is_active=True
        ).order_by(db.desc(BrandAsset.created_at)).all()
    
    @staticmethod
    def get_total_storage_used(user_id: int = None, project_id: int = None) -> int:
        """
        Get total storage used in bytes.
        
        Args:
            user_id: Optional user ID to filter
            project_id: Optional project ID to filter
            
        Returns:
            Total bytes used
            
        Example:
            total_gb = BrandAsset.get_total_storage_used(user_id=1) / (1024**3)
        """
        query = db.session.query(db.func.sum(BrandAsset.file_size))
        
        if project_id:
            query = query.filter(BrandAsset.project_id == project_id)
        elif user_id:
            from app.models.project import BrandProject
            query = query.join(BrandProject).filter(BrandProject.user_id == user_id)
        
        total = query.scalar()
        return total or 0


# ============================================================================
# BRAND VARIANT MODEL
# ============================================================================

class BrandVariant(db.Model):
    """
    Brand Variant model for A/B testing different brand identity versions.
    
    Stores alternative versions of brand identities with performance metrics
    for comparison and testing.
    
    Attributes:
        id (int): Primary key
        project_id (int): Foreign key to BrandProject
        variant_number (int): Variant number (1, 2, 3 for A/B/C)
        visual_identity (dict): Alternative visual design (JSON)
        brand_copy (dict): Alternative copy/messaging (JSON)
        performance_score (float): Predicted performance
        
    Relationships:
        project: Many-to-One with BrandProject
    """
    __tablename__ = 'brand_variants'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = db.Column(db.Integer, primary_key=True)
    
    # ========================================================================
    # FOREIGN KEYS
    # ========================================================================
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('brand_projects.id'),
        nullable=False,
        index=True
    )
    
    # ========================================================================
    # VARIANT INFORMATION
    # ========================================================================
    variant_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3 (A, B, C)
    variant_name = db.Column(db.String(100))  # Optional custom name like "Modern", "Classic"
    description = db.Column(db.Text)
    
    # ========================================================================
    # GENERATED CONTENT
    # ========================================================================
    visual_identity = db.Column(db.JSON)
    brand_copy = db.Column(db.JSON)
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    performance_score = db.Column(db.Float)  # Predicted performance (0-1)
    sentiment_score = db.Column(db.Float)    # Sentiment analysis score (0-1)
    aesthetic_score = db.Column(db.Float)    # Logo/visual quality score (0-1)
    consistency_score = db.Column(db.Float)  # Brand consistency score (0-1)
    
    # ========================================================================
    # A/B TESTING DATA
    # ========================================================================
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    ctr = db.Column(db.Float)  # Click-through rate (%)
    conversion_rate = db.Column(db.Float)  # Conversion rate (%)
    bounce_rate = db.Column(db.Float)  # Bounce rate (%)
    avg_time_on_page = db.Column(db.Float)  # Average time in seconds
    
    # ========================================================================
    # USER FEEDBACK
    # ========================================================================
    user_rating = db.Column(db.Integer)  # 1-5 stars
    user_notes = db.Column(db.Text)
    feedback_count = db.Column(db.Integer, default=0)
    
    # ========================================================================
    # STATUS
    # ========================================================================
    is_selected = db.Column(db.Boolean, default=False)  # Final chosen variant
    is_active = db.Column(db.Boolean, default=True)
    test_start_date = db.Column(db.DateTime)
    test_end_date = db.Column(db.DateTime)
    
    # ========================================================================
    # TIMESTAMPS
    # ========================================================================
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    project = db.relationship('BrandProject', back_populates='variants')
    
    # ========================================================================
    # TABLE CONFIGURATION
    # ========================================================================
    __table_args__ = (
        db.Index('idx_variant_project', 'project_id'),
        db.UniqueConstraint(
            'project_id',
            'variant_number',
            name='uq_project_variant_number'
        ),
    )
    
    # ========================================================================
    # REPRESENTATION
    # ========================================================================
    def __repr__(self):
        return f'<BrandVariant {self.id}: Variant {self.variant_number}>'
    
    # ========================================================================
    # PERFORMANCE TRACKING
    # ========================================================================
    
    def record_impression(self) -> None:
        """
        Record an impression (view) of this variant.
        
        Example:
            variant.record_impression()
        """
        self.impressions += 1
        db.session.commit()
    
    def record_click(self) -> None:
        """
        Record a click on this variant.
        
        Example:
            variant.record_click()
        """
        self.clicks += 1
        self._update_ctr()
        db.session.commit()
    
    def record_conversion(self) -> None:
        """
        Record a conversion for this variant.
        
        Example:
            variant.record_conversion()
        """
        self.conversions += 1
        self._update_conversion_rate()
        db.session.commit()
    
    def _update_ctr(self) -> None:
        """Update click-through rate."""
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
    
    def _update_conversion_rate(self) -> None:
        """Update conversion rate."""
        if self.clicks > 0:
            self.conversion_rate = (self.conversions / self.clicks) * 100
    
    def get_overall_score(self) -> float:
        """
        Calculate overall weighted score for variant comparison.
        
        Returns:
            Overall score (0-1)
            
        Example:
            score = variant.get_overall_score()
        """
        weights = {
            'performance': 0.3,
            'sentiment': 0.2,
            'aesthetic': 0.2,
            'consistency': 0.3
        }
        
        scores = [
            (self.performance_score or 0) * weights['performance'],
            (self.sentiment_score or 0) * weights['sentiment'],
            (self.aesthetic_score or 0) * weights['aesthetic'],
            (self.consistency_score or 0) * weights['consistency']
        ]
        
        return round(sum(scores), 3)
    
    def get_statistical_significance(self, other_variant) -> dict:
        """
        Calculate statistical significance vs another variant.
        
        Args:
            other_variant: Another BrandVariant to compare
            
        Returns:
            Dict with statistical metrics
            
        Example:
            sig = variant_a.get_statistical_significance(variant_b)
        """
        # Simple z-test for conversion rates
        if not other_variant or self.impressions == 0 or other_variant.impressions == 0:
            return {'significant': False, 'confidence': 0}
        
        p1 = self.conversions / self.impressions
        p2 = other_variant.conversions / other_variant.impressions
        
        # Calculate pooled standard error
        p_pool = (self.conversions + other_variant.conversions) / (self.impressions + other_variant.impressions)
        se = ((p_pool * (1 - p_pool)) * (1/self.impressions + 1/other_variant.impressions)) ** 0.5
        
        # Calculate z-score
        z_score = abs((p1 - p2) / se) if se > 0 else 0
        
        # Confidence level (simplified)
        confidence = min(z_score / 2, 0.99)  # Max 99% confidence
        
        return {
            'significant': z_score > 1.96,  # 95% confidence
            'confidence': round(confidence, 3),
            'z_score': round(z_score, 3),
            'lift': round(((p1 / p2) - 1) * 100, 2) if p2 > 0 else 0
        }
    
    # ========================================================================
    # SELECTION
    # ========================================================================
    
    def select_as_final(self) -> None:
        """
        Mark this variant as the selected final version.
        Unselects all other variants for this project.
        
        Example:
            variant.select_as_final()
        """
        # Unselect other variants
        BrandVariant.query.filter_by(
            project_id=self.project_id
        ).update({'is_selected': False})
        
        self.is_selected = True
        db.session.commit()
    
    def start_test(self) -> None:
        """
        Start A/B test for this variant.
        
        Example:
            variant.start_test()
        """
        self.test_start_date = datetime.utcnow()
        self.is_active = True
        db.session.commit()
    
    def end_test(self) -> None:
        """
        End A/B test for this variant.
        
        Example:
            variant.end_test()
        """
        self.test_end_date = datetime.utcnow()
        self.is_active = False
        db.session.commit()
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self, include_full_data: bool = False) -> dict:
        """
        Convert variant to dictionary.
        
        Args:
            include_full_data: Include all generated content
            
        Returns:
            Dictionary representation
            
        Example:
            data = variant.to_dict()
        """
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'variant_number': self.variant_number,
            'variant_name': self.variant_name,
            'description': self.description,
            'performance_score': self.performance_score,
            'sentiment_score': self.sentiment_score,
            'aesthetic_score': self.aesthetic_score,
            'consistency_score': self.consistency_score,
            'overall_score': self.get_overall_score(),
            'is_selected': self.is_selected,
            'is_active': self.is_active,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'ctr': round(self.ctr, 2) if self.ctr else 0,
            'conversion_rate': round(self.conversion_rate, 2) if self.conversion_rate else 0,
            'user_rating': self.user_rating,
            'created_at': self.created_at.isoformat(),
            'test_start_date': self.test_start_date.isoformat() if self.test_start_date else None,
            'test_end_date': self.test_end_date.isoformat() if self.test_end_date else None
        }
        
        if include_full_data:
            data.update({
                'visual_identity': self.visual_identity,
                'brand_copy': self.brand_copy,
                'user_notes': self.user_notes
            })
        
        return data
    
    # ========================================================================
    # STATIC METHODS
    # ========================================================================
    
    @staticmethod
    def get_project_variants(project_id: int):
        """
        Get all active variants for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of BrandVariant objects
            
        Example:
            variants = BrandVariant.get_project_variants(project_id=1)
        """
        return BrandVariant.query.filter_by(
            project_id=project_id,
            is_active=True
        ).order_by(BrandVariant.variant_number).all()
    
    @staticmethod
    def compare_variants(project_id: int) -> list:
        """
        Get comparison data for all variants, sorted by performance.
        
        Args:
            project_id: Project ID
            
        Returns:
            Sorted list of variant dictionaries
            
        Example:
            comparison = BrandVariant.compare_variants(project_id=1)
            best = comparison[0]
        """
        variants = BrandVariant.get_project_variants(project_id)
        
        # Sort by overall score
        sorted_variants = sorted(
            variants,
            key=lambda v: v.get_overall_score(),
            reverse=True
        )
        
        return [v.to_dict() for v in sorted_variants]
    
    @staticmethod
    def get_winning_variant(project_id: int):
        """
        Get the variant with the best performance.