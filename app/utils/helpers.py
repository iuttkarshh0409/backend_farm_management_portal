"""Helper functions for common operations."""

import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify


def generate_otp(length=6):
    """Generate a random OTP."""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_secure_token(length=32):
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def is_otp_valid(created_at, validity_minutes=10):
    """Check if OTP is still valid based on creation time."""
    if not created_at:
        return False
    
    expiry_time = created_at + timedelta(minutes=validity_minutes)
    return datetime.utcnow() < expiry_time


def format_phone_number(phone):
    """Format phone number to standard format."""
    if not phone:
        return None
    
    # Remove all non-digits
    phone_digits = ''.join(filter(str.isdigit, phone))
    
    # Handle Indian numbers
    if len(phone_digits) == 10:
        return phone_digits
    elif len(phone_digits) == 13 and phone_digits.startswith('91'):
        return phone_digits[2:]  # Remove country code
    elif len(phone_digits) == 12 and phone_digits.startswith('0'):
        return phone_digits[1:]  # Remove leading zero
    
    return phone_digits


def create_response(success=True, message="", data=None, errors=None, status_code=200):
    """Create standardized API response."""
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if errors is not None:
        response['errors'] = errors
    
    return jsonify(response), status_code


def success_response(message="Success", data=None, status_code=200):
    """Create success response."""
    return create_response(True, message, data, None, status_code)


def error_response(message="Error", errors=None, status_code=400):
    """Create error response."""
    return create_response(False, message, None, errors, status_code)


def paginate_query(query, page=1, per_page=20, max_per_page=100):
    """Paginate SQLAlchemy query."""
    if per_page > max_per_page:
        per_page = max_per_page
    
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'has_next': page * per_page < total,
        'has_prev': page > 1
    }


def handle_db_error(func):
    """Decorator to handle database errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            from app import db
            db.session.rollback()
            return error_response(
                message="Database operation failed",
                errors=[str(e)],
                status_code=500
            )
    return wrapper


def log_user_activity(user_id, action, details=None):
    """Log user activity (placeholder for future implementation)."""
    # This will be implemented when we add activity logging
    print(f"User {user_id} performed: {action}")
    if details:
        print(f"Details: {details}")


def mask_sensitive_data(data, sensitive_fields=None):
    """Mask sensitive data in responses."""
    if sensitive_fields is None:
        sensitive_fields = ['password', 'password_hash', 'otp_code', 'token']
    
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if key in sensitive_fields:
                masked_data[key] = "***MASKED***"
            elif isinstance(value, (dict, list)):
                masked_data[key] = mask_sensitive_data(value, sensitive_fields)
            else:
                masked_data[key] = value
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_fields) for item in data]
    
    return data