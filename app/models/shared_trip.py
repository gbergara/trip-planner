import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..core.database import Base

class SharedTrip(Base):
    __tablename__ = 'shared_trips'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey('trips.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    invited_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
