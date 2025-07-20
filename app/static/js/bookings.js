// Bookings page JavaScript

let currentBookings = [];
let editingBookingId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadBookings();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Search and filter inputs
    document.getElementById('searchInput').addEventListener('input', debounce(filterBookings, 300));
    document.getElementById('filterType').addEventListener('change', filterBookings);
    document.getElementById('filterStatus').addEventListener('change', filterBookings);

    // Form submission
    document.getElementById('bookingForm').addEventListener('submit', handleBookingSubmit);
}

// Load all bookings
async function loadBookings() {
    const container = document.getElementById('bookings-container');
    
    try {
        currentBookings = await TripPlanner.api.get('/bookings/');
        displayBookings(currentBookings);
    } catch (error) {
        console.error(window.bookingTranslations.errorLoading, error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-exclamation-triangle"></i>
                <p>${window.bookingTranslations.errorLoading}</p>
                <button class="btn btn-primary" onclick="loadBookings()">${window.bookingTranslations.retry}</button>
            </div>
        `;
        TripPlanner.showAlert(window.bookingTranslations.failedToLoad + ' ' + error.message, 'danger');
    }
}

// Display bookings in the container
function displayBookings(bookings) {
    const container = document.getElementById('bookings-container');
    
    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-calendar-x"></i>
                <h5>${window.bookingTranslations.noBookings}</h5>
                <p>${window.bookingTranslations.startPlanning}</p>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#bookingModal" onclick="resetBookingForm()">
                    <i class="bi bi-plus-circle me-2"></i>${window.bookingTranslations.newBooking}
                </button>
            </div>
        `;
        return;
    }

    const bookingsHtml = bookings.map(booking => createBookingCard(booking)).join('');
    container.innerHTML = bookingsHtml;
}

// Create HTML for a booking card
function createBookingCard(booking) {
    const startDate = new Date(booking.start_date);
    const endDate = booking.end_date ? new Date(booking.end_date) : null;
    
    return `
        <div class="booking-item booking-type-${booking.booking_type}" data-booking-id="${booking.id}">
            <div class="row align-items-center">
                <div class="col-md-1">
                    <div class="text-center">
                        <i class="bi bi-${TripPlanner.getBookingTypeIcon(booking.booking_type)} fs-2 text-${TripPlanner.getBookingTypeColorClass(booking.booking_type)}"></i>
                    </div>
                </div>
                <div class="col-md-6">
                    <h5 class="mb-1">${booking.title}</h5>
                    <div class="booking-details">
                        <div class="mb-1">
                            <i class="bi bi-calendar me-1"></i>
                            <span class="date-display">
                                ${TripPlanner.formatDateTime(booking.start_date)}
                                ${endDate ? ' - ' + TripPlanner.formatDateTime(booking.end_date) : ''}
                            </span>
                        </div>
                        ${booking.departure_location && booking.arrival_location ? `
                            <div class="mb-1">
                                <i class="bi bi-arrow-right me-1"></i>
                                ${booking.departure_location} → ${booking.arrival_location}
                            </div>
                        ` : ''}
                        ${booking.provider ? `
                            <div class="mb-1">
                                <i class="bi bi-building me-1"></i>
                                ${booking.provider}
                            </div>
                        ` : ''}
                        ${booking.confirmation_number ? `
                            <div class="mb-1">
                                <i class="bi bi-hash me-1"></i>
                                ${booking.confirmation_number}
                            </div>
                        ` : ''}
                        ${getBookingSpecificDetails(booking)}
                    </div>
                </div>
                <div class="col-md-3 text-center">
                    <div class="mb-2">
                        <span class="status-badge status-${booking.status}">
                            ${booking.status.toUpperCase()}
                        </span>
                    </div>
                    ${booking.price ? `
                        <div class="price-display">
                            ${TripPlanner.formatPrice(booking.price, booking.currency)}
                        </div>
                    ` : ''}
                </div>
                <div class="col-md-2 text-end">
                    <button class="btn-action btn-edit" onclick="editBooking(${booking.id})" title="Edit">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="deleteBooking(${booking.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Get booking type specific details
function getBookingSpecificDetails(booking) {
    let details = '';
    
    switch (booking.booking_type) {
        case 'flight':
            if (booking.flight_number) details += `<div><i class="bi bi-airplane me-1"></i>${booking.flight_number}</div>`;
            if (booking.airline) details += `<div><i class="bi bi-building me-1"></i>${booking.airline}</div>`;
            if (booking.seat_number) details += `<div><i class="bi bi-person-square me-1"></i>Seat ${booking.seat_number}</div>`;
            break;
        case 'accommodation':
            if (booking.room_type) details += `<div><i class="bi bi-door-open me-1"></i>${booking.room_type}</div>`;
            if (booking.guests_count) details += `<div><i class="bi bi-people me-1"></i>${booking.guests_count} guests</div>`;
            break;
        case 'car_rental':
            if (booking.car_model) details += `<div><i class="bi bi-car-front me-1"></i>${booking.car_model}</div>`;
            break;
    }
    
    return details;
}

// Filter bookings based on search and filters
function filterBookings() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const typeFilter = document.getElementById('filterType').value;
    const statusFilter = document.getElementById('filterStatus').value;

    const filtered = currentBookings.filter(booking => {
        const matchesSearch = !searchTerm || 
            booking.title.toLowerCase().includes(searchTerm) ||
            booking.provider?.toLowerCase().includes(searchTerm) ||
            booking.departure_location?.toLowerCase().includes(searchTerm) ||
            booking.arrival_location?.toLowerCase().includes(searchTerm) ||
            booking.confirmation_number?.toLowerCase().includes(searchTerm);

        const matchesType = !typeFilter || booking.booking_type === typeFilter;
        const matchesStatus = !statusFilter || booking.status === statusFilter;

        return matchesSearch && matchesType && matchesStatus;
    });

    displayBookings(filtered);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterType').value = '';
    document.getElementById('filterStatus').value = '';
    displayBookings(currentBookings);
}

// Reset booking form
function resetBookingForm() {
    editingBookingId = null;
    document.getElementById('modalTitle').textContent = window.bookingTranslations.newBooking;
    document.getElementById('submitButton').textContent = window.bookingTranslations.saveBooking;
    document.getElementById('bookingForm').reset();
    hideAllSpecificFields();
}

// Toggle specific fields based on booking type
function toggleSpecificFields() {
    const bookingType = document.getElementById('booking_type').value;
    hideAllSpecificFields();
    
    if (bookingType === 'flight') {
        document.getElementById('flight-fields').style.display = 'block';
    } else if (bookingType === 'accommodation') {
        document.getElementById('accommodation-fields').style.display = 'block';
    } else if (bookingType === 'car_rental') {
        document.getElementById('car-rental-fields').style.display = 'block';
    }
}

// Hide all specific fields
function hideAllSpecificFields() {
    document.getElementById('flight-fields').style.display = 'none';
    document.getElementById('accommodation-fields').style.display = 'none';
    document.getElementById('car-rental-fields').style.display = 'none';
}

// Handle form submission
async function handleBookingSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = document.getElementById('submitButton');
    const formData = new FormData(form);
    
    // Convert form data to object
    const bookingData = {};
    for (const [key, value] of formData.entries()) {
        if (value.trim()) {
            bookingData[key] = value.trim();
        }
    }

    // Convert numeric fields
    if (bookingData.price) bookingData.price = parseFloat(bookingData.price);
    if (bookingData.guests_count) bookingData.guests_count = parseInt(bookingData.guests_count);

    try {
        TripPlanner.setLoading(submitButton, true);

        let result;
        if (editingBookingId) {
            result = await TripPlanner.api.put(`/bookings/${editingBookingId}`, bookingData);
            TripPlanner.showAlert(window.bookingTranslations.bookingUpdated, 'success');
        } else {
            result = await TripPlanner.api.post('/bookings/', bookingData);
            TripPlanner.showAlert(window.bookingTranslations.bookingCreated, 'success');
        }

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('bookingModal'));
        modal.hide();

        // Reload bookings
        await loadBookings();

    } catch (error) {
        console.error(window.bookingTranslations.failedToSave, error);
        TripPlanner.showAlert(window.bookingTranslations.failedToSave + ' ' + error.message, 'danger');
    } finally {
        TripPlanner.setLoading(submitButton, false);
    }
}

// Edit booking
async function editBooking(bookingId) {
    try {
        const booking = await TripPlanner.api.get(`/bookings/${bookingId}`);
        
        editingBookingId = bookingId;
        document.getElementById('modalTitle').textContent = window.bookingTranslations.editBooking;
        document.getElementById('submitButton').textContent = window.bookingTranslations.updateBooking;
        
        // Populate form
        populateForm(booking);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading booking for edit:', error);
        TripPlanner.showAlert('Failed to load booking details: ' + error.message, 'danger');
    }
}

// Populate form with booking data
function populateForm(booking) {
    // Basic fields
    document.getElementById('title').value = booking.title || '';
    document.getElementById('booking_type').value = booking.booking_type || '';
    document.getElementById('status').value = booking.status || 'pending';
    
    // Dates - convert to local datetime format
    if (booking.start_date) {
        const startDate = new Date(booking.start_date);
        document.getElementById('start_date').value = formatDateTimeLocal(startDate);
    }
    if (booking.end_date) {
        const endDate = new Date(booking.end_date);
        document.getElementById('end_date').value = formatDateTimeLocal(endDate);
    }

    // Location
    document.getElementById('departure_location').value = booking.departure_location || '';
    document.getElementById('arrival_location').value = booking.arrival_location || '';

    // Details
    document.getElementById('provider').value = booking.provider || '';
    document.getElementById('confirmation_number').value = booking.confirmation_number || '';
    document.getElementById('price').value = booking.price || '';
    document.getElementById('currency').value = booking.currency || 'USD';
    document.getElementById('description').value = booking.description || '';
    document.getElementById('notes').value = booking.notes || '';
    document.getElementById('contact_email').value = booking.contact_email || '';
    document.getElementById('contact_phone').value = booking.contact_phone || '';

    // Type-specific fields
    if (booking.booking_type === 'flight') {
        document.getElementById('flight_number').value = booking.flight_number || '';
        document.getElementById('airline').value = booking.airline || '';
        document.getElementById('departure_terminal').value = booking.departure_terminal || '';
        document.getElementById('arrival_terminal').value = booking.arrival_terminal || '';
        document.getElementById('seat_number').value = booking.seat_number || '';
    } else if (booking.booking_type === 'accommodation') {
        document.getElementById('room_type').value = booking.room_type || '';
        document.getElementById('guests_count').value = booking.guests_count || '';
        document.getElementById('check_in_time').value = booking.check_in_time || '';
        document.getElementById('check_out_time').value = booking.check_out_time || '';
    } else if (booking.booking_type === 'car_rental') {
        document.getElementById('car_model').value = booking.car_model || '';
        document.getElementById('pickup_location').value = booking.pickup_location || '';
        document.getElementById('return_location').value = booking.return_location || '';
    }

    // Show appropriate fields
    toggleSpecificFields();
}

// Format date for datetime-local input
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Delete booking
function deleteBooking(bookingId) {
    const booking = currentBookings.find(b => b.id === bookingId);
    const bookingTitle = booking ? booking.title : '';
    const confirmMsg = window.bookingTranslations.areYouSureDelete.replace('{title}', bookingTitle);
    TripPlanner.confirm(
        confirmMsg,
        async () => {
            try {
                await TripPlanner.api.delete(`/bookings/${bookingId}`);
                TripPlanner.showAlert(window.bookingTranslations.bookingDeleted, 'success');
                await loadBookings();
            } catch (error) {
                console.error(window.bookingTranslations.failedToDelete, error);
                TripPlanner.showAlert(window.bookingTranslations.failedToDelete + ' ' + error.message, 'danger');
            }
        }
    );
}

// Utility function for debouncing search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Check URL parameters on page load for pre-selected type
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const type = urlParams.get('type');
    if (type) {
        document.getElementById('booking_type').value = type;
        toggleSpecificFields();
        // Show modal if type is specified
        const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
        modal.show();
    }
}); 