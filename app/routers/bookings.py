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
    """Create a new booking (for authenticated users and guests)"""
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
        db_booking = Booking(**booking.model_dump())
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
    """List user's bookings (authenticated users and guests)"""
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
    """Get a specific booking by ID (for authenticated users and guests)"""
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
def update_booking(booking_id: UUID, booking_update: BookingUpdate, db: Session = Depends(get_db)):
    """Update a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Use exclude_none=False to include null values for clearing fields
    update_data = booking_update.model_dump(exclude_unset=True, exclude_none=False)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    return booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: UUID, db: Session = Depends(get_db)):
    """Delete a booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(booking)
    db.commit()
    # For 204, we don't return content
    return None

@router.get("/type/{booking_type}", response_model=List[BookingResponse])
def get_bookings_by_type(booking_type: str, db: Session = Depends(get_db)):
    """Get bookings filtered by type"""
    bookings = db.query(Booking).filter(Booking.booking_type == booking_type).all()
    return bookings

@router.get("/status/{booking_status}", response_model=List[BookingResponse])
def get_bookings_by_status(booking_status: str, db: Session = Depends(get_db)):
    """Get bookings filtered by status"""
    bookings = db.query(Booking).filter(Booking.status == booking_status).all()
    return bookings
