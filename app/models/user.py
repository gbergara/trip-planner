"""
User models for authentication and authorization.

This module contains SQLAlchemy models for user management
with Google OAuth2 integration.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base, get_uuid_type, get_datetime_type


class User(Base):
    """User model for storing authenticated user information from Google OAuth2."""
    __tablename__ = "users"
    
    # Primary key
    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4, index=True)
    
    # Google OAuth2 information
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    given_name = Column(String(255), nullable=True)
    family_name = Column(String(255), nullable=True)
    picture = Column(Text, nullable=True)  # URL to profile picture
    
    # User preferences
    preferred_language = Column(String(10), default="en")
    preferred_currency = Column(String(10), default="USD")
    
    # Account status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), default=datetime.utcnow)
    updated_at = Column(get_datetime_type(), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(get_datetime_type(), nullable=True)
    
    # Relationships
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>" 