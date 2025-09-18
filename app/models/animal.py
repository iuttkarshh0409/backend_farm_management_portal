"""Animal model for livestock management."""

from sqlalchemy import Column, String, Integer, Numeric, Date, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum
from datetime import date
from app.models.base import BaseModel
from app import db

class AnimalSpecies(enum.Enum):
    """Animal species enumeration."""
    CATTLE = "cattle"
    BUFFALO = "buffalo"
    GOAT = "goat"
    SHEEP = "sheep"
    POULTRY = "poultry"
    SWINE = "swine"
    OTHER = "other"

class Gender(enum.Enum):
    """Animal gender enumeration."""
    MALE = "male"
    FEMALE = "female"

class HealthStatus(enum.Enum):
    """Animal health status enumeration."""
    HEALTHY = "healthy"
    SICK = "sick"
    UNDER_TREATMENT = "under_treatment"
    RECOVERING = "recovering"
    QUARANTINE = "quarantine"
    DECEASED = "deceased"

class ProductionStatus(enum.Enum):
    """Animal production status."""
    ACTIVE = "active"
    DRY = "dry"
    PREGNANT = "pregnant"
    LACTATING = "lactating"
    BREEDING = "breeding"
    RETIRED = "retired"

class Animal(BaseModel):
    """Animal model for livestock management."""
    __tablename__ = 'animals'
    # Identification
    tag_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    # Basic information
    species = Column(Enum(AnimalSpecies), nullable=False, index=True)
    breed = Column(String(100), nullable=True)
    gender = Column(Enum(Gender), nullable=False)
    # Physical characteristics
    age_months = Column(Integer, nullable=True)
    birth_date = Column(Date, nullable=True)
    weight_kg = Column(Numeric(8, 2), nullable=True)
    height_cm = Column(Numeric(6, 2), nullable=True)
    color = Column(String(100), nullable=True)
    # Health and status
    health_status = Column(Enum(HealthStatus), default=HealthStatus.HEALTHY, nullable=False)
    production_status = Column(Enum(ProductionStatus), nullable=True)
    # Relationships - Foreign Keys
    farmer_id = Column(String(36), ForeignKey('farmers.id'), nullable=False, index=True)
    veterinarian_id = Column(String(36), ForeignKey('veterinarians.id'), nullable=True, index=True)
    # Additional information
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Numeric(10, 2), nullable=True)
    source = Column(String(200), nullable=True)
    # Medical information
    vaccination_status = Column(Text, nullable=True)
    last_checkup_date = Column(Date, nullable=True)
    # Production data
    daily_milk_yield = Column(Numeric(6, 2), nullable=True)
    lactation_number = Column(Integer, nullable=True)
    last_calving_date = Column(Date, nullable=True)
    # Notes and observations
    notes = Column(Text, nullable=True)
    special_conditions = Column(Text, nullable=True)
    # Photo/image path
    image_path = Column(String(255), nullable=True)
    # Relationships
    farmer = relationship("Farmer", back_populates="animals")
    veterinarian = relationship("Veterinarian", back_populates="assigned_animals")
    health_records = relationship("HealthRecord", back_populates="animal", lazy='dynamic')

    def get_age_years(self):
        """Calculate age in years."""
        if self.birth_date:
            return round((date.today() - self.birth_date).days / 365.25, 1)
        elif self.age_months:
            return round(self.age_months / 12, 1)
        return None

    def is_productive(self):
        """Check if animal is in productive status."""
        if not self.production_status:
            return False
        productive_statuses = [
            ProductionStatus.ACTIVE,
            ProductionStatus.LACTATING,
            ProductionStatus.BREEDING,
            ProductionStatus.PREGNANT
        ]
        return self.production_status in productive_statuses

    def needs_attention(self):
        """Check if animal needs medical attention."""
        attention_statuses = [
            HealthStatus.SICK,
            HealthStatus.UNDER_TREATMENT,
            HealthStatus.QUARANTINE
        ]
        return self.health_status in attention_statuses

    def get_latest_health_record(self):
        """Get the most recent health record."""
        return self.health_records.order_by(
            HealthRecord.created_at.desc()
        ).first()

    def calculate_days_since_checkup(self):
        """Calculate days since last checkup."""
        if self.last_checkup_date:
            return (date.today() - self.last_checkup_date).days
        return None

    def to_dict(self):
        """Convert animal object to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'tag_id': self.tag_id,
            'name': self.name,
            'species': self.species.value if self.species else None,
            'breed': self.breed,
            'gender': self.gender.value if self.gender else None,
            'age_months': self.age_months,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'height_cm': float(self.height_cm) if self.height_cm else None,
            'color': self.color,
            'health_status': self.health_status.value if self.health_status else None,
            'production_status': self.production_status.value if self.production_status else None,
            'farmer_id': str(self.farmer_id),
            'veterinarian_id': str(self.veterinarian_id) if self.veterinarian_id else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'source': self.source,
            'vaccination_status': self.vaccination_status,
            'daily_milk_yield': float(self.daily_milk_yield) if self.daily_milk_yield else None,
            'lactation_number': self.lactation_number,
            'last_calving_date': self.last_calving_date.isoformat() if self.last_calving_date else None,
            'last_checkup_date': self.last_checkup_date.isoformat() if self.last_checkup_date else None,
            'notes': self.notes,
            'special_conditions': self.special_conditions,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'age_years': self.get_age_years(),
            'is_productive': self.is_productive(),
            'needs_attention': self.needs_attention(),
            'days_since_checkup': self.calculate_days_since_checkup()
        }

    def __repr__(self):
        return f'<Animal({self.tag_id}, {self.species.value}, {self.health_status.value})>'

class HealthRecord(BaseModel):
    """Health record for animals."""
    __tablename__ = 'health_records'
    # Relationship
    animal_id = Column(String(36), ForeignKey('animals.id'), nullable=False, index=True)
    recorded_by_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    # Health assessment
    checkup_date = Column(Date, default=date.today, nullable=False)
    temperature = Column(Numeric(4, 2), nullable=True)
    weight_kg = Column(Numeric(8, 2), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    # Observations
    symptoms = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    treatment_given = Column(Text, nullable=True)
    # Follow-up information
    next_checkup_date = Column(Date, nullable=True)
    recommendations = Column(Text, nullable=True)
    # Status assessment
    overall_condition = Column(Enum(HealthStatus), nullable=True)
    # Notes
    notes = Column(Text, nullable=True)
    # Relationships
    animal = relationship("Animal", back_populates="health_records")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])

    def to_dict(self):
        """Convert health record to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'animal_id': str(self.animal_id),
            'recorded_by_id': str(self.recorded_by_id),
            'checkup_date': self.checkup_date.isoformat() if self.checkup_date else None,
            'temperature': float(self.temperature) if self.temperature else None,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'heart_rate': self.heart_rate,
            'respiratory_rate': self.respiratory_rate,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'treatment_given': self.treatment_given,
            'next_checkup_date': self.next_checkup_date.isoformat() if self.next_checkup_date else None,
            'recommendations': self.recommendations,
            'overall_condition': self.overall_condition.value if self.overall_condition else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
    def __repr__(self):
        return f'<HealthRecord({self.animal.tag_id if self.animal else "Unknown"}, {self.checkup_date})>'

# Database indexes for performance
Index('idx_animal_species_health', Animal.species, Animal.health_status)
Index('idx_animal_farmer_active', Animal.farmer_id, Animal.is_active)
Index('idx_health_record_animal_date', HealthRecord.animal_id, HealthRecord.checkup_date)
