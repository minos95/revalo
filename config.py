import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    
    # ============================================
    # FLASK
    # ============================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_APP = os.environ.get('FLASK_APP') or 'run.py'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # ============================================
    # DATABASE
    # ============================================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://dev_team:azerty123@localhost:5432/ecowaste_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
    }
    
    # ============================================
    # UPLOADS
    # ============================================
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    
    # ============================================
    # EMAIL
    # ============================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@ecowaste.com'
    
    # ============================================
    # SESSION & SECURITY
    # ============================================
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.environ.get('REMEMBER_COOKIE_DAYS', 30)))
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF Protection
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY
    
    # ============================================
    # SUBSCRIPTION
    # ============================================
    SUBSCRIPTION_GRACE_PERIOD_DAYS = int(os.environ.get('SUBSCRIPTION_GRACE_PERIOD_DAYS', 14))
    FREE_PLAN_MAX_LISTINGS = int(os.environ.get('FREE_PLAN_MAX_LISTINGS', 3))
    FREE_PLAN_MAX_TEAM_MEMBERS = int(os.environ.get('FREE_PLAN_MAX_TEAM_MEMBERS', 1))
    FREE_PLAN_COMMISSION_RATE = float(os.environ.get('FREE_PLAN_COMMISSION_RATE', 8.0))
    
    # ============================================
    # PAGINATION
    # ============================================
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    ADMIN_ITEMS_PER_PAGE = int(os.environ.get('ADMIN_ITEMS_PER_PAGE', 50))
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/app.log'
    
    # ============================================
    # CACHE (Optional - for future use)
    # ============================================
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # ============================================
    # RATE LIMITING (Optional)
    # ============================================
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'False').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT') or '100/hour'


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Use local PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://postgres:password@localhost:5432/ecowaste_dev'
    
    # Enable debug toolbar
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Email (print to console in dev)
    MAIL_SUPPRESS_SEND = True


class TestingConfig(Config):
    """Testing configuration"""
    
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:password@localhost:5432/ecowaste_test'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable email sending
    MAIL_SUPPRESS_SEND = True
    
    # Use simple cache for testing
    CACHE_TYPE = 'simple'


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Use production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Logging
    LOG_LEVEL = 'WARNING'
    LOG_FILE = 'logs/production.log'
    
    # Rate limiting
    RATELIMIT_ENABLED = True


class StagingConfig(ProductionConfig):
    """Staging configuration (pre-production)"""
    
    FLASK_ENV = 'staging'
    DEBUG = False
    
    # Use staging database
    SQLALCHEMY_DATABASE_URI = os.environ.get('STAGING_DATABASE_URL') or \
        'postgresql://postgres:password@localhost:5432/ecowaste_staging'
    
    # Enable some debug features for staging
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}