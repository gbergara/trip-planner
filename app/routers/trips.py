"""
Trips router for managing trip data.

This module provides CRUD operations for trips.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..models.booking import Trip, Booking
from ..models.user import User
from ..models import TripCreate, TripUpdate, TripResponse, BookingResponse
from .auth import get_current_user_optional
from ..services.session_service import session_service

router = APIRouter(
    prefix="/trips", 
    tags=["trips"]
)


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip: TripCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Create a new trip (for authenticated users or guests)"""
    trip_data = trip.model_dump()
    
    if current_user:
        # Authenticated user
        trip_data["user_id"] = current_user.id
        trip_data["guest_session_id"] = None
    else:
        # Guest user
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trip_data["user_id"] = None
        trip_data["guest_session_id"] = guest_session_id
    
    db_trip = Trip(**trip_data)
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


@router.get("/", response_model=List[TripResponse])
def list_trips(
    request: Request,
    response: Response,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List user's trips (authenticated users) or guest trips (guest users)"""
    if current_user:
        # Authenticated user - show their trips
        trips = db.query(Trip).filter(
            Trip.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    else:
        # Guest user - show trips for their session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trips = db.query(Trip).filter(
            Trip.guest_session_id == guest_session_id
        ).offset(skip).limit(limit).all()
    
    return trips


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific trip by ID"""
    if current_user:
        # Authenticated user - check their trips
        trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        # Guest user - check their session trips
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/{trip_id}/bookings", response_model=List[BookingResponse])
def get_trip_bookings(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get all bookings for a specific trip"""
    if current_user:
        trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
    return bookings


@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: UUID, 
    trip_update: TripUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update a trip"""
    if current_user:
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Update trip with new data
    update_data = trip_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_trip, field, value)
    
    db.commit()
    db.refresh(db_trip)
    return db_trip


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete a trip"""
    if current_user:
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(db_trip)
    db.commit()
    return {"message": "Trip deleted successfully"}


@router.get("/{trip_id}/export", response_class=FileResponse)
def export_trip_pdf(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Export trip details as PDF"""
    if current_user:
        trip = db.query(Trip).options(
            joinedload(Trip.bookings)
        ).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        trip = db.query(Trip).options(
            joinedload(Trip.bookings)
        ).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    from ..services.pdf_service import pdf_service
    
    # Generate PDF
    pdf_path = pdf_service.generate_trip_pdf(trip)
    
    return FileResponse(
        path=pdf_path,
        filename=f"trip_{trip.name.replace(' ', '_')}.pdf",
        media_type="application/pdf"
    )


@router.put("/{trip_id}/status")
def update_trip_status(
    trip_id: UUID, 
    status: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update trip status"""
    if current_user:
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
    
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Update status
    from ..models.booking import TripStatus
    try:
        db_trip.status = TripStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    db.commit()
    db.refresh(db_trip)
    return db_trip 