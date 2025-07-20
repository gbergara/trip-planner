import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Database URL - check environment variable first, fallback to SQLite for local dev only
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trip_planner.db")

def get_uuid_type():
    """Get the appropriate UUID type - PostgreSQL native UUID for tests and production."""
    if DATABASE_URL.startswith("sqlite"):
        # Only for local development - use string storage
        from sqlalchemy import String, TypeDecorator
        
        class SQLiteUUID(TypeDecorator):
            impl = String
            cache_ok = True
            
            def load_dialect_impl(self, dialect):
                return dialect.type_descriptor(String(36))
            
            def process_bind_param(self, value, dialect):
                if value is None:
                    return value
                return str(value)
            
            def process_result_value(self, value, dialect):
                if value is None:
                    return value
                return str(value)
        
        return SQLiteUUID()
    else:
        # PostgreSQL/CockroachDB - use native UUID
        return UUID(as_uuid=True)

def get_datetime_type():
    """Get the appropriate datetime type with timezone support."""
    if DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support TIMESTAMP WITH TIME ZONE, use regular DateTime
        from sqlalchemy import DateTime
        return DateTime
    else:
        # PostgreSQL/CockroachDB - use TIMESTAMP WITH TIME ZONE
        from sqlalchemy.dialects.postgresql import TIMESTAMP
        return TIMESTAMP(timezone=True)

# Create engine with appropriate settings based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings (local development only)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL/CockroachDB settings
    connect_args = {}
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "echo": os.getenv("DB_DEBUG", "false").lower() == "true"
    }
    
    # Special handling for CockroachDB
    if "cockroach" in DATABASE_URL.lower() or "26257" in DATABASE_URL:
        # CockroachDB-specific settings
        connect_args["options"] = "-c timezone=UTC"
        engine_kwargs["connect_args"] = connect_args
        engine_kwargs["pool_timeout"] = 20
        engine_kwargs["pool_size"] = 20
    
    engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize database tables
def create_tables():
    """Create database tables - should be called after models are defined."""
    Base.metadata.create_all(bind=engine) 