"""Database models package."""

from app.models.base import BaseModel
from app.models.user import User, Farmer, Veterinarian, Admin, UserRole, UserStatus
from app.models.animal import Animal, HealthRecord, AnimalSpecies, Gender, HealthStatus, ProductionStatus

# Make models available for import
__all__ = [
    'BaseModel',
    'User',
    'Farmer',
    'Veterinarian',
    'Admin',
    'UserRole',
    'UserStatus',
    'Animal',
    'HealthRecord',
    'AnimalSpecies',
    'Gender',
    'HealthStatus',
    'ProductionStatus'
]
