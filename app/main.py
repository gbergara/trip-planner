from fastapi import FastAPI, Request, Depends, HTTPException, Cookie, Response
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import os

from .core.database import get_db, create_tables
import re
# Utility to detect DB type for footer
def get_db_type():
    from .core.database import DATABASE_URL
    url = DATABASE_URL.lower()
    if "cockroach" in url or "26257" in url:
        return "cockroachdb"
    if "postgres" in url or "5432" in url:
        return "postgresql"
    if "sqlite" in url:
        return "sqlite"
    return "unknown"
from .core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, TEMPLATES_DIR, STATIC_DIR
from starlette.middleware.sessions import SessionMiddleware
from .models.booking import Trip, Booking
from .models.user import User
from .routers import bookings, trips, auth
from .routers import airports
from .routers.auth import get_current_user_optional
from .services.i18n_service import translate as _, detect_language_from_request, get_language_names, get_supported_languages
from .services.pdf_service import create_trip_pdf

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact={
        "name": "Trip Planner API",
        "url": "https://github.com/gbergara/trip-planner",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "trips",
            "description": "**Trip Management** - Create, read, update, and delete trips with full CRUD operations. Includes trip statistics, PDF exports, and TODO list management.",
        },
        {
            "name": "bookings",
            "description": "**Booking Management** - Handle flights, accommodations, car rentals, activities and other travel bookings. Features automatic flight title generation and intelligent grouping.",
        },
        {
            "name": "authentication", 
            "description": "**User Authentication** - Google OAuth2 integration with guest session support. Manage user accounts and session tokens.",
        },
    ],
)

# Add session middleware after app is created
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
)

# Database tables are now managed by Alembic migrations
# @app.on_event("startup")
# async def startup_event():
#     """Initialize database tables on application startup."""
#     if not os.getenv("TESTING"):
#         create_tables()

def get_user_language(request: Request) -> str:
    """Get user's preferred language from cookie or Accept-Language header."""
    # Check for language cookie first
    lang = request.cookies.get("lang")
    supported_languages = get_supported_languages()
    if lang and lang in supported_languages:
        return lang
    
    # Fall back to Accept-Language header
    accept_language = request.headers.get("accept-language")
    return detect_language_from_request(accept_language)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Include API routers with /api prefix first
app.include_router(trips, prefix="/api")
app.include_router(bookings, prefix="/api")
app.include_router(airports, prefix="/api/airports")

# Include authentication router
app.include_router(auth)

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Home page - shows dashboard if user has a session, otherwise redirects to login"""
    language = get_user_language(request)
    
    # Check if user is authenticated
    if current_user:
        # Get authenticated user's recent trips
        recent_trips = db.query(Trip).filter(
            Trip.user_id == current_user.id
        ).order_by(Trip.created_at.desc()).limit(5).all()
    else:
        # Check if user has a guest session
        from .services.session_service import session_service
        guest_session_id = session_service.get_guest_session(request)
        
        if guest_session_id:
            # Get guest user's recent trips
            recent_trips = db.query(Trip).filter(
                Trip.guest_session_id == guest_session_id
            ).order_by(Trip.created_at.desc()).limit(5).all()
        else:
            # No session at all - redirect to login page
            return RedirectResponse(url="/login", status_code=302)
    
    # Check if Google OAuth is enabled
    from .services.auth_service import auth_service
    oauth_enabled = auth_service.oauth_enabled
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_trips": recent_trips,
        "current_user": current_user,
        "oauth_enabled": oauth_enabled,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language),
        "db_type": get_db_type()
    })

@app.get("/start-guest")
async def start_guest_session(request: Request):
    """Create a guest session and redirect to dashboard"""
    from .services.session_service import session_service
    
    # Create a redirect response
    redirect_response = RedirectResponse(url="/", status_code=302)
    
    # Create a new guest session and set the cookie on the redirect response
    session_service.get_or_create_guest_session(request, redirect_response)
    
    return redirect_response


@app.get("/logout") 
async def universal_logout():
    """Universal logout - clears both auth tokens and guest sessions, redirects to login"""
    from .services.session_service import session_service
    
    # Create redirect response to login page
    redirect_response = RedirectResponse(url="/login", status_code=302)
    
    # Clear both authentication methods
    redirect_response.delete_cookie(key="access_token")  # Clear Google OAuth token
    session_service.clear_guest_session(redirect_response)  # Clear guest session
    
    return redirect_response


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Login page"""
    language = get_user_language(request)
    
    # Check if Google OAuth is enabled
    from .services.auth_service import auth_service
    oauth_enabled = auth_service.oauth_enabled
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "language": language,
        "languages": get_language_names(),
        "error": error,
        "oauth_enabled": oauth_enabled,
        "_": lambda text: _(text, language),
        "db_type": get_db_type()
    })

@app.get("/trips", response_class=HTMLResponse)
async def trips_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Trips management page (for authenticated users and guests)"""
    language = get_user_language(request)
    
    return templates.TemplateResponse("trips.html", {
        "request": request,
        "current_user": current_user,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language),
        "db_type": get_db_type()
    })

@app.get("/trips/{trip_id}/bookings", response_class=HTMLResponse)
async def trip_bookings_page(
    request: Request, 
    trip_id: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Trip bookings management page (for authenticated users and guests)"""
    language = get_user_language(request)
    
    # Get the trip details - check ownership (user or guest session or shared)
    trip = None
    can_edit = False
    if current_user:
        trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == current_user.id
        ).first()
        if trip:
            can_edit = True
        else:
            # Check if trip is shared with this user (case-insensitive, trimmed)
            user_email = (current_user.email or '').strip().lower()
            from .models.shared_trip import SharedTrip
            shared = db.query(SharedTrip).filter(
                SharedTrip.trip_id == trip_id,
                SharedTrip.email.ilike(user_email)
            ).first()
            if shared:
                trip = db.query(Trip).filter(Trip.id == trip_id).first()
                can_edit = False
    else:
        from .services.session_service import session_service
        guest_session_id = session_service.get_guest_session(request)
        if guest_session_id:
            trip = db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.guest_session_id == guest_session_id
            ).first()
            can_edit = True if trip else False
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return templates.TemplateResponse("trip_bookings.html", {
        "request": request,
        "trip": trip,
        "current_user": current_user,
        "can_edit": can_edit,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language),
        "db_type": get_db_type()
    })

@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request):
    """Bookings management page"""
    language = get_user_language(request)
    
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language),
        "db_type": get_db_type()
    })


@app.post("/set-language")
async def set_language(request_body: dict, response: Response):
    """Set user language preference"""
    lang = request_body.get("language")
    supported_languages = get_supported_languages()
    if not lang or lang not in supported_languages:
        raise HTTPException(status_code=400, detail="Unsupported language")
    
    response.set_cookie(key="lang", value=lang, max_age=30*24*60*60)  # 30 days
    return {"message": "Language updated", "language": lang}

@app.get("/api/trips/{trip_id}/export/pdf")
async def export_trip_pdf(trip_id: str, request: Request, db: Session = Depends(get_db)):
    """Export trip to PDF"""
    language = get_user_language(request)
    
    # Get trip and bookings
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
    
    # Generate PDF
    pdf_buffer = create_trip_pdf(trip, bookings, language)
    
    # Create response
    filename = f"trip-{trip.name.replace(' ', '_')}-{trip_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Also add without /api prefix for test compatibility
@app.get("/trips/{trip_id}/export/pdf")
async def export_trip_pdf_compat(trip_id: str, request: Request, db: Session = Depends(get_db)):
    """Export trip to PDF (compatibility route)"""
    return await export_trip_pdf(trip_id, request, db)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
