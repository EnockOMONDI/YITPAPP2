/**
 * YITP Timezone Handler
 * Handles automatic timezone detection and datetime conversion
 */

class YITPTimezoneHandler {
    constructor() {
        this.userTimezone = null;
        this.serverTimezone = 'Africa/Nairobi'; // Default server timezone
        this.init();
    }

    /**
     * Initialize timezone handler
     */
    init() {
        this.detectUserTimezone();
        this.sendTimezoneToServer();
        this.convertAllTimestamps();
        this.setupTimezoneChangeListener();
    }

    /**
     * Detect user's timezone using browser API
     */
    detectUserTimezone() {
        try {
            // Use Intl API to detect timezone
            this.userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            console.log('Detected user timezone:', this.userTimezone);
        } catch (error) {
            console.warn('Could not detect timezone, using fallback:', error);
            this.userTimezone = 'UTC'; // Fallback to UTC
        }
    }

    /**
     * Send detected timezone to server via AJAX
     */
    sendTimezoneToServer() {
        if (!this.userTimezone) return;

        // Check if timezone is already stored in session
        const storedTimezone = this.getCookie('user_timezone');
        if (storedTimezone === this.userTimezone) {
            return; // Already stored, no need to send again
        }

        // Send timezone to server
        fetch('/set-timezone/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: `user_timezone=${encodeURIComponent(this.userTimezone)}`
        }).then(response => {
            if (response.ok) {
                this.setCookie('user_timezone', this.userTimezone, 30); // Store for 30 days
                console.log('Timezone sent to server successfully');
            }
        }).catch(error => {
            console.warn('Failed to send timezone to server:', error);
        });
    }

    /**
     * Convert all timestamps on the page to user's local timezone
     */
    convertAllTimestamps() {
        // Find all elements with data-utc-time attribute
        const timestampElements = document.querySelectorAll('[data-utc-time]');
        
        timestampElements.forEach(element => {
            this.convertTimestamp(element);
        });

        // Also convert any elements with specific classes
        const timelineElements = document.querySelectorAll('.timeline-date, .update-date, .commit-date');
        timelineElements.forEach(element => {
            this.convertTimestampFromText(element);
        });
    }

    /**
     * Convert individual timestamp element
     */
    convertTimestamp(element) {
        const utcTime = element.getAttribute('data-utc-time');
        const format = element.getAttribute('data-format') || 'default';
        
        if (!utcTime) return;

        try {
            const utcDate = new Date(utcTime);
            const localTime = this.formatDateForTimezone(utcDate, format);
            
            // Update element content
            element.textContent = localTime;
            
            // Add timezone indicator
            element.setAttribute('title', `Your local time (${this.userTimezone})`);
            
        } catch (error) {
            console.warn('Failed to convert timestamp:', error);
        }
    }

    /**
     * Convert timestamp from text content (for existing elements)
     */
    convertTimestampFromText(element) {
        const text = element.textContent.trim();
        
        // Try to parse existing date formats
        const datePatterns = [
            /(\w{3} \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M)/g,
            /(\d{4}-\d{2}-\d{2})/g,
            /(\w{3} \d{1,2}, \d{4})/g
        ];

        for (const pattern of datePatterns) {
            const match = text.match(pattern);
            if (match) {
                try {
                    const parsedDate = new Date(match[1]);
                    if (!isNaN(parsedDate.getTime())) {
                        const localTime = this.formatDateForTimezone(parsedDate, 'timeline');
                        element.textContent = text.replace(match[1], localTime);
                        element.setAttribute('title', `Your local time (${this.userTimezone})`);
                        break;
                    }
                } catch (error) {
                    console.warn('Failed to parse date:', match[1], error);
                }
            }
        }
    }

    /**
     * Format date for specific timezone
     */
    formatDateForTimezone(date, format = 'default') {
        if (!this.userTimezone) return date.toLocaleString();

        const options = this.getFormatOptions(format);
        
        try {
            return new Intl.DateTimeFormat('en-US', {
                ...options,
                timeZone: this.userTimezone
            }).format(date);
        } catch (error) {
            console.warn('Failed to format date for timezone:', error);
            return date.toLocaleString();
        }
    }

    /**
     * Get format options based on format type
     */
    getFormatOptions(format) {
        const formats = {
            'timeline': {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            },
            'short': {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            },
            'long': {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            },
            'time': {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            },
            'default': {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            }
        };

        return formats[format] || formats['default'];
    }

    /**
     * Setup listener for timezone changes (if user manually changes timezone)
     */
    setupTimezoneChangeListener() {
        // Listen for timezone selector changes (if implemented)
        const timezoneSelector = document.getElementById('timezone-selector');
        if (timezoneSelector) {
            timezoneSelector.addEventListener('change', (event) => {
                this.userTimezone = event.target.value;
                this.sendTimezoneToServer();
                this.convertAllTimestamps();
            });
        }
    }

    /**
     * Get CSRF token for AJAX requests
     */
    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            return csrfToken.value;
        }
        
        // Try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        return '';
    }

    /**
     * Set cookie
     */
    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }

    /**
     * Get cookie value
     */
    getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [cookieName, cookieValue] = cookie.trim().split('=');
            if (cookieName === name) {
                return cookieValue;
            }
        }
        return null;
    }

    /**
     * Get user's current timezone
     */
    getUserTimezone() {
        return this.userTimezone;
    }

    /**
     * Get timezone offset in minutes
     */
    getTimezoneOffset() {
        try {
            const now = new Date();
            return -now.getTimezoneOffset(); // Negative because getTimezoneOffset returns opposite
        } catch (error) {
            return 0;
        }
    }

    /**
     * Convert UTC timestamp to local time string
     */
    static convertUTCToLocal(utcTimestamp, format = 'timeline') {
        try {
            const date = new Date(utcTimestamp);
            const handler = new YITPTimezoneHandler();
            return handler.formatDateForTimezone(date, format);
        } catch (error) {
            console.warn('Failed to convert UTC to local:', error);
            return utcTimestamp;
        }
    }
}

// Initialize timezone handler when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.yitpTimezone = new YITPTimezoneHandler();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YITPTimezoneHandler;
}
