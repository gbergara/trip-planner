// Main JavaScript for Trip Planner

// Utility functions
const TripPlanner = {
    // Show floating alert messages
    showAlert: function(message, type = 'info', duration = 5000) {
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible alert-floating">
                <div class="d-flex align-items-center">
                    <i class="bi bi-${this.getAlertIcon(type)} me-2"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close" onclick="TripPlanner.hideAlert('${alertId}')"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        const alertElement = document.getElementById(alertId);
        
        // Show alert
        setTimeout(() => {
            alertElement.classList.add('show');
        }, 100);
        
        // Auto-hide alert
        setTimeout(() => {
            this.hideAlert(alertId);
        }, duration);
    },

    hideAlert: function(alertId) {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            alertElement.classList.remove('show');
            setTimeout(() => {
                alertElement.remove();
            }, 300);
        }
    },

    getAlertIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'primary': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    // Format date for display, using current language
    formatDate: function(dateString) {
        const date = new Date(dateString);
        // Use window.currentLanguage if set, else browser language, else fallback to 'en-US'
        const lang = window.currentLanguage || navigator.language || 'en-US';
        return date.toLocaleDateString(lang, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },

    // Format datetime for display
    formatDateTime: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Format price for display
    formatPrice: function(price, currency = 'USD') {
        if (!price) return '';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(price);
    },

    // Get booking type icon
    getBookingTypeIcon: function(type) {
        const icons = {
            'flight': 'airplane-engines',
            'accommodation': 'building',
            'car_rental': 'car-front',
            'activity': 'star',
            'restaurant': 'cup-hot',
            'other': 'bookmark'
        };
        return icons[type] || 'bookmark';
    },

    // Get booking type color class
    getBookingTypeColorClass: function(type) {
        const colors = {
            'flight': 'primary',
            'accommodation': 'success',
            'car_rental': 'warning',
            'activity': 'info',
            'restaurant': 'orange',
            'other': 'secondary'
        };
        return colors[type] || 'secondary';
    },

    // API helper functions
    api: {
        baseUrl: '/api',

        request: async function(url, options = {}) {
            const response = await fetch(`${this.baseUrl}${url}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMsg = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(errorMsg);
            }

            // Handle responses with no content (like 204 No Content)
            if (response.status === 204 || response.headers.get('content-length') === '0') {
                return null;
            }

            // Try to parse as JSON, but handle empty responses gracefully
            const text = await response.text();
            if (!text) {
                return null;
            }

            try {
                return JSON.parse(text);
            } catch (e) {
                console.warn('Response is not valid JSON:', text);
                return text;
            }
        },

        get: function(url) {
            return this.request(url);
        },

        post: function(url, data) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        put: function(url, data) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        delete: function(url) {
            return this.request(url, {
                method: 'DELETE'
            });
        }
    },

    // Confirmation dialog
    confirm: function(message, onConfirm, onCancel = null) {
        const confirmed = window.confirm(message);
        if (confirmed && onConfirm) {
            onConfirm();
        } else if (!confirmed && onCancel) {
            onCancel();
        }
    },

    // Loading state management
    setLoading: function(element, loading = true) {
        if (loading) {
            element.classList.add('loading');
            if (element.tagName === 'BUTTON') {
                element.disabled = true;
                element.dataset.originalText = element.innerHTML;
                element.innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i>Loading...';
            }
        } else {
            element.classList.remove('loading');
            if (element.tagName === 'BUTTON') {
                element.disabled = false;
                if (element.dataset.originalText) {
                    element.innerHTML = element.dataset.originalText;
                    delete element.dataset.originalText;
                }
            }
        }
    }
};

// Add CSS for spinning icon
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spin { animation: spin 1s linear infinite; }
`;
document.head.appendChild(style);

// Global error handler for uncaught API errors
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    TripPlanner.showAlert('An unexpected error occurred. Please try again.', 'danger');
});

// Make TripPlanner globally available
window.TripPlanner = TripPlanner; 