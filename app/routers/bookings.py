from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..models.booking import Booking, Trip
from ..models.user import User
from ..models import BookingCreate, BookingUpdate, BookingResponse
from .auth import get_current_user_optional
from ..services.session_service import session_service

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"]
)

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create a new booking with intelligent flight title generation.
    
    **Flight Bookings**: Automatically generates titles in "Source → Destination" format.
    **Timezone Support**: All datetime fields use timezone-aware storage.
    **User Access**: Available to both authenticated users and guest sessions.
    
    **Supported booking types**: Flight, Accommodation, Car Rental, Restaurant, Activity, Other
    """
    # Verify that the trip belongs to the current user or guest session
    if current_user:
        trip = db.query(Trip).filter(
            Trip.id == booking.trip_id,
            Trip.user_id == current_user.id
        ).first()
    else:
        # Guest user - check their session trips
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trip = db.query(Trip).filter(
            Trip.id == booking.trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    try:
        booking_data = booking.model_dump()
        
        # Auto-generate flight title if it's a flight and title needs generation
        if (booking_data.get('booking_type') == 'flight' and 
            booking_data.get('departure_location') and 
            booking_data.get('arrival_location')):
            # Only override title if it's empty or generic
            current_title = booking_data.get('title', '').strip()
            expected_title = f"{booking_data['departure_location']} → {booking_data['arrival_location']}"
            if not current_title or current_title != expected_title:
                booking_data['title'] = expected_title
        
        db_booking = Booking(**booking_data)
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid data")

@router.get("/", response_model=List[BookingResponse])
def list_bookings(
    request: Request,
    response: Response,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all user's bookings across all trips.
    
    **Features:**
    - **Pagination**: Use skip and limit parameters
    - **User Access**: Works for both authenticated users and guest sessions
    - **Comprehensive**: Returns bookings from all user's trips
    
    **Parameters:**
    - **skip**: Number of records to skip (pagination offset)
    - **limit**: Maximum number of records to return (max 100)
    """
    if current_user:
        # Get bookings from trips that belong to the authenticated user
        bookings = db.query(Booking).join(Trip).filter(
            Trip.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        # Get bookings from trips that belong to the guest session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        bookings = db.query(Booking).join(Trip).filter(
            Trip.guest_session_id == guest_session_id
        ).offset(skip).limit(limit).all()
    
    return bookings

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get detailed information for a specific booking.
    
    **Security**: Only returns bookings that belong to the current user or guest session.
    **UUID Format**: booking_id must be a valid UUID string.
    """
    if current_user:
        # Get booking that belongs to user's trips
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.user_id == current_user.id
        ).first()
    else:
        # Get booking that belongs to guest session trips
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: UUID, 
    booking_update: BookingUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Update an existing booking with intelligent flight title management.
    
    **Smart Features:**
    - **Flight Titles**: Automatically updates titles when departure/arrival locations change
    - **Field Clearing**: Send null values to clear optional fields
    - **Partial Updates**: Only specified fields are updated
    
    **Authentication**: Only the booking owner can update their bookings.
    """
    # Verify access to the booking
    if current_user:
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Use exclude_none=False to include null values for clearing fields
    update_data = booking_update.model_dump(exclude_unset=True, exclude_none=False)
    
    # Auto-generate flight title if it's a flight and locations are being updated
    if booking.booking_type == 'flight' or update_data.get('booking_type') == 'flight':
        # Get final departure and arrival locations after update
        departure = update_data.get('departure_location') if 'departure_location' in update_data else booking.departure_location
        arrival = update_data.get('arrival_location') if 'arrival_location' in update_data else booking.arrival_location
        
        if departure and arrival:
            expected_title = f"{departure} → {arrival}"
            # Auto-update title if not explicitly set or if it should be updated
            if 'title' not in update_data or not update_data.get('title'):
                update_data['title'] = expected_title
    
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    return booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Permanently delete a booking.
    
    **Security**: Only the booking owner can delete their bookings.
    **Warning**: This action cannot be undone.
    **Response**: Returns 204 No Content on successful deletion.
    """
    # Verify access to the booking
    if current_user:
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        booking = db.query(Booking).join(Trip).filter(
            Booking.id == booking_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(booking)
    db.commit()
    # For 204, we don't return content
    return None

@router.get("/type/{booking_type}", response_model=List[BookingResponse])
def get_bookings_by_type(
    booking_type: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Filter user's bookings by type.
    
    **Available Types**: flight, accommodation, car_rental, restaurant, activity, other
    **Security**: Only returns bookings belonging to the current user or guest session.
    """
    if current_user:
        bookings = db.query(Booking).join(Trip).filter(
            Trip.user_id == current_user.id,
            Booking.booking_type == booking_type
        ).all()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        bookings = db.query(Booking).join(Trip).filter(
            Trip.guest_session_id == guest_session_id,
            Booking.booking_type == booking_type
        ).all()
    
    return bookings

@router.get("/status/{booking_status}", response_model=List[BookingResponse])
def get_bookings_by_status(
    booking_status: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Filter user's bookings by status.
    
    **Available Statuses**: pending, confirmed, cancelled
    **Security**: Only returns bookings belonging to the current user or guest session.
    """
    if current_user:
        bookings = db.query(Booking).join(Trip).filter(
            Trip.user_id == current_user.id,
            Booking.status == booking_status
        ).all()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        bookings = db.query(Booking).join(Trip).filter(
            Trip.guest_session_id == guest_session_id,
            Booking.status == booking_status
        ).all()
    
    return bookings
