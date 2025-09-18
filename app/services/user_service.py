"""User management service."""

from flask import current_app
from app.models.user import User, Farmer, Veterinarian, Admin, UserRole, UserStatus
from app.services.otp_service import OTPService, SMSService, EmailService
from app.utils.validators import (
    validate_email_format, validate_phone_number, validate_password_strength,
    validate_aadhar_number, validate_required_fields
)
from app.utils.helpers import format_phone_number
from app import db
import uuid


class UserService:
    """Service for user management operations."""
    
    @staticmethod
    def create_farmer(user_data):
        """Create a new farmer user."""
        try:
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'password']
            valid, missing = validate_required_fields(user_data, required_fields)
            if not valid:
                return None, f"Missing required fields: {', '.join(missing)}"
            
            # Validate email format
            if not validate_email_format(user_data['email']):
                return None, "Invalid email format"
            
            # Validate phone number
            formatted_phone = format_phone_number(user_data['phone'])
            if not validate_phone_number(formatted_phone):
                return None, "Invalid phone number format"
            
            # Validate password strength
            is_strong, errors = validate_password_strength(user_data['password'])
            if not is_strong:
                return None, f"Password requirements not met: {'; '.join(errors)}"
            
            # Validate Aadhar if provided
            if user_data.get('aadhar_no') and not validate_aadhar_number(user_data['aadhar_no']):
                return None, "Invalid Aadhar number format"
            
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data['email'].lower()) | 
                (User.phone == formatted_phone)
            ).first()
            
            if existing_user:
                return None, "User with this email or phone already exists"
            
            # Create farmer
            farmer = Farmer(
                name=user_data['name'].strip(),
                email=user_data['email'].lower().strip(),
                phone=formatted_phone,
                user_type=UserRole.FARMER,
                status=UserStatus.PENDING,
                aadhar_no=user_data.get('aadhar_no'),
                farm_name=user_data.get('farm_name'),
                farm_size=user_data.get('farm_size'),
                farm_type=user_data.get('farm_type'),
                district=user_data.get('district'),
                state=user_data.get('state'),
                pincode=user_data.get('pincode'),
                address=user_data.get('address')
            )
            
            farmer.set_password(user_data['password'])
            
            db.session.add(farmer)
            db.session.commit()
            
            current_app.logger.info(f"Farmer created: {farmer.email}")
            return farmer, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create farmer: {str(e)}")
            return None, f"Failed to create farmer: {str(e)}"
    
    @staticmethod
    def create_veterinarian(user_data):
        """Create a new veterinarian user."""
        try:
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'password', 'license_no']
            valid, missing = validate_required_fields(user_data, required_fields)
            if not valid:
                return None, f"Missing required fields: {', '.join(missing)}"
            
            # Validate email format
            if not validate_email_format(user_data['email']):
                return None, "Invalid email format"
            
            # Validate phone number
            formatted_phone = format_phone_number(user_data['phone'])
            if not validate_phone_number(formatted_phone):
                return None, "Invalid phone number format"
            
            # Validate password strength
            is_strong, errors = validate_password_strength(user_data['password'])
            if not is_strong:
                return None, f"Password requirements not met: {'; '.join(errors)}"
            
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data['email'].lower()) | 
                (User.phone == formatted_phone)
            ).first()
            
            if existing_user:
                return None, "User with this email or phone already exists"
            
            # Check if license number already exists
            existing_vet = Veterinarian.query.filter_by(license_no=user_data['license_no']).first()
            if existing_vet:
                return None, "Veterinarian with this license number already exists"
            
            # Create veterinarian
            vet = Veterinarian(
                name=user_data['name'].strip(),
                email=user_data['email'].lower().strip(),
                phone=formatted_phone,
                user_type=UserRole.VETERINARIAN,
                status=UserStatus.PENDING,  # Requires admin approval
                license_no=user_data['license_no'],
                specialization=user_data.get('specialization'),
                qualification=user_data.get('qualification'),
                experience_years=user_data.get('experience_years'),
                clinic_name=user_data.get('clinic_name'),
                clinic_address=user_data.get('clinic_address'),
                consultation_fee=user_data.get('consultation_fee'),
                address=user_data.get('address')
            )
            
            vet.set_password(user_data['password'])
            
            db.session.add(vet)
            db.session.commit()
            
            current_app.logger.info(f"Veterinarian created: {vet.email}")
            return vet, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create veterinarian: {str(e)}")
            return None, f"Failed to create veterinarian: {str(e)}"
    
    @staticmethod
    def create_admin(user_data, created_by_admin_id=None):
        """Create a new admin user (admin only operation)."""
        try:
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'password', 'employee_id']
            valid, missing = validate_required_fields(user_data, required_fields)
            if not valid:
                return None, f"Missing required fields: {', '.join(missing)}"
            
            # Validate email format
            if not validate_email_format(user_data['email']):
                return None, "Invalid email format"
            
            # Validate phone number
            formatted_phone = format_phone_number(user_data['phone'])
            if not validate_phone_number(formatted_phone):
                return None, "Invalid phone number format"
            
            # Validate password strength
            is_strong, errors = validate_password_strength(user_data['password'])
            if not is_strong:
                return None, f"Password requirements not met: {'; '.join(errors)}"
            
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data['email'].lower()) | 
                (User.phone == formatted_phone)
            ).first()
            
            if existing_user:
                return None, "User with this email or phone already exists"
            
            # Check if employee ID already exists
            existing_admin = Admin.query.filter_by(employee_id=user_data['employee_id']).first()
            if existing_admin:
                return None, "Admin with this employee ID already exists"
            
            # Create admin
            admin = Admin(
                name=user_data['name'].strip(),
                email=user_data['email'].lower().strip(),
                phone=formatted_phone,
                user_type=UserRole.ADMIN,
                status=UserStatus.ACTIVE,  # Admins are immediately active
                email_verified=True,  # Admins are pre-verified
                phone_verified=True,
                employee_id=user_data['employee_id'],
                department=user_data.get('department'),
                designation=user_data.get('designation'),
                permissions=user_data.get('permissions', '["user_management", "system_admin"]'),
                address=user_data.get('address')
            )
            
            admin.set_password(user_data['password'])
            
            db.session.add(admin)
            db.session.commit()
            
            current_app.logger.info(f"Admin created: {admin.email} by admin {created_by_admin_id}")
            return admin, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create admin: {str(e)}")
            return None, f"Failed to create admin: {str(e)}"
    
    @staticmethod
    def initiate_user_verification(user, verification_type='both'):
        """Initiate verification process for user."""
        try:
            # Generate OTP
            otp_code = OTPService.generate_otp_for_user(user, 'verification')
            
            success_messages = []
            
            # Send SMS if phone verification requested
            if verification_type in ['phone', 'both']:
                sms_success, sms_message = SMSService.send_otp_sms(user.phone, otp_code, user.name)
                if sms_success:
                    success_messages.append("OTP sent to phone")
                else:
                    current_app.logger.warning(f"SMS sending failed for {user.email}: {sms_message}")
            
            # Send email if email verification requested
            if verification_type in ['email', 'both']:
                email_success, email_message = EmailService.send_verification_email(user.email, otp_code, user.name)
                if email_success:
                    success_messages.append("OTP sent to email")
                else:
                    current_app.logger.warning(f"Email sending failed for {user.email}: {email_message}")
            
            if success_messages:
                return True, "; ".join(success_messages), otp_code
            else:
                return False, "Failed to send verification code", None
            
        except Exception as e:
            current_app.logger.error(f"Failed to initiate verification for {user.email}: {str(e)}")
            return False, f"Verification initiation failed: {str(e)}", None
    
    @staticmethod
    def verify_user_account(user, otp_code, verification_type='both'):
        """Verify user account with OTP."""
        try:
            # Verify OTP
            valid, message = OTPService.verify_user_otp(user, otp_code)
            if not valid:
                return False, message
            
            # Mark user as verified
            if verification_type in ['email', 'both']:
                user.email_verified = True
            
            if verification_type in ['phone', 'both']:
                user.phone_verified = True
            
            # Activate user if both email and phone are verified
            if user.email_verified and user.phone_verified:
                user.status = UserStatus.ACTIVE
            
            # Clear OTP
            OTPService.clear_user_otp(user)
            
            db.session.commit()
            
            # Send welcome messages
            if user.status == UserStatus.ACTIVE:
                SMSService.send_welcome_sms(user.phone, user.name)
                EmailService.send_welcome_email(user.email, user.name)
            
            current_app.logger.info(f"User verified successfully: {user.email}")
            return True, "Account verified successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to verify user {user.email}: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    @staticmethod
    def update_user_profile(user, update_data):
        """Update user profile data."""
        try:
            # Fields that can be updated by user
            updatable_fields = {
                'name', 'address', 'profile_image'
            }
            
            # Role-specific updatable fields
            if hasattr(user, 'farm_name'):  # Farmer
                updatable_fields.update({
                    'farm_name', 'farm_size', 'farm_type', 'district', 'state', 'pincode'
                })
            elif hasattr(user, 'license_no'):  # Veterinarian
                updatable_fields.update({
                    'specialization', 'qualification', 'experience_years', 
                    'clinic_name', 'clinic_address', 'consultation_fee'
                })
            elif hasattr(user, 'employee_id'):  # Admin
                updatable_fields.update({
                    'department', 'designation'
                })
            
            # Update allowed fields
            updated_fields = []
            for field, value in update_data.items():
                if field in updatable_fields and hasattr(user, field):
                    setattr(user, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                db.session.commit()
                current_app.logger.info(f"Profile updated for {user.email}: {', '.join(updated_fields)}")
                return True, f"Profile updated: {', '.join(updated_fields)}"
            else:
                return False, "No valid fields to update"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update profile for {user.email}: {str(e)}")
            return False, f"Profile update failed: {str(e)}"
    
    @staticmethod
    def deactivate_user(user, reason=None):
        """Deactivate user account."""
        try:
            user.status = UserStatus.INACTIVE
            user.is_active = False
            
            db.session.commit()
            
            current_app.logger.info(f"User deactivated: {user.email}, Reason: {reason}")
            return True, "User account deactivated"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to deactivate user {user.email}: {str(e)}")
            return False, f"Deactivation failed: {str(e)}"
    
    @staticmethod
    def reactivate_user(user):
        """Reactivate user account."""
        try:
            if user.is_verified():
                user.status = UserStatus.ACTIVE
            else:
                user.status = UserStatus.PENDING
            
            user.is_active = True
            
            db.session.commit()
            
            current_app.logger.info(f"User reactivated: {user.email}")
            return True, "User account reactivated"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to reactivate user {user.email}: {str(e)}")
            return False, f"Reactivation failed: {str(e)}"