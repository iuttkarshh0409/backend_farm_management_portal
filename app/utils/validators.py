"""Input validation functions."""

import re
from email_validator import validate_email, EmailNotValidError
from app.models.user import UserRole


def validate_email_format(email):
    """Validate email format."""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_phone_number(phone):
    """Validate Indian phone number format."""
    # Indian phone number: 10 digits, starting with 6-9
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_password_strength(password):
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def validate_aadhar_number(aadhar):
    """Validate Aadhar number format."""
    if not aadhar:
        return True  # Optional field
    
    # Remove spaces and check if 12 digits
    aadhar_clean = re.sub(r'\s+', '', aadhar)
    pattern = r'^\d{12}$'
    return bool(re.match(pattern, aadhar_clean))


def validate_user_role(role):
    """Validate user role."""
    if isinstance(role, str):
        try:
            UserRole(role)
            return True
        except ValueError:
            return False
    return isinstance(role, UserRole)


def validate_required_fields(data, required_fields):
    """Validate required fields in request data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == '':
            missing_fields.append(field)
    return len(missing_fields) == 0, missing_fields


def sanitize_string(value, max_length=None):
    """Sanitize string input."""
    if not isinstance(value, str):
        return str(value)
    
    # Strip whitespace
    value = value.strip()
    
    # Remove potential XSS characters
    value = re.sub(r'[<>\"\'&]', '', value)
    
    # Truncate if max_length specified
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_json_data(data, schema):
    """Validate JSON data against schema."""
    errors = []
    
    for field, rules in schema.items():
        value = data.get(field)
        
        # Required field check
        if rules.get('required', False) and not value:
            errors.append(f"{field} is required")
            continue
        
        # Skip validation if field is optional and empty
        if not rules.get('required', False) and not value:
            continue
        
        # Type validation
        expected_type = rules.get('type')
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"{field} must be of type {expected_type.__name__}")
            continue
        
        # Length validation
        min_length = rules.get('min_length')
        max_length = rules.get('max_length')
        
        if isinstance(value, str):
            if min_length and len(value) < min_length:
                errors.append(f"{field} must be at least {min_length} characters")
            if max_length and len(value) > max_length:
                errors.append(f"{field} must be at most {max_length} characters")
        
        # Custom validator
        validator = rules.get('validator')
        if validator and not validator(value):
            message = rules.get('message', f"{field} is invalid")
            errors.append(message)
    
    return len(errors) == 0, errors