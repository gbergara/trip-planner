import pytest
import os
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import uuid

# Set test environment before importing app modules
os.environ["TESTING"] = "true"

from app.main import app
from app.core.database import get_db, Base
from app.models.booking import Trip, Booking, BookingType, BookingStatus


# Test database setup - use PostgreSQL for tests
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://test_user:test_pass@localhost:5433/trip_planner_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Drop and recreate all tables for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")  
def client(db_session):
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        # Use context manager to ensure proper cleanup
        with TestClient(app, base_url="http://testserver") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client_with_guest_session(client):
    """Create a test client with a guest session established."""
    # Create a guest session by calling the start-guest endpoint
    response = client.get("/start-guest", allow_redirects=False)
    assert response.status_code == 302
    # The client now has a guest session cookie
    return client


@pytest.fixture
def client_with_auth_user(client, db_session):
    """Create a test client with an authenticated user."""
    from app.models.user import User
    import uuid
    from app.services.auth_service import auth_service
    
    # Create a test user
    user = User(
        id=uuid.uuid4(),
        google_id="test_google_id_123",
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create a mock JWT token for this user
    from unittest.mock import patch
    
    def mock_get_current_user(db, token):
        return user
    
    # Patch the auth service to return our test user
    with patch.object(auth_service, 'get_current_user', mock_get_current_user):
        # Set a mock access_token cookie
        client.cookies.set("access_token", "mock_jwt_token")
        yield client, user


@pytest.fixture
def sample_trip(db_session):
    """Create a sample trip for testing."""
    from datetime import datetime
    trip = Trip(
        name="Test Trip to Paris",
        description="A wonderful test trip",
        start_date=datetime(2024, 6, 1, 10, 0),
        end_date=datetime(2024, 6, 7, 18, 0)
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


@pytest.fixture
def sample_booking(db_session, sample_trip):
    """Create a sample booking for testing."""
    from datetime import datetime
    booking = Booking(
        title="Test Hotel Booking",
        booking_type=BookingType.ACCOMMODATION,
        trip_id=sample_trip.id,
        start_date=datetime(2024, 6, 1, 15, 0),
        end_date=datetime(2024, 6, 7, 11, 0),
        departure_location="Hotel Address, Paris",
        arrival_location="Reception Desk",
        status=BookingStatus.CONFIRMED,
        price=150.00,
        currency="EUR",
        confirmation_number="HTL123456",
        notes="Ground floor room requested"
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def multiple_bookings(db_session, sample_trip):
    """Create multiple bookings for testing."""
    from datetime import datetime
    bookings = [
        Booking(
            title="Flight to Paris",
            booking_type=BookingType.FLIGHT, 
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1, 8, 0),
            departure_location="JFK",
            arrival_location="CDG",
            status=BookingStatus.CONFIRMED,
            price=450.00,
            currency="USD",
            confirmation_number="FL789"
        ),
        Booking(
            title="City Tour",
            booking_type=BookingType.ACTIVITY,
            trip_id=sample_trip.id, 
            start_date=datetime(2024, 6, 3, 14, 0),
            departure_location="Hotel Lobby",
            arrival_location="Eiffel Tower",
            status=BookingStatus.PENDING,
            price=75.00,
            currency="EUR"
        ),
        Booking(
            title="Car Rental",
            booking_type=BookingType.CAR_RENTAL,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 2, 9, 0),
            end_date=datetime(2024, 6, 6, 18, 0),
            departure_location="CDG Airport",
            arrival_location="CDG Airport",
            status=BookingStatus.CONFIRMED,
            price=200.00,
            currency="EUR",
            confirmation_number="CAR456"
        )
    ]
    
    for booking in bookings:
        db_session.add(booking)
    db_session.commit()
    
    for booking in bookings:
        db_session.refresh(booking)
    
    return bookings 