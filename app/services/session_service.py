"""
Session service for managing guest user sessions.

This service handles session management for unauthenticated users,
allowing them to use the app without Google authentication.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, Response
from itsdangerous import URLSafeSerializer, BadSignature


class SessionService:
    """Service for managing guest user sessions."""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.serializer = URLSafeSerializer(self.secret_key)
        self.session_cookie_name = "guest_session"
        self.session_max_age = 60 * 60 * 24 * 30  # 30 days
    
    def get_or_create_guest_session(self, request: Request, response: Response) -> str:
        """Get existing guest session ID or create a new one."""
        # Try to get existing session
        session_id = self.get_guest_session(request)
        
        if session_id:
            return session_id
        
        # Create new session
        session_id = str(uuid.uuid4())
        self.set_guest_session(response, session_id)
        return session_id
    
    def get_guest_session(self, request: Request) -> Optional[str]:
        """Get the current guest session ID from cookies."""
        try:
            session_cookie = request.cookies.get(self.session_cookie_name)
            if session_cookie:
                # Decode the signed session ID
                session_id = self.serializer.loads(session_cookie)
                return session_id
        except BadSignature:
            # Invalid or tampered cookie
            pass
        
        return None
    
    def set_guest_session(self, response: Response, session_id: str):
        """Set guest session ID in cookies."""
        # Sign the session ID to prevent tampering
        signed_session = self.serializer.dumps(session_id)
        
        response.set_cookie(
            key=self.session_cookie_name,
            value=signed_session,
            max_age=self.session_max_age,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
    
    def clear_guest_session(self, response: Response):
        """Clear guest session cookie."""
        response.delete_cookie(key=self.session_cookie_name)
    
    def is_guest_session(self, request: Request) -> bool:
        """Check if the current request has a guest session."""
        return self.get_guest_session(request) is not None


# Global instance of the session service
session_service = SessionService() 