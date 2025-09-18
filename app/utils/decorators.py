"""Authentication and authorization decorators."""

from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.user import User, UserRole, UserStatus
from app.utils.helpers import error_response


def auth_required(f):
    """Require valid JWT authentication."""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.filter_by(id=current_user_id, is_active=True).first()
            
            if not current_user:
                return error_response("User not found or inactive", status_code=401)
            
            if not current_user.can_login():
                return error_response("User account is not active or not verified", status_code=403)
            
            # Make current user available in the request context
            kwargs['current_user'] = current_user
            return f(*args, **kwargs)
            
        except Exception as e:
            return error_response("Authentication failed", errors=[str(e)], status_code=401)
    
    return decorated_function


def role_required(*allowed_roles):
    """Require specific user roles."""
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated_function(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                return error_response("Authentication required", status_code=401)
            
            if current_user.user_type not in allowed_roles:
                return error_response(
                    f"Access denied. Required roles: {[role.value for role in allowed_roles]}", 
                    status_code=403
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Require admin role."""
    @wraps(f)
    @role_required(UserRole.ADMIN)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def vet_required(f):
    """Require veterinarian role."""
    @wraps(f)
    @role_required(UserRole.VETERINARIAN)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def farmer_required(f):
    """Require farmer role."""
    @wraps(f)
    @role_required(UserRole.FARMER)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def vet_or_admin_required(f):
    """Require veterinarian or admin role."""
    @wraps(f)
    @role_required(UserRole.VETERINARIAN, UserRole.ADMIN)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def verified_user_required(f):
    """Require user to be verified (email and phone)."""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if not current_user.is_verified():
            return error_response(
                "Account verification required. Please verify your email and phone number.", 
                status_code=403
            )
        
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """Require user account to be active."""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if current_user.status != UserStatus.ACTIVE:
            status_messages = {
                UserStatus.PENDING: "Account is pending approval",
                UserStatus.INACTIVE: "Account is inactive", 
                UserStatus.SUSPENDED: "Account is suspended"
            }
            message = status_messages.get(current_user.status, "Account is not active")
            
            return error_response(message, status_code=403)
        
        return f(*args, **kwargs)
    return decorated_function


def same_user_or_admin_required(f):
    """Allow access to same user or admin."""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get('current_user')
        user_id = kwargs.get('user_id') or kwargs.get('id')
        
        # Admin can access any user
        if current_user.user_type == UserRole.ADMIN:
            return f(*args, **kwargs)
        
        # User can only access their own data
        if str(current_user.id) != str(user_id):
            return error_response("Access denied. You can only access your own data.", status_code=403)
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_by_user(f):
    """Rate limit by user ID (placeholder for future implementation)."""
    @wraps(f)
    @auth_required
    def decorated_function(*args, **kwargs):
        # This is a placeholder - actual rate limiting would be implemented here
        # For now, we'll just pass through
        return f(*args, **kwargs)
    return decorated_function


def log_api_access(f):
    """Log API access (placeholder for future implementation)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log API access
        try:
            current_user_id = get_jwt_identity() if get_jwt_identity() else 'anonymous'
            endpoint = f.__name__
            current_app.logger.info(f"API Access: {endpoint} by user {current_user_id}")
        except:
            pass  # Don't fail if logging fails
        
        return f(*args, **kwargs)
    return decorated_function