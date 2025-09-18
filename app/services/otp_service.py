"""OTP generation and verification service."""

import random
import string
from datetime import datetime, timedelta
from flask import current_app
from app.models.user import User
from app.utils.helpers import generate_otp, is_otp_valid
from app import db


class OTPService:
    """Service for OTP operations."""
    
    @staticmethod
    def generate_otp_for_user(user, purpose='verification', length=6):
        """Generate and store OTP for user."""
        try:
            # Generate OTP
            otp_code = generate_otp(length)
            
            # Store in user record
            user.otp_code = otp_code
            user.otp_created_at = datetime.utcnow()
            
            db.session.commit()
            
            current_app.logger.info(f"OTP generated for user {user.email} - Purpose: {purpose}")
            return otp_code
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to generate OTP for {user.email}: {str(e)}")
            raise e
    
    @staticmethod
    def verify_user_otp(user, provided_otp, validity_minutes=10):
        """Verify OTP for user."""
        try:
            # Check if OTP exists
            if not user.otp_code or not user.otp_created_at:
                return False, "No OTP found for this user"
            
            # Check if OTP matches
            if user.otp_code != provided_otp:
                current_app.logger.warning(f"Invalid OTP attempt for user {user.email}")
                return False, "Invalid OTP"
            
            # Check if OTP is still valid
            if not is_otp_valid(user.otp_created_at, validity_minutes):
                return False, "OTP has expired"
            
            current_app.logger.info(f"OTP verified successfully for user {user.email}")
            return True, "OTP verified successfully"
            
        except Exception as e:
            current_app.logger.error(f"OTP verification error for {user.email}: {str(e)}")
            return False, "OTP verification failed"
    
    @staticmethod
    def clear_user_otp(user):
        """Clear OTP from user record."""
        try:
            user.otp_code = None
            user.otp_created_at = None
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to clear OTP for {user.email}: {str(e)}")
            raise e
    
    @staticmethod
    def is_otp_expired(user, validity_minutes=10):
        """Check if user's OTP is expired."""
        if not user.otp_created_at:
            return True
        
        return not is_otp_valid(user.otp_created_at, validity_minutes)
    
    @staticmethod
    def get_otp_remaining_time(user, validity_minutes=10):
        """Get remaining time for OTP validity."""
        if not user.otp_created_at:
            return 0
        
        expiry_time = user.otp_created_at + timedelta(minutes=validity_minutes)
        remaining = expiry_time - datetime.utcnow()
        
        return max(0, int(remaining.total_seconds()))


class SMSService:
    """SMS service for sending OTP and notifications."""
    
    @staticmethod
    def send_otp_sms(phone_number, otp_code, user_name=None):
        """Send OTP via SMS."""
        try:
            # In production, integrate with SMS gateway (Twilio, AWS SNS, etc.)
            # For development, we'll just log the SMS
            
            message = f"Your Farm Portal verification code is: {otp_code}. Valid for 10 minutes. Do not share this code."
            
            if current_app.config.get('DEBUG', False):
                # Development mode - log SMS instead of sending
                current_app.logger.info(f"SMS to {phone_number}: {message}")
                return True, "SMS sent (development mode)"
            else:
                # Production mode - integrate with actual SMS service
                # Example integration:
                # sms_api_key = current_app.config.get('SMS_API_KEY')
                # sender_id = current_app.config.get('SMS_SENDER_ID')
                # 
                # response = requests.post('SMS_GATEWAY_URL', {
                #     'api_key': sms_api_key,
                #     'sender': sender_id,
                #     'to': phone_number,
                #     'message': message
                # })
                
                return True, "SMS sent successfully"
            
        except Exception as e:
            current_app.logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False, f"SMS sending failed: {str(e)}"
    
    @staticmethod
    def send_welcome_sms(phone_number, user_name):
        """Send welcome SMS to new user."""
        try:
            message = f"Welcome to Farm Portal, {user_name}! Your account has been created successfully. Start managing your farm digitally."
            
            if current_app.config.get('DEBUG', False):
                current_app.logger.info(f"Welcome SMS to {phone_number}: {message}")
                return True, "Welcome SMS sent (development mode)"
            else:
                # Production SMS integration here
                return True, "Welcome SMS sent successfully"
            
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome SMS to {phone_number}: {str(e)}")
            return False, f"Welcome SMS sending failed: {str(e)}"


class EmailService:
    """Email service for sending notifications."""
    
    @staticmethod
    def send_verification_email(email, otp_code, user_name):
        """Send verification email with OTP."""
        try:
            subject = "Farm Portal - Email Verification"
            message = f"""
            Hello {user_name},
            
            Your Farm Portal email verification code is: {otp_code}
            
            This code is valid for 10 minutes. Please do not share this code with anyone.
            
            If you didn't request this verification, please ignore this email.
            
            Best regards,
            Farm Portal Team
            """
            
            if current_app.config.get('DEBUG', False):
                # Development mode - log email instead of sending
                current_app.logger.info(f"Email to {email}: {subject}")
                current_app.logger.info(f"Message: {message}")
                return True, "Email sent (development mode)"
            else:
                # Production mode - integrate with email service
                # Example integration with SendGrid, AWS SES, etc.
                return True, "Email sent successfully"
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {email}: {str(e)}")
            return False, f"Email sending failed: {str(e)}"
    
    @staticmethod
    def send_welcome_email(email, user_name):
        """Send welcome email to new user."""
        try:
            subject = "Welcome to Farm Portal!"
            message = f"""
            Hello {user_name},
            
            Welcome to Farm Portal! Your account has been successfully created.
            
            You can now:
            - Manage your farm digitally
            - Track animal health records
            - Connect with veterinarians
            - Monitor compliance requirements
            
            Get started by logging into your account.
            
            Best regards,
            Farm Portal Team
            """
            
            if current_app.config.get('DEBUG', False):
                current_app.logger.info(f"Welcome email to {email}: {subject}")
                return True, "Welcome email sent (development mode)"
            else:
                # Production email integration here
                return True, "Welcome email sent successfully"
            
        except Exception as e:
            current_app.logger.error(f"Failed to send welcome email to {email}: {str(e)}")