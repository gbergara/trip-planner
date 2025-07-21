from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from .booking import BookingType, BookingStatus, TripStatus, TodoCategory
from .shared_trip import SharedTrip
# SharedTrip schemas
class SharedTripBase(BaseModel):
    trip_id: UUID
    email: str
    invited_by: Optional[str] = None

class SharedTripCreate(SharedTripBase):
    pass

class SharedTripResponse(SharedTripBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# User schemas
class UserBase(BaseModel):
    email: str
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    preferred_language: str = "en"
    preferred_currency: str = "USD"

class UserCreate(UserBase):
    google_id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    preferred_language: Optional[str] = None
    preferred_currency: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    google_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CurrentUser(UserResponse):
    """User information for the currently authenticated user."""
    pass

# Trip schemas
class TripBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: TripStatus = TripStatus.PLANNING
    start_date: datetime
    end_date: Optional[datetime] = None
    primary_destination: Optional[str] = None
    destinations: Optional[str] = None  # JSON string of destinations
    budget: Optional[float] = None
    currency: str = "USD"
    traveler_count: int = 1
    notes: Optional[str] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TripStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    primary_destination: Optional[str] = None
    destinations: Optional[str] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    traveler_count: Optional[int] = None
    notes: Optional[str] = None

class TripResponse(TripBase):
    id: UUID
    user_id: Optional[UUID] = None  # For authenticated users
    guest_session_id: Optional[str] = None  # For guest users
    created_at: datetime
    updated_at: datetime
    # bookings: List["BookingResponse"] = []  # Will be populated when needed

    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    trip_id: UUID
    title: str
    booking_type: BookingType
    status: BookingStatus = BookingStatus.PENDING
    start_date: datetime
    end_date: Optional[datetime] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    confirmation_number: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Flight specific
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    seat_number: Optional[str] = None
    
    # Accommodation specific
    room_type: Optional[str] = None
    guests_count: Optional[int] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    
    # Car rental specific
    car_model: Optional[str] = None
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    trip_id: Optional[UUID] = None
    title: Optional[str] = None
    booking_type: Optional[BookingType] = None
    status: Optional[BookingStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    confirmation_number: Optional[str] = None
    provider: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    seat_number: Optional[str] = None
    room_type: Optional[str] = None
    guests_count: Optional[int] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    car_model: Optional[str] = None
    pickup_location: Optional[str] = None
    return_location: Optional[str] = None

class BookingResponse(BookingBase):
    id: UUID
    booking_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Todo schemas
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: TodoCategory = TodoCategory.OTHER
    priority: int = 2  # 1=high, 2=medium, 3=low
    due_date: Optional[datetime] = None

class TodoCreate(TodoBase):
    trip_id: UUID

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TodoCategory] = None
    priority: Optional[int] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None

class TodoResponse(TodoBase):
    id: UUID
    trip_id: UUID
    completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
