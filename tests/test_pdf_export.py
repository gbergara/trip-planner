import pytest
import io
from unittest.mock import Mock, patch
from app.services.pdf_service import create_trip_pdf
from app.models.booking import Trip, Booking, BookingType, BookingStatus
from datetime import datetime


@pytest.mark.unit
class TestPDFExport:
    """Test cases for PDF export functionality."""
    
    def test_create_trip_pdf_basic(self, sample_trip, multiple_bookings):
        """Test creating a basic PDF for a trip with bookings."""
        # Create PDF
        pdf_buffer = create_trip_pdf(sample_trip, multiple_bookings)
        
        # Verify PDF was created
        assert isinstance(pdf_buffer, io.BytesIO)
        
        # Verify PDF has content
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
        
        # Check PDF header (PDF files start with %PDF-)
        pdf_buffer.seek(0)
        header = pdf_buffer.read(4)
        assert header == b'%PDF'
    
    def test_create_trip_pdf_no_bookings(self, sample_trip):
        """Test creating a PDF for a trip with no bookings."""
        empty_bookings = []
        
        pdf_buffer = create_trip_pdf(sample_trip, empty_bookings)
        
        # Should still create a valid PDF
        assert isinstance(pdf_buffer, io.BytesIO)
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
        
        # Check PDF header
        pdf_buffer.seek(0)
        header = pdf_buffer.read(4)
        assert header == b'%PDF'
    
    def test_create_trip_pdf_with_all_booking_types(self, db_session, sample_trip):
        """Test PDF creation with all different booking types."""
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
                confirmation_number="FL123"
            ),
            Booking(
                title="Hotel Paris",
                booking_type=BookingType.ACCOMMODATION,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 15, 0),
                departure_location="123 Rue de Rivoli",
                status=BookingStatus.CONFIRMED,
                price=150.00,
                currency="EUR",
                confirmation_number="HTL456"
            ),
            Booking(
                title="Car Rental",
                booking_type=BookingType.CAR_RENTAL,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 2, 9, 0),
                departure_location="CDG Airport",
                arrival_location="CDG Airport",
                status=BookingStatus.CONFIRMED,
                price=200.00,
                currency="EUR"
            ),
            Booking(
                title="Louvre Tour",
                booking_type=BookingType.ACTIVITY,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 3, 14, 0),
                departure_location="Hotel Lobby",
                arrival_location="Louvre Museum",
                status=BookingStatus.PENDING,
                price=35.00,
                currency="EUR"
            ),
            Booking(
                title="Travel Insurance",
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 0, 0),
                status=BookingStatus.CONFIRMED,
                price=50.00,
                currency="USD"
            )
        ]
        
        for booking in bookings:
            db_session.add(booking)
        db_session.commit()
        
        pdf_buffer = create_trip_pdf(sample_trip, bookings)
        
        # Verify PDF was created successfully with all booking types
        assert isinstance(pdf_buffer, io.BytesIO)
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
    
    def test_create_trip_pdf_with_special_characters(self, db_session):
        """Test PDF creation with special characters in trip and booking names."""
        # Create trip with special characters
        trip = Trip(
            name="Viaje a España & França - Été 2024",
            description="Un viaje increíble con acentos y símbolos: ñ, é, è, ç",
            start_date=datetime(2024, 6, 1, 10, 0),
            end_date=datetime(2024, 6, 7, 18, 0)
        )
        db_session.add(trip)
        db_session.commit()
        
        # Create booking with special characters
        booking = Booking(
            title="Hôtel Café & Résidence",
            booking_type=BookingType.ACCOMMODATION,
            trip_id=trip.id,
            start_date=datetime(2024, 6, 1, 15, 0),
            departure_location="123 Rue du Château, Café García",
            notes="Habitación con vista al café & terraza",
            status=BookingStatus.CONFIRMED,
            price=120.50,
            currency="EUR"
        )
        db_session.add(booking)
        db_session.commit()
        
        pdf_buffer = create_trip_pdf(trip, [booking])
        
        # Should handle special characters without errors
        assert isinstance(pdf_buffer, io.BytesIO)
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
    
    def test_create_trip_pdf_large_data(self, db_session, sample_trip):
        """Test PDF creation with a large number of bookings."""
        # Create many bookings
        bookings = []
        for i in range(50):
            booking = Booking(
                title=f"Test Booking {i+1}",
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 10 + (i % 12), 0),
                status=BookingStatus.CONFIRMED,
                price=100.00 + i,
                currency="USD",
                notes=f"This is test booking number {i+1} with some notes."
            )
            bookings.append(booking)
            db_session.add(booking)
        
        db_session.commit()
        
        pdf_buffer = create_trip_pdf(sample_trip, bookings)
        
        # Should handle large datasets
        assert isinstance(pdf_buffer, io.BytesIO)
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
        
        # PDF should be larger due to more content
        assert len(pdf_content) > 5000  # Arbitrary size check
    
    @patch('app.services.pdf_service.SimpleDocTemplate')
    def test_create_trip_pdf_canvas_error(self, mock_doc, sample_trip, sample_booking):
        """Test PDF creation handles canvas errors gracefully."""
        # Mock SimpleDocTemplate to raise an exception
        mock_doc.side_effect = Exception("Document creation failed")
        
        # Should raise an exception when document creation fails
        with pytest.raises(Exception, match="Document creation failed"):
            create_trip_pdf(sample_trip, [sample_booking])
    
    def test_create_trip_pdf_currency_formatting(self, db_session, sample_trip):
        """Test PDF handles different currency formats correctly."""
        bookings = [
            Booking(
                title="USD Booking",
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 10, 0),
                status=BookingStatus.CONFIRMED,
                price=123.45,
                currency="USD"
            ),
            Booking(
                title="EUR Booking", 
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 11, 0),
                status=BookingStatus.CONFIRMED,
                price=99.99,
                currency="EUR"
            ),
            Booking(
                title="No Price Booking",
                booking_type=BookingType.OTHER,
                trip_id=sample_trip.id,
                start_date=datetime(2024, 6, 1, 12, 0),
                status=BookingStatus.CONFIRMED,
                price=None,
                currency=None
            )
        ]
        
        for booking in bookings:
            db_session.add(booking)
        db_session.commit()
        
        pdf_buffer = create_trip_pdf(sample_trip, bookings)
        
        # Should handle different currency formats without error
        assert isinstance(pdf_buffer, io.BytesIO)
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0


@pytest.mark.integration
class TestPDFExportAPI:
    """Integration tests for PDF export API endpoint."""
    
    def test_export_trip_pdf(self, client, sample_trip, multiple_bookings):
        """Test the PDF export API endpoint."""
        response = client.get(f"/trips/{sample_trip.id}/export/pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert f"{sample_trip.name.replace(' ', '_')}" in response.headers["content-disposition"]
        
        # Verify PDF content
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF')
    
    def test_export_trip_pdf_not_found(self, client):
        """Test PDF export for non-existent trip."""
        non_existent_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/trips/{non_existent_id}/export/pdf")
        
        assert response.status_code == 404
    
    def test_export_trip_pdf_no_bookings(self, client, sample_trip):
        """Test PDF export for trip with no bookings."""
        response = client.get(f"/trips/{sample_trip.id}/export/pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # Should still generate PDF even with no bookings
        pdf_content = response.content
        assert len(pdf_content) > 0
        assert pdf_content.startswith(b'%PDF') 