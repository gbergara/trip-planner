import pytest
from datetime import datetime
from fastapi import status
from unittest.mock import Mock, patch
import uuid


@pytest.mark.integration
class TestTripsAPI:
    """Test cases for the trips API endpoints."""
    
    def test_get_empty_trips_guest(self, client_with_guest_session):
        """Test getting trips when none exist as a guest user."""
        response = client_with_guest_session.get("/api/trips/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_get_empty_trips_no_session(self, client):
        """Test getting trips without any session - should create guest session."""
        response = client.get("/api/trips/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
        # Should have set a guest session cookie
        assert "guest_session" in response.cookies
    
    def test_create_trip_guest(self, client_with_guest_session):
        """Test creating a new trip as a guest user."""
        trip_data = {
            "name": "Test Trip API",
            "description": "API test trip",
            "start_date": "2024-06-01T10:00:00",
            "end_date": "2024-06-07T18:00:00"
        }
        
        response = client_with_guest_session.post("/api/trips/", json=trip_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_trip = response.json()
        assert created_trip["name"] == trip_data["name"]
        assert created_trip["description"] == trip_data["description"]
        assert created_trip["start_date"] == trip_data["start_date"]
        assert created_trip["end_date"] == trip_data["end_date"]
        assert "id" in created_trip
        assert created_trip["user_id"] is None  # Guest user
        assert created_trip["guest_session_id"] is not None
    
    def test_create_trip_authenticated(self, client_with_auth_user):
        """Test creating a new trip as an authenticated user."""
        client, user = client_with_auth_user
        trip_data = {
            "name": "Authenticated User Trip",
            "description": "Trip by authenticated user",
            "start_date": "2024-06-01T10:00:00",
            "end_date": "2024-06-07T18:00:00"
        }
        
        response = client.post("/api/trips/", json=trip_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_trip = response.json()
        assert created_trip["name"] == trip_data["name"]
        assert created_trip["user_id"] == str(user.id)
        assert created_trip["guest_session_id"] is None
    
    def test_create_trip_minimal_data(self, client_with_guest_session):
        """Test creating a trip with minimal required data."""
        trip_data = {
            "name": "Minimal Trip",
            "start_date": "2024-06-01T10:00:00"
        }
        
        response = client_with_guest_session.post("/api/trips/", json=trip_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        created_trip = response.json()
        assert created_trip["name"] == trip_data["name"]
        assert created_trip["start_date"] == trip_data["start_date"]
        assert created_trip["description"] is None
        assert created_trip["end_date"] is None

    def test_trip_isolation_between_guests(self, client):
        """Test that guest users can only see their own trips."""
        # Create a trip with first guest session
        trip_data = {"name": "Guest 1 Trip", "start_date": "2024-06-01T10:00:00"}
        
        # First guest session
        response1 = client.post("/api/trips/", json=trip_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Get trips for first guest - should see 1 trip
        response1_get = client.get("/api/trips/")
        assert response1_get.status_code == status.HTTP_200_OK
        assert len(response1_get.json()) == 1
        
        # Clear cookies to simulate new guest session
        client.cookies.clear()
        
        # Second guest session - should see 0 trips
        response2_get = client.get("/api/trips/")
        assert response2_get.status_code == status.HTTP_200_OK
        assert len(response2_get.json()) == 0
    
    def test_trip_isolation_guest_vs_authenticated(self, client_with_guest_session, client_with_auth_user):
        """Test that guest and authenticated users can't see each other's trips."""
        # Create trip as guest
        guest_trip_data = {"name": "Guest Trip", "start_date": "2024-06-01T10:00:00"}
        guest_response = client_with_guest_session.post("/api/trips/", json=guest_trip_data)
        assert guest_response.status_code == status.HTTP_201_CREATED
        
        # Create trip as authenticated user
        auth_client, _ = client_with_auth_user
        auth_trip_data = {"name": "Auth Trip", "start_date": "2024-06-01T10:00:00"}
        auth_response = auth_client.post("/api/trips/", json=auth_trip_data)
        assert auth_response.status_code == status.HTTP_201_CREATED
        
        # Each should only see their own trip
        guest_trips = client_with_guest_session.get("/api/trips/").json()
        auth_trips = auth_client.get("/api/trips/").json()
        
        assert len(guest_trips) == 1
        assert len(auth_trips) == 1
        assert guest_trips[0]["name"] == "Guest Trip"
        assert auth_trips[0]["name"] == "Auth Trip"
    
    def test_get_trip_by_id_guest(self, client_with_guest_session):
        """Test getting a specific trip by ID as a guest."""
        # Create a trip first
        trip_data = {"name": "Test Trip", "start_date": "2024-06-01T10:00:00"}
        create_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = create_response.json()["id"]
        
        # Get the trip by ID
        response = client_with_guest_session.get(f"/api/trips/{trip_id}")
        assert response.status_code == status.HTTP_200_OK
        
        trip = response.json()
        assert trip["id"] == trip_id
        assert trip["name"] == "Test Trip"
    
    def test_get_trip_by_id_unauthorized_access(self, client_with_guest_session, client):
        """Test that users cannot access trips from other sessions."""
        # Create trip with first guest session
        trip_data = {"name": "Private Trip", "start_date": "2024-06-01T10:00:00"}
        create_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = create_response.json()["id"]
        
        # Try to access with different session (clear cookies)
        client.cookies.clear()
        response = client.get(f"/api/trips/{trip_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_trip_guest(self, client_with_guest_session):
        """Test updating a trip as a guest user."""
        # Create a trip first
        trip_data = {"name": "Original Trip", "start_date": "2024-06-01T10:00:00"}
        create_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = create_response.json()["id"]
        
        # Update the trip
        update_data = {"name": "Updated Trip", "description": "Updated description"}
        response = client_with_guest_session.put(f"/api/trips/{trip_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        updated_trip = response.json()
        assert updated_trip["name"] == "Updated Trip"
        assert updated_trip["description"] == "Updated description"
    
    def test_delete_trip_guest(self, client_with_guest_session):
        """Test deleting a trip as a guest user."""
        # Create a trip first
        trip_data = {"name": "Trip to Delete", "start_date": "2024-06-01T10:00:00"}
        create_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = create_response.json()["id"]
        
        # Delete the trip
        response = client_with_guest_session.delete(f"/api/trips/{trip_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's deleted
        get_response = client_with_guest_session.get(f"/api/trips/{trip_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_trip_validation_errors(self, client_with_guest_session):
        """Test trip creation validation errors."""
        # Missing required field
        invalid_data = {"description": "Trip without name"}
        response = client_with_guest_session.post("/api/trips/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Invalid date format
        invalid_date_data = {
            "name": "Invalid Date Trip",
            "start_date": "invalid-date"
        }
        response = client_with_guest_session.post("/api/trips/", json=invalid_date_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestBookingsAPI:
    """Test cases for the bookings API endpoints."""
    
    def test_get_empty_bookings_guest(self, client_with_guest_session):
        """Test getting bookings when none exist as a guest user."""
        response = client_with_guest_session.get("/api/bookings/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_create_booking_for_guest_trip(self, client_with_guest_session):
        """Test creating a booking for a guest user's trip."""
        # Create a trip first
        trip_data = {"name": "Test Trip", "start_date": "2024-06-01T10:00:00"}
        trip_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = trip_response.json()["id"]
        
        # Create a booking for the trip
        booking_data = {
            "title": "Test Hotel",
            "booking_type": "accommodation",
            "trip_id": trip_id,
            "start_date": "2024-06-01T15:00:00",
            "departure_location": "Hotel Address"
        }
        
        response = client_with_guest_session.post("/api/bookings/", json=booking_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        booking = response.json()
        assert booking["title"] == "Test Hotel"
        assert booking["trip_id"] == trip_id
    
    def test_booking_trip_access_control(self, client_with_guest_session, client):
        """Test that users can only create bookings for their own trips."""
        # Create trip with first guest session
        trip_data = {"name": "Private Trip", "start_date": "2024-06-01T10:00:00"}
        trip_response = client_with_guest_session.post("/api/trips/", json=trip_data)
        trip_id = trip_response.json()["id"]
        
        # Try to create booking with different session
        client.cookies.clear()
        booking_data = {
            "title": "Unauthorized Booking",
            "booking_type": "accommodation", 
            "trip_id": trip_id,
            "start_date": "2024-06-01T15:00:00",
            "departure_location": "Hotel Address"
        }
        
        response = client.post("/api/bookings/", json=booking_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestAuthenticationAPI:
    """Test cases for the authentication endpoints."""
    
    def test_start_guest_session(self, client):
        """Test creating a guest session."""
        response = client.get("/start-guest", allow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/"
        assert "guest_session" in response.cookies
    
    def test_guest_session_persistence(self, client):
        """Test that guest sessions persist across requests."""
        # Start guest session
        response1 = client.get("/start-guest", allow_redirects=False)
        guest_cookie = response1.cookies["guest_session"]
        
        # Make another request with the same client (cookies preserved)
        response2 = client.get("/api/trips/")
        assert response2.status_code == status.HTTP_200_OK
    
    def test_login_page_oauth_disabled(self, client):
        """Test login page when OAuth is disabled."""
        response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Google Authentication is not configured" in content
        assert "Start Using Trip Planner" in content
    
    @patch('app.services.auth_service.auth_service.oauth_enabled', True)
    def test_login_page_oauth_enabled(self, client):
        """Test login page when OAuth is enabled."""
        response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Continue with Google" in content
        assert "Continue as Guest" in content
    
    def test_auth_endpoints_oauth_disabled(self, client):
        """Test auth endpoints when OAuth is disabled."""
        # OAuth login should return 503
        response = client.get("/auth/login", allow_redirects=False)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        
        # OAuth callback should return 503
        response = client.get("/auth/callback")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    def test_home_redirect_logic(self, client):
        """Test home page redirect logic."""
        # No session should redirect to login
        response = client.get("/", allow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/login"
        
        # With guest session should show dashboard
        client.get("/start-guest")  # Create guest session
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "Dashboard" in response.text


@pytest.mark.integration 
class TestWebPages:
    """Test cases for web page endpoints."""
    
    def test_login_page_rendering(self, client):
        """Test that login page renders correctly."""
        response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK
        assert "Trip Planner" in response.text
        assert "Start Using Trip Planner" in response.text
    
    def test_dashboard_guest_access(self, client_with_guest_session):
        """Test dashboard access as guest user."""
        response = client_with_guest_session.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "Dashboard" in response.text
        assert "Guest User" in response.text
    
    def test_trips_page_guest_access(self, client_with_guest_session):
        """Test trips page access as guest user."""
        response = client_with_guest_session.get("/trips")
        assert response.status_code == status.HTTP_200_OK
        assert "Trips" in response.text 