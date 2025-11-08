"""
User Model - Handles user authentication, authorization, and subscription management.

This module contains the User model and related enums for managing user accounts,
authentication, subscription tiers, and usage tracking.
"""

from app import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import enum


class UserTier(enum.Enum):
    """User subscription tiers with different feature limits."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserStatus(enum.Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(db.Model):
    """
    User model representing registered users of the platform.
    
    Handles authentication, authorization, subscription management, and usage tracking.
    
    Attributes:
        id (int): Primary key
        email (str): Unique email address (indexed)
        password_hash (str): Bcrypt hashed password
        full_name (str): User's full name
        company_name (str): Optional company name
        tier (UserTier): Subscription tier (FREE, PREMIUM, ENTERPRISE)
        status (UserStatus): Account status
        generations_this_month (int): Usage counter for current month
        total_generations (int): Total lifetime generations
        
    Relationships:
        projects: One-to-Many with BrandProject
    """
    __tablename__ = 'users'
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    id = db.Column(db.Integer, primary_key=True)
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = db.Column(db.String(255), nullable=False)
    
    # ========================================================================
    # PROFILE INFORMATION
    # ========================================================================
    full_name = db.Column(db.String(100))
    company_name = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    website = db.Column(db.String(200))
    
    # ========================================================================
    # ACCOUNT STATUS
    # ========================================================================
    tier = db.Column(
        db.Enum(UserTier),
        default=UserTier.FREE,
        nullable=False,
        index=True
    )
    status = db.Column(
        db.Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True
    )
    is_email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    
    # ========================================================================
    # USAGE TRACKING
    # ========================================================================
    generations_this_month = db.Column(db.Integer, default=0)
    total_generations = db.Column(db.Integer, default=0)
    last_generation_reset = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    # ========================================================================
    # SUBSCRIPTION INFORMATION
    # ========================================================================
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    subscription_auto_renew = db.Column(db.Boolean, default=True)
    
    # Payment Integration (Stripe)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    stripe_subscription_id = db.Column(db.String(100))
    payment_method_last4 = db.Column(db.String(4))
    
    # ========================================================================
    # SETTINGS & PREFERENCES
    # ========================================================================
    preferences = db.Column(db.JSON, default=dict)
    notification_settings = db.Column(db.JSON, default=dict)
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    
    # ========================================================================
    # SECURITY
    # ========================================================================
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))  # IPv6 compatible
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(100))
    password_reset_expires = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    
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
    deleted_at = db.Column(db.DateTime)
    last_active_at = db.Column(db.DateTime)
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    projects = db.relationship(
        'BrandProject',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # ========================================================================
    # TABLE CONFIGURATION
    # ========================================================================
    __table_args__ = (
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_tier', 'tier'),
        db.Index('idx_user_status', 'status'),
        db.Index('idx_user_created_at', 'created_at'),
        db.Index('idx_user_stripe_customer', 'stripe_customer_id'),
    )
    
    # ========================================================================
    # REPRESENTATION
    # ========================================================================
    def __repr__(self):
        return f'<User {self.id}: {self.email}>'
    
    # ========================================================================
    # PASSWORD MANAGEMENT
    # ========================================================================
    
    def set_password(self, password: str) -> None:
        """
        Hash and set user password using bcrypt.
        
        Args:
            password: Plain text password to hash
        
        Example:
            user.set_password("SecurePass123")
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
            
        Example:
            if user.check_password("password123"):
                # Login successful
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_password_reset_token(self) -> str:
        """
        Generate a password reset token valid for 1 hour.
        
        Returns:
            Reset token string
            
        Example:
            token = user.generate_password_reset_token()
            send_reset_email(user.email, token)
        """
        import secrets
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return token
    
    def verify_password_reset_token(self, token: str) -> bool:
        """
        Verify password reset token is valid and not expired.
        
        Args:
            token: Reset token to verify
            
        Returns:
            True if valid, False otherwise
        """
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        if self.password_reset_token != token:
            return False
        
        if datetime.utcnow() > self.password_reset_expires:
            return False
        
        return True
    
    def reset_password(self, new_password: str) -> None:
        """
        Reset password and clear reset token.
        
        Args:
            new_password: New plain text password
        """
        self.set_password(new_password)
        self.password_reset_token = None
        self.password_reset_expires = None
        db.session.commit()
    
    # ========================================================================
    # USAGE & LIMITS MANAGEMENT
    # ========================================================================
    
    def can_generate(self) -> bool:
        """
        Check if user has remaining generations for the current month.
        Automatically resets counter if it's a new month.
        
        Returns:
            True if user can generate more brand identities
            
        Example:
            if user.can_generate():
                # Proceed with generation
                user.increment_generation_count()
        """
        # Reset counter if it's a new month
        now = datetime.utcnow()
        if (self.last_generation_reset.month != now.month or 
            self.last_generation_reset.year != now.year):
            self.generations_this_month = 0
            self.last_generation_reset = now
            db.session.commit()
        
        # Check against tier limits
        limits = self._get_tier_limits()
        
        # Enterprise tier gets unlimited
        if limits['generations_per_month'] == -1:
            return True
        
        return self.generations_this_month < limits['generations_per_month']
    
    def increment_generation_count(self) -> None:
        """
        Increment the generation counter for both monthly and total counts.
        Call this after successful generation.
        
        Example:
            project = create_brand_project(user)
            user.increment_generation_count()
        """
        self.generations_this_month += 1
        self.total_generations += 1
        self.last_active_at = datetime.utcnow()
        db.session.commit()
    
    def get_remaining_generations(self) -> int:
        """
        Get the number of remaining generations for the current month.
        
        Returns:
            Number of remaining generations (-1 for unlimited)
            
        Example:
            remaining = user.get_remaining_generations()
            print(f"You have {remaining} generations left")
        """
        limits = self._get_tier_limits()
        
        # Unlimited for enterprise
        if limits['generations_per_month'] == -1:
            return -1
        
        remaining = limits['generations_per_month'] - self.generations_this_month
        return max(0, remaining)
    
    def _get_tier_limits(self) -> dict:
        """
        Get feature limits based on user tier.
        
        Returns:
            Dictionary of tier limits and features
        """
        tier_limits = {
            UserTier.FREE: {
                'generations_per_month': 10,
                'max_variants': 3,
                'max_projects': 5,
                'max_storage_gb': 1,
                'export_formats': ['json'],
                'analytics': False,
                'priority_support': False,
                'custom_branding': False,
                'api_access': False,
                'team_members': 1
            },
            UserTier.PREMIUM: {
                'generations_per_month': 100,
                'max_variants': 5,
                'max_projects': 50,
                'max_storage_gb': 10,
                'export_formats': ['json', 'pdf', 'zip'],
                'analytics': True,
                'priority_support': False,
                'custom_branding': True,
                'api_access': False,
                'team_members': 3
            },
            UserTier.ENTERPRISE: {
                'generations_per_month': -1,  # Unlimited
                'max_variants': 10,
                'max_projects': -1,  # Unlimited
                'max_storage_gb': 100,
                'export_formats': ['json', 'pdf', 'zip', 'api'],
                'analytics': True,
                'priority_support': True,
                'custom_branding': True,
                'api_access': True,
                'team_members': -1  # Unlimited
            }
        }
        
        return tier_limits.get(self.tier, tier_limits[UserTier.FREE])
    
    def get_tier_info(self) -> dict:
        """
        Get comprehensive tier information.
        
        Returns:
            Dictionary with tier limits, usage, and features
        """
        limits = self._get_tier_limits()
        
        return {
            'tier': self.tier.value,
            'limits': limits,
            'usage': {
                'generations_this_month': self.generations_this_month,
                'generations_remaining': self.get_remaining_generations(),
                'total_generations': self.total_generations
            },
            'subscription': {
                'is_active': self.is_subscription_active(),
                'start_date': self.subscription_start_date.isoformat() if self.subscription_start_date else None,
                'end_date': self.subscription_end_date.isoformat() if self.subscription_end_date else None,
                'auto_renew': self.subscription_auto_renew
            }
        }
    
    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================
    
    def upgrade_tier(self, new_tier: UserTier) -> None:
        """
        Upgrade user to a new tier.
        
        Args:
            new_tier: New subscription tier
            
        Example:
            user.upgrade_tier(UserTier.PREMIUM)
        """
        old_tier = self.tier
        self.tier = new_tier
        self.subscription_start_date = datetime.utcnow()
        
        # Set subscription end date (1 month for monthly plans)
        self.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        
        db.session.commit()
        
        print(f"User {self.email} upgraded from {old_tier.value} to {new_tier.value}")
    
    def downgrade_tier(self, new_tier: UserTier) -> None:
        """
        Downgrade user to a lower tier.
        
        Args:
            new_tier: New subscription tier
            
        Example:
            user.downgrade_tier(UserTier.FREE)
        """
        old_tier = self.tier
        self.tier = new_tier
        db.session.commit()
        
        print(f"User {self.email} downgraded from {old_tier.value} to {new_tier.value}")
    
    def is_subscription_active(self) -> bool:
        """
        Check if user's subscription is currently active.
        
        Returns:
            True if subscription is active
            
        Example:
            if not user.is_subscription_active():
                # Show upgrade prompt
        """
        # Free tier is always "active"
        if self.tier == UserTier.FREE:
            return True
        
        # Check if subscription end date exists and is in future
        if not self.subscription_end_date:
            return False
        
        return datetime.utcnow() < self.subscription_end_date
    
    def renew_subscription(self, months: int = 1) -> None:
        """
        Renew subscription for specified months.
        
        Args:
            months: Number of months to renew
            
        Example:
            user.renew_subscription(months=12)  # Annual renewal
        """
        if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
            # Extend from current end date
            self.subscription_end_date += timedelta(days=30 * months)
        else:
            # Start new subscription from now
            self.subscription_end_date = datetime.utcnow() + timedelta(days=30 * months)
        
        db.session.commit()
    
    def cancel_subscription(self) -> None:
        """
        Cancel subscription (will downgrade at end of billing period).
        
        Example:
            user.cancel_subscription()
            # User keeps access until subscription_end_date
        """
        self.subscription_auto_renew = False
        db.session.commit()
    
    # ========================================================================
    # SECURITY & ACCOUNT MANAGEMENT
    # ========================================================================
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """
        Lock account temporarily (usually after failed login attempts).
        
        Args:
            duration_minutes: How long to lock the account
            
        Example:
            user.lock_account(duration_minutes=60)
        """
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        db.session.commit()
    
    def unlock_account(self) -> None:
        """
        Manually unlock account.
        
        Example:
            user.unlock_account()
        """
        self.account_locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
    
    def is_account_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Returns:
            True if account is locked
            
        Example:
            if user.is_account_locked():
                return "Account is locked. Try again later."
        """
        if not self.account_locked_until:
            return False
        
        # Check if lock has expired
        if datetime.utcnow() > self.account_locked_until:
            # Lock has expired, clear it
            self.unlock_account()
            return False
        
        return True
    
    def record_login_attempt(self, success: bool, ip_address: str = None) -> None:
        """
        Record a login attempt and handle account locking.
        
        Args:
            success: Whether the login was successful
            ip_address: IP address of login attempt
            
        Example:
            if user.check_password(password):
                user.record_login_attempt(success=True, ip_address=request.remote_addr)
            else:
                user.record_login_attempt(success=False, ip_address=request.remote_addr)
        """
        if success:
            self.last_login = datetime.utcnow()
            self.last_login_ip = ip_address
            self.failed_login_attempts = 0
            self.account_locked_until = None
            self.last_active_at = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.lock_account(duration_minutes=30)
        
        db.session.commit()
    
    def soft_delete(self) -> None:
        """
        Soft delete user account (mark as deleted but keep data).
        Useful for GDPR compliance and data recovery.
        
        Example:
            user.soft_delete()
            # User marked as deleted but data preserved
        """
        self.status = UserStatus.DELETED
        self.deleted_at = datetime.utcnow()
        # Anonymize email to prevent reuse
        self.email = f"deleted_{self.id}_{int(datetime.utcnow().timestamp())}@deleted.local"
        db.session.commit()
    
    def hard_delete(self) -> None:
        """
        Permanently delete user and all associated data.
        WARNING: This action cannot be undone!
        
        Example:
            user.hard_delete()
            # User and all projects permanently deleted
        """
        db.session.delete(self)
        db.session.commit()
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user object to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dictionary representation of user
            
        Example:
            user_data = user.to_dict()
            return jsonify(user_data)
        """
        tier_info = self.get_tier_info()
        
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'company_name': self.company_name,
            'phone_number': self.phone_number,
            'profile_image_url': self.profile_image_url,
            'bio': self.bio,
            'website': self.website,
            'tier': self.tier.value,
            'status': self.status.value,
            'is_email_verified': self.is_email_verified,
            'tier_info': tier_info,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None
        }
        
        if include_sensitive:
            data.update({
                'stripe_customer_id': self.stripe_customer_id,
                'stripe_subscription_id': self.stripe_subscription_id,
                'payment_method_last4': self.payment_method_last4,
                'preferences': self.preferences,
                'notification_settings': self.notification_settings,
                'language': self.language,
                'timezone': self.timezone,
                'two_factor_enabled': self.two_factor_enabled
            })
        
        return data
    
    def to_public_dict(self) -> dict:
        """
        Convert user to public-safe dictionary (minimal information).
        Used for public profiles or shared content.
        
        Returns:
            Public user data
            
        Example:
            author_info = project.user.to_public_dict()
        """
        return {
            'id': self.id,
            'full_name': self.full_name,
            'profile_image_url': self.profile_image_url,
            'bio': self.bio,
            'website': self.website,
            'tier': self.tier.value,
            'created_at': self.created_at.isoformat()
        }
    
    # ========================================================================
    # STATIC METHODS & QUERIES
    # ========================================================================
    
    @staticmethod
    def get_active_users_count() -> int:
        """Get count of active users."""
        return User.query.filter_by(status=UserStatus.ACTIVE).count()
    
    @staticmethod
    def get_by_email(email: str):
        """
        Get user by email address.
        
        Args:
            email: User email (case-insensitive)
            
        Returns:
            User object or None
            
        Example:
            user = User.get_by_email("john@example.com")
        """
        return User.query.filter_by(email=email.lower().strip()).first()
    
    @staticmethod
    def get_by_stripe_customer_id(customer_id: str):
        """
        Get user by Stripe customer ID.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            User object or None
        """
        return User.query.filter_by(stripe_customer_id=customer_id).first()
    
    @staticmethod
    def get_users_by_tier(tier: UserTier, limit: int = 100):
        """
        Get users by subscription tier.
        
        Args:
            tier: UserTier enum
            limit: Maximum number of results
            
        Returns:
            List of User objects
        """
        return User.query.filter_by(tier=tier).limit(limit).all()
    
    @staticmethod
    def get_expiring_subscriptions(days: int = 7):
        """
        Get users whose subscriptions are expiring soon.
        
        Args:
            days: Number of days before expiration
            
        Returns:
            List of User objects with expiring subscriptions
            
        Example:
            users = User.get_expiring_subscriptions(days=7)
            for user in users:
                send_renewal_reminder(user.email)
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        return User.query.filter(
            User.subscription_end_date.isnot(None),
            User.subscription_end_date <= cutoff_date,
            User.subscription_end_date > datetime.utcnow(),
            User.subscription_auto_renew == False
        ).all()
    
    @staticmethod
    def get_statistics() -> dict:
        """
        Get overall user statistics.
        
        Returns:
            Dictionary with user statistics
            
        Example:
            stats = User.get_statistics()
            print(f"Total users: {stats['total_users']}")
        """
        total = User.query.count()
        active = User.query.filter_by(status=UserStatus.ACTIVE).count()
        
        free_users = User.query.filter_by(tier=UserTier.FREE).count()
        premium_users = User.query.filter_by(tier=UserTier.PREMIUM).count()
        enterprise_users = User.query.filter_by(tier=UserTier.ENTERPRISE).count()
        
        total_generations = db.session.query(
            db.func.sum(User.total_generations)
        ).scalar() or 0
        
        return {
            'total_users': total,
            'active_users': active,
            'tier_breakdown': {
                'free': free_users,
                'premium': premium_users,
                'enterprise': enterprise_users
            },
            'total_generations': int(total_generations),
            'avg_generations_per_user': round(total_generations / total, 2) if total > 0 else 0
        }