"""
Application-wide constants to avoid magic numbers.

This module centralizes all hardcoded values used throughout the application.
Using named constants improves code readability and maintainability.
"""


class PaginationDefaults:
    """Default pagination limits for list endpoints"""
    
    # Default page sizes
    DEFAULT_LIMIT_SMALL = 10    # For activity feeds, small lists
    DEFAULT_LIMIT_MEDIUM = 20   # For AB tests, moderate lists
    DEFAULT_LIMIT_LARGE = 50    # For campaigns, assets, most paginated endpoints
    DEFAULT_LIMIT_COMMENTS = 100  # For comment analysis
    
    # Maximum page sizes (prevent excessive data transfer)
    MAX_LIMIT_SMALL = 50
    MAX_LIMIT_MEDIUM = 100
    MAX_LIMIT_LARGE = 200
    MAX_LIMIT_COMMENTS = 500
    
    # Default skip/offset
    DEFAULT_SKIP = 0
    
    # Page-based pagination
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 50
    MAX_PER_PAGE = 100


class FileLimits:
    """File size limits in bytes"""
    
    # Base units
    KB = 1024
    MB = 1024 * 1024
    
    # Specific file type limits
    MAX_LOGO_SIZE_BYTES = 5 * MB       # 5MB for logos
    MAX_PROFILE_SIZE_BYTES = 5 * MB     # 5MB for profile images
    MAX_CONTENT_SIZE_BYTES = 50 * MB    # 50MB for videos/large content
    MAX_TEMP_FILE_SIZE_BYTES = 50 * MB  # 50MB for temporary files
    MAX_ATTACHMENT_SIZE_BYTES = 10 * MB # 10MB for general attachments/uploads
    
    # Human-readable sizes (for error messages)
    MAX_LOGO_SIZE_MB = 5
    MAX_PROFILE_SIZE_MB = 5
    MAX_CONTENT_SIZE_MB = 50
    MAX_TEMP_FILE_SIZE_MB = 50
    MAX_ATTACHMENT_SIZE_MB = 10


class TimeRangeDefaults:
    """Default time ranges for analytics and historical queries"""
    
    DEFAULT_DAYS_SHORT = 7    # 1 week
    DEFAULT_DAYS_MEDIUM = 30  # 1 month
    MAX_DAYS_MEDIUM = 90      # 3 months


class OTPDefaults:
    """OTP/security related constants"""
    
    OTP_LENGTH = 6
    OTP_MAX_VALUE = 1000000  # For randbelow(1000000) to generate 6-digit OTP


class ValidationDefaults:
    """Input validation constants"""
    
    # MongoDB ObjectId
    OBJECTID_LENGTH = 24
    OBJECTID_CHARSET = '0123456789abcdefABCDEF'
