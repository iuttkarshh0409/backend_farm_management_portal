"""Authentication utility functions."""

from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models.user import User
from app.utils.helpers import generate_otp, is_otp_valid
from app import db


def create_tokens(user):
    """Create access and refresh tokens for user."""
    # Create token identity with user ID and role
    identity = {
        'user_id': str(user.id),
        'user_type': user.user_type.value,
        'email': user.email
    }
    
    # Additional claims
    additional_claims = {
        'user_type': user.user_type.value,
        'verified': user.is_verified(),
        'status': user.status.value
    }
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
    }


def authenticate_user(email, password):
    """Authenticate user with email and password."""
    if not email or not password:
        return None, "Email and password are required"
    
    user = User.query.filter_by(email=email.lower(), is_active=True).first()
    
    if not user:
        return None, "Invalid email or password"
    
    if not user.check_password(password):
        return None, "Invalid email or password"
    
    if not user.can_login():
        if user.status.value == 'pending':
            return None, "Account is pending verification"
        elif user.status.value == 'inactive':
            return None, "Account is inactive"
        elif user.status.value == 'suspended':
            return None, "Account is suspended"
        else:
            return None, "Account verification required"
    
    return user, None


def generate_and_store_otp(user, purpose='verification'):
    """Generate and store OTP for user."""
    otp_code = generate_otp(6)
    
    # Store OTP in user record
    user.otp_code = otp_code
    user.otp_created_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return otp_code
    except Exception as e:
        db.session.rollback()
        raise e


def verify_otp(user, provided_otp, validity_minutes=10):
    """Verify OTP for user."""
    if not user.otp_code or not user.otp_created_at:
        return False, "No OTP found for this user"
    
    if user.otp_code != provided_otp:
        return False, "Invalid OTP"
    
    if not is_otp_valid(user.otp_created_at, validity_minutes):
        return False, "OTP has expired"
    
    return True, "OTP verified successfully"


def clear_otp(user):
    """Clear OTP from user record."""
    user.otp_code = None
    user.otp_created_at = None
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def verify_user_account(user, verification_type='both'):
    """Mark user account as verified."""
    if verification_type in ['email', 'both']:
        user.email_verified = True
    
    if verification_type in ['phone', 'both']:
        user.phone_verified = True
    
    # Activate user if both email and phone are verified
    if user.email_verified and user.phone_verified:
        user.status = user.status.__class__.ACTIVE
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def reset_user_password(user, new_password):
    """Reset user password."""
    user.set_password(new_password)
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def check_user_permissions(user, required_permissions):
    """Check if user has required permissions."""
    if user.user_type.value == 'admin':
        # Check admin permissions
        from app.models.user import Admin
        admin = Admin.query.filter_by(id=user.id).first()
        if admin:
            for permission in required_permissions:
                if not admin.has_permission(permission):
                    return False
            return True
    
    # For non-admin users, basic role-based permissions
    role_permissions = {
        'farmer': ['view_own_animals', 'update_own_profile', 'view_own_treatments'],
        'veterinarian': ['view_assigned_animals', 'create_treatments', 'update_animal_health', 'view_farmer_contacts'],
        'admin': ['all']  # Admins have all permissions by default
    }
    
    user_permissions = role_permissions.get(user.user_type.value, [])
    
    for permission in required_permissions:
        if permission not in user_permissions and 'all' not in user_permissions:
            return False
    
    return True


def get_user_profile_data(user):
    """Get user profile data for token payload."""
    profile_data = {
        'id': str(user.id),
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'user_type': user.user_type.value,
        'status': user.status.value,
        'verified': user.is_verified(),
        'created_at': user.created_at.isoformat()
    }
    
    # Add role-specific data
    if user.user_type.value == 'farmer':
        from app.models.user import Farmer
        farmer = Farmer.query.filter_by(id=user.id).first()
        if farmer:
            profile_data.update({
                'farm_name': farmer.farm_name,
                'farm_type': farmer.farm_type,
                'district': farmer.district,
                'state': farmer.state
            })
    
    elif user.user_type.value == 'veterinarian':
        from app.models.user import Veterinarian
        vet = Veterinarian.query.filter_by(id=user.id).first()
        if vet:
            profile_data.update({
                'license_no': vet.license_no,
                'specialization': vet.specialization,
                'clinic_name': vet.clinic_name
            })
    
    elif user.user_type.value == 'admin':
        from app.models.user import Admin
        admin = Admin.query.filter_by(id=user.id).first()
        if admin:
            profile_data.update({
                'employee_id': admin.employee_id,
                'department': admin.department,
                'designation': admin.designation
            })
    
    return profile_data


def log_authentication_event(user, event_type, success=True, ip_address=None, user_agent=None):
    """Log authentication events (placeholder for future implementation)."""
    # This would typically log to a security audit table
    event_data = {
        'user_id': str(user.id) if user else None,
        'event_type': event_type,  # login, logout, token_refresh, password_change, etc.
        'success': success,
        'timestamp': datetime.utcnow(),
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    # For now, just log to application logs
    current_app.logger.info(f"Auth Event: {event_type} for user {user.email if user else 'unknown'} - {'Success' if success else 'Failed'}")