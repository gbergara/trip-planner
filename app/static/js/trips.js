// Trips page JavaScript

let currentTrips = [];
let editingTripId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadTrips();
    setupEventListeners();
    checkUrlActions();
});

// Setup event listeners
function setupEventListeners() {
    // Search and filter inputs
    document.getElementById('searchInput').addEventListener('input', debounce(filterTrips, 300));
    document.getElementById('filterStatus').addEventListener('change', filterTrips);
    document.getElementById('sortBy').addEventListener('change', filterTrips);

    // Form submission
    document.getElementById('tripForm').addEventListener('submit', handleTripSubmit);
}

// Check URL for actions (like ?action=new or ?action=edit)
function checkUrlActions() {
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');
    const tripId = urlParams.get('id') || sessionStorage.getItem('editTripId');
    
    if (action === 'new') {
        const modal = new bootstrap.Modal(document.getElementById('tripModal'));
        modal.show();
        // Clean up URL
        window.history.replaceState({}, '', window.location.pathname);
    } else if (action === 'edit' && tripId) {
        // Wait for trips to load then edit the specified trip
        setTimeout(() => {
            editTrip(tripId);
        }, 500);
        // Clean up session storage and URL
        sessionStorage.removeItem('editTripId');
        window.history.replaceState({}, '', window.location.pathname);
    }
}

// Load all trips
async function loadTrips() {
    const container = document.getElementById('trips-container');
    
    try {
        currentTrips = await TripPlanner.api.get('/trips/');
        displayTrips(currentTrips);
    } catch (error) {
        console.error('Error loading trips:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-exclamation-triangle"></i>
                <p>Error loading trips. Please try again.</p>
                <button class="btn btn-primary" onclick="loadTrips()">Retry</button>
            </div>
        `;
        TripPlanner.showAlert('Failed to load trips: ' + error.message, 'danger');
    }
}

// Display trips in the container
function displayTrips(trips) {
    const container = document.getElementById('trips-container');
    
    if (trips.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-map"></i>
                <h5>${window.tripTranslations?.noTripsYet || 'No trips planned yet'}</h5>
                <p>${window.tripTranslations?.startPlanning || 'Start planning your next adventure by creating your first trip.'}</p>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#tripModal" onclick="resetTripForm()">
                    <i class="bi bi-plus-circle me-2"></i>${window.tripTranslations?.planFirstTrip || 'Plan Your First Trip'}
                </button>
            </div>
        `;
        return;
    }

    const tripsHtml = trips.map(trip => createTripCard(trip)).join('');
    container.innerHTML = tripsHtml;
}

// Create HTML for a trip card
function createTripCard(trip) {
    const startDate = new Date(trip.start_date);
    const endDate = new Date(trip.end_date);
    const duration = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
    const daysUntil = Math.ceil((startDate - new Date()) / (1000 * 60 * 60 * 24));
    // Pluralize day(s) for duration
    let durationStr = '';
    if (window.tripTranslations) {
        if (duration === 1) {
            durationStr = window.tripTranslations.daySingular || 'day';
        } else {
            durationStr = window.tripTranslations.dayPlural || 'days';
        }
    } else {
        durationStr = duration === 1 ? 'day' : 'days';
    }
    
    // Ensure trip.id is always treated as string for large integers
    const tripIdStr = String(trip.id);
    
    return `
        <div class="trip-item trip-status-${trip.status}" data-trip-id="${tripIdStr}">
            <div class="row align-items-center">
                <div class="col-md-1">
                    <div class="text-center">
                        <i class="bi bi-map fs-2 text-primary"></i>
                    </div>
                </div>
                <div class="col-md-6">
                    <h5 class="mb-1">
                        <a href="/trips/${tripIdStr}/bookings" class="text-decoration-none text-primary fw-bold">${trip.name}</a>
                        <button class="btn btn-sm btn-outline-primary ms-2" onclick="viewTripBookings('${tripIdStr}')" title="${window.tripTranslations?.viewBookings || 'View Bookings'}">
                            <i class="bi bi-calendar-check"></i>
                        </button>
                    </h5>
                    <div class="trip-details">
                        <div class="mb-1">
                            <i class="bi bi-calendar me-1"></i>
                            <span class="date-display">
                                ${TripPlanner.formatDate(trip.start_date)} - ${TripPlanner.formatDate(trip.end_date)}
                                <small class="text-muted">(${duration} ${durationStr})</small>
                            </span>
                        </div>
                        ${trip.primary_destination ? `
                            <div class="mb-1">
                                <i class="bi bi-geo-alt me-1"></i>
                                ${trip.primary_destination}
                            </div>
                        ` : ''}
                        ${trip.traveler_count > 1 ? `
                            <div class="mb-1">
                                <i class="bi bi-people me-1"></i>
                                ${trip.traveler_count} ${window.tripTranslations?.travelers || 'travelers'}
                            </div>
                        ` : ''}
                        ${trip.description ? `
                            <div class="mb-1">
                                <i class="bi bi-info-circle me-1"></i>
                                ${trip.description}
                            </div>
                        ` : ''}
                        ${daysUntil > 0 ? `
                            <div class="mb-1">
                                <i class="bi bi-clock me-1"></i>
                                <span class="text-info">${daysUntil} ${window.tripTranslations?.daysUntilDeparture || 'days until departure'}</span>
                            </div>
                        ` : daysUntil < -duration ? `
                            <div class="mb-1">
                                <i class="bi bi-check-circle me-1"></i>
                                <span class="text-success">${window.tripTranslations?.tripCompleted || 'Trip completed'}</span>
                            </div>
                        ` : daysUntil <= 0 ? `
                            <div class="mb-1">
                                <i class="bi bi-airplane me-1"></i>
                                <span class="text-warning">${window.tripTranslations?.tripInProgress || 'Trip in progress!'}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                <div class="col-md-3 text-center">
                    <div class="mb-2">
                        <span class="status-badge status-${trip.status}">
                            ${trip.status.replace('_', ' ').toUpperCase()}
                        </span>
                    </div>
                    ${trip.budget ? `
                        <div class="price-display">
                            ${window.tripTranslations?.budget || 'Budget:'} ${TripPlanner.formatPrice(trip.budget, trip.currency)}
                        </div>
                    ` : ''}
                    <div class="small text-muted mt-1">
                        ${window.tripTranslations?.created || 'Created'} ${TripPlanner.formatDate(trip.created_at)}
                    </div>
                </div>
                                 <div class="col-md-2 text-end">
                     <button class="btn-action btn-edit" onclick="editTrip('${tripIdStr}')" title="${window.tripTranslations?.editTrip || 'Edit Trip'}">
                         <i class="bi bi-pencil"></i>
                     </button>
                     <button class="btn-action btn-delete" onclick="deleteTrip('${tripIdStr}')" title="${window.tripTranslations?.deleteTrip || 'Delete Trip'}">
                         <i class="bi bi-trash"></i>
                     </button>
                 </div>
            </div>
        </div>
    `;
}

// Filter and sort trips
function filterTrips() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('filterStatus').value;
    const sortBy = document.getElementById('sortBy').value;

    let filtered = currentTrips.filter(trip => {
        const matchesSearch = !searchTerm || 
            trip.name.toLowerCase().includes(searchTerm) ||
            trip.description?.toLowerCase().includes(searchTerm) ||
            trip.primary_destination?.toLowerCase().includes(searchTerm);

        const matchesStatus = !statusFilter || trip.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    // Sort trips
    filtered.sort((a, b) => {
        switch (sortBy) {
            case 'start_date':
                return new Date(a.start_date) - new Date(b.start_date);
            case 'name':
                return a.name.localeCompare(b.name);
            case 'status':
                return a.status.localeCompare(b.status);
            case 'created_at':
            default:
                return new Date(b.created_at) - new Date(a.created_at);
        }
    });

    displayTrips(filtered);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('sortBy').value = 'created_at';
    displayTrips(currentTrips);
}

// Reset trip form
function resetTripForm() {
    editingTripId = null;
    document.getElementById('modalTitle').textContent = 'New Trip';
    document.getElementById('submitButton').textContent = 'Create Trip';
    document.getElementById('tripForm').reset();
    
    // Set default dates (today and tomorrow)
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    document.getElementById('start_date').value = today.toISOString().split('T')[0];
    document.getElementById('end_date').value = tomorrow.toISOString().split('T')[0];
}

// Handle form submission
async function handleTripSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = document.getElementById('submitButton');
    const formData = new FormData(form);
    
    // Convert form data to object
    const tripData = {};
    for (const [key, value] of formData.entries()) {
        if (value.trim()) {
            tripData[key] = value.trim();
        }
    }

    // Convert numeric fields
    if (tripData.budget) tripData.budget = parseFloat(tripData.budget);
    if (tripData.traveler_count) tripData.traveler_count = parseInt(tripData.traveler_count);

    // Convert dates to ISO format
    if (tripData.start_date) tripData.start_date = new Date(tripData.start_date).toISOString();
    if (tripData.end_date) tripData.end_date = new Date(tripData.end_date).toISOString();

    // Validate dates
    if (new Date(tripData.start_date) >= new Date(tripData.end_date)) {
        TripPlanner.showAlert('End date must be after start date', 'danger');
        return;
    }

    try {
        TripPlanner.setLoading(submitButton, true);

        let result;
        if (editingTripId) {
            result = await TripPlanner.api.put(`/trips/${editingTripId}`, tripData);
            TripPlanner.showAlert('Trip updated successfully!', 'success');
        } else {
            result = await TripPlanner.api.post('/trips/', tripData);
            TripPlanner.showAlert('Trip created successfully!', 'success');
        }

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('tripModal'));
        modal.hide();

        // Reload trips
        await loadTrips();

    } catch (error) {
        console.error('Error saving trip:', error);
        TripPlanner.showAlert('Failed to save trip: ' + error.message, 'danger');
    } finally {
        TripPlanner.setLoading(submitButton, false);
    }
}

// Edit trip
async function editTrip(tripId) {
    try {
        // Ensure tripId is treated as string to avoid JavaScript number precision issues
        const tripIdStr = String(tripId);
        
        const trip = await TripPlanner.api.get(`/trips/${tripIdStr}`);
        
        editingTripId = tripIdStr;
        document.getElementById('modalTitle').textContent = 'Edit Trip';
        document.getElementById('submitButton').textContent = 'Update Trip';
        
        // Populate form
        populateForm(trip);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('tripModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading trip for edit:', error);
        TripPlanner.showAlert('Failed to load trip details: ' + error.message, 'danger');
    }
}

// Populate form with trip data
function populateForm(trip) {
    document.getElementById('name').value = trip.name || '';
    document.getElementById('status').value = trip.status || 'planning';
    document.getElementById('primary_destination').value = trip.primary_destination || '';
    document.getElementById('traveler_count').value = trip.traveler_count || 1;
    document.getElementById('budget').value = trip.budget || '';
    document.getElementById('currency').value = trip.currency || 'USD';
    document.getElementById('description').value = trip.description || '';
    document.getElementById('destinations').value = trip.destinations || '';
    document.getElementById('notes').value = trip.notes || '';
    
    // Convert dates back to local date format
    if (trip.start_date) {
        const startDate = new Date(trip.start_date);
        document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    }
    if (trip.end_date) {
        const endDate = new Date(trip.end_date);
        document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    }
}

// Delete trip
function deleteTrip(tripId) {
    const tripIdStr = String(tripId);
    const trip = currentTrips.find(t => String(t.id) === tripIdStr);
    const tripName = trip ? trip.name : 'this trip';
    
    TripPlanner.confirm(
        `Are you sure you want to delete "${tripName}"? This will also delete all associated bookings. This action cannot be undone.`,
        async () => {
            try {
                const response = await TripPlanner.api.delete(`/trips/${tripIdStr}`);
                TripPlanner.showAlert(response.message || 'Trip deleted successfully!', 'success');
                await loadTrips();
            } catch (error) {
                console.error('Error deleting trip:', error);
                TripPlanner.showAlert('Failed to delete trip: ' + error.message, 'danger');
            }
        }
    );
}

// View trip bookings
function viewTripBookings(tripId) {
    const tripIdStr = String(tripId);
    window.location.href = `/trips/${tripIdStr}/bookings`;
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