from fastapi import FastAPI, Request, Depends, HTTPException, Cookie, Response
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional
import os

from .core.database import get_db, create_tables
from .core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, TEMPLATES_DIR, STATIC_DIR
from .models.booking import Trip, Booking
from .models.user import User
from .routers import bookings, trips, auth
from .routers.auth import get_current_user_optional
from .services.i18n_service import translate as _, detect_language_from_request, get_language_names, get_supported_languages
from .services.pdf_service import create_trip_pdf

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION
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
app.include_router(trips.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")

# Include authentication router
app.include_router(auth.router)

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
        "_": lambda text: _(text, language)
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
        "_": lambda text: _(text, language)
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
        "_": lambda text: _(text, language)
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
    
    # Get the trip details - check ownership (user or guest session)
    if current_user:
        trip = db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == current_user.id
        ).first()
    else:
        # For guest users, we need to import session service
        from .services.session_service import session_service
        guest_session_id = session_service.get_guest_session(request)
        if guest_session_id:
            trip = db.query(Trip).filter(
                Trip.id == trip_id,
                Trip.guest_session_id == guest_session_id
            ).first()
        else:
            trip = None
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return templates.TemplateResponse("trip_bookings.html", {
        "request": request, 
        "trip": trip,
        "current_user": current_user,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language)
    })

@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request):
    """Bookings management page"""
    language = get_user_language(request)
    
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "language": language,
        "languages": get_language_names(),
        "_": lambda text: _(text, language)
    })

# Include routers without /api prefix for backward compatibility with tests
# These come after the specific HTML routes to avoid conflicts
app.include_router(trips.router, tags=["trips-api"])
app.include_router(bookings.router, tags=["bookings-api"])

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
