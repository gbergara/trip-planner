"""
Trips router for managing trip data.

This module provides CRUD operations for trips.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..core.database import get_db
from ..models.booking import Trip, Booking, Todo, TodoCategory
from ..models.user import User
from ..models import TripCreate, TripUpdate, TripResponse, BookingResponse, TodoCreate, TodoUpdate, TodoResponse
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

# TODO Endpoints

@router.get("/{trip_id}/todos", response_model=List[TodoResponse])
def get_trip_todos(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get all todos for a specific trip."""
    # Find the trip and verify access
    query = db.query(Trip)
    if current_user:
        query = query.filter(Trip.user_id == current_user.id)
    else:
        # Guest user - verify by session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        query = query.filter(Trip.guest_session_id == guest_session_id)
    
    db_trip = query.filter(Trip.id == trip_id).first()
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get todos for this trip
    todos = db.query(Todo).filter(Todo.trip_id == trip_id).order_by(Todo.priority, Todo.created_at).all()
    return todos

@router.post("/{trip_id}/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    trip_id: UUID,
    todo: TodoCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Create a new todo for a trip."""
    # Find the trip and verify access
    query = db.query(Trip)
    if current_user:
        query = query.filter(Trip.user_id == current_user.id)
    else:
        # Guest user - verify by session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        query = query.filter(Trip.guest_session_id == guest_session_id)
    
    db_trip = query.filter(Trip.id == trip_id).first()
    if db_trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Create the todo
    db_todo = Todo(
        trip_id=trip_id,
        title=todo.title,
        description=todo.description,
        category=todo.category,
        priority=todo.priority,
        due_date=todo.due_date
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@router.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: UUID,
    todo_update: TodoUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Update a todo."""
    # Find the todo and verify access through the trip
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Verify access to the trip
    query = db.query(Trip).filter(Trip.id == db_todo.trip_id)
    if current_user:
        query = query.filter(Trip.user_id == current_user.id)
    else:
        # Guest user - verify by session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        query = query.filter(Trip.guest_session_id == guest_session_id)
    
    db_trip = query.first()
    if db_trip is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the todo
    update_data = todo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    # If marking as completed, set completed_at
    if todo_update.completed is True and not db_todo.completed_at:
        db_todo.completed_at = datetime.utcnow()
    elif todo_update.completed is False:
        db_todo.completed_at = None
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete a todo."""
    # Find the todo and verify access through the trip
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    # Verify access to the trip
    query = db.query(Trip).filter(Trip.id == db_todo.trip_id)
    if current_user:
        query = query.filter(Trip.user_id == current_user.id)
    else:
        # Guest user - verify by session
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        query = query.filter(Trip.guest_session_id == guest_session_id)
    
    db_trip = query.first()
    if db_trip is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the todo
    db.delete(db_todo)
    db.commit() 