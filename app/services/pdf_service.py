"""
PDF generation service for the trip planner application.

This service handles the generation of trip reports as PDF documents
using ReportLab library.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any

from ..models.booking import Trip, Booking
from ..core.config import PDF_DEFAULT_PAGESIZE

def create_trip_pdf(trip: Trip, bookings: List[Booking], language: str = "en") -> BytesIO:
    """Generate a PDF report for a trip with all its bookings."""
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Add title
    title = Paragraph(f"Trip Report: {trip.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Trip information section
    trip_info = [
        ["Trip Details", ""],
        ["Name:", trip.name],
        ["Description:", trip.description or "N/A"],
        ["Destination:", trip.primary_destination or "N/A"],
        ["Start Date:", trip.start_date.strftime('%B %d, %Y') if trip.start_date else "N/A"],
        ["End Date:", trip.end_date.strftime('%B %d, %Y') if trip.end_date else "N/A"],
        ["Status:", trip.status.value.title()],
        ["Budget:", f"{trip.currency} {trip.budget:.2f}" if trip.budget else "N/A"],
        ["Travelers:", str(trip.traveler_count)],
    ]
    
    if trip.destinations:
        trip_info.append(["All Destinations:", trip.destinations.replace('\n', ', ')])
    
    if trip.notes:
        trip_info.append(["Notes:", trip.notes])
    
    # Create trip info table
    trip_table = Table(trip_info, colWidths=[2*inch, 4*inch])
    trip_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(trip_table)
    elements.append(Spacer(1, 20))
    
    # Bookings section
    if bookings:
        booking_title = Paragraph("Bookings", heading_style)
        elements.append(booking_title)
        elements.append(Spacer(1, 12))
        
        # Create bookings table data
        booking_data = [
            ["Type", "Title", "Date", "Status", "Location", "Price", "Confirmation"]
        ]
        
        total_cost = 0
        for booking in bookings:
            booking_type = booking.booking_type.value.title()
            title = booking.title
            date = booking.start_date.strftime('%m/%d/%Y') if booking.start_date else "N/A"
            status = booking.status.value.title()
            
            location = ""
            if booking.departure_location and booking.arrival_location:
                location = f"{booking.departure_location} → {booking.arrival_location}"
            elif booking.departure_location:
                location = booking.departure_location
            elif booking.arrival_location:
                location = booking.arrival_location
            elif booking.address:
                location = booking.address
            else:
                location = "N/A"
                
            price = f"{booking.currency} {booking.price:.2f}" if booking.price else "N/A"
            if booking.price:
                total_cost += booking.price
                
            confirmation = booking.confirmation_number or "N/A"
            
            booking_data.append([
                booking_type,
                title,
                date,
                status,
                location,
                price,
                confirmation
            ])
        
        # Add total row
        booking_data.append([
            "TOTAL", "", "", "", "", 
            f"{trip.currency} {total_cost:.2f}", 
            ""
        ])
        
        # Create bookings table
        bookings_table = Table(booking_data, colWidths=[0.8*inch, 1.5*inch, 1*inch, 0.8*inch, 1.5*inch, 0.8*inch, 1*inch])
        bookings_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (4, 1), (5, -1), 'RIGHT'),  # Right align price column
        ]))
        
        elements.append(bookings_table)
    else:
        no_bookings = Paragraph("No bookings found for this trip.", styles['Normal'])
        elements.append(no_bookings)
    
    elements.append(Spacer(1, 20))
    
    # Statistics section
    if bookings:
        stats_title = Paragraph("Trip Statistics", heading_style)
        elements.append(stats_title)
        elements.append(Spacer(1, 12))
        
        # Calculate statistics
        confirmed_count = len([b for b in bookings if b.status.value == 'confirmed'])
        pending_count = len([b for b in bookings if b.status.value == 'pending'])
        cancelled_count = len([b for b in bookings if b.status.value == 'cancelled'])
        
        booking_types = {}
        for booking in bookings:
            booking_type = booking.booking_type.value.title()
            booking_types[booking_type] = booking_types.get(booking_type, 0) + 1
        
        stats_data = [
            ["Statistics", ""],
            ["Total Bookings:", str(len(bookings))],
            ["Confirmed:", str(confirmed_count)],
            ["Pending:", str(pending_count)],
            ["Cancelled:", str(cancelled_count)],
            ["Total Cost:", f"{trip.currency} {total_cost:.2f}"],
        ]
        
        # Add booking type breakdown
        for booking_type, count in booking_types.items():
            stats_data.append([f"{booking_type}s:", str(count)])
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(stats_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    buffer.seek(0)
    return buffer 