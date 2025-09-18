"""Application constants."""

# User roles
USER_ROLES = {
    'FARMER': 'farmer',
    'VETERINARIAN': 'veterinarian',
    'ADMIN': 'admin'
}

# User statuses
USER_STATUSES = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'PENDING': 'pending',
    'SUSPENDED': 'suspended'
}

# Animal species
ANIMAL_SPECIES = {
    'CATTLE': 'cattle',
    'BUFFALO': 'buffalo',
    'GOAT': 'goat',
    'SHEEP': 'sheep',
    'POULTRY': 'poultry',
    'SWINE': 'swine',
    'OTHER': 'other'
}

# Health statuses
HEALTH_STATUSES = {
    'HEALTHY': 'healthy',
    'SICK': 'sick',
    'UNDER_TREATMENT': 'under_treatment',
    'RECOVERING': 'recovering',
    'QUARANTINE': 'quarantine',
    'DECEASED': 'deceased'
}

# API response messages
API_MESSAGES = {
    'SUCCESS': 'Operation successful',
    'CREATED': 'Resource created successfully',
    'UPDATED': 'Resource updated successfully',
    'DELETED': 'Resource deleted successfully',
    'NOT_FOUND': 'Resource not found',
    'UNAUTHORIZED': 'Unauthorized access',
    'FORBIDDEN': 'Access forbidden',
    'VALIDATION_ERROR': 'Validation failed',
    'SERVER_ERROR': 'Internal server error'
}

# Validation rules
VALIDATION_RULES = {
    'PASSWORD_MIN_LENGTH': 8,
    'NAME_MAX_LENGTH': 100,
    'EMAIL_MAX_LENGTH': 120,
    'PHONE_LENGTH': 10,
    'AADHAR_LENGTH': 12,
    'OTP_LENGTH': 6,
    'OTP_VALIDITY_MINUTES': 10,
    'PASSWORD_RESET_VALIDITY_MINUTES': 30
}

# Pagination defaults
PAGINATION = {
    'DEFAULT_PAGE': 1,
    'DEFAULT_PER_PAGE': 20,
    'MAX_PER_PAGE': 100
}

# File upload settings
FILE_UPLOAD = {
    'MAX_SIZE_MB': 16,
    'ALLOWED_IMAGE_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif'},
    'ALLOWED_DOCUMENT_EXTENSIONS': {'pdf', 'doc', 'docx'},
    'UPLOAD_FOLDER': 'app/static/uploads'
}

# SMS/Email templates
NOTIFICATION_TEMPLATES = {
    'SMS_OTP': 'Your Farm Portal verification code is: {otp}. Valid for {validity} minutes. Do not share this code.',
    'SMS_WELCOME': 'Welcome to Farm Portal, {name}! Your account has been created successfully.',
    'EMAIL_VERIFICATION_SUBJECT': 'Farm Portal - Email Verification',
    'EMAIL_WELCOME_SUBJECT': 'Welcome to Farm Portal!'
}

# Indian states for validation
INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry', 'Chandigarh',
    'Dadra and Nagar Haveli and Daman and Diu', 'Lakshadweep',
    'Andaman and Nicobar Islands'
]

# Farm types
FARM_TYPES = [
    'dairy', 'poultry', 'goat', 'sheep', 'cattle', 'buffalo', 'mixed', 'organic', 'other'
]

# Veterinarian specializations
VET_SPECIALIZATIONS = [
    'Large Animal Medicine', 'Small Animal Medicine', 'Poultry Medicine',
    'Dairy Science', 'Animal Reproduction', 'Animal Nutrition',
    'Veterinary Surgery', 'Animal Pathology', 'Public Health',
    'Wildlife Medicine', 'Laboratory Animal Medicine', 'General Practice'
]

# API rate limits
RATE_LIMITS = {
    'LOGIN': '5 per minute',
    'REGISTRATION': '3 per minute', 
    'OTP_REQUEST': '3 per minute',
    'PASSWORD_RESET': '3 per hour',
    'GENERAL_API': '100 per hour',
    'ADMIN_API': '500 per hour'
}

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Database query limits
DATABASE_LIMITS = {
    'MAX_QUERY_RESULTS': 1000,
    'DEFAULT_QUERY_TIMEOUT': 30,
    'BULK_INSERT_BATCH_SIZE': 100
}

# Security settings
SECURITY = {
    'JWT_EXPIRY_HOURS': 1,
    'REFRESH_TOKEN_EXPIRY_DAYS': 30,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION_MINUTES': 15,
    'PASSWORD_HISTORY_COUNT': 5
}