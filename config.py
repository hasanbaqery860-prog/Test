#!/usr/bin/env python3
"""
Configuration file for the IP and Browser Detection API
Supports environment variables and production settings
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # Server settings
    HOST = os.getenv('API_HOST', '0.0.0.0')
    PORT = int(os.getenv('API_PORT', 8080))
    DEBUG = os.getenv('API_DEBUG', 'false').lower() == 'true'
    RELOADER = os.getenv('API_RELOADER', 'false').lower() == 'true'
    
    # API Keys (in production, use environment variables)
    API_KEYS = {
        "web_frontend_key": os.getenv('API_KEY_WEB', "web_1234567890abcdef"),
        "android_app_key": os.getenv('API_KEY_ANDROID', "android_9876543210fedcba"),
        "other_project_key": os.getenv('API_KEY_OTHER', "other_abcdef1234567890")
    }
    
    # Cache settings
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', 10000))
    
    # Performance settings
    MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', 1000))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Security settings
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    ENABLE_CORS = os.getenv('ENABLE_CORS', 'true').lower() == 'true'
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))  # seconds
    
    # Redis settings (for production)
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Monitoring
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))
    
    @classmethod
    def get_api_keys(cls) -> Dict[str, str]:
        """Get API keys dictionary"""
        return cls.API_KEYS
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return not cls.DEBUG and os.getenv('ENVIRONMENT', 'development') == 'production'
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Get cache configuration"""
        return {
            "enabled": cls.CACHE_ENABLED,
            "ttl": cls.CACHE_TTL,
            "max_size": cls.CACHE_MAX_SIZE,
            "redis_enabled": cls.REDIS_ENABLED,
            "redis_config": {
                "host": cls.REDIS_HOST,
                "port": cls.REDIS_PORT,
                "db": cls.REDIS_DB,
                "password": cls.REDIS_PASSWORD
            } if cls.REDIS_ENABLED else None
        }
    
    @classmethod
    def get_rate_limit_config(cls) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            "enabled": cls.RATE_LIMIT_ENABLED,
            "max_requests": cls.MAX_REQUESTS_PER_MINUTE,
            "window": cls.RATE_LIMIT_WINDOW
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    RELOADER = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    RELOADER = False
    LOG_LEVEL = 'WARNING'
    CACHE_ENABLED = True
    REDIS_ENABLED = True
    RATE_LIMIT_ENABLED = True

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    CACHE_ENABLED = False
    RATE_LIMIT_ENABLED = False

# Configuration mapping
configs = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    return configs.get(env, DevelopmentConfig)