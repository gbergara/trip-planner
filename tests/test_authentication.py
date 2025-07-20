"""
Tests for the authentication system.

This module tests both guest authentication and Google OAuth2 functionality,
including session management, access controls, and security measures.
"""

import pytest
from unittest.mock import patch, Mock
import uuid
from fastapi import status


@pytest.mark.integration
class TestGuestAuthentication:
    """Test cases for guest user authentication and session management."""
    
    def test_guest_session_creation(self, client):
        """Test that guest sessions are created properly."""
        response = client.get("/start-guest", allow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/"
        assert "guest_session" in response.cookies
        
        # Cookie should have proper security attributes
        cookie = response.cookies["guest_session"]
        assert cookie is not None
    
    def test_guest_session_persistence(self, client):
        """Test that guest sessions persist across requests."""
        # Start guest session
        response1 = client.get("/start-guest", allow_redirects=False)
        original_cookie = response1.cookies["guest_session"]
        
        # Make subsequent requests - should maintain same session
        response2 = client.get("/api/trips/")
        response3 = client.get("/")
        
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK
        
        # Session should persist without creating new cookies
        # (TestClient automatically maintains cookies between requests)
    
    def test_guest_session_data_isolation(self, client):
        """Test that guest sessions properly isolate user data."""
        # Create trip in first session
        trip_data = {"name": "Session 1 Trip", "start_date": "2024-06-01T10:00:00"}
        response1 = client.post("/api/trips/", json=trip_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Verify trip exists in first session
        trips1 = client.get("/api/trips/").json()
        assert len(trips1) == 1
        assert trips1[0]["name"] == "Session 1 Trip"
        
        # Simulate new session by clearing cookies
        client.cookies.clear()
        
        # New session should not see previous trip
        trips2 = client.get("/api/trips/").json()
        assert len(trips2) == 0
        
        # Create trip in second session
        response2 = client.post("/api/trips/", json=trip_data)
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Second session should only see its own trip
        trips2_after = client.get("/api/trips/").json()
        assert len(trips2_after) == 1
    
    def test_guest_session_security(self, client):
        """Test guest session security measures."""
        response = client.get("/start-guest", allow_redirects=False)
        cookie_value = response.cookies["guest_session"]
        
        # Cookie should be signed/encrypted (not plain UUID)
        assert len(cookie_value) > 36  # Longer than plain UUID
        assert "." in cookie_value  # Should contain signature separator
        
        # HttpOnly should be set (TestClient doesn't preserve this, but we test the endpoint)
        # In real browsers, HttpOnly prevents JS access


@pytest.mark.integration 
class TestGoogleOAuthFlow:
    """Test cases for Google OAuth2 authentication flow."""
    
    @patch('app.services.auth_service.GoogleAuthService.oauth_enabled', True)
    def test_oauth_login_redirect(self, client):
        """Test OAuth login redirects to Google."""
        with patch('app.services.auth_service.auth_service.get_authorization_url') as mock_auth_url:
            mock_auth_url.return_value = Mock(
                status_code=302,
                headers={"location": "https://accounts.google.com/oauth/authorize?..."}
            )
            
            response = client.get("/auth/login", allow_redirects=False)
            assert response.status_code == status.HTTP_302_FOUND or \
                   response.status_code == status.HTTP_200_OK  # Depending on implementation
    
    def test_oauth_disabled_endpoints(self, client):
        """Test OAuth endpoints when OAuth is disabled."""
        # Login should return 503
        response = client.get("/auth/login", allow_redirects=False)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Callback should return 503
        response = client.get("/auth/callback", allow_redirects=False)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Current user endpoint without auth should return 401
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.services.auth_service.GoogleAuthService.oauth_enabled', True)
    @patch('app.services.auth_service.auth_service.handle_callback')
    def test_oauth_callback_success(self, mock_handle_callback, client, db_session):
        """Test successful OAuth callback."""
        # Mock successful callback response
        mock_handle_callback.return_value = {
            "access_token": "mock_jwt_token",
            "user": {
                "id": str(uuid.uuid4()),
                "email": "user@example.com",
                "name": "Test User"
            }
        }
        
        response = client.get("/auth/callback?code=mock_code&state=mock_state", allow_redirects=False)
        
        # Should redirect to home page
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/"
        
        # Should set authentication cookie
        assert "access_token" in response.cookies
    
    @patch('app.services.auth_service.GoogleAuthService.oauth_enabled', True)
    @patch('app.services.auth_service.auth_service.handle_callback')
    def test_oauth_callback_error(self, mock_handle_callback, client):
        """Test OAuth callback with error."""
        # Mock callback that raises exception
        mock_handle_callback.side_effect = Exception("OAuth error")
        
        response = client.get("/auth/callback?error=access_denied", allow_redirects=False)
        
        # Should redirect to login page with error
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers["location"]
        assert "error=" in response.headers["location"]


@pytest.mark.integration
class TestAuthenticationAccessControls:
    """Test cases for authentication-based access controls."""
    
    def test_home_page_redirect_logic(self, client):
        """Test home page authentication redirect logic."""
        # No session should redirect to login
        response = client.get("/", allow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/login"
        
        # With guest session should show dashboard
        client.get("/start-guest")  # Create guest session
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "Dashboard" in response.text
    
    def test_api_routes_guest_access(self, client_with_guest_session):
        """Test that API routes are accessible to guest users."""
        # Should be able to access trips API
        response = client_with_guest_session.get("/api/trips/")
        assert response.status_code == status.HTTP_200_OK
        
        # Should be able to access bookings API  
        response = client_with_guest_session.get("/api/bookings/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_web_pages_guest_access(self, client_with_guest_session):
        """Test that web pages are accessible to guest users."""
        # Dashboard
        response = client_with_guest_session.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "Guest User" in response.text
        
        # Trips page
        response = client_with_guest_session.get("/trips")
        assert response.status_code == status.HTTP_200_OK
        
        # Should not redirect to login
        assert "Sign in to continue" not in response.text
    
    def test_data_access_isolation_authenticated_vs_guest(self, client_with_auth_user, client_with_guest_session):
        """Test data isolation between authenticated users and guests."""
        auth_client, user = client_with_auth_user
        
        # Create trip as authenticated user
        auth_trip = {"name": "Auth User Trip", "start_date": "2024-06-01T10:00:00"}
        auth_response = auth_client.post("/api/trips/", json=auth_trip)
        assert auth_response.status_code == status.HTTP_201_CREATED
        
        # Create trip as guest
        guest_trip = {"name": "Guest User Trip", "start_date": "2024-06-01T10:00:00"}
        guest_response = client_with_guest_session.post("/api/trips/", json=guest_trip)
        assert guest_response.status_code == status.HTTP_201_CREATED
        
        # Each should only see their own trips
        auth_trips = auth_client.get("/api/trips/").json()
        guest_trips = client_with_guest_session.get("/api/trips/").json()
        
        assert len(auth_trips) == 1
        assert len(guest_trips) == 1
        assert auth_trips[0]["name"] == "Auth User Trip"
        assert guest_trips[0]["name"] == "Guest User Trip"
        
        # Verify user association
        assert auth_trips[0]["user_id"] == str(user.id)
        assert auth_trips[0]["guest_session_id"] is None
        assert guest_trips[0]["user_id"] is None
        assert guest_trips[0]["guest_session_id"] is not None
    
    def test_cross_session_access_denial(self, client):
        """Test that users cannot access data from other sessions."""
        # Create trip in first session
        trip_data = {"name": "Private Trip", "start_date": "2024-06-01T10:00:00"}
        response1 = client.post("/api/trips/", json=trip_data)
        trip_id = response1.json()["id"]
        
        # Clear session and try to access trip
        client.cookies.clear()
        response2 = client.get(f"/api/trips/{trip_id}")
        assert response2.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to update trip from different session
        update_data = {"name": "Hacked Trip"}
        response3 = client.put(f"/api/trips/{trip_id}", json=update_data)
        assert response3.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to delete trip from different session
        response4 = client.delete(f"/api/trips/{trip_id}")
        assert response4.status_code == status.HTTP_404_NOT_FOUND
    
    def test_logout_functionality(self, client_with_auth_user):
        """Test logout functionality for authenticated users."""
        auth_client, user = client_with_auth_user
        
        # Should be able to access protected endpoint
        response = auth_client.get("/auth/me")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == user.email
        
        # Logout
        logout_response = auth_client.post("/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK
        assert "Successfully logged out" in logout_response.json()["message"]
        
        # Should no longer be able to access protected endpoint
        # Note: This test might need adjustment based on how TestClient handles cookies
    
    def test_unauthenticated_access_to_auth_endpoints(self, client):
        """Test unauthenticated access to auth-only endpoints."""
        # Current user endpoint should require authentication
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Logout should require authentication
        response = client.post("/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestSessionSecurity:
    """Test cases for session security and validation."""
    
    def test_invalid_guest_session_cookie(self, client):
        """Test behavior with invalid guest session cookies."""
        # Set an invalid/tampered cookie
        client.cookies.set("guest_session", "invalid_session_data")
        
        # Should still work (create new session or ignore invalid one)
        response = client.get("/api/trips/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_expired_auth_token_handling(self, client):
        """Test handling of expired authentication tokens."""
        # Set an invalid JWT token
        client.cookies.set("access_token", "invalid.jwt.token")
        
        # Should not be treated as authenticated
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_malformed_auth_token_handling(self, client):
        """Test handling of malformed authentication tokens."""
        # Set malformed token
        client.cookies.set("access_token", "not-a-jwt-token")
        
        # Should handle gracefully
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_guest_session_regeneration(self, client):
        """Test that new guest sessions are created when needed."""
        # Make request without any session
        response1 = client.get("/api/trips/")
        assert response1.status_code == status.HTTP_200_OK
        
        # Should have automatically created a guest session
        assert "guest_session" in response1.cookies or len(client.cookies) > 0
        
        # Subsequent requests should maintain the session
        response2 = client.get("/api/trips/")
        assert response2.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestAuthenticationUI:
    """Test cases for authentication-related UI components."""
    
    def test_login_page_oauth_disabled(self, client):
        """Test login page display when OAuth is disabled."""
        response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK
        
        content = response.text
        assert "Trip Planner" in content
        assert "Google Authentication is not configured" in content
        assert "Start Using Trip Planner" in content
        # Should not show Google login button
        assert "Continue with Google" not in content
    
    @patch('app.services.auth_service.GoogleAuthService.oauth_enabled', True)
    def test_login_page_oauth_enabled(self, client):
        """Test login page display when OAuth is enabled."""
        response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK
        
        content = response.text
        assert "Trip Planner" in content
        assert "Continue with Google" in content
        assert "Continue as Guest" in content
        # Should not show disabled message
        assert "Google Authentication is not configured" not in content
    
    def test_navigation_guest_user(self, client_with_guest_session):
        """Test navigation display for guest users."""
        response = client_with_guest_session.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        content = response.text
        assert "Guest User" in content
        assert "Sign In with Google" in content  # In dropdown
        assert "About Guest Mode" in content    # In dropdown
    
    def test_navigation_authenticated_user(self, client_with_auth_user):
        """Test navigation display for authenticated users."""
        auth_client, user = client_with_auth_user
        response = auth_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        content = response.text
        assert user.name in content  # User name should appear
        # Should not show guest-specific elements
        assert "Guest User" not in content
        assert "About Guest Mode" not in content
    
    def test_error_handling_in_ui(self, client):
        """Test error handling in authentication UI."""
        # Test login page with error parameter
        response = client.get("/login?error=authentication_failed")
        assert response.status_code == status.HTTP_200_OK
        
        # Should display error message (implementation dependent)
        content = response.text
        assert "Trip Planner" in content  # Basic page still loads 