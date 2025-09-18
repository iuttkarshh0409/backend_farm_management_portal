"""User models for Farmer, Veterinarian, and Admin."""

from sqlalchemy import Column, String, Boolean, Integer, Text, Enum, Index
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from app.models.base import BaseModel
from app import db


class UserRole(enum.Enum):
    """User role enumeration."""
    FARMER = "farmer"
    VETERINARIAN = "veterinarian"
    ADMIN = "admin"


class UserStatus(enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class User(BaseModel):
    """Base user model with polymorphic inheritance."""
    
    __tablename__ = 'users'
    
    # Basic user information
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(15), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User type and status
    user_type = Column(Enum(UserRole), nullable=False, index=True)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    # Verification fields
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String(6), nullable=True)
    otp_created_at = Column(db.DateTime, nullable=True)
    
    # Profile fields
    address = Column(Text, nullable=True)
    profile_image = Column(String(255), nullable=True)
    
    # Polymorphic identity
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_verified(self):
        """Check if user is fully verified."""
        return self.email_verified and self.phone_verified
    
    def can_login(self):
        """Check if user can login."""
        return self.status == UserStatus.ACTIVE and self.is_verified()
    
    def to_dict(self):
        """Convert to dictionary, excluding sensitive data."""
        data = super().to_dict()
        # Remove sensitive information
        data.pop('password_hash', None)
        data.pop('otp_code', None)
        return data
    
    def __repr__(self):
        return f'<User({self.name}, {self.user_type.value})>'


class Farmer(User):
    """Farmer user model."""
    
    __tablename__ = 'farmers'
    
    # Foreign key to users table
    id = Column(db.ForeignKey('users.id'), primary_key=True)
    
    # Farmer-specific fields
    aadhar_no = Column(String(12), unique=True, nullable=True, index=True)
    farm_name = Column(String(150), nullable=True)
    farm_size = Column(String(50), nullable=True)
    farm_type = Column(String(50), nullable=True)
    registration_number = Column(String(50), nullable=True, unique=True)
    
    # Location information
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Relationships
    animals = relationship("Animal", back_populates="farmer", lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': UserRole.FARMER
    }
    
    def get_animal_count(self):
        """Get total number of animals."""
        return self.animals.filter_by(is_active=True).count()
    
    def get_healthy_animals(self):
        """Get count of healthy animals."""
        from app.models.animal import HealthStatus
        return self.animals.filter_by(
            is_active=True, 
            health_status=HealthStatus.HEALTHY
        ).count()
    
    def __repr__(self):
        return f'<Farmer({self.name}, {self.farm_name})>'


class Veterinarian(User):
    """Veterinarian user model."""
    
    __tablename__ = 'veterinarians'
    
    # Foreign key to users table
    id = Column(db.ForeignKey('users.id'), primary_key=True)
    
    # Veterinarian-specific fields
    license_no = Column(String(50), unique=True, nullable=False, index=True)
    specialization = Column(String(100), nullable=True)
    qualification = Column(String(200), nullable=True)
    experience_years = Column(Integer, nullable=True)
    
    # Professional information
    clinic_name = Column(String(150), nullable=True)
    clinic_address = Column(Text, nullable=True)
    consultation_fee = Column(db.Numeric(10, 2), nullable=True)
    
    # Relationships
    assigned_animals = relationship("Animal", back_populates="veterinarian", lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': UserRole.VETERINARIAN
    }
    
    def get_assigned_animals_count(self):
        """Get count of assigned animals."""
        return self.assigned_animals.filter_by(is_active=True).count()
    
    def get_active_treatments_count(self):
        """Get count of animals under treatment."""
        from app.models.animal import HealthStatus
        return self.assigned_animals.filter_by(
            is_active=True,
            health_status=HealthStatus.UNDER_TREATMENT
        ).count()
    
    def __repr__(self):
        return f'<Veterinarian({self.name}, {self.license_no})>'


class Admin(User):
    """Admin user model."""
    
    __tablename__ = 'admins'
    
    # Foreign key to users table
    id = Column(db.ForeignKey('users.id'), primary_key=True)
    
    # Admin-specific fields
    employee_id = Column(String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    
    # Permissions (JSON field for flexible permission system)
    permissions = Column(Text, nullable=True)
    
    __mapper_args__ = {
        'polymorphic_identity': UserRole.ADMIN
    }
    
    def has_permission(self, permission):
        """Check if admin has specific permission."""
        if not self.permissions:
            return False
        import json
        try:
            perms = json.loads(self.permissions)
            return permission in perms or 'all' in perms
        except:
            return False
    
    def __repr__(self):
        return f'<Admin({self.name}, {self.employee_id})>'
