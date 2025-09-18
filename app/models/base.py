"""Base model with common fields and methods."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from app import db


class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    # NEW (SQLite compatible)  
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    
    # Timestamp fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete functionality
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle UUID, datetime, and other non-serializable types
            if isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def soft_delete(self):
        """Soft delete the record."""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        db.session.commit()
    
    def restore(self):
        """Restore soft deleted record."""
        self.is_active = True
        self.deleted_at = None
        db.session.commit()
    
    @classmethod
    def get_active(cls):
        """Get all active (non-deleted) records."""
        return cls.query.filter_by(is_active=True)
    
    def __repr__(self):
        return f'<{self.__class__.__name__}({self.id})>'
