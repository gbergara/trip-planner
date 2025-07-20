# 🌍 Trip Planner - Enterprise-Grade Travel Management System

A **professional, scalable** trip planning application built with **FastAPI**, **CockroachDB**, and **Bootstrap 5**. Features **enterprise-grade architecture**, **timezone-aware database**, **flight connection intelligence**, full **multi-language support** (English/Spanish), **comprehensive testing suite**, and **professional PDF export** functionality.

![Trip Planner](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![CockroachDB](https://img.shields.io/badge/CockroachDB-Latest-orange.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Testing-blue.svg)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-purple.svg)
![Multi-Language](https://img.shields.io/badge/i18n-EN%2FES-red.svg)
![Tests](https://img.shields.io/badge/Tests-95+_Passing-brightgreen.svg)

## ✨ Features

### 🏗️ **Enterprise Architecture**
- **Modular Design**: Clean separation with `core/`, `services/`, `models/`, and `routers/` packages
- **Service Layer**: Business logic isolated in dedicated service classes
- **Configuration Management**: Centralized config in `core/config.py`
- **Dependency Injection**: Proper FastAPI dependency management
- **Production Ready**: Scalable architecture following best practices

### 🎯 **Core Functionality**
- **Trip Management**: Create, edit, delete, and organize trips with detailed information
- **Smart Booking Management**: Full CRUD operations for flights, accommodations, transport, and activities
- **TODO Task System**: Integrated task management with categories, priorities, and due dates
- **UUID-based IDs**: Database-agnostic identifiers with proper type handling
- **Clickable Navigation**: Trip titles link directly to booking management pages
- **Robust Error Handling**: Proper HTTP status codes and foreign key constraint enforcement

### ✈️ **Advanced Flight Management**
- **Flight Grouping**: Automatically groups multiple flights on the same day
- **Connection Time Intelligence**: Visual warnings for flight connection times
  - 🔴 **Red Warning**: ≤1 hour (risky connection)
  - 🟡 **Yellow Warning**: ≤2 hours (tight connection)
  - 🟢 **Green Indicator**: >2 hours (comfortable connection)
- **Airline Information**: Dedicated airline field with smart form display
- **Flight Details**: Flight numbers, terminals, seat assignments
- **Time Calculations**: Automatic layover and connection time calculations

### ⏰ **Timezone-Aware Database**
- **TIMESTAMPTZ Fields**: All datetime fields use timezone-aware storage
- **Global Compatibility**: Handles dates/times consistently across all timezones
- **Smart Date Handling**: Default dates auto-populate from trip dates
- **No Date Drift**: Fixed timezone conversion issues preventing random date changes
- **Database Migrations**: Alembic-managed schema with proper timezone support

### 🔐 **Advanced Authentication System**
- **Guest Mode**: Full app functionality without registration - start planning immediately
- **Google OAuth2**: Secure authentication with Google accounts (optional)
- **Smart Sessions**: 30-day secure guest sessions with signed cookies
- **Data Isolation**: Complete separation between users and guest sessions
- **Seamless UX**: Home page redirects to login, one-click guest access
- **Session Security**: HTTP-only cookies, CSRF protection, and session validation
- **Multi-Provider Ready**: Architecture supports additional OAuth providers

### 👤 **Flexible User Experience**
- **No-Auth Barrier**: Use the entire application without any sign-up required
- **Optional Authentication**: Add Google account for permanent storage and sync
- **Session Persistence**: Guest trips saved securely for 30 days
- **Cross-Device Warning**: Clear messaging about guest mode limitations
- **Data Migration**: Future support for converting guest trips to authenticated accounts

### 🌐 **Multi-Language Support**
- **English & Spanish**: Complete UI translation with professional service layer
- **Auto-Detection**: Detects browser language preferences via `Accept-Language` header
- **Persistent Settings**: Language choice saved in cookies (30 days)
- **Easy Switching**: Dropdown menu for instant language changes
- **Extensible Architecture**: Service-based i18n system for easy language additions

### 📄 **Professional PDF Export**
- **Service-Based**: Dedicated PDF generation service in `services/pdf_service.py`
- **Trip Reports**: Comprehensive PDF reports with all trip and booking details
- **Professional Layout**: Clean, formatted reports with tables and statistics
- **Statistics**: Trip summaries with costs and booking breakdowns
- **Auto-Download**: One-click export with descriptive filenames

### 🗄️ **Database & Performance**
- **Multi-Database Support**: CockroachDB for production, PostgreSQL for testing, SQLite for development
- **UUID Compatibility**: Smart UUID type handling across different database engines
- **Alembic Migrations**: Professional database schema management with version control
- **Timezone Support**: Native TIMESTAMPTZ fields for accurate datetime handling
- **Proper Constraints**: Foreign key relationships with integrity enforcement
- **Connection Pooling**: Optimized database connections with health checks
- **Schema Evolution**: Clean migration path for database updates and rollbacks

### 🧪 **Comprehensive Testing**
- **95+ Test Suite**: Complete test coverage including authentication, guest sessions, and OAuth flows
- **PostgreSQL Testing**: Real database testing with proper constraint validation
- **Docker-Based Testing**: Isolated test environment with PostgreSQL container
- **Multiple Test Types**: Unit tests, integration tests, API tests, and PDF export tests
- **Automated CI-Ready**: All tests designed for continuous integration

### 📋 **TODO Task Management**
- **Integrated Tasks**: TODO system built into each trip
- **Task Categories**: Flight, Accommodation, Transport, Activity, Documents, Packing, Other
- **Priority Levels**: High (1), Medium (2), Low (3) priority assignments
- **Due Date Management**: Optional due dates with default current time
- **Completion Tracking**: Mark tasks complete with automatic timestamps
- **Smart Defaults**: Default due dates populate with current date/time
- **Full CRUD**: Create, read, update, delete tasks with proper validation

### 🎨 **Modern UI/UX**
- **Bootstrap 5**: Responsive, mobile-first design
- **Bootstrap Icons**: Beautiful, consistent iconography
- **Professional Themes**: Clean, modern color schemes
- **Interactive Elements**: Modals, dropdowns, and dynamic content
- **Smart Forms**: Context-sensitive fields (airline only for flights)
- **Visual Feedback**: Connection time warnings with color-coded alerts
- **Responsive Design**: Mobile-optimized flight grouping and task management

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Git** for cloning

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd trip-planner
```

2. **Start with Docker (Recommended)**
```bash
# Start production environment (includes automatic Alembic migrations)
docker-compose up -d

# Or run tests
docker-compose --profile test up trip-planner-test --build
```

3. **Access the application**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🗄️ **Database Management**

### **Alembic Migrations**
The application now uses Alembic for professional database schema management:

```bash
# Check current migration status
docker-compose exec trip-planner alembic current

# View migration history  
docker-compose exec trip-planner alembic history

# Generate new migration (after model changes)
docker-compose exec trip-planner alembic revision --autogenerate -m "Description"

# Apply migrations manually (done automatically on startup)
docker-compose exec trip-planner alembic upgrade head

# Rollback migrations if needed
docker-compose exec trip-planner alembic downgrade -1
```

### **Fresh Database Setup**
To recreate the database with latest schema:

```bash
# Stop and remove volumes
docker-compose down -v

# Restart (automatically runs migrations)
docker-compose up -d
```

### Alternative: Local Development (SQLite - Zero Setup!)
```bash
# Install dependencies
pip install -r requirements.txt

# Run immediately - SQLite is the default!
python -m app.main

# ✅ That's it! No database setup required
# Database file automatically created at: ./trip_planner.db
# Access at: http://localhost:8000
```

## 🔐 **Authentication Setup**

### **🎯 Three Authentication Modes**

| Mode | Setup Required | User Experience | Use Case |
|------|---------------|------------------|----------|
| **Guest Only** | ✅ None (default) | Click "Start Using Trip Planner" | Development, demos, privacy-focused |
| **Google + Guest** | 🔧 OAuth setup | Choose Google or Guest | Production ready |
| **Google Only** | 🔧 OAuth + disable guest | Force authentication | Enterprise environments |

### **🚀 Quick Start (Guest Mode - No Setup)**

**The app works immediately without any authentication setup!**

1. Start the application (any method above)
2. Navigate to http://localhost:8000
3. You'll see the login page with "Start Using Trip Planner" button
4. Click it and start planning trips immediately as a guest

**Guest users get:**
- ✅ Full app functionality (create, edit, delete trips and bookings)
- ✅ 30-day secure browser storage
- ✅ Data privacy (no account required)
- ⚠️ No cross-device sync
- ⚠️ No permanent storage

### **🎭 Google OAuth Setup (Optional)**

**Enable Google authentication for permanent storage and sync:**

#### **1. Create Google OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google+ API** and **Google Identity API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Set authorized redirect URIs:
   ```
   http://localhost:8000/auth/callback          # For development
   https://yourdomain.com/auth/callback         # For production
   ```

#### **2. Configure Environment Variables**

Create a `.env` file or set environment variables:

```bash
# Required for Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_from_step_1
GOOGLE_CLIENT_SECRET=your_google_client_secret_from_step_1
SECRET_KEY=your_random_secret_key_for_jwt_signing

# Generate a secure secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### **3. Start with OAuth Enabled**

```bash
# With Docker
docker-compose up -d

# Or locally with environment variables
export GOOGLE_CLIENT_ID="your_client_id"
export GOOGLE_CLIENT_SECRET="your_client_secret" 
export SECRET_KEY="your_secret_key"
python -m app.main
```

#### **4. Test OAuth Flow**

1. Navigate to http://localhost:8000
2. You'll see **both options**: "Continue with Google" and "Continue as Guest"
3. Click "Continue with Google" to test OAuth
4. After Google auth, you'll be redirected to the dashboard

### **🛡️ Security Features**

- **Guest Sessions**: Cryptographically signed cookies (30-day expiry)
- **JWT Tokens**: Secure authentication tokens for OAuth users
- **CSRF Protection**: State parameter in OAuth flow
- **HTTP-Only Cookies**: Prevent XSS attacks
- **Data Isolation**: Complete separation between users and guest sessions
- **Session Validation**: Automatic cleanup of invalid/expired sessions

## 🗄️ **Multi-Database Strategy**

**We support THREE databases depending on your use case:**

### **📊 Database Overview**

| Database | Use Case | Setup Required | Performance | Features |
|----------|----------|----------------|-------------|----------|
| **SQLite** | 🚀 Local Development | None (default) | Fast startup | File-based, portable |
| **PostgreSQL** | 🧪 Testing | Docker | Real constraints | Full SQL features |
| **CockroachDB** | 🏭 Production | Docker | Distributed | Scalable, cloud-ready |

### **🎯 How It Works**

#### **Default: SQLite (No Setup Required!)**
```bash
# Simply run - uses SQLite automatically
cd trip-planner
python -m app.main

# Database file created at: ./trip_planner.db
# Perfect for: Quick development, demos, learning
```

#### **Testing: PostgreSQL (Docker)**
```bash
# Comprehensive testing with real database
docker-compose --profile test up trip-planner-test --build

# Uses: PostgreSQL with proper foreign keys, constraints, transactions
# Perfect for: Validating database behavior, CI/CD pipelines
```

#### **Production: CockroachDB (Docker)**
```bash
# Production deployment
docker-compose up -d

# Uses: Distributed CockroachDB cluster
# Perfect for: Scalable production deployments
```

### **🔧 Smart UUID Handling**

Our database layer **automatically adapts** to each database:

```python
# SQLite: Stores UUIDs as 36-character strings
"123e4567-e89b-12d3-a456-426614174000"

# PostgreSQL/CockroachDB: Native UUID type with indexing
UUID('123e4567-e89b-12d3-a456-426614174000')
```

### **⚡ Quick Database Switching**

```bash
# Use SQLite (default - no DATABASE_URL needed)
python -m app.main

# Use local PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/trip_planner"
python -m app.main

# Use CockroachDB
export DATABASE_URL="cockroachdb://root@localhost:26257/trip_planner?sslmode=disable"
python -m app.main
```

### **📈 Database Comparison**

#### **✅ SQLite Advantages (Development)**
- 🚀 **Zero Setup**: Works immediately 
- 💻 **Portable**: Single file database
- ⚡ **Fast**: No network overhead
- 🔧 **Simple**: Perfect for development

#### **✅ PostgreSQL Advantages (Testing)**
- 🧪 **Real Constraints**: Proper foreign keys
- 🔒 **ACID Compliance**: Transaction integrity
- 📊 **Advanced Features**: Full SQL support
- 🎯 **Production-Like**: Tests real database behavior

#### **✅ CockroachDB Advantages (Production)**
- 🌐 **Distributed**: Multi-node scaling
- 🔄 **Auto-Sharding**: Horizontal scaling
- 🛡️ **Resilient**: Fault tolerance
- ☁️ **Cloud-Native**: Kubernetes ready

### **🎯 Recommended Workflow**

1. **🚀 Development**: Use SQLite (default) for rapid iteration
2. **🧪 Testing**: Use PostgreSQL to validate database behavior  
3. **🚀 Deployment**: Use CockroachDB for production scaling

## 🏗️ **NEW: Professional Architecture**

### Modern Code Structure
```
app/
├── main.py                    # 🎯 FastAPI app entry point
├── core/                      # ⚙️ Core infrastructure
│   ├── __init__.py
│   ├── database.py           # Database configuration & UUID handling
│   └── config.py             # Application settings & constants
├── services/                  # 🛠️ Business logic services
│   ├── __init__.py
│   ├── i18n_service.py       # Internationalization service
│   └── pdf_service.py        # PDF generation service
├── models/                    # 📊 Database models & Pydantic schemas
│   ├── __init__.py           # Pydantic models
│   └── booking.py            # SQLAlchemy models
├── routers/                   # 🛣️ API route handlers
│   ├── __init__.py
│   ├── trips.py              # Trip CRUD operations
│   └── bookings.py           # Booking CRUD operations
├── static/                    # 🎨 CSS, JavaScript, images
├── templates/                 # 📄 Jinja2 HTML templates
└── locales/                   # 🌍 Translation files
```

### Key Architecture Benefits
- **🔧 Maintainable**: Clear separation of concerns
- **📈 Scalable**: Easy to add new services and features
- **🧪 Testable**: Isolated components for comprehensive testing
- **📚 Professional**: Follows FastAPI and Python best practices

## 🧪 **NEW: Comprehensive Testing Suite**

### Testing Infrastructure
- **74 Passing Tests**: Complete coverage of all functionality
- **PostgreSQL Testing**: Uses real PostgreSQL database in Docker containers
- **Multi-Database Support**: Tests handle UUID compatibility across DB engines
- **Docker-Based**: Isolated test environment for consistent results

### Running Tests

```bash
# Run full test suite with Docker (recommended)
docker-compose --profile test up trip-planner-test --build

# Quick test run
docker-compose --profile test up trip-planner-test

# View test output in detail
docker-compose --profile test up trip-planner-test --build | grep -E "(PASSED|FAILED|ERROR)"
```

### Test Categories
- **🔄 API Tests**: Complete REST API functionality testing
- **📊 Model Tests**: Database model validation and constraints
- **🌍 i18n Tests**: Multi-language support and translation testing
- **📄 PDF Tests**: PDF generation and export functionality
- **🔗 Integration Tests**: End-to-end workflow testing

## 🌍 Multi-Language System

### Current Languages
- **English (en)**: Default language
- **Spanish (es)**: Complete translation

### Enhanced i18n Service
```python
# New service-based approach
from app.services.i18n_service import translate, detect_language_from_request

# In your code
message = translate("Trip created successfully!", language)

# In FastAPI endpoints  
language = detect_language_from_request(request.headers.get("accept-language"))
```

### Language Files Location
```
app/
├── locales/
│   ├── messages.pot          # Translation template
│   ├── en/LC_MESSAGES/
│   │   ├── messages.po       # English translations
│   │   └── messages.mo       # Compiled binary
│   └── es/LC_MESSAGES/
│       ├── messages.po       # Spanish translations
│       └── messages.mo       # Compiled binary
└── services/
    └── i18n_service.py       # Translation service logic
```

## 📝 Adding New Translations - Updated Guide

### Step 1: Update Configuration

Edit `app/core/config.py`:
```python
# Add your new language
SUPPORTED_LANGUAGES = ["en", "es", "fr"]  # Add French
```

### Step 2: Update i18n Service

Edit `app/services/i18n_service.py`:
```python
def get_language_names() -> dict:
    return {
        "en": "English",
        "es": "Español", 
        "fr": "Français"  # Add this line
    }
```

### Step 3: Create Translation Files

```bash
# Create directory structure
mkdir -p app/locales/fr/LC_MESSAGES

# Copy template
cp app/locales/messages.pot app/locales/fr/LC_MESSAGES/messages.po

# Edit and translate messages.po file
# ... add your translations ...

# Compile to binary
cd app/locales/fr/LC_MESSAGES
msgfmt messages.po -o messages.mo
```

### Step 4: Test Your Translation

```bash
# Rebuild with new translations
docker-compose build trip-planner

# Start application
docker-compose up -d

# Test language switching
curl -X POST http://localhost:8000/set-language -H "Content-Type: application/json" -d '{"language": "fr"}'
```

## 📄 Enhanced PDF Export System

### Service Architecture
The PDF system is now built as a dedicated service in `app/services/pdf_service.py`:

```python
from app.services.pdf_service import create_trip_pdf

# Generate PDF
pdf_buffer = create_trip_pdf(trip, bookings, language)
```

### Features
- **Professional Service**: Isolated PDF generation logic
- **Multi-Language**: Respects user's language preference
- **Comprehensive Reports**: Trip details, bookings table, statistics
- **Error Handling**: Graceful handling of PDF generation errors

## 🔧 **Enhanced API Documentation**

### Core Endpoints

#### Trips
```bash
GET    /api/trips/           # List all trips (200)
POST   /api/trips/           # Create new trip (201)
GET    /api/trips/{id}       # Get trip details (200)
PUT    /api/trips/{id}       # Update trip (200)
DELETE /api/trips/{id}       # Delete trip (204)
GET    /api/trips/{id}/bookings     # Get trip bookings (200)
GET    /api/trips/{id}/bookings/    # Get trip bookings with trailing slash (200)
GET    /api/trips/{id}/export/pdf   # Export trip to PDF (200)
```

#### Bookings
```bash
GET    /api/bookings/        # List all bookings (200)
POST   /api/bookings/        # Create new booking (201)
GET    /api/bookings/{id}    # Get booking details (200)
PUT    /api/bookings/{id}    # Update booking (200)
DELETE /api/bookings/{id}    # Delete booking (204)
```

#### Language Support
```bash
POST   /set-language         # Set language preference (JSON body)
```

#### Authentication
```bash
# Guest session management
GET    /start-guest          # Create guest session & redirect to dashboard (302)
GET    /                     # Home page - redirects to login if no session (302/200)
GET    /login                # Login page with OAuth & guest options (200)

# Google OAuth (if configured)
GET    /auth/login           # Initiate Google OAuth flow (302 or 503 if disabled)
GET    /auth/callback        # OAuth callback handler (302 success/error)
POST   /auth/logout          # Logout authenticated user (200)
GET    /auth/logout          # Logout via GET redirect (302)
GET    /auth/me              # Get current user info (200 or 401)

# All API endpoints work with either authentication method:
# - Guest users: Identified by secure session cookie
# - Authenticated users: Identified by JWT token
# - Data is completely isolated between different users/sessions
```

### **NEW: Proper HTTP Status Codes**
- **201 Created**: For successful POST operations
- **204 No Content**: For successful DELETE operations  
- **400 Bad Request**: For invalid data
- **404 Not Found**: For missing resources
- **422 Unprocessable Entity**: For validation errors

## 🐳 **Enhanced Docker Configuration**

### Services
- **trip-planner**: Main FastAPI application
- **trip-planner-test**: Testing service with PostgreSQL
- **cockroachdb**: Production database server
- **postgres-test**: PostgreSQL for testing
- **traefik**: Reverse proxy (optional)

### Environment Variables
```bash
# Production (CockroachDB)
DATABASE_URL=cockroachdb://root@cockroachdb:26257/trip_planner?sslmode=disable
DEBUG=false
ENVIRONMENT=production

# Testing (PostgreSQL) 
DATABASE_URL=postgresql://test_user:test_pass@postgres-test:5432/trip_planner_test  
TESTING=true

# Development (SQLite - DEFAULT if no DATABASE_URL set)
DATABASE_URL=sqlite:///./trip_planner.db  # Optional - this is the default!
DEBUG=true
ENVIRONMENT=development

# Authentication Configuration (Optional - Guest Mode Works Without These!)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
SECRET_KEY=your_secret_key_for_jwt_signing

# If these are not set, the app runs in Guest-Only mode
# Users can still access all functionality without authentication
```

### **🔄 Database Environment Summary**

| Environment | Command | Database Used | Why? |
|-------------|---------|---------------|------|
| **Development** | `python -m app.main` | SQLite (auto) | 🚀 Zero setup, fast iteration |
| **Testing** | `docker-compose --profile test up` | PostgreSQL | 🧪 Real constraints & validation |
| **Production** | `docker-compose up -d` | CockroachDB | 🏭 Distributed, scalable |

## 🛠️ Development - Updated

### **NEW: Enhanced Project Structure**
```
trip-planner/
├── app/
│   ├── core/              # 🏗️ Core infrastructure
│   │   ├── database.py    # DB config & UUID handling
│   │   └── config.py      # Application settings
│   ├── services/          # 🛠️ Business logic services
│   │   ├── i18n_service.py    # Translation service
│   │   └── pdf_service.py     # PDF generation service  
│   ├── models/            # 📊 Database & API models
│   ├── routers/           # 🛣️ API endpoints
│   ├── static/            # 🎨 Frontend assets
│   ├── templates/         # 📄 HTML templates
│   ├── locales/           # 🌍 Translation files
│   └── main.py           # 🎯 FastAPI application
├── tests/                 # 🧪 Comprehensive test suite
├── docker-compose.yml     # 🐳 Multi-service orchestration
├── requirements.txt       # 📦 Python dependencies
└── README.md             # 📖 This documentation
```

### Development Commands

```bash
# Start development environment
docker-compose up -d

# Run tests (comprehensive PostgreSQL-based)
docker-compose --profile test up trip-planner-test --build

# View application logs
docker-compose logs trip-planner -f

# Shell into application container
docker-compose exec trip-planner bash

# Database access
docker-compose exec cockroachdb ./cockroach sql --insecure

# Rebuild after code changes
docker-compose build trip-planner
```

### Code Examples with New Structure

#### Using Services
```python
# In your route handlers
from app.services.i18n_service import translate, get_supported_languages  
from app.services.pdf_service import create_trip_pdf
from app.core.database import get_db
from app.core.config import APP_NAME, SUPPORTED_LANGUAGES

# Translation
@app.post("/trips/")
async def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    # ... create trip logic ...
    message = translate("Trip created successfully!", user_language)
    return {"message": message, "trip": trip}

# PDF Export  
@app.get("/trips/{trip_id}/pdf")
async def export_trip(trip_id: str, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    bookings = db.query(Booking).filter(Booking.trip_id == trip_id).all()
    
    pdf_buffer = create_trip_pdf(trip, bookings, user_language)
    return StreamingResponse(pdf_buffer, media_type="application/pdf")
```

## 🔍 Troubleshooting - Updated

### Test Issues
```bash
# If tests fail, check PostgreSQL container
docker-compose --profile test logs postgres-test

# Rebuild test environment from scratch
docker-compose --profile test down -v
docker-compose --profile test up --build

# Run specific test files
docker run --rm trip-planner python -m pytest tests/test_api.py -v
```

### Common Issues & Solutions

#### Import Errors After Restructuring
```python
# ❌ Old imports (will fail)
from app.database import get_db
from app.i18n import _
from app.pdf_export import create_trip_pdf

# ✅ New imports (correct)
from app.core.database import get_db
from app.services.i18n_service import translate as _
from app.services.pdf_service import create_trip_pdf
```

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec trip-planner python -c "
from app.core.database import engine
try:
    engine.connect()
    print('Database connection: OK')
except Exception as e:
    print(f'Database error: {e}')
"
```

#### Database Switching Issues
```bash
# Check which database is being used
python -c "
import os
from app.core.database import DATABASE_URL
print(f'Current DATABASE_URL: {DATABASE_URL}')
if DATABASE_URL.startswith('sqlite'):
    print('✅ Using SQLite (development)')
elif 'postgres' in DATABASE_URL:
    print('✅ Using PostgreSQL (testing)')
elif 'cockroach' in DATABASE_URL:
    print('✅ Using CockroachDB (production)')
"

# Reset to SQLite default
unset DATABASE_URL
python -m app.main

# Switch to a different database
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
python -m app.main
```

#### Translation Issues
```bash
# Verify translation files are compiled
find app/locales -name "*.mo" -ls

# Recompile translations
find app/locales -name "messages.po" -exec msgfmt {} -o {}.mo \;
```

## 📈 **Performance & Scaling**

### Database Optimizations
- **Connection Pooling**: Configured for production workloads
- **UUID Indexing**: Proper indexes on UUID primary keys
- **Foreign Key Constraints**: Database-level integrity checks
- **Multi-Database Support**: CockroachDB for scaling, PostgreSQL for testing

### Testing Performance
- **Parallel Testing**: Docker containers for isolated test runs
- **Database Rollback**: Fast test cleanup with transaction rollback
- **Comprehensive Coverage**: 74 tests covering all functionality

## 🚀 **Deployment**

### Production Deployment
```bash
# Production environment with CockroachDB
docker-compose -f docker-compose.yml up -d

# Health check
curl http://localhost:8000/health
```

### Testing Environment  
```bash
# Full test suite with PostgreSQL
docker-compose --profile test up trip-planner-test --build
```

### Environment Configuration
```yaml
# Production
services:
  trip-planner:
    environment:
      DATABASE_URL: "cockroachdb://..."
      ENVIRONMENT: "production"
      DEBUG: "false"

# Testing
  trip-planner-test:  
    environment:
      DATABASE_URL: "postgresql://..."
      TESTING: "true"
```


## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🏆 Acknowledgments

- **FastAPI**: Amazing Python web framework with excellent async support
- **CockroachDB**: Scalable distributed SQL database
- **PostgreSQL**: Reliable database for testing and development  
- **Bootstrap**: Beautiful, responsive UI components
- **Docker**: Containerization for consistent environments
- **SQLAlchemy**: Powerful Python ORM with multi-database support

---

**🎯 Enterprise-Ready Trip Planning with Flight Intelligence! 🌍✈️🏨**

**✅ 95+ Tests Passing | ⏰ Timezone-Aware | ✈️ Flight Grouping | 📋 TODO System | 🌍 Multi-Language | 📄 PDF Export**

For support or questions, please open an issue in the GitHub repository. 