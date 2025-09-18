"""User management API endpoints."""

from flask import request, jsonify
from app.api import bp
from app.models.user import User, Farmer, Veterinarian, Admin, UserRole, UserStatus
from app.services.user_service import UserService
from app.services.otp_service import OTPService
from app.utils.decorators import auth_required, admin_required, role_required
from app.utils.helpers import success_response, error_response, handle_db_error, paginate_query
from app.utils.validators import validate_required_fields, validate_json_data
from app import db


@bp.route('/users/register/farmer', methods=['POST'])
@handle_db_error
def register_farmer():
    """Register a new farmer."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Create farmer using service
    farmer, error_msg = UserService.create_farmer(data)
    
    if not farmer:
        return error_response(error_msg, status_code=400)
    
    # Initiate verification process
    verification_success, verification_msg, otp = UserService.initiate_user_verification(farmer)
    
    response_data = {
        'user': farmer.to_dict(),
        'verification_initiated': verification_success,
        'verification_message': verification_msg
    }
    
    # Include OTP in response for development mode
    if request.environ.get('FLASK_DEBUG') and otp:
        response_data['otp'] = otp
    
    return success_response(
        message="Farmer registered successfully. Please verify your account.",
        data=response_data,
        status_code=201
    )


@bp.route('/users/register/veterinarian', methods=['POST'])
@handle_db_error
def register_veterinarian():
    """Register a new veterinarian."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Create veterinarian using service
    vet, error_msg = UserService.create_veterinarian(data)
    
    if not vet:
        return error_response(error_msg, status_code=400)
    
    # Initiate verification process
    verification_success, verification_msg, otp = UserService.initiate_user_verification(vet)
    
    response_data = {
        'user': vet.to_dict(),
        'verification_initiated': verification_success,
        'verification_message': verification_msg,
        'note': 'Veterinarian accounts require admin approval after verification.'
    }
    
    # Include OTP in response for development mode
    if request.environ.get('FLASK_DEBUG') and otp:
        response_data['otp'] = otp
    
    return success_response(
        message="Veterinarian registered successfully. Please verify your account and wait for admin approval.",
        data=response_data,
        status_code=201
    )


@bp.route('/users/register/admin', methods=['POST'])
@admin_required
@handle_db_error
def register_admin(current_user):
    """Register a new admin (admin only)."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Create admin using service
    admin, error_msg = UserService.create_admin(data, current_user.id)
    
    if not admin:
        return error_response(error_msg, status_code=400)
    
    return success_response(
        message="Admin created successfully",
        data={'user': admin.to_dict()},
        status_code=201
    )


@bp.route('/users/verify', methods=['POST'])
@handle_db_error
def verify_user():
    """Verify user account with OTP."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email', 'otp'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    otp_code = data['otp'].strip()
    verification_type = data.get('type', 'both')  # email, phone, or both
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    # Verify account
    success, message = UserService.verify_user_account(user, otp_code, verification_type)
    
    if success:
        return success_response(message, data={'user': user.to_dict()})
    else:
        return error_response(message, status_code=400)


@bp.route('/users/resend-verification', methods=['POST'])
@handle_db_error
def resend_verification():
    """Resend verification OTP."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['email'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    email = data['email'].lower().strip()
    verification_type = data.get('type', 'both')
    
    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    if user.is_verified():
        return error_response("User is already verified", status_code=400)
    
    # Resend verification
    success, message, otp = UserService.initiate_user_verification(user, verification_type)
    
    response_data = {'verification_message': message}
    
    # Include OTP in response for development mode
    if request.environ.get('FLASK_DEBUG') and otp:
        response_data['otp'] = otp
    
    if success:
        return success_response("Verification code sent", data=response_data)
    else:
        return error_response(message, status_code=500)


@bp.route('/users/<user_id>', methods=['GET'])
@auth_required
def get_user(current_user, user_id):
    """Get user details by ID."""
    # Users can only view their own profile, admins can view any
    if current_user.user_type != UserRole.ADMIN and str(current_user.id) != user_id:
        return error_response("Access denied", status_code=403)
    
    user = User.query.filter_by(id=user_id, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    return success_response("User retrieved successfully", data=user.to_dict())


@bp.route('/users', methods=['GET'])
@admin_required
def list_users(current_user):
    """List all users (admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_type = request.args.get('type')
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = User.query.filter_by(is_active=True)
    
    # Filter by user type
    if user_type and user_type in ['farmer', 'veterinarian', 'admin']:
        query = query.filter_by(user_type=UserRole(user_type))
    
    # Filter by status
    if status and status in ['active', 'inactive', 'pending', 'suspended']:
        query = query.filter_by(status=UserStatus(status))
    
    # Search by name or email
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_term)) | (User.email.ilike(search_term))
        )
    
    # Order by creation date
    query = query.order_by(User.created_at.desc())
    
    # Paginate results
    pagination = paginate_query(query, page, per_page)
    
    return success_response(
        "Users retrieved successfully",
        data={
            'users': [user.to_dict() for user in pagination['items']],
            'pagination': {
                'page': pagination['page'],
                'per_page': pagination['per_page'],
                'total': pagination['total'],
                'pages': pagination['pages'],
                'has_next': pagination['has_next'],
                'has_prev': pagination['has_prev']
            }
        }
    )


@bp.route('/users/<user_id>/profile', methods=['PUT'])
@auth_required
def update_user_profile(current_user, user_id):
    """Update user profile."""
    # Users can only update their own profile, admins can update any
    if current_user.user_type != UserRole.ADMIN and str(current_user.id) != user_id:
        return error_response("Access denied", status_code=403)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    user = User.query.filter_by(id=user_id, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    # Update profile using service
    success, message = UserService.update_user_profile(user, data)
    
    if success:
        return success_response(message, data=user.to_dict())
    else:
        return error_response(message, status_code=400)


@bp.route('/users/<user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(current_user, user_id):
    """Update user status (admin only)."""
    data = request.get_json()
    if not data:
        return error_response("No data provided", status_code=400)
    
    # Validate required fields
    valid, missing = validate_required_fields(data, ['status'])
    if not valid:
        return error_response("Missing required fields", errors=missing, status_code=400)
    
    new_status = data['status']
    reason = data.get('reason', '')
    
    # Validate status
    if new_status not in ['active', 'inactive', 'pending', 'suspended']:
        return error_response("Invalid status", status_code=400)
    
    user = User.query.filter_by(id=user_id, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    # Update status
    try:
        user.status = UserStatus(new_status)
        if new_status == 'inactive':
            user.is_active = False
        elif new_status in ['active', 'pending']:
            user.is_active = True
        
        db.session.commit()
        
        return success_response(
            f"User status updated to {new_status}",
            data={'user': user.to_dict(), 'reason': reason}
        )
    
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update status: {str(e)}", status_code=500)


@bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Soft delete user (admin only)."""
    user = User.query.filter_by(id=user_id, is_active=True).first()
    if not user:
        return error_response("User not found", status_code=404)
    
    # Don't allow deletion of other admins
    if user.user_type == UserRole.ADMIN and str(user.id) != str(current_user.id):
        return error_response("Cannot delete other admin users", status_code=403)
    
    try:
        # Soft delete
        success, message = UserService.deactivate_user(user, "Deleted by admin")
        
        if success:
            return success_response("User deleted successfully")
        else:
            return error_response(message, status_code=500)
    
    except Exception as e:
        return error_response(f"Failed to delete user: {str(e)}", status_code=500)


@bp.route('/users/stats', methods=['GET'])
@admin_required
def get_user_stats(current_user):
    """Get user statistics (admin only)."""
    try:
        stats = {
            'total_users': User.query.filter_by(is_active=True).count(),
            'active_users': User.query.filter_by(is_active=True, status=UserStatus.ACTIVE).count(),
            'pending_users': User.query.filter_by(is_active=True, status=UserStatus.PENDING).count(),
            'farmers': User.query.filter_by(is_active=True, user_type=UserRole.FARMER).count(),
            'veterinarians': User.query.filter_by(is_active=True, user_type=UserRole.VETERINARIAN).count(),
            'admins': User.query.filter_by(is_active=True, user_type=UserRole.ADMIN).count(),
            'verified_users': User.query.filter_by(
                is_active=True, 
                email_verified=True, 
                phone_verified=True
            ).count()
        }
        
        return success_response("User statistics retrieved successfully", data=stats)
    
    except Exception as e:
        return error_response(f"Failed to get statistics: {str(e)}", status_code=500)