import pytest
from datetime import datetime
from app.models.booking import Trip, Booking, BookingType, BookingStatus
from sqlalchemy.exc import IntegrityError


@pytest.mark.unit
class TestTripModel:
    """Test cases for the Trip model."""
    
    def test_create_trip_basic(self, db_session):
        """Test creating a trip with all fields."""
        trip = Trip(
            name="Test Trip to Paris",
            description="A wonderful test trip",
            start_date=datetime(2024, 6, 1, 10, 0),
            end_date=datetime(2024, 6, 7, 18, 0),
            primary_destination="Paris, France",
            budget=2500.00,
            currency="EUR",
            traveler_count=2,
            notes="First international trip"
        )
        db_session.add(trip)
        db_session.commit()
        
        assert trip.id is not None
        assert trip.name == "Test Trip to Paris"
        assert trip.description == "A wonderful test trip"
        assert trip.primary_destination == "Paris, France"
        assert trip.budget == 2500.00
        assert trip.currency == "EUR"
        assert trip.traveler_count == 2
        
    def test_create_trip_minimal_required_fields(self, db_session):
        """Test creating a trip with only required fields."""
        trip = Trip(
            name="Minimal Trip",
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2024, 6, 8)  # end_date is required according to model
        )
        db_session.add(trip)
        db_session.commit()
        
        assert trip.id is not None
        assert trip.name == "Minimal Trip"
        assert trip.description is None
        # Accept both naive and UTC-aware datetimes
        expected = datetime(2024, 6, 8)
        actual = trip.end_date
        if actual.tzinfo is not None:
            actual = actual.replace(tzinfo=None)
        assert actual == expected
    
    def test_trip_name_required(self, db_session):
        """Test that name is required."""
        trip = Trip(
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2024, 6, 8)
        )
        db_session.add(trip)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_trip_start_date_required(self, db_session):
        """Test that start date is required."""
        trip = Trip(name="Test Trip", end_date=datetime(2024, 6, 8))
        db_session.add(trip)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_trip_end_date_optional(self, db_session):
        """Test that end date is now optional."""
        trip = Trip(name="Test Trip", start_date=datetime(2024, 6, 1))
        db_session.add(trip)
        db_session.commit()
        
        # Should succeed since end_date is now optional
        assert trip.id is not None
        assert trip.end_date is None
    
    def test_trip_bookings_relationship(self, db_session):
        """Test the trip-bookings relationship."""
        trip = Trip(
            name="Test Trip",
            start_date=datetime(2024, 6, 1),
            end_date=datetime(2024, 6, 8)
        )
        db_session.add(trip)
        db_session.commit()

        booking1 = Booking(
            title="Hotel",
            booking_type=BookingType.ACCOMMODATION,
            trip_id=trip.id,
            start_date=datetime(2024, 6, 1, 15, 0),
            status=BookingStatus.CONFIRMED
        )
        booking2 = Booking(
            title="Flight",
            booking_type=BookingType.FLIGHT,
            trip_id=trip.id,
            start_date=datetime(2024, 6, 1, 8, 0),
            status=BookingStatus.CONFIRMED
        )

        db_session.add_all([booking1, booking2])
        db_session.commit()

        db_session.refresh(trip)
        assert len(trip.bookings) == 2
        
        # Check booking IDs since objects may be different instances after reload
        booking_ids = {booking.id for booking in trip.bookings}
        assert booking1.id in booking_ids
        assert booking2.id in booking_ids


@pytest.mark.unit
class TestBookingModel:
    """Test cases for the Booking model."""
    
    def test_create_booking_basic(self, db_session, sample_trip):
        """Test creating a basic booking."""
        booking = Booking(
            title="Test Booking",
            booking_type=BookingType.ACCOMMODATION,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1, 15, 0),
            end_date=datetime(2024, 6, 7, 11, 0),
            departure_location="Hotel Address",
            arrival_location="Reception",
            status=BookingStatus.CONFIRMED,
            price=150.00,
            currency="EUR",
            confirmation_number="HTL123",
            notes="Test notes"
        )
        db_session.add(booking)
        db_session.commit()
        
        assert booking.id is not None
        assert booking.title == "Test Booking"
        assert booking.booking_type == BookingType.ACCOMMODATION
        assert booking.price == 150.00
        assert booking.currency == "EUR"
        assert booking.confirmation_number == "HTL123"
        
    def test_create_booking_minimal_fields(self, db_session, sample_trip):
        """Test creating a booking with only required fields."""
        booking = Booking(
            title="Minimal Booking",
            booking_type=BookingType.OTHER,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1, 10, 0),
            status=BookingStatus.PENDING
        )
        db_session.add(booking)
        db_session.commit()
        
        assert booking.id is not None
        assert booking.title == "Minimal Booking"
        assert booking.booking_type == BookingType.OTHER
        assert booking.price is None
        assert booking.end_date is None
        
    def test_booking_required_fields(self, db_session, sample_trip):
        """Test that required fields are enforced."""
        # Test missing title
        booking = Booking(
            booking_type=BookingType.FLIGHT,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1),
            status=BookingStatus.PENDING
        )
        db_session.add(booking)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_booking_types_enum(self, db_session, sample_trip):
        """Test all booking type enum values."""
        booking_types = [
            BookingType.FLIGHT,
            BookingType.ACCOMMODATION,
            BookingType.CAR_RENTAL,
            BookingType.ACTIVITY,
            BookingType.RESTAURANT,
            BookingType.OTHER
        ]
        
        for booking_type in booking_types:
            booking = Booking(
                title=f"Test {booking_type.value}",
                booking_type=booking_type,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1),
                status=BookingStatus.PENDING
            )
            db_session.add(booking)
        
        db_session.commit()
        
        # Verify all bookings were created
        bookings = db_session.query(Booking).all()
        assert len(bookings) == len(booking_types)
        
        # Verify booking types
        actual_types = {booking.booking_type for booking in bookings}
        expected_types = set(booking_types)
        assert actual_types == expected_types
        
    def test_booking_status_enum(self, db_session, sample_trip):
        """Test all booking status enum values."""
        statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED]
        
        for status in statuses:
            booking = Booking(
                title=f"Test {status.value}",
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1),
                status=status
            )
            db_session.add(booking)
        
        db_session.commit()
        
        bookings = db_session.query(Booking).all()
        assert len(bookings) == len(statuses)
        
        # Verify statuses
        actual_statuses = {booking.status for booking in bookings}
        expected_statuses = set(statuses)
        assert actual_statuses == expected_statuses
        
    def test_booking_trip_relationship(self, db_session, sample_trip):
        """Test the booking-trip relationship."""
        booking = Booking(
            title="Test Booking",
            booking_type=BookingType.ACCOMMODATION,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1),
            status=BookingStatus.PENDING
        )
        db_session.add(booking)
        db_session.commit()
        
        db_session.refresh(booking)
        assert booking.trip is not None
        assert booking.trip.id == sample_trip.id
        assert booking.trip.name == sample_trip.name
        
    def test_booking_foreign_key_constraint(self, db_session):
        """Test foreign key constraint for trip_id."""
        import uuid
        booking = Booking(
            title="Invalid Booking",
            booking_type=BookingType.OTHER,
            trip_id=str(uuid.uuid4()),  # Use a valid UUID format but non-existent ID
            start_date=datetime(2024, 6, 1),
            status=BookingStatus.PENDING
        )
        db_session.add(booking)
        
        # PostgreSQL properly enforces foreign key constraints
        # so this should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()
        
    def test_booking_price_validation(self, db_session, sample_trip):
        """Test that price can be None or a valid decimal."""
        # Test with None price
        booking1 = Booking(
            title="No Price Booking",
            booking_type=BookingType.OTHER,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1),
            status=BookingStatus.PENDING,
            price=None
        )
        
        # Test with valid price
        booking2 = Booking(
            title="Priced Booking",
            booking_type=BookingType.OTHER,
            trip_id=sample_trip.id,
            start_date=datetime(2024, 6, 1),
            status=BookingStatus.PENDING,
            price=99.99
        )
        
        db_session.add_all([booking1, booking2])
        db_session.commit()
        
        assert booking1.price is None
        assert booking2.price == 99.99 