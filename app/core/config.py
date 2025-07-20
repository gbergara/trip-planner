"""
Application configuration settings.

This module contains configuration constants and settings
used throughout the trip planner application.
"""

import os
from typing import List

# Application settings
APP_NAME = "Trip Planner API"
APP_VERSION = "2.1.0"
APP_DESCRIPTION = """
🧳 **Trip Planner** - A comprehensive travel management platform with intelligent booking organization.

## ✨ **Key Features**

### 🛫 **Smart Flight Management**
- **Auto-generated titles** in "Source → Destination" format
- **Intelligent flight grouping** by date with connection time analysis
- **Color-coded warnings** for tight connections (Red ≤1hr, Yellow ≤2hrs, Green >2hrs)
- **Airline tracking** with dedicated fields for flight bookings

### 🌍 **Global Timezone Support**
- **TIMESTAMPTZ database fields** for accurate worldwide datetime handling
- **Alembic migrations** for professional schema management with rollback support
- **No date drift** - consistent timezone handling between frontend and backend

### 📋 **Integrated TODO System**
- **Task management** within each trip with due dates and priorities
- **7 categories**: Flight, Accommodation, Transport, Activity, Documents, Packing, Other
- **3-level priority system** with visual indicators and completion tracking

### 🔐 **Flexible Authentication**
- **Google OAuth2** integration for permanent account sync
- **Guest mode** with 30-day session storage for quick access
- **Cross-device syncing** for authenticated users

### 🎯 **Enhanced User Experience**
- **Multi-language support** (English, Spanish) with browser detection
- **PDF trip reports** with comprehensive booking summaries
- **Mobile-optimized** responsive design with modern UI
- **Real-time validation** and smart form defaults

### 🏗️ **Professional Architecture**
- **Three-database strategy**: SQLite (dev), PostgreSQL (test), CockroachDB (prod)
- **Service layer architecture** with clean separation of concerns
- **Comprehensive testing** with 95+ test coverage
- **Docker containerization** with development and production configurations

## 📊 **API Capabilities**
- **RESTful endpoints** for trips, bookings, todos, and authentication
- **UUID-based identifiers** with proper database constraints
- **JSON responses** with comprehensive error handling
- **OpenAPI 3.0 specification** with interactive documentation
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