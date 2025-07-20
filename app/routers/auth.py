"""
Authentication router for Google OAuth2.

This module provides endpoints for user authentication and dependency functions
for getting current user information.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User
from ..models import CurrentUser
from ..services.auth_service import auth_service


# Dependency functions for authentication
def get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT token from HTTP-only cookie."""
    return request.cookies.get("access_token")


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency to optionally get the current authenticated user."""
    token = get_token_from_cookie(request)
    
    if not token:
        return None
    
    try:
        return auth_service.get_current_user(db, token)
    except:
        return None


def get_current_user(
    request: Request, 
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get the current authenticated user."""
    token = get_token_from_cookie(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Router for authentication endpoints
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


@router.get("/login")
async def auth_login(request: Request):
    """Initiate Google OAuth2 login."""
    if not auth_service.oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth2 is not configured"
        )
    
    # Generate redirect URI
    redirect_uri = str(request.base_url) + "auth/callback"
    
    # Get authorization URL and redirect
    return auth_service.get_authorization_url(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback."""
    try:
        # Handle the callback and get user information
        auth_data = await auth_service.handle_callback(request, db)
        
        # Create response with redirect to home page
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        
        # Set the access token as an HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=auth_data["access_token"],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7  # 7 days
        )
        
        return response
        
    except Exception as e:
        # Redirect to login page with error
        return RedirectResponse(
            url="/login?error=authentication_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.post("/logout")
async def logout(response: Response, current_user: Optional[User] = Depends(get_current_user_optional)):
    """Logout the current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Clear the access token cookie
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/logout")
async def logout_get():
    """Logout via GET request (for convenience)."""
    from ..services.session_service import session_service
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    # Clear both authentication methods
    response.delete_cookie(key="access_token")  # Clear Google OAuth token
    session_service.clear_guest_session(response)  # Clear guest session
    return response


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get information about the current authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return current_user 