"""
AllowedGoogleAccount model for restricting Google OAuth logins.
"""
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from ..core.database import Base, get_uuid_type, get_datetime_type

class AllowedGoogleAccount(Base):
    __tablename__ = "allowed_google_accounts"
    id = Column(get_uuid_type(), primary_key=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    domain = Column(String(255), nullable=True, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(get_datetime_type(), default=datetime.utcnow)
    updated_at = Column(get_datetime_type(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AllowedGoogleAccount email={self.email} domain={self.domain} active={self.active}>"
