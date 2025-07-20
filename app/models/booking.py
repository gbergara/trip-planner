from sqlalchemy import Column, Integer, String, DateTime, Float, Enum, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from ..core.database import Base, get_uuid_type, get_datetime_type

class TripStatus(enum.Enum):
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.PLANNING)
    
    # User relationship (nullable for guest users)
    user_id = Column(get_uuid_type(), ForeignKey("users.id"), nullable=True, index=True)
    
    # Guest session ID for unauthenticated users
    guest_session_id = Column(String(255), nullable=True, index=True)
    
    # Trip dates
    start_date = Column(get_datetime_type(), nullable=False)
    end_date = Column(get_datetime_type(), nullable=True)
    
    # Destinations
    primary_destination = Column(String(200), nullable=True)
    destinations = Column(Text, nullable=True)  # JSON string of destinations
    
    # Budget information
    budget = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    
    # Trip metadata
    traveler_count = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), default=datetime.utcnow)
    updated_at = Column(get_datetime_type(), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trips")  # Will be None for guest users
    bookings = relationship("Booking", back_populates="trip", cascade="all, delete-orphan")
    todos = relationship("Todo", back_populates="trip", cascade="all, delete-orphan")

class BookingType(enum.Enum):
    FLIGHT = "flight"
    ACCOMMODATION = "accommodation"
    CAR_RENTAL = "car_rental"
    ACTIVITY = "activity"
    RESTAURANT = "restaurant"
    OTHER = "other"

class BookingStatus(enum.Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4, index=True)
    trip_id = Column(get_uuid_type(), ForeignKey("trips.id"), nullable=False)
    title = Column(String(200), nullable=False)
    booking_type = Column(Enum(BookingType), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    
    # Dates
    booking_date = Column(get_datetime_type(), default=datetime.utcnow)
    start_date = Column(get_datetime_type(), nullable=False)
    end_date = Column(get_datetime_type(), nullable=True)
    
    # Location info
    departure_location = Column(String(200), nullable=True)
    arrival_location = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    
    # Financial info
    price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    
    # Booking details
    confirmation_number = Column(String(100), nullable=True)
    provider = Column(String(200), nullable=True)  # Airline, hotel chain, etc.
    
    # Additional details
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Contact info
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Specific fields for different booking types
    # Flight specific
    flight_number = Column(String(20), nullable=True)
    airline = Column(String(100), nullable=True)
    departure_terminal = Column(String(10), nullable=True)
    arrival_terminal = Column(String(10), nullable=True)
    seat_number = Column(String(10), nullable=True)
    
    # Accommodation specific
    room_type = Column(String(100), nullable=True)
    guests_count = Column(Integer, nullable=True)
    check_in_time = Column(String(10), nullable=True)
    check_out_time = Column(String(10), nullable=True)
    
    # Car rental specific
    car_model = Column(String(100), nullable=True)
    pickup_location = Column(String(200), nullable=True)
    return_location = Column(String(200), nullable=True)
    
    created_at = Column(get_datetime_type(), default=datetime.utcnow)
    updated_at = Column(get_datetime_type(), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trip = relationship("Trip", back_populates="bookings")

class TodoCategory(enum.Enum):
    FLIGHT = "flight"
    ACCOMMODATION = "accommodation"  
    TRANSPORT = "transport"
    ACTIVITY = "activity"
    DOCUMENTS = "documents"
    PACKING = "packing"
    OTHER = "other"

class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(get_uuid_type(), primary_key=True, default=uuid.uuid4, index=True)
    trip_id = Column(get_uuid_type(), ForeignKey("trips.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(TodoCategory), default=TodoCategory.OTHER)
    
    # Status
    completed = Column(Boolean, default=False)
    completed_at = Column(get_datetime_type(), nullable=True)
    
    # Priority (1 = high, 2 = medium, 3 = low)
    priority = Column(Integer, default=2)
    
    # Due date (optional)
    due_date = Column(get_datetime_type(), nullable=True)
    
    # Timestamps
    created_at = Column(get_datetime_type(), default=datetime.utcnow)
    updated_at = Column(get_datetime_type(), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships  
    trip = relationship("Trip", back_populates="todos")
