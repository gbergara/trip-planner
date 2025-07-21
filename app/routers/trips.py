

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..core.database import get_db
from ..models.booking import Trip, Booking, Todo, TodoCategory
from ..models.user import User
from ..models import TripCreate, TripUpdate, TripResponse, BookingResponse, TodoCreate, TodoUpdate, TodoResponse, SharedTripCreate, SharedTripResponse
from ..models.shared_trip import SharedTrip
from .auth import get_current_user_optional
from ..services.session_service import session_service

router = APIRouter(
    prefix="/trips",
    tags=["trips"]
)

# ...existing code...

# All endpoints must be registered on this router, with no duplicate or misplaced code below.

# All endpoints must be below this line:



# (Removed duplicate router and duplicate endpoint definitions)
# Remove a shared user from a trip
@router.delete("/{trip_id}/share/{email}", status_code=status.HTTP_204_NO_CONTENT)
def remove_shared_trip(
    trip_id: UUID,
    email: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Remove a shared user (by email) from a trip. Only the trip owner can remove sharing.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not current_user or trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify sharing for this trip")
    shared = db.query(SharedTrip).filter(SharedTrip.trip_id == trip_id, SharedTrip.email == email).first()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared user not found for this trip")
    db.delete(shared)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# List all users (emails) a trip is shared with
@router.get("/{trip_id}/shared-users", response_model=List[str])
def list_shared_users(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all user emails a trip is shared with. Only the trip owner can view this list.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not current_user or trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view shared users for this trip")
    shared_users = db.query(SharedTrip.email).filter(SharedTrip.trip_id == trip_id).all()
    return [row[0] for row in shared_users]

# Share a trip with another user by email
@router.post("/{trip_id}/share", response_model=SharedTripResponse, status_code=status.HTTP_201_CREATED)
def share_trip(
    trip_id: UUID,
    payload: SharedTripCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Share a trip with another user by email.
    Only the trip owner can share their trip.
    """
    # Check trip ownership
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if not current_user or trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to share this trip")

    # Prevent duplicate sharing
    existing = db.query(SharedTrip).filter(SharedTrip.trip_id == trip_id, SharedTrip.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Trip already shared with this email")

    shared = SharedTrip(
        trip_id=trip_id,
        email=payload.email,
        invited_by=current_user.email if current_user else None
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)
    return shared

# List trips shared with the current user
@router.get("/shared", response_model=List[TripResponse])
def list_shared_trips(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List all trips shared with the current user (by email).
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    user_email = (current_user.email or '').strip().lower()
    shared_trip_ids = db.query(SharedTrip.trip_id).filter(SharedTrip.email.ilike(user_email)).all()
    trip_ids = [row[0] for row in shared_trip_ids]
    if not trip_ids:
        return []
    trips = db.query(Trip).filter(Trip.id.in_(trip_ids)).all()
    return trips


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip: TripCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create a new trip with automatic user association.
    
    **Features:**
    - **Automatic Ownership**: Associates trip with authenticated user or guest session
    - **Timezone Support**: All datetime fields use timezone-aware storage
    - **Flexible Access**: Works for both authenticated users and guest sessions
    
    **Required Fields:**
    - **name**: Trip title/name
    - **start_date**: Trip start date (ISO 8601 format)
    
    **Optional Fields:**
    - **description**: Trip description/notes
    - **end_date**: Trip end date
    - **destinations**: JSON string of destinations
    - **budget**: Estimated trip budget
    - **currency**: Budget currency (default: USD)
    """
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
    """
    List user's trips with pagination support.
    
    **Features:**
    - **Pagination**: Configurable skip/limit parameters
    - **User-Specific**: Only returns trips belonging to current user/session
    - **Ordering**: Results ordered by creation date (newest first)
    
    **Parameters:**
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 100)
    """
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
    print(f"[DEBUG] get_trip called for trip_id={trip_id}, user={getattr(current_user, 'email', None)}", flush=True)
    trip = None
    print(f"[DEBUG] get_trip: trip_id={trip_id}, user={getattr(current_user, 'email', None)}", flush=True)
    if current_user:
        # Authenticated user - check their trips
        trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
        print(f"[DEBUG] get_trip: owned trip found? {bool(trip)}", flush=True)
        if not trip:
            print(f"[DEBUG] get_trip: not owned, checking shared...", flush=True)
            user_email = (current_user.email or '').strip().lower()
            shared = db.query(SharedTrip).filter(
                SharedTrip.trip_id == trip_id,
                SharedTrip.email.ilike(user_email)
            ).first()
            print(f"[DEBUG] get_trip: shared trip found? {bool(shared)} (email checked: '{user_email}')", flush=True)
            if shared:
                trip = db.query(Trip).filter(Trip.id == trip_id).first()
                print(f"[DEBUG] get_trip: trip found via sharing? {bool(trip)}", flush=True)
            else:
                print(f"[DEBUG] get_trip: not found in shared trips", flush=True)
        else:
            print(f"[DEBUG] get_trip: trip found as owner", flush=True)
    else:
        # If not authenticated, do not allow access to shared trips
        print(f"[DEBUG] get_trip: user not authenticated, cannot access shared trips", flush=True)
        raise HTTPException(status_code=401, detail="Authentication required to access shared trips")
    if trip is None:
        print(f"[DEBUG] get_trip: trip not found, raising 404", flush=True)
        raise HTTPException(status_code=404, detail="Trip not found")
    print(f"[DEBUG] get_trip: returning trip {trip.id}", flush=True)
    return trip
    return trip
    # Remove duplicate unreachable code after return
@router.get("/{trip_id}/bookings", response_model=List[BookingResponse])
def get_trip_bookings(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    print(f"[DEBUG] get_trip_bookings called for trip_id={trip_id}", flush=True)
    """
    Get all bookings associated with a specific trip.
    
    **Features:**
    - **Complete Booking Details**: Returns full booking information
    - **Intelligent Grouping**: Frontend can group flights by date
    - **Security**: Only accessible by trip owner
    
    **Use Case**: Primary endpoint for trip booking management pages.
    """
    trip = None
    print(f"[DEBUG] get_trip_bookings: trip_id={trip_id}, user={getattr(current_user, 'email', None)}", flush=True)
    if current_user:
        trip = db.query(Trip).filter(
            Trip.id == trip_id, 
            Trip.user_id == current_user.id
        ).first()
        print(f"[DEBUG] get_trip_bookings: owned trip found? {bool(trip)}", flush=True)
        if not trip:
            print(f"[DEBUG] get_trip_bookings: not owned, checking shared...", flush=True)
            user_email = (current_user.email or '').strip().lower()
            shared = db.query(SharedTrip).filter(
                SharedTrip.trip_id == trip_id,
                SharedTrip.email.ilike(user_email)
            ).first()
            print(f"[DEBUG] get_trip_bookings: shared record found? {bool(shared)} (email checked: '{user_email}')", flush=True)
            if shared:
                trip = db.query(Trip).filter(Trip.id == trip_id).first()
                print(f"[DEBUG] get_trip_bookings: trip found via sharing? {bool(trip)}", flush=True)
            else:
                print(f"[DEBUG] get_trip_bookings: not found in shared trips", flush=True)
        else:
            print(f"[DEBUG] get_trip_bookings: trip found as owner", flush=True)
    else:
        # If not authenticated, do not allow access to shared trips
        print(f"[DEBUG] get_trip_bookings: user not authenticated, cannot access shared trips", flush=True)
        raise HTTPException(status_code=401, detail="Authentication required to access shared trips")
    if not trip:
        print(f"[DEBUG] get_trip_bookings: trip not found, raising 404", flush=True)
        raise HTTPException(status_code=404, detail="Trip not found")
    bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
    print(f"[DEBUG] get_trip_bookings: returning {len(bookings)} bookings", flush=True)
    return bookings


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: UUID,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Permanently delete a trip and all associated data.
    
    **Warning**: This action cannot be undone and will delete:
    - The trip record
    - All associated bookings
    - All associated TODO items
    
    **Security**: Only trip owner can delete their trips.
    **Response**: Returns success message on completion.
    """
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
    """
    Export trip details as a professionally formatted PDF report.
    
    **Features:**
    - **Complete Trip Summary**: Includes all trip details and bookings
    - **Professional Format**: Well-structured PDF with tables and styling
    - **Automatic Download**: Returns PDF file for immediate download
    
    **Content Includes:**
    - Trip overview and dates
    - Complete booking itinerary
    - Financial summary with totals
    - Contact information and confirmations
    
    **File Format**: PDF with filename pattern: trip_[name].pdf
    """
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
    """
    Update trip status for progress tracking.
    
    **Available Statuses:**
    - **planning**: Trip is being planned (default)
    - **confirmed**: Trip bookings are confirmed
    - **in_progress**: Trip is currently happening
    - **completed**: Trip has finished
    - **cancelled**: Trip was cancelled
    
    **Use Case**: Track trip lifecycle and display appropriate UI states.
    """
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
    """
    Get all TODO items for a specific trip.
    
    **Features:**
    - **Organized Tasks**: Returns tasks ordered by priority then creation date
    - **Complete Information**: Includes due dates, categories, and completion status
    - **7 Categories**: Flight, Accommodation, Transport, Activity, Documents, Packing, Other
    
    **Security**: Only accessible by trip owner.
    **Ordering**: High priority first, then by creation date.
    """
    # Find the trip and verify access
    db_trip = None
    if current_user:
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == current_user.id
        ).first()
        if not db_trip:
            # Check if trip is shared with this user (case-insensitive, trimmed)
            user_email = (current_user.email or '').strip().lower()
            shared = db.query(SharedTrip).filter(
                SharedTrip.trip_id == trip_id,
                SharedTrip.email.ilike(user_email)
            ).first()
            if shared:
                db_trip = db.query(Trip).filter(Trip.id == trip_id).first()
    else:
        guest_session_id = session_service.get_or_create_guest_session(request, response)
        db_trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.guest_session_id == guest_session_id
        ).first()
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
    """
    Create a new TODO item for a trip.
    
    **Features:**
    - **Flexible Categories**: Choose from 7 predefined categories
    - **Priority System**: 3 levels (1=High, 2=Medium, 3=Low)
    - **Due Date Support**: Optional due date with timezone awareness
    - **Auto-Assignment**: Automatically associates with the specified trip
    
    **Required Fields:**
    - **title**: Task description
    - **category**: One of the 7 available categories
    
    **Optional Fields:**
    - **description**: Detailed task notes
    - **priority**: Priority level (default: 2=Medium)
    - **due_date**: When the task should be completed
    """
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
    """
    Update an existing TODO item.
    
    **Features:**
    - **Partial Updates**: Only specified fields are modified
    - **Smart Completion**: Automatically sets completion timestamp when marked complete
    - **Security**: Only accessible by trip owner
    
    **Special Behavior:**
    - **Completion Tracking**: Setting completed=true records completion timestamp
    - **Reopening Tasks**: Setting completed=false clears completion timestamp
    
    **Updatable Fields**: All TODO fields except ID and creation date.
    """
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
    """
    Permanently delete a TODO item.
    
    **Security**: Only the trip owner can delete TODO items from their trips.
    **Warning**: This action cannot be undone.
    **Response**: Returns 204 No Content on successful deletion.
    """
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