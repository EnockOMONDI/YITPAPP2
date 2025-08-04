"""
Timezone utilities for YITP Learning Management System
Handles timezone-aware datetime display and conversion
"""

from django.utils import timezone
from django.conf import settings
import pytz
from datetime import datetime
import json


def get_user_timezone_from_request(request):
    """
    Get user's timezone from request session or headers
    Returns timezone string or None if not available
    """
    # Try to get timezone from session (set by JavaScript)
    user_timezone = request.session.get('user_timezone')
    if user_timezone:
        try:
            # Validate timezone
            pytz.timezone(user_timezone)
            return user_timezone
        except pytz.exceptions.UnknownTimeZoneError:
            pass
    
    # Fallback to default timezone
    return None


def convert_to_user_timezone(dt, user_timezone_str=None):
    """
    Convert datetime to user's timezone
    
    Args:
        dt: datetime object (timezone-aware)
        user_timezone_str: timezone string (e.g., 'America/New_York')
    
    Returns:
        datetime object in user's timezone
    """
    if not dt:
        return dt
    
    # Ensure datetime is timezone-aware
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    
    # If no user timezone provided, return as-is
    if not user_timezone_str:
        return dt
    
    try:
        user_tz = pytz.timezone(user_timezone_str)
        return dt.astimezone(user_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return dt


def format_datetime_for_display(dt, user_timezone_str=None, format_string=None):
    """
    Format datetime for display in user's timezone
    
    Args:
        dt: datetime object
        user_timezone_str: user's timezone string
        format_string: custom format string
    
    Returns:
        formatted datetime string
    """
    if not dt:
        return ''
    
    # Convert to user timezone
    local_dt = convert_to_user_timezone(dt, user_timezone_str)
    
    # Default format for YITP (matches existing timeline format)
    if not format_string:
        format_string = '%b %d, %Y at %I:%M %p'
    
    return local_dt.strftime(format_string)


def get_timezone_offset_minutes(timezone_str):
    """
    Get timezone offset in minutes from UTC
    
    Args:
        timezone_str: timezone string (e.g., 'America/New_York')
    
    Returns:
        offset in minutes (positive for east of UTC, negative for west)
    """
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        offset = now.utcoffset()
        return int(offset.total_seconds() / 60)
    except (pytz.exceptions.UnknownTimeZoneError, AttributeError):
        return 0


def get_common_timezones():
    """
    Get list of common timezones for YITP users
    
    Returns:
        dict of timezone groups
    """
    return {
        'africa': {
            'name': 'Africa',
            'timezones': [
                ('Africa/Nairobi', 'Nairobi, Kenya (EAT)'),
                ('Africa/Lagos', 'Lagos, Nigeria (WAT)'),
                ('Africa/Cairo', 'Cairo, Egypt (EET)'),
                ('Africa/Johannesburg', 'Johannesburg, South Africa (SAST)'),
                ('Africa/Casablanca', 'Casablanca, Morocco (WET)'),
                ('Africa/Addis_Ababa', 'Addis Ababa, Ethiopia (EAT)'),
                ('Africa/Accra', 'Accra, Ghana (GMT)'),
                ('Africa/Kigali', 'Kigali, Rwanda (CAT)'),
                ('Africa/Kampala', 'Kampala, Uganda (EAT)'),
                ('Africa/Dar_es_Salaam', 'Dar es Salaam, Tanzania (EAT)'),
            ]
        },
        'usa': {
            'name': 'United States',
            'timezones': [
                ('America/New_York', 'Eastern Time (EST/EDT)'),
                ('America/Chicago', 'Central Time (CST/CDT)'),
                ('America/Denver', 'Mountain Time (MST/MDT)'),
                ('America/Los_Angeles', 'Pacific Time (PST/PDT)'),
                ('America/Phoenix', 'Arizona (MST)'),
                ('America/Anchorage', 'Alaska (AKST/AKDT)'),
                ('Pacific/Honolulu', 'Hawaii (HST)'),
            ]
        },
        'other': {
            'name': 'Other Regions',
            'timezones': [
                ('UTC', 'UTC (Coordinated Universal Time)'),
                ('Europe/London', 'London, UK (GMT/BST)'),
                ('Europe/Paris', 'Paris, France (CET/CEST)'),
                ('Asia/Dubai', 'Dubai, UAE (GST)'),
                ('Asia/Kolkata', 'India (IST)'),
                ('Australia/Sydney', 'Sydney, Australia (AEST/AEDT)'),
            ]
        }
    }


def create_timezone_context(request):
    """
    Create timezone context for templates
    
    Args:
        request: Django request object
    
    Returns:
        dict with timezone information
    """
    user_timezone = get_user_timezone_from_request(request)
    
    return {
        'user_timezone': user_timezone,
        'server_timezone': str(timezone.get_current_timezone()),
        'timezone_offset': get_timezone_offset_minutes(user_timezone) if user_timezone else 0,
        'common_timezones': get_common_timezones(),
    }


class TimezoneMiddleware:
    """
    Middleware to handle timezone detection and session management
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if timezone is being set via POST
        if request.method == 'POST' and 'user_timezone' in request.POST:
            timezone_str = request.POST.get('user_timezone')
            try:
                # Validate timezone
                pytz.timezone(timezone_str)
                request.session['user_timezone'] = timezone_str
            except pytz.exceptions.UnknownTimeZoneError:
                pass
        
        response = self.get_response(request)
        return response


def get_timezone_aware_now():
    """
    Get current datetime in server timezone (timezone-aware)
    
    Returns:
        timezone-aware datetime object
    """
    return timezone.now()


def parse_datetime_with_timezone(date_string, timezone_str=None):
    """
    Parse datetime string and make it timezone-aware
    
    Args:
        date_string: datetime string to parse
        timezone_str: timezone to apply (defaults to server timezone)
    
    Returns:
        timezone-aware datetime object
    """
    try:
        # Parse the datetime string
        dt = datetime.strptime(date_string, '%Y-%m-%d')
        
        # Make it timezone-aware
        if timezone_str:
            tz = pytz.timezone(timezone_str)
            dt = tz.localize(dt)
        else:
            dt = timezone.make_aware(dt)
        
        return dt
    except (ValueError, pytz.exceptions.UnknownTimeZoneError):
        return None
