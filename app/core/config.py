"""
Application configuration settings.

This module contains configuration constants and settings
used throughout the trip planner application.
"""

import os
from typing import List

# Application settings
APP_NAME = "Trip Planner API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
🧳 **Trip Planner** - A comprehensive travel management platform with intelligent booking organization.
"""

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Database settings (imported from DATABASE_URL in database.py)
DB_DEBUG = os.getenv("DB_DEBUG", "false").lower() == "true"

# Supported languages for i18n
SUPPORTED_LANGUAGES = ["en", "es"]

# Default language
DEFAULT_LANGUAGE = "en"

# File paths
STATIC_DIR = "app/static"
TEMPLATES_DIR = "app/templates" 
LOCALES_DIR = "app/locales"

# PDF Export settings
PDF_TEMP_DIR = "/tmp"
PDF_DEFAULT_PAGESIZE = "A4"

# Authentication settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# JWT settings
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days 