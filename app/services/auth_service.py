"""
Authentication service for Google OAuth2 integration.

This service handles user authentication, OAuth2 flow, and session management
using Google as the identity provider.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from jose import JWTError, jwt
from fastapi import HTTPException, status

from ..core.config import DEFAULT_LANGUAGE
from ..models.user import User
from ..models import UserCreate, UserResponse, CurrentUser
from ..models.allowed_google_account import AllowedGoogleAccount


class GoogleAuthService:
    """Service for handling Google OAuth2 authentication."""
    
    def __init__(self):
        self.oauth = OAuth()


        # Get configuration from environment variables
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24 * 7  # 7 days

        # OAuth credentials are optional - app can run in guest-only mode
        self.oauth_enabled = bool(self.google_client_id and self.google_client_secret)

        # Configure Google OAuth2 only if credentials are provided
        if self.oauth_enabled:
            self.oauth.register(
                name='google',
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
    
    def get_authorization_url(self, request, redirect_uri: str) -> str:
        """Get the authorization URL for Google OAuth2."""
        if not self.oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth2 is not configured"
            )
        return self.oauth.google.authorize_redirect(request, redirect_uri)
    
    async def handle_callback(self, request, db: Session) -> Dict[str, Any]:
        """Handle the OAuth2 callback from Google."""
        if not self.oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth2 is not configured"
            )
        
        try:
            # Get the access token
            token = await self.oauth.google.authorize_access_token(request)
            
            # Get user info from Google
            user_info = token.get('userinfo')
            if not user_info:
                # If userinfo is not in token, fetch it
                resp = await self.oauth.google.parse_id_token(request, token)
                user_info = resp
            
            # Create or update user
            user = self.create_or_update_user(db, user_info)
            
            # Create access token
            access_token = self.create_access_token({"sub": str(user.id)})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse.from_orm(user)
            }
            
        except OAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {str(e)}"
            )
    
    def create_or_update_user(self, db: Session, user_info: Dict[str, Any]) -> User:
        """Create a new user or update an existing user from Google user info, with allowlist check."""
        google_id = user_info.get('sub')
        email = user_info.get('email')
        domain = email.split('@')[-1] if email else None

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user information from Google"
            )

        # Check if user already exists
        existing_user = db.query(User).filter(User.google_id == google_id).first()

        # Always check DB-based allowlist for both new and existing users
        allowed = False
        if email:
            try:
                allowed_email = db.query(AllowedGoogleAccount).filter(AllowedGoogleAccount.email == email, AllowedGoogleAccount.active == True).first()
                if allowed_email:
                    allowed = True
            except Exception:
                pass
        if not allowed and domain:
            allowed_domain = db.query(AllowedGoogleAccount).filter(AllowedGoogleAccount.domain == domain, AllowedGoogleAccount.active == True).first()
            if allowed_domain:
                allowed = True
        if not allowed:
            raise HTTPException(status_code=403, detail="Email or domain is not allowed to log in.")

        if existing_user:
            # Update existing user
            existing_user.email = email
            existing_user.name = user_info.get('name', email)
            existing_user.given_name = user_info.get('given_name')
            existing_user.family_name = user_info.get('family_name')
            existing_user.picture = user_info.get('picture')
            existing_user.updated_at = datetime.utcnow()
            existing_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            return existing_user

        else:
            # Create new user
            user_data = UserCreate(
                google_id=google_id,
                email=email,
                name=user_info.get('name', email),
                given_name=user_info.get('given_name'),
                family_name=user_info.get('family_name'),
                picture=user_info.get('picture'),
                preferred_language=self.detect_user_language(user_info)
            )
            new_user = User(**user_data.model_dump())
            new_user.last_login = datetime.utcnow()
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
    
    def detect_user_language(self, user_info: Dict[str, Any]) -> str:
        """Detect user's preferred language from Google user info."""
        # Google provides locale information
        locale = user_info.get('locale', '')
        
        if locale.startswith('es'):
            return 'es'
        elif locale.startswith('en'):
            return 'en'
        else:
            return DEFAULT_LANGUAGE
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        user_id = self.verify_token(token)
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            return None
        
        return user
    
    def logout_user(self, user: User, db: Session) -> bool:
        """Logout user (mainly for tracking last login)."""
        # Note: JWT tokens can't be "revoked" without a blacklist
        # For now, we just track that the user logged out
        # In a production app, you might want to implement token blacklisting
        return True


# Global instance of the auth service
auth_service = GoogleAuthService()