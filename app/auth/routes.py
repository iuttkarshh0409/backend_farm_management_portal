"""Authentication routes."""

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.auth import bp
from app.models.user import User, UserStatus
from app.auth.utils import (
    authenticate_user, create_tokens, generate_and_store_otp, 
    verify_otp, clear_otp, verify_user_account, reset_user_password,
    get_user_profile_data, log_authentication_event
)
from app.utils.helpers import success_response, error_response, handle_db_error
from app.utils.validators import validate_email_format, validate_required_fields, validate_json_data
from app.utils.decorators import auth_required
from app import db


@bp.route('/login', methods=['POST'])
@handle_db_error
def login():
    """User login endpoint."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email', 'password'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    password = data['password']
    
    # Validate email format
    if not validate_email_format(email):
        return error_response("Invalid email format", status_code=400)
    
    # Authenticate user
    user, error_msg = authenticate_user(email, password)
    
    if not user:
        log_authentication_event(None, 'login_failed', False, request.remote_addr, request.user_agent.string)
        return error_response(error_msg, status_code=401)
    
    # Create tokens
    try:
        tokens = create_tokens(user)
        profile_data = get_user_profile_data(user)
        
        log_authentication_event(user, 'login_success', True, request.remote_addr, request.user_agent.string)
        
        return success_response(
            message="Login successful",
            data={
                'user': profile_data,
                'tokens': tokens
            }
        )
    
    except Exception as e:
        log_authentication_event(user, 'login_error', False, request.remote_addr, request.user_agent.string)
        return error_response("Token creation failed", errors=[str(e)], status_code=500)


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        
        # In a production app, you would add the token to a blacklist here
        # For now, we'll just log the logout event
        log_authentication_event(user, 'logout', True, request.remote_addr, request.user_agent.string)
        
        return success_response("Logged out successfully")
    
    except Exception as e:
        return error_response("Logout failed", errors=[str(e)], status_code=500)


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_active=True).first()
        
        if not user or not user.can_login():
            return error_response("Invalid user or user cannot login", status_code=401)
        
        # Create new access token
        from flask_jwt_extended import create_access_token
        
        additional_claims = {
            'user_type': user.user_type.value,
            'verified': user.is_verified(),
            'status': user.status.value
        }
        
        new_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        log_authentication_event(user, 'token_refresh', True, request.remote_addr, request.user_agent.string)
        
        return success_response(
            message="Token refreshed successfully",
            data={
                'access_token': new_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
        )
    
    except Exception as e:
        return error_response("Token refresh failed", errors=[str(e)], status_code=500)


@bp.route('/verify-otp', methods=['POST'])
@handle_db_error  
def verify_otp_endpoint():
    """Verify OTP for account verification."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email', 'otp'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    provided_otp = data['otp'].strip()
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    # Verify OTP
    valid, message = verify_otp(user, provided_otp)
    
    if not valid:
        return error_response(message, status_code=400)
    
    # Mark user as verified and clear OTP
    verification_type = data.get('type', 'both')  # email, phone, or both
    verify_user_account(user, verification_type)
    clear_otp(user)
    
    log_authentication_event(user, 'otp_verification', True, request.remote_addr, request.user_agent.string)
    
    return success_response("Account verified successfully")


@bp.route('/resend-otp', methods=['POST'])
@handle_db_error
def resend_otp():
    """Resend OTP for account verification."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    if user.is_verified():
        return error_response("User is already verified", status_code=400)
    
    # Generate and store new OTP
    try:
        otp_code = generate_and_store_otp(user)
        
        # In a real application, you would send the OTP via SMS/Email here
        # For development, we'll return it in the response
        response_data = {"message": "OTP sent successfully"}
        
        # Include OTP in response only in development mode
        if current_app.config.get('DEBUG', False):
            response_data['otp'] = otp_code  # Remove this in production
        
        log_authentication_event(user, 'otp_resent', True, request.remote_addr, request.user_agent.string)
        
        return success_response("OTP sent successfully", data=response_data)
    
    except Exception as e:
        return error_response("Failed to send OTP", errors=[str(e)], status_code=500)


@bp.route('/forgot-password', methods=['POST'])
@handle_db_error
def forgot_password():
    """Initiate password reset process."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return success_response("If the email exists, a reset code has been sent")
    
    # Generate and store OTP for password reset
    try:
        otp_code = generate_and_store_otp(user, 'password_reset')
        
        # In a real application, you would send the reset code via email here
        response_data = {"message": "Password reset code sent to your email"}
        
        # Include OTP in response only in development mode
        if current_app.config.get('DEBUG', False):
            response_data['reset_code'] = otp_code  # Remove this in production
        
        log_authentication_event(user, 'password_reset_requested', True, request.remote_addr, request.user_agent.string)
        
        return success_response("Password reset code sent", data=response_data)
    
    except Exception as e:
        return error_response("Failed to send reset code", errors=[str(e)], status_code=500)


@bp.route('/reset-password', methods=['POST'])
@handle_db_error
def reset_password():
    """Reset password using OTP."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email', 'reset_code', 'new_password'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    reset_code = data['reset_code'].strip()
    new_password = data['new_password']
    
    # Validate password strength
    from app.utils.validators import validate_password_strength
    is_strong, errors = validate_password_strength(new_password)
    if not is_strong:
        return error_response("Password does not meet requirements", errors=errors, status_code=400)
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return error_response("Invalid reset code", status_code=400)
    
    # Verify reset code (OTP)
    valid, message = verify_otp(user, reset_code, validity_minutes=30)  # 30 minutes for password reset
    
    if not valid:
        return error_response(message, status_code=400)
    
    # Reset password
    success = reset_user_password(user, new_password)
    if not success:
        return error_response("Failed to reset password", status_code=500)
    
    # Clear OTP
    clear_otp(user)
    
    log_authentication_event(user, 'password_reset_success', True, request.remote_addr, request.user_agent.string)
    
    return success_response("Password reset successfully")


@bp.route('/change-password', methods=['POST'])
@auth_required
@handle_db_error
def change_password(current_user):
    """Change password for authenticated user."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['current_password', 'new_password'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Verify current password
    if not current_user.check_password(current_password):
        return error_response("Current password is incorrect", status_code=400)
    
    # Validate new password strength
    from app.utils.validators import validate_password_strength
    is_strong, errors = validate_password_strength(new_password)
    if not is_strong:
        return error_response("New password does not meet requirements", errors=errors, status_code=400)
    
    # Check if new password is different from current
    if current_user.check_password(new_password):
        return error_response("New password must be different from current password", status_code=400)
    
    # Change password
    success = reset_user_password(current_user, new_password)
    if not success:
        return error_response("Failed to change password", status_code=500)
    
    log_authentication_event(current_user, 'password_change', True, request.remote_addr, request.user_agent.string)
    
    return success_response("Password changed successfully")


@bp.route('/profile', methods=['GET'])
@auth_required
def get_profile(current_user):
    """Get current user profile."""
    try:
        profile_data = get_user_profile_data(current_user)
        return success_response("Profile retrieved successfully", data=profile_data)
    
    except Exception as e:
        return error_response("Failed to retrieve profile", errors=[str(e)], status_code=500)


@bp.route('/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate JWT token."""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user or not user.can_login():
            return error_response("Invalid token or user", status_code=401)
        
        return success_response("Token is valid", data={
            'user_id': user_id,
            'user_type': claims.get('user_type'),
            'verified': claims.get('verified'),
            'status': claims.get('status')
        })
    
    except Exception as e:
        return error_response("Token validation failed")